# -*- coding: utf-8 -*-
"""
Step 2: Experiment Section Identification
Input : <paper>.parsed.json  (from Step 1)
Output: <paper>.sections.json (sentence IDs grouped by section)
"""

from __future__ import annotations
import json, os, re
from typing import Dict, List, Any

# section name -> header keywords (lowercased)
SECTION_KEYS: Dict[str, List[str]] = {
    "Methods":      ["method", "materials", "experimental setup", "implementation"],
    "Experiments":  ["experiment", "evaluation", "experimental results"],
    "Results":      ["result"],
    "Discussion":   ["discussion", "analysis"],
    "Conclusion":   ["conclusion", "future work", "limitations"],
}

# Recognize References/Appendix to reduce noise
SECTION_KEYS.update({
    "References": ["references", "bibliography"],
    "Appendix":   ["appendix", "supplementary"],
})

TITLE_MAX_TOKENS = 12  # a "title-like" line is usually short

def _looks_like_header(text: str) -> bool:
    # short, little punctuation, starts with capital often
    if len(text.split()) > TITLE_MAX_TOKENS:
        return False
    # avoid figure/table captions
    low = text.lower()
    if low.startswith(("figure", "table", "algorithm", "appendix")):
        return False
    # mostly no trailing period
    if text.strip().endswith("."):
        return False
    return True

def _match_section_name(text: str) -> str | None:
    low = text.lower()
    for name, kws in SECTION_KEYS.items():
        for kw in kws:
            if kw in low:
                return name
    return None

def load_parsed(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def identify_sections(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Return {"paper_id":..., "sections":[{"name":..., "sids":[...]}]}"""
    paper_id = parsed.get("paper_id", "paper")
    sents = parsed.get("sentences", [])

    buckets: Dict[str, List[str]] = {k: [] for k in SECTION_KEYS.keys()}

    current: str | None = None
    for s in sents:
        txt = s["text"].strip()
        sid = s["sid"]

        # header detection
        if _looks_like_header(txt):
            sec = _match_section_name(txt)
            if sec:
                current = sec
                continue  # the header line itself usually not included

        # collect if inside a section
        if current:
            buckets[current].append(sid)

    # weak sweep: if a section is empty, try keyword hit inside sentences
    for sec, kws in SECTION_KEYS.items():
        if len(buckets[sec]) == 0:
            for s in sents:
                low = s["text"].lower()
                if any(kw in low for kw in kws) and len(buckets[sec]) < 150:  # cap to avoid swallowing all
                    buckets[sec].append(s["sid"])

    sections = [{"name": name, "sids": buckets[name]} for name in SECTION_KEYS.keys()]
    return {"paper_id": paper_id, "sections": sections}

def save_sections(obj: Dict[str, Any], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
