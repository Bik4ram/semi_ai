#!/usr/bin/env python3
"""
Run the same fixed benchmark against any checkpoint (base model, or
any of the four LoRA stages) so you can compare honestly.

Usage:
  python3 evaluate.py --model Qwen/Qwen2.5-Coder-1.5B-Instruct --tag baseline
  python3 evaluate.py --model ../models/sft-lora --tag sft
  python3 evaluate.py --model ../models/dpo-lora --tag dpo
  python3 evaluate.py --model ../models/grpo-lora --tag grpo
"""
import argparse
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
BENCHMARK = Path(__file__).parent / "benchmark.jsonl"
RESULTS_DIR = Path(__file__).parent / "results"


def sv_compiles(code: str) -> bool:
    with tempfile.NamedTemporaryFile(suffix=".sv", mode="w", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        result = subprocess.run(["verilator", "--lint-only", "-Wno-fatal", path],
                                 capture_output=True, text=True, timeout=15)
        return result.returncode == 0
    except Exception:
        return False
    finally:
        os.unlink(path)


def rouge_l_approx(pred: str, ref: str) -> float:
    """Very small dependency-free ROUGE-L approximation (LCS-based)."""
    p, r = pred.split(), ref.split()
    if not p or not r:
        return 0.0
    dp = [[0] * (len(r) + 1) for _ in range(len(p) + 1)]
    for i in range(1, len(p) + 1):
        for j in range(1, len(r) + 1):
            if p[i - 1] == r[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    lcs = dp[-1][-1]
    if lcs == 0:
        return 0.0
    prec, rec = lcs / len(p), lcs / len(r)
    return 2 * prec * rec / (prec + rec)


def run_model(model_path: str, prompt: str) -> str:
    # Lazy import so this file can be inspected/tested without unsloth installed
    from unsloth import FastLanguageModel
    global _cached_model, _cached_tok, _cached_path
    if globals().get("_cached_path") != model_path:
        m, t = FastLanguageModel.from_pretrained(model_path, max_seq_length=2048, load_in_4bit=True)
        FastLanguageModel.for_inference(m)
        globals()["_cached_model"], globals()["_cached_tok"], globals()["_cached_path"] = m, t, model_path
    model, tok = globals()["_cached_model"], globals()["_cached_tok"]
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    start = time.time()
    out = model.generate(**inputs, max_new_tokens=300, do_sample=False)
    elapsed = time.time() - start
    text = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    tok_per_sec = out.shape[1] / max(elapsed, 1e-6)
    return text, tok_per_sec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()

    benchmark = [json.loads(l) for l in open(BENCHMARK)]
    results = []
    for item in benchmark:
        prompt = f"### Instruction:\n{item['instruction']}\n\n### Input:\n{item['input']}\n\n### Response:\n"
        pred, tok_per_sec = run_model(args.model, prompt)
        rec = {"task_type": item["task_type"], "prediction": pred, "tok_per_sec": tok_per_sec}
        if item.get("reference"):
            rec["rouge_l"] = rouge_l_approx(pred, item["reference"])
        code_blocks = re.findall(r"```(?:systemverilog)?\n(.*?)\n```", pred, re.DOTALL) or [pred]
        if item["task_type"] in ("sva_assertion_generation", "rtl_bug_finding"):
            rec["compiles"] = sv_compiles(code_blocks[0])
        results.append(rec)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"{args.tag}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    avg_rouge = sum(r.get("rouge_l", 0) for r in results) / max(1, len(results))
    compile_rate = sum(r.get("compiles", False) for r in results) / max(
        1, sum(1 for r in results if "compiles" in r) or 1)
    print(f"[{args.tag}] avg ROUGE-L(approx)={avg_rouge:.3f}  "
          f"compile_rate={compile_rate:.1%}  -> {out_path}")


if __name__ == "__main__":
    main()
