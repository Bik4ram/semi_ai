#!/usr/bin/env python3
"""
STAGE 2 of 4 — SUPERVISED FINE-TUNING (SFT)

WHAT THIS STAGE DOES: teaches the model BEHAVIOR -- given an
instruction + input, produce a specific-shaped output. This is where
your real (mechanically-verified) instruction pairs from
data/train.jsonl actually change how the model responds, not just
what it knows.

WHICH MODEL TO START FROM: by default this loads the same base model
CPT started from. If you actually ran 10_cpt_train.py and want to
build on top of it, set START_FROM_CPT = True below -- this is how
you CHAIN the four stages together into one final model.
"""
from pathlib import Path

from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig

ROOT = Path(__file__).parent.parent

# ---- CONFIG ----
BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
START_FROM_CPT = False   # set True to continue from models/cpt-lora instead
MAX_SEQ_LEN = 2048
# -----------------

CPT_DIR = ROOT / "models" / "cpt-lora"
OUT_DIR = ROOT / "models" / "sft-lora"


def format_example(ex):
    return {
        "text": (
            f"### Instruction:\n{ex['instruction']}\n\n"
            f"### Input:\n{ex['input']}\n\n"
            f"### Response:\n{ex['output']}"
        )
    }


def main():
    model_path = str(CPT_DIR) if START_FROM_CPT and CPT_DIR.exists() else BASE_MODEL
    print(f"Loading base model for SFT: {model_path}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=MAX_SEQ_LEN,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model, r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",
    )

    data_files = {"train": str(ROOT / "data" / "train.jsonl")}
    val_path = ROOT / "data" / "val.jsonl"
    if val_path.exists() and val_path.stat().st_size > 0:
        data_files["validation"] = str(val_path)
    dataset = load_dataset("json", data_files=data_files)
    dataset = dataset.map(format_example)

    eval_kwargs = {}
    if "validation" in dataset:
        eval_kwargs = dict(eval_dataset=dataset["validation"])

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        args=SFTConfig(
            output_dir=str(OUT_DIR),
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            num_train_epochs=3,
            learning_rate=2e-4,
            logging_steps=5,
            eval_strategy="steps" if "validation" in dataset else "no",
            eval_steps=10,
            save_strategy="epoch",
            report_to="none",
        ),
        **eval_kwargs,
    )

    print("Starting SFT training...")
    trainer.train()
    model.save_pretrained(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))
    print(f"SFT adapter saved -> {OUT_DIR}")
    print("Next: run 30_dpo_train.py.")


if __name__ == "__main__":
    main()
