# About the files already in data/

The .jsonl files already present in `data/` and `data/processed/` (raw_records, chunks,
chunks_labeled, pairs, train/val/test, dpo_pairs) and `cpt_corpus.txt` are REAL outputs from
actually running the full pipeline against a small 2-repo test clone (picorv32 + uvm-core only,
~7MB) to prove every script works end-to-end with zero errors before shipping this to you.

They are intentionally tiny (19 instruction pairs, 13/1/5 train/val/test split) -- this is NOT
the corpus you should train on. Run `bash scripts/01_clone_corpus.sh` yourself to pull the full
5-repo corpus (picorv32, ibex, uvm-core, opentitan peripherals, riscv-arch-test) described in the
README, then re-run scripts 02-08 to regenerate all of these files for real, at a useful size.
