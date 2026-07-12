# Semiconductor AI Pilot v2 — Fixed, Real, 4-Stage Pipeline

Every script in this repo was actually executed in a sandbox before being included here
(parsing/dedup/labeling/pair-generation/DPO-pairing all ran against a real cloned corpus;
`verilator` and `pyslang` were confirmed installed and working; every `.py` file passed
`python3 -m py_compile` with zero errors). This fixes every broken/faked piece identified
in the previous version's audit. Training scripts (which need a GPU) are syntax-verified
and logically complete, ready to run on your hardware.

## Which of your two setups to use

**Use Google Colab (recommended).** Your 16GB-RAM laptop almost certainly has no CUDA GPU,
and CPU training a 1.5B+ model is painfully slow even for a pilot. Colab's free tier gives you
a T4 GPU (16GB VRAM) for free, which comfortably fits everything below via 4-bit QLoRA.

1. Go to https://colab.research.google.com, upload `Semiconductor_AI_Pipeline.ipynb`
   (or open it from Google Drive after uploading this whole folder there).
2. `Runtime → Change runtime type → T4 GPU`.
3. Upload this entire `semiconductor-ai-v2/` folder into the Colab session (drag-and-drop
   into the file browser on the left, or `git clone` if you push this to your own GitHub repo
   first — recommended so you don't have to re-upload every session).
4. Run cells top to bottom.

Your laptop is still useful for: writing/editing scripts, running the non-GPU stages
(everything in `scripts/`, which is pure CPU/data-engineering work) locally to save Colab time,
and downloading/testing the final quantized model once it's built.

## The four training stages, and what "make room for everything" means concretely

You asked for all four stages — CPT, SFT, DPO, and RL — to actually exist, not be skipped.
Here's what each one does and, honestly, what to expect from each at this small scale:

| Stage | Script | What it teaches the model | Needs | Expected effect at pilot scale |
|---|---|---|---|---|
| 1. CPT (Continued Pretraining) | `training/10_cpt_train.py` | Domain **vocabulary/style** via raw next-token prediction on `data/cpt_corpus.txt` (no instruction format at all) | `data/cpt_corpus.txt` (built by `scripts/05_build_cpt_corpus.py`) | **Small.** Your corpus here is a few MB; real CPT needs GB-scale data to meaningfully shift a model's knowledge. Run it to see the mechanics (loss should still visibly drop over the pass), but don't expect a dramatic before/after — the base model already knows general SystemVerilog syntax. |
| 2. SFT (Supervised Fine-Tuning) | `training/20_sft_train.py` | **Behavior**: given an instruction, produce the right shaped answer | `data/train.jsonl` | **This is where you'll see the clearest, most legitimate improvement** at this scale — instruction-following on your specific task types (bug-finding, assertion generation, etc.) |
| 3. DPO (Preference Optimization) | `training/30_dpo_train.py` | Prefers "good" over "bad" responses for the same prompt | `data/dpo_pairs.jsonl` | **Small but real** — you likely only have a handful of preference pairs at this corpus size; treat any improvement as directional, and scale `08_generate_dpo_pairs.py`'s inputs before trusting it further |
| 4. GRPO (RL with Verifiable Reward) | `training/40_grpo_train.py` | Directly optimizes against `verilator`'s pass/fail signal — no reward model, no human labels needed | `verilator` installed, a handful of assertion-generation prompts | **The most fragile at this scale** (needs the most data/compute of the four to show a clean signal) but architecturally the most important — this is your genuine, hard-to-replicate advantage over generic AI, because your domain has a free, automatic correctness checker that most domains don't |

**Run order**: 1 → 2 → 3 → 4, each stage building on the previous one's saved adapter
(`models/cpt-lora/` → `models/sft-lora/` → `models/dpo-lora/` → `models/grpo-lora/`). You can
also skip CPT and go straight SFT → DPO → GRPO if you want faster iteration — set
`START_FROM_CPT = False` (the default) in `20_sft_train.py`.

## Full run order (all scripts, in order)

```bash
# --- Data pipeline (CPU-only, runs fine on your laptop) ---
bash scripts/01_clone_corpus.sh          # Station 1: collect real public RTL/UVM repos
python3 scripts/02_parse_corpus.py       # Station 2: raw files -> structured JSON records
python3 scripts/03_dedupe_chunk.py       # Station 3: remove near-duplicate modules
python3 scripts/04_label_chunks.py       # Station 4: tag domain/assertion/register metadata
python3 scripts/05_build_cpt_corpus.py   # Station 5: build raw-text corpus for CPT
python3 scripts/06_generate_pairs.py     # Station 6: real instruction pairs + verilator verification
python3 scripts/07_split_data.py         # Station 7: train/val/test split (no leakage)
python3 scripts/08_generate_dpo_pairs.py # Station 8: auto-labeled DPO preference pairs

# --- Training (needs GPU -- run on Colab) ---
python3 training/00_env_check.py         # confirms GPU + packages before you waste time
python3 training/10_cpt_train.py         # Stage 1/4
python3 training/20_sft_train.py         # Stage 2/4
python3 training/30_dpo_train.py         # Stage 3/4
python3 training/40_grpo_train.py        # Stage 4/4

# --- Evaluation ---
python3 evaluation/evaluate.py --model Qwen/Qwen2.5-Coder-1.5B-Instruct --tag baseline
python3 evaluation/evaluate.py --model models/sft-lora  --tag sft
python3 evaluation/evaluate.py --model models/dpo-lora  --tag dpo
python3 evaluation/evaluate.py --model models/grpo-lora --tag grpo

# --- Export + serve your final model ---
bash inference/export_and_serve.sh dpo-lora   # or grpo-lora if you ran stage 4
```

Or just open `Semiconductor_AI_Pipeline.ipynb` in Colab and run every cell top to bottom —
it runs this exact sequence.

## What changed vs. the previous (broken) version — quick reference

- **Base model is real**: `Qwen/Qwen2.5-Coder-1.5B-Instruct` (swap to the 7B variant by editing
  one line in each training script once you're on a bigger GPU), not a random-init toy model.
- **Real Unsloth + TRL + PEFT** LoRA/QLoRA training, not a hand-rolled loop.
- **`generate_pairs.py` actually runs** (no syntax error, no missing `import re`) and pulls real
  content from your cloned corpus via mechanical bug-injection, instead of 100% hardcoded strings.
- **CPT stage now exists** (it didn't before at all).
- **DPO pairs are auto-labeled by a checkable rule** (does the assertion still exist after a
  mechanical edit?) instead of being manually guessed.
- **A real GRPO/RLVR stage exists**, using `verilator` as the reward function.
- **`export_and_serve.sh` actually executes every step** (real `git clone`, real `cmake build`,
  real GGUF conversion, real server start) — nothing is commented out or replaced with a `cp`.
- **`split_data.py` exists** (it was missing entirely before) and splits by source file to avoid
  train/test leakage.

## Honest expectations for this pilot

You will not get a dramatically smarter chip-design assistant out of a few hundred training
examples and a 1.5B model — that was never realistic, and no version of this pipeline changes
that. What you *will* get, if you run this end-to-end, is a **complete, correct, personally-executed
understanding of all four training stages**, a real (if small) fine-tuned model you can hold in
your hand and query, and a pipeline architecture that scales cleanly: swap in a bigger base model,
a bigger corpus (add OpenTitan's full tree, more RISC-V cores, your own sanitized work examples
once you're ready), and rent a bigger GPU when the numbers tell you it's worth it — every script
here is written to take that scaling with a one-line config change, not a rewrite.
