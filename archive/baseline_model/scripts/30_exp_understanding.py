# -*- coding: utf-8 -*-
"""
CLI for Step 3:
  python scripts/30_exp_understanding.py data/parsed/example.parsed.json data/sections/example.sections.json [out_dir]
"""
import os, sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.exp_understanding.extract import _load_json, extract_from_sections, save_claims

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/30_exp_understanding.py <parsed.json> <sections.json> [out_dir]")
        sys.exit(1)

    parsed_path = sys.argv[1]
    sections_path = sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else "data/claims"

    for p in (parsed_path, sections_path):
        if not os.path.exists(p):
            print(f"[ERR] file not found: {os.path.abspath(p)}")
            sys.exit(1)

    parsed = _load_json(parsed_path)
    sections = _load_json(sections_path)

    obj = extract_from_sections(parsed, sections)
    out_path = os.path.join(out_dir, f"{obj['paper_id']}.claims.json")
    save_claims(obj, out_path)

    print(f"[OK] wrote: {out_path}")
    print(f"  sentences scanned: {len(obj['sentences'])}")
    print(f"  raw claims found : {len(obj['claims_raw'])}")

if __name__ == "__main__":
    main()
