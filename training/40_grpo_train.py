#!/usr/bin/env python3
"""
STAGE 4 of 4 — REINFORCEMENT LEARNING WITH VERIFIABLE REWARD (GRPO)

WHAT THIS STAGE DOES: this is the stage that doesn't exist for most
domains, and is your biggest real advantage. GRPO (Group Relative
Policy Optimization) samples several completions per prompt and
rewards the ones scored higher by a REWARD FUNCTION -- and because
SystemVerilog has a real, free, automatic correctness check
(does it compile? does the assertion construct actually exist?), we
can grade completions with verilator instead of a trained reward
model or human labels. This is "RLVR" (RL with Verifiable Rewards).

REWARD FUNCTION USED HERE: for each generated completion to an
assertion-generation prompt, extract SystemVerilog code and give:
  +1.0 if it compiles AND contains a real `assert property` construct
  +0.3 if it compiles but has no real assertion (e.g. just a comment)
   0.0 if it fails to compile at all

WHEN TO SKIP: if you have very few verifiable-task examples (this
pilot's corpus is small), GRPO's benefit will be minimal and noisy.
Run it anyway to see the mechanics; scale the assertion-generation
portion of your dataset before expecting a real quality lift here.

HARDWARE: this is the most compute-intensive of the four stages
(it runs multiple generations per prompt every step). Expect it to
be slow on a T4 -- keep NUM_GENERATIONS and dataset size small.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import GRPOConfig, GRPOTrainer

ROOT = Path(__file__).parent.parent
DPO_DIR = ROOT / "models" / "dpo-lora"
SFT_DIR = ROOT / "models" / "sft-lora"
OUT_DIR = ROOT / "models" / "grpo-lora"
MAX_SEQ_LEN = 2048


def sv_reward(code: str) -> float:
    if "assert property" not in code:
        base_ok = False
    else:
        base_ok = True
    with tempfile.NamedTemporaryFile(suffix=".sv", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = subprocess.run(
            ["verilator", "--lint-only", "-Wno-fatal", path],
            capture_output=True, text=True, timeout=15,
        )
        compiles = result.returncode == 0
    except Exception:
        compiles = False
    finally:
        os.unlink(path)

    if compiles and base_ok:
        return 1.0
    if compiles and not base_ok:
        return 0.3
    return 0.0


def reward_fn(completions, **kwargs):
    """TRL's GRPOTrainer calls this with a list of generated completions
    (strings) and expects a list of float rewards back, one per completion."""
    rewards = []
    for completion in completions:
        code_blocks = re.findall(r"```(?:systemverilog)?\n(.*?)\n```", completion, re.DOTALL)
        code = code_blocks[0] if code_blocks else completion
        rewards.append(sv_reward(code))
    return rewards


def main():
    start_dir = DPO_DIR if DPO_DIR.exists() else SFT_DIR
    if not start_dir.exists():
        raise SystemExit("Neither dpo-lora nor sft-lora found -- run stages 2 and 3 first.")

    print(f"Loading starting checkpoint for GRPO: {start_dir}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(start_dir), max_seq_length=MAX_SEQ_LEN, load_in_4bit=True,
    )
    FastLanguageModel.for_training(model)

    # Build a small prompt-only dataset from the assertion-generation
    # examples in train.jsonl -- GRPO needs prompts, not full pairs,
    # since it generates its own completions to grade.
    train_path = ROOT / "data" / "train.jsonl"
    full = load_dataset("json", data_files=str(train_path))["train"]
    assertion_prompts = full.filter(lambda ex: ex["task_type"] == "sva_assertion_generation")
    prompts = assertion_prompts.map(lambda ex: {
        "prompt": f"{ex['instruction']}\n\nCode:\n{ex['input']}"
    })
    print(f"Built {len(prompts)} verifiable-reward prompts for GRPO")
    if len(prompts) == 0:
        raise SystemExit("No sva_assertion_generation examples in train.jsonl -- "
                          "generate more via 06_generate_pairs.py before running GRPO.")

    trainer = GRPOTrainer(
        model=model,
        reward_funcs=reward_fn,
        args=GRPOConfig(
            output_dir=str(OUT_DIR),
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            num_generations=4,          # completions sampled per prompt, graded against each other
            max_completion_length=300,
            num_train_epochs=1,
            learning_rate=1e-5,
            logging_steps=1,
            report_to="none",
        ),
        train_dataset=prompts,
        tokenizer=tokenizer,
    )

    print("Starting GRPO training (this is the slowest stage -- be patient)...")
    trainer.train()
    model.save_pretrained(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))
    print(f"GRPO adapter saved -> {OUT_DIR}")
    print("This is your final fine-tuned model. Next: run inference/export_and_serve.sh")


if __name__ == "__main__":
    main()
