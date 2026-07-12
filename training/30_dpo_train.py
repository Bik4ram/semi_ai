#!/usr/bin/env python3
"""
STAGE 3 of 4 — DIRECT PREFERENCE OPTIMIZATION (DPO)

WHAT THIS STAGE DOES: given (prompt, chosen, rejected) triples, shifts
the model's output distribution to prefer "chosen"-style responses.
Unlike full RLHF, DPO needs no separate reward model -- it directly
optimizes against your preference pairs, which is why it's the
pragmatic default for a pilot like this.

This loads the SFT adapter from stage 2 and continues training on top
of it (this is what "chaining stages" means in practice: each stage's
output directory becomes the next stage's input).
"""
from pathlib import Path

from datasets import load_dataset
from unsloth import FastLanguageModel
from trl import DPOTrainer, DPOConfig

ROOT = Path(__file__).parent.parent
SFT_DIR = ROOT / "models" / "sft-lora"
OUT_DIR = ROOT / "models" / "dpo-lora"
MAX_SEQ_LEN = 2048


def main():
    if not SFT_DIR.exists():
        raise SystemExit(f"{SFT_DIR} not found -- run 20_sft_train.py first.")

    print(f"Loading SFT adapter as DPO starting point: {SFT_DIR}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(SFT_DIR),
        max_seq_length=MAX_SEQ_LEN,
        load_in_4bit=True,
    )
    FastLanguageModel.for_training(model)

    dpo_path = ROOT / "data" / "dpo_pairs.jsonl"
    dataset = load_dataset("json", data_files=str(dpo_path))["train"]
    print(f"Loaded {len(dataset)} DPO preference pairs")
    if len(dataset) < 4:
        print("WARNING: very few DPO pairs. This stage will still run, "
              "but treat results as illustrative only until you scale "
              "up 08_generate_dpo_pairs.py's inputs.")

    trainer = DPOTrainer(
        model=model,
        ref_model=None,   # Unsloth handles the implicit reference model via the frozen base + PEFT
        args=DPOConfig(
            output_dir=str(OUT_DIR),
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            num_train_epochs=1,
            learning_rate=5e-5,
            beta=0.1,
            logging_steps=2,
            report_to="none",
        ),
        train_dataset=dataset,
        tokenizer=tokenizer,
    )

    print("Starting DPO training...")
    trainer.train()
    model.save_pretrained(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))
    print(f"DPO adapter saved -> {OUT_DIR}")
    print("Next: optionally run 40_grpo_train.py, then export/serve.")


if __name__ == "__main__":
    main()
