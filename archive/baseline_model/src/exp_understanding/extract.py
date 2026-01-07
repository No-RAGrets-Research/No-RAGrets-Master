# -*- coding: utf-8 -*-
"""
Step 3: Experiment Understanding (entity & pattern extraction)
- From Methods/Experiments/Results sections, extract:
  - datasets, metrics, baselines/model names, numeric results
- Build simple candidate claims with anchors
"""

from __future__ import annotations
import os, json, re
from typing import Dict, Any, List, Tuple, Set

# ---- lexicons (expand over time) ----
DATASETS = {
    # CV
    "mnist","cifar-10","cifar10","cifar-100","cifar100","imagenet","imagenet-1k","coco",
    # NLP
    "squad","glue","superglue","fever","scifact","pubmedqa","ms marco","msmarco","wikiqa",
    # MT/ASR/etc.
    "wmt14","wmt16","librispeech",
}
METRICS = {
    "accuracy","acc","top-1","top1","f1","bleu","rouge","exact match","em",
    "auc","auroc","mse","mae","rmse","perplexity","ppl","map","mrr"
}
BASELINE_HINTS = {"baseline","compared to","vs.","versus","outperform","improv","beat"}
ABLATION_HINTS = {"ablation","component analysis"}
VAR_HINTS = {"±","std","variance","confidence interval","ci"}

# numeric pattern: 85, 85.2, 0.852, 85%, 85.2%
NUM = r"(?:[-+]?\d+(?:\.\d+)?)%?"
NUM_RE = re.compile(NUM)

def _load_json(path:str)->Dict[str,Any]:
    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)

def _build_sid_map(parsed:Dict[str,Any])->Dict[str,Dict[str,Any]]:
    # sid -> {text, page}
    return {s["sid"]: s for s in parsed.get("sentences",[])}

def _gather_section_sents(sections:Dict[str,Any], sid_map:Dict[str,Any],
                          names:List[str])->List[Dict[str,Any]]:
    sents=[]
    for sec in sections.get("sections",[]):
        if sec["name"] in names:
            for sid in sec["sids"]:
                if sid in sid_map:
                    sents.append(sid_map[sid])
    return sents

def _has_any(hay:str, vocab:Set[str])->bool:
    low = hay.lower()
    return any(v in low for v in vocab)

def _extract_datasets(text:str)->List[str]:
    low = text.lower()
    found = [d for d in DATASETS if d in low]
    # normalize variants
    norm=[]
    for d in found:
        if d in {"cifar10"}: d = "cifar-10"
        if d in {"cifar100"}: d = "cifar-100"
        if d in {"ms marco"}: d = "msmarco"
        norm.append(d)
    return sorted(list(set(norm)))

def _extract_metrics(text:str)->List[str]:
    low = text.lower()
    found=[m for m in METRICS if m in low]
    # normalize
    norm=[]
    for m in found:
        if m in {"acc"}: m="accuracy"
        if m in {"top1"}: m="top-1"
        if m in {"em"}: m="exact match"
        norm.append(m)
    return sorted(list(set(norm)))

def _extract_numbers(text:str)->List[str]:
    return NUM_RE.findall(text)

def _is_baseline_sentence(text:str)->bool:
    return _has_any(text, BASELINE_HINTS)

def _has_variance(text:str)->bool:
    return _has_any(text, VAR_HINTS)

def _is_ablation(text:str)->bool:
    return _has_any(text, ABLATION_HINTS)

def extract_from_sections(parsed:Dict[str,Any], sections:Dict[str,Any])->Dict[str,Any]:
    """Return candidate claims and per-sentence anchors from selected sections."""
    sid_map = _build_sid_map(parsed)
    # focus on Methods / Experiments / Results; Discussion 常有结论也可纳入
    sents = _gather_section_sents(sections, sid_map, ["Methods","Experiments","Results","Discussion"])

    sent_records=[]
    for s in sents:
        txt=s["text"]
        rec={
            "sid": s["sid"],
            "page": s["page"],
            "text": txt,
            "datasets": _extract_datasets(txt),
            "metrics": _extract_metrics(txt),
            "numbers": _extract_numbers(txt),
            "is_baseline": _is_baseline_sentence(txt),
            "has_variance": _has_variance(txt),
            "is_ablation": _is_ablation(txt),
        }
        sent_records.append(rec)

    # ---- build simple candidate claims ----
    # strategy:
    # 1) sentences that mention a metric + a number (+ dataset) are potential "result" claims
    # 2) if also baseline-hinted, mark as comparative

    # Skip citation-like sentences (e.g., containing year, conference, volume/page)
    def is_citation_like(text: str) -> bool:
        # Matches patterns like (Author et al., 2020), [12], CVPR 2021, etc.
        citation_patterns = [
            r"\(\s*[\w\-]+(?: et al\.)?,? \d{4}\s*\)",  # (Author et al., 2020)
            r"\[\d+\]",                                 # [12]
            r"\b(?:cvpr|iclr|icml|nips|neurips|aaai|acl|emnlp|naacl|coling|eccv|iccv|sigir|kdd|wsdm|ijcai|aaai)\s*\d{4}\b",  # conf + year
            r"\b\d{4}\b",                               # year alone
            r"\bvol\.?\s*\d+",                          # volume
            r"\bpp\.?\s*\d+(-\d+)?",                    # page numbers
        ]
        for pat in citation_patterns:
            if re.search(pat, text.lower()):
                return True
        return False

    sent_records = [r for r in sent_records if not is_citation_like(r["text"])]

    # build claims
    claims=[]
    cid=0
    for r in sent_records:
        if (r["metrics"] and r["numbers"]) or (r["is_baseline"] and r["numbers"]):
            cid+=1
            claim_txt = r["text"]
            anchors={
                "datasets": r["datasets"],
                "metrics": r["metrics"],
                "numbers": r["numbers"],
                "comparative": bool(r["is_baseline"])
            }
            claims.append({
                "cid": f"c{cid}",
                "claim_text": claim_txt,
                "source_sid": r["sid"],
                "anchors": anchors
            })

    return {
        "paper_id": parsed.get("paper_id","paper"),
        "sentences": sent_records,
        "claims_raw": claims
    }

def save_claims(obj:Dict[str,Any], out_path:str)->None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path,"w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
