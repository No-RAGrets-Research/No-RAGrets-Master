
# Baseline Model: Scientific Paper Evaluation

This repository implements a **baseline pipeline** for evaluating scientific papers.
The system parses papers, identifies experimental sections, extracts claims, and checks their **truthfulness** and **reasonableness**, producing an overall **scoring report**.

---

## Pipeline Overview

1. **Paper Parsing**

   - Tool: `PyMuPDF`
   - Extracts text from PDF into structured JSON (`parsed/`).
2. **Experiment Section Identification**

   - Tool: Rule-based classifier (keywords + heuristics)
   - Splits paper into *Methods / Experiments / Results / Discussion / Conclusion*.
3. **Experiment Understanding**

   - Extracts candidate claims from experimental sections.
   - Marks properties: baselines, variance reporting, ablations, reproducibility signals.
4. **Reasonableness + Truthfulness Check**

   - Uses **sentence-transformers (BERT/SciBERT)** for claim–evidence retrieval.
   - Computes: support probability, numeric consistency, reasonableness flags.
5. **Scoring & Reporting**

   - Combines sub-scores (truthfulness, variance, reproducibility, etc.).
   - Outputs JSON + Markdown reports with claim-level and overall grades.

---

## Run the Full Pipeline

```bash
# 1) create & activate venv (optional)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2) install dependencies
pip install -r requirements.txt

# 3) run the full pipeline on a PDF
python scripts/run_pipeline.py path/to/paper.pdf
```
