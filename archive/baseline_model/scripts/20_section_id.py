# -*- coding: utf-8 -*-
"""
CLI for Step 2:
  python scripts/20_section_id.py data/parsed/example.parsed.json [out_dir]
"""
import os, sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.section_id.section_id import load_parsed, identify_sections, save_sections

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/20_section_id.py <path/to/parsed.json> [out_dir]")
        sys.exit(1)

    in_path = sys.argv[1]
    if not os.path.exists(in_path):
        print(f"[ERR] file not found: {os.path.abspath(in_path)}")
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else "data/sections"
    parsed = load_parsed(in_path)
    obj = identify_sections(parsed)

    paper_id = obj["paper_id"]
    out_path = os.path.join(out_dir, f"{paper_id}.sections.json")
    save_sections(obj, out_path)

    # brief stats
    sizes = {s["name"]: len(s["sids"]) for s in obj["sections"]}
    print(f"[OK] wrote: {out_path}")
    for k, v in sizes.items():
        print(f"  {k:12s}: {v:>4d} sentences")

if __name__ == "__main__":
    main()
