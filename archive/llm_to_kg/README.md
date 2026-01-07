# LLM-to-Knowledge-Graph Pipeline (Updated Nov. 3, 2025)

## Overview

This project implements an **end-to-end Graph-RAG pipeline** that transforms scientific PDFs into structured **knowledge graphs (KGs)** by extracting *textual* and *visual* factual triples using large multimodal models (Qwen2.5 & Qwen3-VL).

It now successfully supports both text and image extraction, merging, and graph construction, producing interpretable graphs per paper and a combined meta-graph.

---

## Folder Structure

```
llm_to_knowledge_graph/
│
├── main.py                        # Full pipeline runner
│
├── src/
│   ├── pdf_to_text.py             # Step 1A: PDF → structured JSON (Docling)
│   ├── pdf_to_image.py            # Step 1B: Extract figures & captions via PyMuPDF
│   ├── chunk_text.py              # Step 2: Split text into ~1000-char chunks
│   ├── extract_triples_text.py    # Step 3A: Text-based triple extraction (Qwen2.5)
│   ├── extract_triples_visual.py  # Step 3B: Visual triple extraction (Qwen3-VL)
│   ├── merge_triples.py           # Step 4: Combine textual + visual triples
│   ├── merge_clean_graph.py       # Step 5: Clean, normalize, and export graphs
│   └── visualize_graph.py         # (Optional) Visual graph rendering utilities
│
├── data/
│   ├── papers_pdf/                # Input PDFs (50 total)
│   ├── parsed_json/               # Docling outputs
│   ├── chunks/                    # Chunked text segments
│   ├── images/                    # Extracted figures + metadata per paper
│   ├── triples_text/              # Textual triples (JSON per paper)
│   ├── triples_visual/            # Visual triples (JSON per paper)
│   ├── triples_merged/            # Combined triples
│   └── graph_per_paper/           # Per-paper graphs (.png + .gpickle)
│
└── outputs/
    ├── merged_triples.json        # Global merged triple file
    └── knowledge_graph.gpickle    # Combined KG for analysis
```

---

## Progress Summary


| Step                                  | Description                                  | Model / Tool            | Status           |
| ------------------------------------- | -------------------------------------------- | ----------------------- | ---------------- |
| **1A. PDF → JSON**                   | Parse structured text using**Docling**       | `docling-parse`         | ✅ Done          |
| **1B. PDF → Image (Figures)**        | Extract figures + captions via**PyMuPDF**    | `fitz (PyMuPDF)`        | ✅ Done          |
| **2. Text Chunking**                  | Split text into semantic\~1000-char chunks   | Python                  | ✅ Done          |
| **3A. Text Triples**                  | Extract text-based triples                   | `Qwen2.5-1.5B-Instruct` | ✅ Done          |
| **3B. Visual Triples**                | Extract figure-based triples                 | `Qwen3-VL-4B-Instruct`  | ✅ Fully working |
| **4. Merge Triples**                  | Merge text + visual triples per paper        | Python                  | ✅ Done          |
| **5. Graph Construction**             | Build per-paper and global graphs            | `NetworkX`+`matplotlib` | ✅ Done          |
| **6. Graph Cleaning / Visualization** | Normalize entity names, export clean layouts | In progress             | ⚙️ Planned     |

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

## ⚠️ Known Issues


| Category                          | Description                                                   | Planned Fix                                               |
| --------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| **Tiny/blank images**             | Some PDFs contain <100×100 px images; skipped automatically. | ✅ Already filtered                                       |
| **VRAM fragmentation (Qwen3-VL)** | Out-of-memory errors after many batches.                      | ✅ Mitigated via`torch.cuda.empty_cache()`+`gc.collect()` |
| **Noisy triples**                 | Some decoded strings are not valid JSON triples.              | ⚙️ To be post-cleaned                                   |
| **Graph redundancy**              | Entity duplicates (e.g.,`CH₄`,`methane`,`Methane`).          | 🔧 Normalization in next release                          |

---

## Pipeline Flow Summary

```
PDF (input)
  ↓
Docling → structured JSON text
  ↓
PyMuPDF → extracted figures & captions
  ↓
Qwen2.5-1.5B → text triples
  ↓
Qwen3-VL-4B → visual triples
  ↓
merge_triples.py → unified JSON
  ↓
merge_clean_graph.py → per-paper KGs
  ↓
outputs/knowledge_graph.gpickle → combined KG
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
| Peak Memory Use | ≈ 9 GB (Qwen3-VL-4B)        |

## Future Work

1. **Entity normalization & relation cleaning**
   → unify synonyms, normalize relation verbs
2. **Visual-Text Graph Fusion**
   → link visual and textual entities through shared nodes
3. **Graph metrics analysis**
   → degree / centrality / density statistics per paper
4. **Neo4j or Graphviz export**
   → enable interactive browsing of extracted KGs

## Summary

As of **Nov 3 2025**, the LLM-to-Knowledge-Graph pipeline is **fully functional** from PDF ingestion to multi-modal triple extraction and graph generation.
The next milestone focuses on **graph cleaning, unification, and visualization** to support large-scale analysis across all 50 scientific papers.
