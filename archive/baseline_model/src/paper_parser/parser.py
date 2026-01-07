# src/paper_parser/parser.py
# Minimal parser using the official import style: `import pymupdf`

from __future__ import annotations
import os, re, json
from typing import Dict, Any, List
import pymupdf  # official module name for PyMuPDF

# sentence split: simple fallback; you can later swap to blingfire if needed
_SENT_SPLIT = re.compile(r'(?<!\b[A-Z][a-z])(?<=[.!?])\s+(?=[A-Z(])')
_WS = re.compile(r"[ \t]+")

def _clean_text(t: str) -> str:
    t = t.replace("\xad", "")
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)  # merge hyphen linebreaks
    t = t.replace("\r", "\n")
    t = re.sub(r"\n{2,}", "\n", t)
    t = _WS.sub(" ", t)
    return t.strip()

def _sent_split(text: str) -> List[str]:
    parts = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        parts.extend(_SENT_SPLIT.split(para))
    return [s.strip() for s in parts if len(s.strip()) >= 3]

def parse_pdf(pdf_path: str, mode: str = "auto") -> Dict[str, Any]:
    doc = pymupdf.open(pdf_path)              # ← exactly like the docs
    pages, sentences = [], []
    sid = 0

    for i, page in enumerate(doc, start=1):
        raw = page.get_text() or ""           # ← same as page.get_text("text")
        clean = _clean_text(raw)
        pages.append({"page": i, "text": clean})
        for s in _sent_split(clean):
            sid += 1
            sentences.append({"sid": f"s{sid}", "text": s, "page": i})

    meta = {
        "filename": os.path.basename(pdf_path),
        "n_pages": len(doc),
        "n_sentences": len(sentences),
        "title": (doc.metadata or {}).get("title") or "",
        "author": (doc.metadata or {}).get("author") or "",
    }
    return {"paper_id": os.path.splitext(meta["filename"])[0],
            "meta": meta, "pages": pages, "sentences": sentences}

def save_json(obj: Dict[str, Any], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
