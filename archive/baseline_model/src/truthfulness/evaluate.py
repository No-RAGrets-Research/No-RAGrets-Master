# -*- coding: utf-8 -*-
"""
Step 4: Claim Evaluation (Truthfulness + Reasonableness)
- Evidence Retrieval: embed claim & all paper sentences, retrieve Top-k evidence.
- Truthfulness (baseline heuristic):
    * p_support based on overlap (dataset/metric) + numeric consistency + polarity hints
    * numeric consistency check with tolerance (supports % vs decimal)
- Reasonableness:
    * has_baseline / has_variance / is_ablation (re-use from step3 if present)
    * reproducibility via keywords (code/github/available)
Outputs a verdicts object per paper.
"""

from __future__ import annotations
import os, json, re
from typing import Dict, Any, List, Tuple
import numpy as np
import re

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    raise RuntimeError(
        "sentence-transformers is required. Install with: pip install sentence-transformers"
    ) from e


# --------------------- I/O helpers ---------------------
def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(obj: Dict[str, Any], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# --------------------- Retrieval -----------------------
def cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return a @ b.T  # (n_a, n_b)

def topk_indices(sim_row: np.ndarray, k: int) -> List[int]:
    if k >= sim_row.shape[0]:
        return list(np.argsort(-sim_row))
    return list(np.argpartition(-sim_row, kth=k-1)[:k][np.argsort(-sim_row[np.argpartition(-sim_row, kth=k-1)[:k]])])


# --------------------- Numeric consistency -------------
_NUM_RE = re.compile(r'[-+]?\d+(?:\.\d+)?%?')

def _extract_numbers(text: str) -> List[str]:
    return _NUM_RE.findall(text)

def _to_float(s: str) -> Tuple[float, bool]:
    """Return (value, is_percent). '85%'->(0.85, True), '0.85'->(0.85, False)"""
    s = s.strip()
    is_pct = s.endswith('%')
    if is_pct:
        s = s[:-1]
    try:
        v = float(s)
        if is_pct:  # normalize percent to 0-1
            v = v / 100.0
        return v, is_pct
    except Exception:
        return float("nan"), is_pct

def numeric_consistent(claim_text: str, evidence_texts: List[str],
                       rel_tol: float = 0.02, abs_tol: float = 0.01) -> str:
    """
    Return 'true' / 'false' / 'none'
    - rel_tol: relative tolerance (e.g., 2%)
    - abs_tol: absolute tolerance (e.g., 0.01 absolute)
    """
    cn = [_to_float(x)[0] for x in _extract_numbers(claim_text)]
    if not cn:
        return "none"
    ev_nums: List[float] = []
    for ev in evidence_texts:
        ev_nums += [_to_float(x)[0] for x in _extract_numbers(ev)]
    ev_nums = [x for x in ev_nums if np.isfinite(x)]
    if not ev_nums:
        return "false"
    # if any claim number matches any evidence number within tolerance -> true
    for c in cn:
        for e in ev_nums:
            if abs(c - e) <= max(abs_tol, rel_tol * max(abs(c), abs(e), 1e-9)):
                return "true"
    return "false"


# --------------------- Polarity / overlap heuristics ----
POS_HINTS = ("improv", "higher", "better", "increase", "outperform", "beat")
NEG_HINTS = ("lower", "worse", "decrease", "no improvement", "not better", "underperform")

def polarity(text: str) -> int:
    low = text.lower()
    if any(p in low for p in POS_HINTS): return +1
    if any(n in low for n in NEG_HINTS): return -1
    return 0

def overlap_match(claim: Dict[str, Any], evidence_text: str) -> bool:
    low = evidence_text.lower()
    # simple overlap on datasets & metrics from step3 anchors
    ds_ok = any(d.lower() in low for d in claim.get("anchors", {}).get("datasets", []))
    mt_ok = any(m.lower() in low for m in claim.get("anchors", {}).get("metrics", []))
    return ds_ok or mt_ok


# --------------------- Main evaluation ------------------
def evaluate_claims(parsed: Dict[str, Any],
                    claims_obj: Dict[str, Any],
                    model_name: str = "allenai/specter2_base",
                    top_k: int = 8) -> Dict[str, Any]:
    """
    Return verdicts:
    {
      "paper_id": "...",
      "verdicts": [
        {
          "cid": "...",
          "claim_text": "...",
          "truthfulness": { "evidence_sids": [...], "p_support": 0.75, "numeric_consistency": "true" },
          "reasonableness": { "has_baseline": true, "has_variance": false, "is_ablation": false, "reproducibility": false }
        }, ...
      ]
    }
    """
    paper_id = claims_obj.get("paper_id", "paper")
    # --- retrieval corpus: all sentences in paper ---
    corpus = parsed.get("sentences", [])
    corpus_texts = [s["text"] for s in corpus]
    corpus_sids   = [s["sid"]  for s in corpus]

    # embed corpus once
    model = SentenceTransformer(model_name)
    emb_corpus = model.encode(corpus_texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)

    verdicts = []
    # reproducibility keyword on whole paper (simple)
    REPO_URL = re.compile(
        r'(https?://(?:www\.)?(?:github|gitlab|bitbucket)\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+)',
        re.IGNORECASE
    )
    CODE_HINTS = (
        "code is available", "our code is available", "we release the code",
        "release our code", "open-source", "open source",
        "replication package", "artifact evaluation", "supplementary material"
    )

    paper_text_all = " ".join(corpus_texts)          
    paper_text_low = paper_text_all.lower()

    repo_urls = REPO_URL.findall(paper_text_all)     
    has_repo_url = len(repo_urls) > 0
    has_code_hint = any(h in paper_text_low for h in CODE_HINTS)

    has_reproducibility = has_repo_url or has_code_hint

    for c in claims_obj.get("claims_raw", []):
        claim_text = c["claim_text"]
        # --- retrieval ---
        emb_claim = model.encode([claim_text], normalize_embeddings=True)
        sim = cosine_sim(emb_claim, emb_corpus)[0]  # (n_corpus,)
        idxs = topk_indices(sim, top_k)
        evidence_texts = [corpus_texts[i] for i in idxs]
        evidence_sids  = [corpus_sids[i]  for i in idxs]

        # --- numeric consistency ---
        num_flag = numeric_consistent(claim_text, evidence_texts)  # 'true'/'false'/'none'

        # --- overlap & polarity for p_support (weighted formula) ---
        # 1) overlap ratio
        overlap_hits = sum(1 for ev in evidence_texts if overlap_match(c, ev))
        overlap_ratio = overlap_hits / max(1, len(evidence_texts))   # 0.0 ~ 1.0

        # 2) numeric consistency weight
        num_w = {"true": 0.15, "none": 0.00, "false": -0.10}.get(num_flag, 0.0)

        # 3) polarity alignment
        pol_c = polarity(claim_text)
        pol_e = max([polarity(ev) for ev in evidence_texts] + [0]) 
        pol_bonus = 0.0
        if pol_c != 0 and pol_c == pol_e:
            pol_bonus = 0.05
        elif pol_c != 0 and pol_e == -pol_c:
            pol_bonus = -0.05

        # 4) combine to p_support in [0.05, 0.95]
        p_support = 0.45 + 0.40 * overlap_ratio + num_w + pol_bonus
        p_support = float(min(max(p_support, 0.05), 0.95))

        # --- reasonableness (reuse anchors from step3) ---
        anchors = c.get("anchors", {})
        reason = {
            "has_baseline": bool(anchors.get("comparative", False)),
            "has_variance": False,  # default false; can be refined using step3 sentence flags if available
            "is_ablation": False,
            "reproducibility": has_reproducibility
        }

        # If step3 stored sentence-level flags, carry them over
        # (optional, depending on your step3 implementation)
        src_sid = c.get("source_sid")
        if src_sid:
            # find that sentence in step3 sentences list (if provided)
            for srec in claims_obj.get("sentences", []):
                if srec.get("sid") == src_sid:
                    reason["has_variance"] = bool(srec.get("has_variance", False))
                    reason["is_ablation"]  = bool(srec.get("is_ablation", False))
                    break

        verdicts.append({
            "cid": c["cid"],
            "source_sid": src_sid,
            "claim_text": claim_text,
            "truthfulness": {
                "evidence_sids": evidence_sids,
                "p_support": round(float(p_support), 3),
                "numeric_consistency": num_flag
            },
            "reasonableness": reason
        })

    return {"paper_id": paper_id, "verdicts": verdicts}
