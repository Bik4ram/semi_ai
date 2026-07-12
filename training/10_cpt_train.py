#!/usr/bin/env python3
"""
STAGE 1 of 4 — CONTINUED PRETRAINING (CPT)

WHAT THIS STAGE DOES DIFFERENTLY FROM SFT:
CPT trains on RAW TEXT with the plain next-token-prediction objective
-- no instruction/response format, no "chat" structure. The model
just reads your domain corpus (real RTL + UVM + docs, from
data/cpt_corpus.txt) the same way it read its original pretraining
data, except now that data is 100% semiconductor-focused. This is how
a model absorbs DOMAIN VOCABULARY AND STYLE (SVA idioms, UVM macro
naming, register-map phrasing) -- not behavior. SFT (stage 2) is what
teaches behavior.

WHEN TO SKIP THIS STAGE: if your corpus is small (a few MB, like this
pilot's), CPT's effect will be minor -- the base model already knows
general SystemVerilog syntax. CPT starts to matter once your corpus
is large (100MB+, ideally GB-scale) and/or covers vocabulary the base
model genuinely hasn't seen (obscure internal tool report formats,
company-specific naming conventions). Running it here anyway is
worthwhile purely so you understand the mechanics -- see README.

HARDWARE: designed for a free Google Colab T4 GPU (16GB VRAM) or a
local GPU with >=8GB VRAM using the default 1.5B model. To use the
7B model instead, just change BASE_MODEL below (needs a T4 or better,
still fits via 4-bit QLoRA).
"""
from pathlib import Path

from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig

ROOT = Path(__file__).parent.parent

# ---- CONFIG: change these two lines to scale up later ----
BASE_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"   # swap to "Qwen/Qwen2.5-Coder-7B-Instruct" on a bigger GPU
MAX_SEQ_LEN = 2048
# ------------------------------------------------------------

CPT_CORPUS = ROOT / "data" / "cpt_corpus.txt"
OUT_DIR = ROOT / "models" / "cpt-lora"


def load_cpt_dataset():
    raw = CPT_CORPUS.read_text()
    docs = [d.strip() for d in raw.split("<|endofdoc|>") if len(d.strip()) > 30]
    print(f"Loaded {len(docs)} raw documents for CPT")
    return Dataset.from_dict({"text": docs})


def main():
    print(f"Loading base model for CPT: {BASE_MODEL}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        load_in_4bit=True,
    )

    # For CPT specifically, include embed_tokens/lm_head in the trainable
    # set -- domain vocabulary absorption benefits from touching the
    # embedding layer, unlike pure behavior-shaping SFT/DPO stages below.
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=32,
        lora_dropout=0.0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj",
                         "embed_tokens", "lm_head"],
        use_gradient_checkpointing="unsloth",
    )

    dataset = load_cpt_dataset()

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        args=SFTConfig(
            output_dir=str(OUT_DIR),
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            num_train_epochs=1,          # CPT usually needs only 1-2 passes over raw text
            learning_rate=1e-4,           # lower LR than SFT -- we're nudging knowledge, not behavior
            logging_steps=5,
            save_strategy="epoch",
            report_to="none",
        ),
    )

    print("Starting CPT training...")
    trainer.train()
    model.save_pretrained(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))
    print(f"CPT adapter saved -> {OUT_DIR}")
    print("Next: run 20_sft_train.py, pointing BASE_MODEL at this CPT "
          "checkpoint (see README for how to chain stages).")


if __name__ == "__main__":
    main()
