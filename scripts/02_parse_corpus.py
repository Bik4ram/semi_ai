#!/usr/bin/env python3
"""
STATION 2 — Parse raw files into uniform JSON records.

Walks data/raw/ and, for every SystemVerilog/Verilog file, uses pyslang
(a real SV parser) to split it into per-module records. For every
markdown/rst file, splits by heading. Falls back to whole-file text
if pyslang can't parse something (some files use constructs pyslang's
parser version doesn't support yet -- that's fine, we just keep the
raw text rather than losing the file).

Input : data/raw/**
Output: data/processed/raw_records.jsonl
"""
import json
import re
from pathlib import Path

import pyslang

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_FILE = ROOT / "data" / "processed" / "raw_records.jsonl"


def extract_sv_modules(path: Path) -> list[dict]:
    text = path.read_text(errors="ignore")
    records = []
    try:
        tree = pyslang.SyntaxTree.fromText(text, str(path))
        root = tree.root
        # root.members holds top-level syntax nodes (modules, packages, etc.)
        members = getattr(root, "members", None)
        found_module = False
        if members:
            for member in members:
                kind = str(getattr(member, "kind", ""))
                if "Module" in kind:
                    found_module = True
                    mod_text = str(member)
                    # pull the module name out for metadata, best-effort
                    name_match = re.search(r"module\s+(\w+)", mod_text)
                    records.append({
                        "type": "sv_module",
                        "module_name": name_match.group(1) if name_match else None,
                        "content": mod_text.strip(),
                        "source_path": str(path.relative_to(ROOT)),
                    })
        if not found_module:
            raise ValueError("no module nodes found via pyslang, falling back")
    except Exception:
        # Fallback: regex-split on module ... endmodule blocks.
        # Not as precise as an AST, but far better than treating the
        # whole file as one blob, and never crashes the pipeline.
        for m in re.finditer(r"\bmodule\s+(\w+).*?\bendmodule\b", text, re.DOTALL):
            records.append({
                "type": "sv_module",
                "module_name": m.group(1),
                "content": m.group(0).strip(),
                "source_path": str(path.relative_to(ROOT)),
            })
        if not records:
            # last resort: keep the whole file as one record so nothing is lost
            records.append({
                "type": "sv_file",
                "module_name": None,
                "content": text.strip(),
                "source_path": str(path.relative_to(ROOT)),
            })
    return records


def extract_md_sections(path: Path) -> list[dict]:
    text = path.read_text(errors="ignore")
    records = []
    # split on markdown headings (##, ###) or rst-style underlines are skipped for simplicity
    parts = re.split(r"(?m)^(#{1,4}\s.+)$", text)
    if len(parts) <= 1:
        if text.strip():
            records.append({"type": "md_section", "title": None,
                             "content": text.strip(), "source_path": str(path.relative_to(ROOT))})
        return records
    # parts alternates [preamble, heading, body, heading, body, ...]
    preamble = parts[0].strip()
    if preamble:
        records.append({"type": "md_section", "title": None, "content": preamble,
                         "source_path": str(path.relative_to(ROOT))})
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        content = f"{heading}\n\n{body}".strip()
        if content:
            records.append({"type": "md_section", "title": heading, "content": content,
                             "source_path": str(path.relative_to(ROOT))})
    return records


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_records = []
    sv_files = list(RAW_DIR.rglob("*.sv")) + list(RAW_DIR.rglob("*.v")) + list(RAW_DIR.rglob("*.svh"))
    md_files = list(RAW_DIR.rglob("*.md")) + list(RAW_DIR.rglob("*.rst"))

    print(f"Found {len(sv_files)} SV/V files, {len(md_files)} markdown/rst files")

    for p in sv_files:
        try:
            all_records.extend(extract_sv_modules(p))
        except Exception as e:
            print(f"  [skip] {p}: {e}")

    for p in md_files:
        try:
            all_records.extend(extract_md_sections(p))
        except Exception as e:
            print(f"  [skip] {p}: {e}")

    with open(OUT_FILE, "w") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")

    print(f"Wrote {len(all_records)} records -> {OUT_FILE}")


if __name__ == "__main__":
    main()
