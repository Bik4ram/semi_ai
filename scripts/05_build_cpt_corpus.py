#!/usr/bin/env python3
"""
STATION 5 — Build the CONTINUED PRETRAINING (CPT) corpus.

CPT is different in kind from SFT: it is NOT instruction/answer pairs.
It's raw text that the model reads and does next-token prediction on,
exactly like its original pretraining -- just narrowed to your domain.
This is how a model actually absorbs domain VOCABULARY and STYLE
(SVA idioms, UVM macro patterns, register-map phrasing) rather than
just learning "when asked X, answer with shape Y" (that's SFT's job).

We simply concatenate all labeled chunks (RTL + UVM + docs) into one
big plain-text file, separated by a document boundary the tokenizer
can use. No labels, no instructions -- just clean domain text.

Input : data/processed/chunks_labeled.jsonl
Output: data/cpt_corpus.txt
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
IN_FILE = ROOT / "data" / "processed" / "chunks_labeled.jsonl"
OUT_FILE = ROOT / "data" / "cpt_corpus.txt"

EOS_MARKER = "\n<|endofdoc|>\n"  # simple document boundary


def main():
    records = [json.loads(l) for l in open(IN_FILE)]
    n_chars = 0
    with open(OUT_FILE, "w") as f:
        for r in records:
            text = r.get("content", "").strip()
            if len(text) < 30:
                continue
            f.write(text)
            f.write(EOS_MARKER)
            n_chars += len(text)
    print(f"Wrote CPT corpus: {len(records)} candidate docs, "
          f"{n_chars:,} chars -> {OUT_FILE}")
    print("NOTE: this is intentionally tiny (a real CPT run uses "
          "billions of tokens). This is enough to exercise the "
          "pipeline mechanics, not to meaningfully change the model's "
          "knowledge -- see README for what to expect from this stage.")


if __name__ == "__main__":
    main()
