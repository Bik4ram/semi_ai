#!/usr/bin/env python3
"""
STATION 3 — Remove near-duplicate records (RTL repos massively
reimplement the same FIFO/UART/counter patterns; without this your
tiny corpus becomes even tinier in effective diversity).

Uses MinHash (cheap similarity fingerprint) + LSH (fast lookup of
similar fingerprints) instead of comparing every record to every
other record, which would be too slow.

Input : data/processed/raw_records.jsonl
Output: data/processed/chunks.jsonl
"""
import json
from pathlib import Path
from collections import Counter

from datasketch import MinHash, MinHashLSH

ROOT = Path(__file__).parent.parent
IN_FILE = ROOT / "data" / "processed" / "raw_records.jsonl"
OUT_FILE = ROOT / "data" / "processed" / "chunks.jsonl"

NUM_PERM = 128
THRESHOLD = 0.85
SHINGLE_SIZE = 5


def shingles(text: str, k: int = SHINGLE_SIZE) -> set[str]:
    text = " ".join(text.lower().split())
    return {text[i:i + k] for i in range(max(0, len(text) - k + 1))}


def minhash_of(text: str) -> MinHash:
    m = MinHash(num_perm=NUM_PERM)
    for s in shingles(text):
        m.update(s.encode("utf-8"))
    return m


def main():
    records = [json.loads(l) for l in open(IN_FILE)]
    print(f"Loaded {len(records)} records")

    lsh = MinHashLSH(threshold=THRESHOLD, num_perm=NUM_PERM)
    signatures = {}
    for i, rec in enumerate(records):
        text = rec.get("content", "")
        if len(text) < 50:
            continue
        mh = minhash_of(text)
        signatures[i] = mh
        lsh.insert(str(i), mh)

    duplicates = set()
    for i, mh in signatures.items():
        if i in duplicates:
            continue
        similar = [int(x) for x in lsh.query(mh) if int(x) != i]
        for j in similar:
            if j in signatures and j not in duplicates and j > i:
                duplicates.add(j)

    keep = sorted(i for i in signatures if i not in duplicates)
    deduped = [records[i] for i in keep]

    with open(OUT_FILE, "w") as f:
        for r in deduped:
            f.write(json.dumps(r) + "\n")

    print(f"{len(records)} -> {len(deduped)} records "
          f"({len(deduped)/max(1,len(records))*100:.1f}% retained)")
    print("Breakdown by type:", dict(Counter(r["type"] for r in deduped)))


if __name__ == "__main__":
    main()
