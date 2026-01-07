# Knowledge Graph Pipeline Output Organization

This directory contains organized output from the knowledge graph generation pipeline. Each paper is processed through multiple stages, with outputs stored in dedicated folders.

## Folder Structure

```
output/
├── docling_json/           # PDF → Structured JSON conversion
│   ├── paper1.json
│   └── paper2.json
├── text_chunks/            # JSON → Text chunks with provenance
│   ├── paper1.texts_chunks.jsonl
│   └── paper2.texts_chunks.jsonl
├── text_triples/           # Text chunks → Extracted knowledge graphs
│   ├── paper1_kg_results_20251115_143022.json
│   └── paper2_kg_results_20251115_143022.json
├── visual_triples/         # Visual content → Extracted knowledge graphs
│   ├── paper1_visual_kg_format_20251115_143022.json
│   └── paper2_visual_kg_format_20251115_143022.json
├── raw_visual_triples/     # Raw visual extraction outputs
│   ├── paper1_visual_triples_kg_format.json
│   └── paper2_visual_triples_kg_format.json
└── reports/                # Processing summaries and reports
    ├── paper1_kg_summary_20251115_143022.json
    ├── paper2_kg_summary_20251115_143022.json
    └── paper1_processing_report.json
```

## File Types

### Docling JSON (`docling_json/`)

- **Source**: PDF files from `../papers/`
- **Content**: Structured document layout with text, tables, figures
- **Format**: Single JSON file per paper
- **Used for**: Text chunking and provenance tracking

### Text Chunks (`text_chunks/`)

- **Source**: Docling JSON files
- **Content**: Document sections split into manageable chunks
- **Format**: JSONL (one JSON object per line)
- **Features**: Preserves provenance (page, bbox, section)
- **Used for**: Knowledge graph extraction

### Text Triples (`text_triples/`)

- **Source**: Text chunks
- **Content**: Extracted entities and relationships from text
- **Format**: JSON with summary and detailed results
- **Features**: Entity types, relationship predicates, confidence scores
- **Used for**: Loading into Dgraph database

### Visual Triples (`visual_triples/`)

- **Source**: Figures and diagrams from papers
- **Content**: Extracted entities and relationships from visual content
- **Format**: JSON with visual knowledge graph results
- **Features**: Visual evidence, figure metadata, extracted concepts
- **Used for**: Complementing text-based knowledge extraction

### Raw Visual Triples (`raw_visual_triples/`)

- **Source**: Visual extraction pipeline intermediate results
- **Content**: Unprocessed visual triple extractions
- **Format**: JSON with raw extraction outputs
- **Features**: Direct vision model outputs before formatting
- **Used for**: Debugging and format development

### Reports (`reports/`)

- **Content**: Processing summaries and statistics
- **Types**:
  - Individual paper summaries (`*_kg_summary_*.json`)
  - Processing reports (`*_processing_report.json`)
- **Features**: Processing time, entity/relation counts, error tracking, success/failure status

## Processing Pipeline Flow

```
../papers/paper.pdf
    ↓ PDF Conversion
output/docling_json/paper.json
    ↓ Text Chunking
output/text_chunks/paper.texts_chunks.jsonl
    ↓ Text KG Extraction
output/text_triples/paper_kg_results_*.json
    ↓ Visual Processing (parallel)
output/visual_triples/paper_visual_kg_format_*.json
    ↓ Report Generation
output/reports/paper_kg_summary_*.json
output/reports/paper_processing_report.json
```

## Processing with Main Pipeline

Run the complete pipeline using the main entry point:

```bash
cd kg_gen_pipeline

# Process all papers
python main.py --all --papers-dir ../papers

# Process individual paper
python main.py "../papers/paper.pdf"
```

This will process PDFs and organize outputs in this structure.

## Loading into Database

Knowledge graph results can be loaded into Dgraph database:

```bash
cd ../knowledge_graph

# Start database
docker compose up -d

# Load schema
python dgraph_manager.py

# Load KG results
python kg_data_loader.py ../kg_gen_pipeline/output/text_triples/paper_kg_results_*.json
```

## Cleanup

To clean all generated files:

```bash
# Remove all outputs (use with caution)
rm -rf output/

# Remove specific stages
rm -rf output/docling_json/      # Remove JSON conversions
rm -rf output/text_chunks/       # Remove text chunks
rm -rf output/text_triples/      # Remove text KG results
rm -rf output/visual_triples/    # Remove visual KG results
rm -rf output/raw_visual_triples/ # Remove raw visual outputs
rm -rf output/reports/           # Remove processing reports
```
