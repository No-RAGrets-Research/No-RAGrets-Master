# -*- coding: utf-8 -*-
"""
Step 5: Scoring & Aggregation
- Per-claim score: 0.7 * p_support + 0.3 * (reason_subscore / 4)
- Paper-level score: average of per-claim scores
- Also emits a simple Markdown report for humans
"""

from __future__ import annotations
import os, json
from typing import Dict, Any, List

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(obj: Dict[str, Any], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _reason_subscore(reason: Dict[str, Any]) -> int:
    items = [
        bool(reason.get("has_baseline", False)),
        bool(reason.get("has_variance", False)),
        bool(reason.get("is_ablation", False)),
        bool(reason.get("reproducibility", False)),
    ]
    return sum(1 for x in items if x)

def grade(score: float) -> str:
    if score >= 0.80: return "A"
    if score >= 0.60: return "B"
    if score >= 0.40: return "C"
    return "D"

def score_verdicts(verdicts_obj: Dict[str, Any],
                   w_truth: float = 0.7,
                   w_reason: float = 0.3) -> Dict[str, Any]:
    paper_id = verdicts_obj.get("paper_id", "paper")
    claims = verdicts_obj.get("verdicts", [])

    per_claim = []
    scores = []
    for v in claims:
        p_support = float(v["truthfulness"]["p_support"])
        r_sub = _reason_subscore(v.get("reasonableness", {}))
        final = w_truth * p_support + w_reason * (r_sub / 4.0)
        rec = {
            "cid": v.get("cid"),
            "source_sid": v.get("source_sid"),
            "claim_text": v.get("claim_text"),
            "p_support": round(p_support, 3),
            "reason_sub": r_sub,
            "final_score": round(final, 3),
            "grade": grade(final),
            "evidence_sids": v["truthfulness"]["evidence_sids"],
            "numeric_consistency": v["truthfulness"]["numeric_consistency"],
            "reason": v.get("reasonableness", {})
        }
        per_claim.append(rec)
        scores.append(final)

    paper_score = round(sum(scores) / max(1, len(scores)), 3)
    paper_grade = grade(paper_score)

    return {
        "paper_id": paper_id,
        "weights": {"truthfulness": w_truth, "reasonableness": w_reason},
        "paper_score": paper_score,
        "paper_grade": paper_grade,
        "n_claims": len(per_claim),
        "claims": per_claim
    }

def save_markdown(report: Dict[str, Any], out_md: str) -> None:
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    lines: List[str] = []
    lines.append(f"# Paper Report: {report['paper_id']}\n")
    lines.append(f"- **Overall Score**: {report['paper_score']}  (**{report['paper_grade']}**)")
    lines.append(f"- **Claims Evaluated**: {report['n_claims']}\n")
    lines.append("## Claims\n")
    for i, c in enumerate(report["claims"], 1):
        lines.append(f"### {i}. CID {c['cid']}  —  Grade **{c['grade']}**  (Score {c['final_score']})")
        lines.append(f"- Claim: {c['claim_text']}")
        lines.append(f"- p_support: {c['p_support']} | numeric: {c['numeric_consistency']} | reason_sub: {c['reason_sub']}/4")
        r = c["reason"]
        lines.append(f"- Reason hits: baseline={r.get('has_baseline', False)}, variance={r.get('has_variance', False)}, "
                     f"ablation={r.get('is_ablation', False)}, reproducibility={r.get('reproducibility', False)}")
        lines.append(f"- Evidence SIDs: {', '.join(c['evidence_sids'][:5])}\n")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
