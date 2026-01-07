# -*- coding: utf-8 -*-
"""
CLI:
  python scripts/50_scoring.py data/verdicts/example.verdicts.json [out_dir]
Outputs:
  - data/reports/example.report.json
  - data/reports/example.report.md
"""
import os, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.scoring.score import load_json, save_json, score_verdicts, save_markdown

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/50_scoring.py <verdicts.json> [out_dir]")
        sys.exit(1)

    in_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "data/reports"
    if not os.path.exists(in_path):
        print(f"[ERR] file not found: {os.path.abspath(in_path)}")
        sys.exit(1)

    verdicts = load_json(in_path)
    report = score_verdicts(verdicts)

    base = report["paper_id"]
    out_json = os.path.join(out_dir, f"{base}.report.json")
    out_md   = os.path.join(out_dir, f"{base}.report.md")

    save_json(report, out_json)
    save_markdown(report, out_md)

    print(f"[OK] wrote: {out_json}")
    print(f"[OK] wrote: {out_md}")
    print(f"Overall score: {report['paper_score']}  ({report['paper_grade']})")

if __name__ == "__main__":
    main()
