#!/usr/bin/env python3
"""
STATION 7 — Split into train/val/test.

Splits by SOURCE FILE, not by individual record, so no file's chunks
end up in more than one split (avoids train/test leakage). This file
did not exist at all in the previous version of this repo.

Input : data/processed/pairs.jsonl
Output: data/train.jsonl, data/val.jsonl, data/test.jsonl
"""
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
IN_FILE = ROOT / "data" / "processed" / "pairs.jsonl"

random.seed(42)


def main():
    pairs = [json.loads(l) for l in open(IN_FILE)]

    # group by source_path so a file's examples never span splits;
    # hand-written seed examples (no source_path) get their own bucket key
    groups = defaultdict(list)
    for p in pairs:
        key = p.get("source_path") or f"seed::{p['task_type']}::{id(p) % 997}"
        groups[key].append(p)

    keys = list(groups.keys())
    random.shuffle(keys)
    n = len(keys)
    n_train = max(1, int(n * 0.8))
    n_val = max(1, int(n * 0.1)) if n > 2 else 0
    train_keys = keys[:n_train]
    val_keys = keys[n_train:n_train + n_val]
    test_keys = keys[n_train + n_val:]

    def flatten(ks):
        out = []
        for k in ks:
            out.extend(groups[k])
        return out

    splits = {"train": flatten(train_keys), "val": flatten(val_keys), "test": flatten(test_keys)}

    for name, recs in splits.items():
        out_path = ROOT / "data" / f"{name}.jsonl"
        with open(out_path, "w") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
        print(f"{name}: {len(recs)} examples -> {out_path}")

    if len(splits["val"]) == 0 or len(splits["test"]) == 0:
        print("\nWARNING: dataset is small enough that val/test are tiny or empty. "
              "This is expected at pilot scale -- treat eval numbers as directional, "
              "not statistically rigorous, until you scale up the corpus (see README).")


if __name__ == "__main__":
    main()
