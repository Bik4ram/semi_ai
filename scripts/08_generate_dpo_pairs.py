#!/usr/bin/env python3
"""
STATION 8 — Build a small DPO (preference) dataset.

For every assertion-generation example we already verified compiles
(the "chosen" response), we mechanically construct a "rejected"
counterpart that is objectively worse by a checkable rule: we comment
out the actual `assert property` construct, turning it into a no-op
that LOOKS like an assertion but checks nothing. This gives a
genuinely low-noise preference signal (chosen has a real assertion;
rejected doesn't) rather than a manually-guessed label.

Input : data/train.jsonl
Output: data/dpo_pairs.jsonl
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
IN_FILE = ROOT / "data" / "train.jsonl"
OUT_FILE = ROOT / "data" / "dpo_pairs.jsonl"


def make_rejected(chosen_output: str) -> str | None:
    if "assert property" not in chosen_output:
        return None
    # comment out every assert property line -> objectively worse:
    # it no longer checks anything, but still "looks" plausible
    rejected = re.sub(
        r"^(\s*)(assert property.*)$",
        r"\1// \2  (disabled - checks nothing)",
        chosen_output, flags=re.MULTILINE,
    )
    return rejected if rejected != chosen_output else None


def main():
    records = [json.loads(l) for l in open(IN_FILE)]
    dpo_pairs = []
    for r in records:
        if r.get("task_type") != "sva_assertion_generation":
            continue
        rejected = make_rejected(r["output"])
        if rejected is None:
            continue
        dpo_pairs.append({
            "prompt": f"{r['instruction']}\n\nCode:\n{r['input']}",
            "chosen": r["output"],
            "rejected": rejected,
        })

    with open(OUT_FILE, "w") as f:
        for p in dpo_pairs:
            f.write(json.dumps(p) + "\n")
    print(f"Wrote {len(dpo_pairs)} DPO preference pairs -> {OUT_FILE}")
    if len(dpo_pairs) == 0:
        print("WARNING: 0 pairs generated -- you need at least a few "
              "sva_assertion_generation examples in train.jsonl. Clone more "
              "repos / run the LLM augmentation path in 06_generate_pairs.py "
              "to get more assertion examples.")


if __name__ == "__main__":
    main()
