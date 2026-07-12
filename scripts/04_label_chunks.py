#!/usr/bin/env python3
"""
STATION 4 — Tag every chunk with cheap, rule-based metadata so later
stages (and any future retrieval system) can filter by domain.

No ML here on purpose -- plain string matching is fast, free, and
good enough for these coarse tags.

Input : data/processed/chunks.jsonl
Output: data/processed/chunks_labeled.jsonl
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
IN_FILE = ROOT / "data" / "processed" / "chunks.jsonl"
OUT_FILE = ROOT / "data" / "processed" / "chunks_labeled.jsonl"


def label(rec: dict) -> dict:
    text = rec.get("content", "")
    if "uvm_component" in text or "uvm_sequence" in text or "`uvm_" in text:
        domain = "uvm"
    elif rec["type"] in ("sv_module", "sv_file"):
        domain = "rtl"
    else:
        domain = "doc"
    rec["domain"] = domain
    rec["contains_assertion"] = ("assert property" in text) or ("assume property" in text)
    rec["contains_register_map"] = any(k in text.lower() for k in ["register map", "reg_map", "offset 0x"])
    rec["n_chars"] = len(text)
    return rec


def main():
    records = [json.loads(l) for l in open(IN_FILE)]
    labeled = [label(r) for r in records]
    with open(OUT_FILE, "w") as f:
        for r in labeled:
            f.write(json.dumps(r) + "\n")
    from collections import Counter
    print(f"Labeled {len(labeled)} records")
    print("Domain breakdown:", dict(Counter(r["domain"] for r in labeled)))
    print("Contains assertion:", sum(r["contains_assertion"] for r in labeled))


if __name__ == "__main__":
    main()
