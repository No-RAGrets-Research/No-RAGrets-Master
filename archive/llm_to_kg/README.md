# LLM-to-Knowledge-Graph Pipeline (Updated Nov. 3, 2025)

## Overview

This project implements an **end-to-end Graph-RAG pipeline** that transforms scientific PDFs into structured **knowledge graphs (KGs)** by extracting *textual* and *visual* factual triples using large multimodal models (Qwen2.5 & Qwen3-VL).

It now successfully supports both text and image extraction, merging, and graph construction, producing interpretable graphs per paper and a combined meta-graph.

---

## Folder Structure

```
llm_to_knowledge_graph/
”‚
””€”€ main.py                        # Full pipeline runner
”‚
””€”€ src/
”‚  OK””€”€ pdf_to_text.py             # Step 1A: PDFOK†’ structured JSON (Docling)
”‚  OK””€”€ pdf_to_image.py            # Step 1B: Extract figures & captions via PyMuPDF
”‚  OK””€”€ chunk_text.py              # Step 2: Split text into ~1000-char chunks
”‚  OK””€”€ extract_triples_text.py    # Step 3A: Text-based triple extraction (Qwen2.5)
”‚  OK””€”€ extract_triples_visual.py  # Step 3B: Visual triple extraction (Qwen3-VL)
”‚  OK””€”€ merge_triples.py           # Step 4: Combine textual + visual triples
”‚  OK””€”€ merge_clean_graph.py       # Step 5: Clean, normalize, and export graphs
”‚  OK”””€”€ visualize_graph.py         # (Optional) Visual graph rendering utilities
”‚
””€”€ data/
”‚  OK””€”€ papers_pdf/                # Input PDFs (50 total)
”‚  OK””€”€ parsed_json/               # Docling outputs
”‚  OK””€”€ chunks/                    # Chunked text segments
”‚  OK””€”€ images/                    # Extracted figures + metadata per paper
”‚  OK””€”€ triples_text/              # Textual triples (JSON per paper)
”‚  OK””€”€ triples_visual/            # Visual triples (JSON per paper)
”‚  OK””€”€ triples_merged/            # Combined triples
”‚  OK”””€”€ graph_per_paper/           # Per-paper graphs (.png + .gpickle)
”‚
”””€”€ outputs/
   OK””€”€ merged_triples.json        # Global merged triple file
   OK”””€”€ knowledge_graph.gpickle    # Combined KG for analysis
```

---

## Progress Summary


| Step                                  | Description                                  | Model / Tool            | Status           |
| ------------------------------------- | -------------------------------------------- | ----------------------- | ---------------- |
| **1A. PDFOK†’ JSON**                   | Parse structured text using**Docling**       | `docling-parse`         |OKOK Done          |
| **1B. PDFOK†’ Image (Figures)**        | Extract figures + captions via**PyMuPDF**    | `fitz (PyMuPDF)`        |OKOK Done          |
| **2. Text Chunking**                  | Split text into semantic\~1000-char chunks   | Python                  |OKOK Done          |
| **3A. Text Triples**                  | Extract text-based triples                   | `Qwen2.5-1.5B-Instruct` |OKOK Done          |
| **3B. Visual Triples**                | Extract figure-based triples                 | `Qwen3-VL-4B-Instruct`  |OKOK Fully working |
| **4. Merge Triples**                  | Merge text + visual triples per paper        | Python                  |OKOK Done          |
| **5. Graph Construction**             | Build per-paper and global graphs            | `NetworkX`+`matplotlib` |OKOK Done          |
| **6. Graph Cleaning / Visualization** | Normalize entity names, export clean layouts | In progress             |OK™OK Planned     |

---

## Key Improvements (Nov 2025)


| Improvement                         | Description                                                                      |
| ----------------------------------- | -------------------------------------------------------------------------------- |
| **Visual pipeline completed**       | Full extraction of figure images + captions, with JSON metadata.                 |
| **Qwen3-VL integration stabilized** | Added automatic memory release & image filtering; pipeline now runs on RTX 4070. |
| **Merged text + visual KGs**        | Each paper now includes both textual and visual factual triples.                 |
| **Skip & resume support**           | Auto-skips existing visual triple JSON files; safe to resume runs.               |
| **Graph normalization (draft)**     | Planned regex-based node cleanup and entity unification.                         |

---

##OKOK Known Issues


| Category                          | Description                                                   | Planned Fix                                               |
| --------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| **Tiny/blank images**             | Some PDFs contain <100Ã—100 px images; skipped automatically. |OKOK Already filtered                                       |
| **VRAM fragmentation (Qwen3-VL)** | Out-of-memory errors after many batches.                      |OKOK Mitigated via`torch.cuda.empty_cache()`+`gc.collect()` |
| **Noisy triples**                 | Some decoded strings are not valid JSON triples.              |OK™OK To be post-cleaned                                   |
| **Graph redundancy**              | Entity duplicates (e.g.,`CH‚„`,`methane`,`Methane`).          | ðŸ”§ Normalization in next release                          |

---

## Pipeline Flow Summary

```
PDF (input)
 OK†
DoclingOK†’ structured JSON text
 OK†
PyMuPDFOK†’ extracted figures & captions
 OK†
Qwen2.5-1.5BOK†’ text triples
 OK†
Qwen3-VL-4BOK†’ visual triples
 OK†
merge_triples.pyOK†’ unified JSON
 OK†
merge_clean_graph.pyOK†’ per-paper KGs
 OK†
outputs/knowledge_graph.gpickleOK†’ combined KG
```

---

## Example Run Commands

```bash
# Run full pipeline
python main.py

# Run step by step
python src/pdf_to_text.py
python src/pdf_to_image.py
python src/chunk_text.py
python src/extract_triples_text.py
python src/extract_triples_visual.py
python src/merge_triples.py
python src/merge_clean_graph.py
```

---

## Environment


| Component       | Version / Info               |
| --------------- | ---------------------------- |
| OS              | Windows 10 / 11              |
| GPU             | NVIDIA RTX 4070 (12 GB VRAM) |
| Python          | 3.11 (venv)                  |
| PyTorch         | 2.5.1 + CUDA 12.1            |
| Transformers    | 4.57                         |
| Docling         | 2.58                         |
| Poppler         | Installed (for`pdf2image`)   |
| Peak Memory Use |OK‰ˆ 9 GB (Qwen3-VL-4B)        |

## Future Work

1. **Entity normalization & relation cleaning**
  OK†’ unify synonyms, normalize relation verbs
2. **Visual-Text Graph Fusion**
  OK†’ link visual and textual entities through shared nodes
3. **Graph metrics analysis**
  OK†’ degree / centrality / density statistics per paper
4. **Neo4j or Graphviz export**
  OK†’ enable interactive browsing of extracted KGs

## Summary

As of **Nov 3 2025**, the LLM-to-Knowledge-Graph pipeline is **fully functional** from PDF ingestion to multi-modal triple extraction and graph generation.
The next milestone focuses on **graph cleaning, unification, and visualization** to support large-scale analysis across all 50 scientific papers.
