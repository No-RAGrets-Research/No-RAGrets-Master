# -*- coding: utf-8 -*-
"""
End-to-end baseline pipeline (one command).
Usage:
  python scripts/run_pipeline.py /path/to/paper.pdf [out_root]

Outputs under out_root (default: data/):
  parsed/    <paper>.parsed.json
  sections/  <paper>.sections.json
  claims/    <paper>.claims.json
  verdicts/  <paper>.verdicts.json
  reports/   <paper>.report.json  +  <paper>.report.md
"""

import os, sys
from pathlib import Path

# allow "src" imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Step 1
from src.paper_parser.parser import parse_pdf as _parse_pdf, save_json as _save_json

# Step 2
from src.section_id.section_id import identify_sections, save_sections, load_parsed as _load_parsed_step2

# Step 3
from src.exp_understanding.extract import _load_json as _load_json, extract_from_sections, save_claims

# Step 4
from src.truthfulness.evaluate import evaluate_claims, load_json as _load_json4, save_json as _save_json4

# Step 5
from src.scoring.score import score_verdicts, load_json as _load_json5, save_json as _save_json5, save_markdown

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_pipeline.py <paper.pdf> [out_root]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    out_root = sys.argv[2] if len(sys.argv) > 2 else "data"
    if not os.path.exists(pdf_path):
        print(f"[ERR] file not found: {os.path.abspath(pdf_path)}")
        sys.exit(1)

    # ---- dirs ----
    d_parsed    = os.path.join(out_root, "parsed");    ensure_dir(d_parsed)
    d_sections  = os.path.join(out_root, "sections");  ensure_dir(d_sections)
    d_claims    = os.path.join(out_root, "claims");    ensure_dir(d_claims)
    d_verdicts  = os.path.join(out_root, "verdicts");  ensure_dir(d_verdicts)
    d_reports   = os.path.join(out_root, "reports");   ensure_dir(d_reports)

    # ===== Step 1: Parse PDF =====
    parsed_obj = _parse_pdf(pdf_path)   # uses pymupdf
    paper_id = parsed_obj["paper_id"]
    f_parsed = os.path.join(d_parsed, f"{paper_id}.parsed.json")
    _save_json(parsed_obj, f_parsed)
    print(f"[1/5] Parsed -> {f_parsed}  (pages={parsed_obj['meta']['n_pages']}, sents={len(parsed_obj['sentences'])})")

    # ===== Step 2: Section Identification =====
    parsed_for_s2 = _load_parsed_step2(f_parsed)
    sections_obj = identify_sections(parsed_for_s2)
    f_sections = os.path.join(d_sections, f"{paper_id}.sections.json")
    save_sections(sections_obj, f_sections)
    sizes = {s['name']: len(s['sids']) for s in sections_obj['sections']}
    print(f"[2/5] Sections -> {f_sections}  {sizes}")

    # ===== Step 3: Experiment Understanding =====
    parsed_for_s3   = _load_json(f_parsed)
    sections_for_s3 = _load_json(f_sections)
    claims_obj = extract_from_sections(parsed_for_s3, sections_for_s3)
    f_claims = os.path.join(d_claims, f"{paper_id}.claims.json")
    save_claims(claims_obj, f_claims)
    print(f"[3/5] Claims -> {f_claims}  (sentences={len(claims_obj['sentences'])}, claims={len(claims_obj['claims_raw'])})")

    # ===== Step 4: Truthfulness + Reasonableness =====
    parsed_for_s4 = _load_json4(f_parsed)
    claims_for_s4 = _load_json4(f_claims)
    verdicts_obj = evaluate_claims(parsed_for_s4, claims_for_s4)  # uses sentence-transformers
    f_verdicts = os.path.join(d_verdicts, f"{paper_id}.verdicts.json")
    _save_json4(verdicts_obj, f_verdicts)
    ps = [v['truthfulness']['p_support'] for v in verdicts_obj['verdicts']]
    print(f"[4/5] Verdicts -> {f_verdicts}  (claims={len(ps)}, p_support_mean={sum(ps)/max(1,len(ps)):.3f})")

    # ===== Step 5: Scoring & Report =====
    verdicts_for_s5 = _load_json5(f_verdicts)
    report = score_verdicts(verdicts_for_s5)  # returns final per-claim + paper score
    f_report_json = os.path.join(d_reports, f"{paper_id}.report.json")
    f_report_md   = os.path.join(d_reports, f"{paper_id}.report.md")
    _save_json5(report, f_report_json)
    save_markdown(report, f_report_md)
    print(f"[5/5] Reports -> {f_report_json}")
    print(f"[5/5] Reports -> {f_report_md}")
    print(f"Overall score: {report['paper_score']}  ({report['paper_grade']})")

if __name__ == "__main__":
    main()
