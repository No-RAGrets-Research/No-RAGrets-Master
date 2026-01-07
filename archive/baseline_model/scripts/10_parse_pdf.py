# -*- coding: utf-8 -*-
"""
CLI entry for Step 1: parse PDF -> parsed JSON with pages & sentences.
Usage:
  python scripts/10_parse_pdf.py <path/to/paper.pdf> [output_dir] [mode]
mode in {auto, text, blocks, dict}; default: auto
"""

import os, sys
from pathlib import Path

# allow "src" imports when running as script
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.paper_parser.parser import parse_pdf, save_json

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/10_parse_pdf.py <path/to/paper.pdf> [output_dir] [mode]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "data/parsed"
    mode = sys.argv[3] if len(sys.argv) > 3 else "auto"

    obj = parse_pdf(pdf_path, mode=mode)
    out_path = os.path.join(out_dir, f"{obj['paper_id']}.parsed.json")
    save_json(obj, out_path)

    n_pages = obj["meta"]["n_pages"]
    n_sents = len(obj["sentences"])
    print(f"[OK] wrote: {out_path}")
    print(f"pages={n_pages}  sentences={n_sents}  mode={mode}")

if __name__ == "__main__":
    main()
