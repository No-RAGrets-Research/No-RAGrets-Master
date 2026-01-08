# Knowledge Graph Generation Pipeline

## Overview

The Knowledge Graph Generation Pipeline is a comprehensive system for automatically extracting structured knowledge from scientific research papers. It processes PDFs through multiple stages to extract entities, relationships, and provenance information from both textual content and visual elements (figures, charts, diagrams).

## Architecture

### Pipeline Flow

```
PDF Document
   OK†
[1] PDF to Docling JSON Conversion
   OK†
[2] Text Chunking with Provenance
   OK†
[3] Text-based KG ExtractionOK”€”€†’ Text Triples Output
   OK†
[4] Figure Detection
   OK†
[5] Visual KG ExtractionOK”€”€†’ Visual Triples Output
   OK†
[6] Output Organization & Reporting
```

### Core Components

The pipeline consists of several specialized components working together:

**Pipeline Orchestrator** (`pipeline_orchestrator.py`)

- Main coordinator for the entire extraction workflow
- Manages sequential processing of multiple papers
- Handles duplicate detection and batch processing
- Provides progress reporting and error handling
- Generates processing reports and summaries
- Manages resource cleanup (GPU memory, intermediate files)

**PDF Converter** (`pdf_converter.py`)

- Converts PDF files to structured Docling JSON format
- Uses the Docling library to extract document structure
- Preserves layout information, text, tables, and figure metadata
- Handles various PDF formats and complex layouts
- Maintains page-level provenance for all extracted elements

**Text Chunker** (`text_chunker.py`)

- Breaks documents into processable text segments using intelligent sentence segmentation
- Uses spaCy (`en_core_web_sm` model) for accurate sentence boundary detection
- Falls back to regex-based splitting if spaCy is unavailable
- Preserves document structure (sections, paragraphs, sentences)
- Maintains provenance links to source document locations
- Tracks page numbers, bounding boxes, and document offsets
- Creates sentence-level mappings with precise character offsets for fine-grained relation extraction
- Outputs JSONL format with one chunk per line

**Text KG Extractor** (`text_kg_extractor.py`)

- Extracts entities and relationships from text chunks using LLM models
- Uses KG-GEN library with configurable LLM backends (Ollama, OpenAI)
- Default model: Mistral 7B via Ollama
- Processes chunks with context preservation
- Maps extracted relations back to specific sentences
- Calculates confidence scores based on entity positions
- Outputs structured triple format with full provenance

**Figure Detector** (`figure_detection.py`)

- Analyzes Docling JSON to identify extractable visual content
- Detects figures, charts, diagrams, and tables
- Determines if visual extraction should be attempted
- Filters out decorative or non-informational images
- Provides extraction recommendations based on content analysis

**Visual KG Extractor** (`visual_kg_extractor.py`)

- Extracts knowledge from figures using vision-language models
- Default model: Qwen3-VL-4B-Instruct
- Combines Docling metadata with actual image content from PDFs
- Matches figure captions to extracted images
- Analyzes visual content to extract entities and relationships
- Handles complex visual elements (charts, diagrams, flowcharts)
- Manages GPU memory efficiently with cleanup between papers

**Visual KG Formatter** (`visual_kg_formatter.py`)

- Formats visual extraction results for database loading
- Ensures consistency with text extraction output format
- Adds visual-specific metadata (figure IDs, page numbers)
- Structures results for seamless integration with text triples

## Processing Stages

### Detailed Data Flow

The pipeline processes documents through six main stages with careful attention to provenance and accuracy:

```
PDF Document
   OK†
[Stage 1] Docling Conversion
   OK””€ Text extraction with bounding boxes
   OK””€ Table detection and structure extraction
   OK””€ Figure identification and metadata
   OK”””€ Output: Docling JSON with full document structure
   OK†
[Stage 2] Text Chunking + Sentence Segmentation
   OK””€ Load spaCy en_core_web_sm model
   OK””€ Section identification (Introduction, Methods, etc.)
   OK””€ Paragraph splitting
   OK””€ Sentence segmentation using spaCy NLP:
   OK”‚  OK€¢ doc = nlp(text)
   OK”‚  OK€¢ for sent in doc.sents: ...
   OK”‚  OK€¢ Extract sent.start_char, sent.end_char
   OK””€ Calculate document-level character offsets
   OK””€ Track page numbers and bounding boxes
   OK””€ Build sentence provenance metadata
   OK”””€ Output: Text chunks JSONL with sentence-level provenance
   OK†
[Stage 3] Text-based KG Extraction
   OK””€ LLM processing (Mistral 7B via Ollama)
   OK””€ Entity extraction from chunks
   OK””€ Relation extraction with context
   OK””€ Map relations back to specific sentences (using spaCy offsets)
   OK””€ Calculate confidence scores
   OK”””€ Output: Text triples with full provenance
   OK†
[Stage 4] Figure Detection
   OK””€ Analyze Docling JSON for extractable figures
   OK””€ Count figures with valid page numbers
   OK””€ Filter non-extractable images
   OK”””€ Decision: Proceed to visual extraction if figures present
   OK†
[Stage 5] Visual KG Extraction (if figures detected)
   OK””€ Extract images from PDF using fitz
   OK””€ Match images to Docling figure metadata
   OK””€ Vision-language model processing (Qwen3-VL)
   OK””€ Extract visual entities and relationships
   OK””€ Add figure-specific provenance
   OK”””€ Output: Visual triples with figure IDs
   OK†
[Stage 6] Optional: Table-Only Extraction
   OK””€ Load table elements from Docling JSON
   OK””€ Create chunks from table content
   OK””€ Sentence segmentation using spaCy (same as Stage 2)
   OK””€ LLM extraction on table chunks
   OK””€ Add table-specific provenance (table_id)
   OK”””€ Output: Table triples (supplemental)
```

**Key Technical Points**:

1. **spaCy Integration**: Used in Stages 2 and 6 for consistent sentence segmentation
2. **Provenance Chain**: Character offsets from spaCy enable precise source tracking
3. **Modular Design**: Each stage can run independently if prior outputs exist
4. **Fallback Mechanisms**: Regex fallback if spaCy unavailable, chunk-level provenance if sentence mapping fails
5. **Parallel Processing**: Text and visual extraction use same provenance structure for unified knowledge graph

### Stage 1: PDF to Docling JSON Conversion

**Purpose**: Convert unstructured PDF into structured JSON format

**Input**:

- PDF file (e.g., `research_paper.pdf`)

**Process**:

- Docling library analyzes PDF layout and structure
- Extracts text blocks with bounding boxes
- Identifies tables, figures, captions, and references
- Detects table structure (rows, columns, cells)
- Preserves page numbers and spatial relationships
- Handles multi-column layouts and complex formatting

**Output**:

- Docling JSON file (`research_paper.json`)
- Contains structured representation of document
- Includes text content, layout metadata, figure information, and table data

**Location**: `output/docling_json/`

**Docling JSON Structure**:

The JSON contains multiple key sections:

```json
{
  "texts": [
    {"text": "Introduction", "label": "section_header", "page_no": 1},
    {"text": "Methanotrophs are...", "label": "text", "page_no": 1},
    {"text": "Row 1 Cell 1 | Row 1 Cell 2", "label": "table", "page_no": 3}
  ],
  "tables": [
    {
      "text": "Table content as text",
      "label": "table",
      "prov": [{"page_no": 3, "bbox": {"l": 72, "t": 200, "r": 540, "b": 400}}],
      "data": {
        "grid": [
          ["Header 1", "Header 2", "Header 3"],
          ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
          ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
        ]
      }
    }
  ],
  "figures": [
    {
      "label": "Figure",
      "caption": "Figure 1: CH4 flux measurements",
      "prov": [{"page_no": 5, "bbox": {...}}]
    }
  ]
}
```

**Table Representation**:

Tables in Docling JSON have two representations:

1. **Text Form**: Linearized text in the `texts` array

   - Used for reading flow and context
   - Format: "Cell1 | Cell2 | Cell3"
   - Preserves reading order

2. **Structured Form**: Grid data in the `tables` array
   - Preserves row/column structure
   - Format: 2D array (list of lists)
   - Maintains table semantics
   - Includes headers and data rows

Both representations are used during table extraction to maintain context and structure.

### Stage 2: Text Chunking with Provenance

**Purpose**: Break document into processable chunks while maintaining source tracking

**Input**:

- Docling JSON file

**Process**:

- Identifies document sections (Introduction, Methods, Results, etc.)
- Splits text into paragraphs and sentences using spaCy NLP
- Calculates document-level character offsets for each sentence
- Tracks page numbers and bounding boxes
- Creates chunk metadata for context preservation
- Assigns unique IDs to chunks and sentences

**Sentence Segmentation Details**:

The text chunker uses **spaCy** for accurate sentence boundary detection:

1. **Primary Method**: spaCy `en_core_web_sm` model

   - Loads the spaCy English small model during initialization
   - Provides accurate sentence segmentation using linguistic rules
   - Handles complex cases (abbreviations, ellipses, quotes)
   - Tracks precise character offsets (start/end positions)
   - Returns sentence objects with `.start_char` and `.end_char` attributes

2. **Fallback Method**: Regex-based splitting
   - Activates if spaCy model is not installed
   - Uses simple period/question mark/exclamation point detection
   - Less accurate but functional for basic sentence splitting
   - Warning message displayed when fallback is used

**Implementation**:

```python
# From text_chunker.py
try:
    import spacy
    self.nlp = spacy.load("en_core_web_sm")
    print("Loaded spaCy model for sentence segmentation")
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found. Falling back to basic sentence splitting.")
    self.nlp = None

# Sentence segmentation with spaCy
doc = self.nlp(text)
for sent_idx, sent in enumerate(doc.sents):
    sentence_text = sent.text.strip()
    if sentence_text:
        sentences.append({
            "sentence_id": sent_idx,
            "text": sentence_text,
            "char_start": sent.start_char,
            "char_end": sent.end_char,
            "document_start": document_char_offset + sent.start_char,
            "document_end": document_char_offset + sent.end_char
        })
```

**Why spaCy**:

- **Accuracy**: Handles complex sentence boundaries better than regex
- **Provenance**: Provides exact character offsets for relation mapping
- **Performance**: Fast processing even for long documents
- **Robustness**: Trained on large English corpus, handles scientific text well

**Output**:

- Text chunks JSONL file (`research_paper.texts_chunks.jsonl`)
- Each line contains one chunk with:
  - Chunk text content
  - Section information
  - Page numbers
  - Sentence-level provenance data with precise offsets
  - Document offsets for every sentence

**Location**: `output/text_chunks/`

**Chunk Structure**:

```json
{
  "chunk_id": 19,
  "text": "Methanotrophs are bacteria that use methane as their primary carbon and energy source...",
  "section": "1. Introduction",
  "pages": [2, 3],
  "sentences": [
    {
      "sentence_id": 0,
      "text": "Methanotrophs are bacteria...",
      "char_start": 0,
      "char_end": 111,
      "document_start": 1234,
      "document_end": 1345,
      "page_no": 2
    }
  ]
}
```

### Stage 3: Text-based KG Extraction

**Purpose**: Extract entities and relationships from text using LLM models

**Input**:

- Text chunks JSONL file (with sentence-level provenance from spaCy)

**Process**:

- Loads chunks sequentially for processing
- Sends each chunk to LLM (Mistral 7B via Ollama)
- LLM identifies entities (chemicals, organisms, processes, etc.)
- LLM extracts relationships between entities
- Maps each relation back to specific sentences using character offsets
- Calculates entity positions within sentences
- Assigns confidence scores based on mapping quality
- Aggregates results across all chunks
- Generates summary statistics

**Sentence Mapping Algorithm**:

After the LLM extracts a relation (e.g., "Methanotrophs oxidize methane"), the pipeline:

1. **Search for Entity Mentions**: Locate subject and object in chunk text

   ```python
   subject_pos = chunk_text.lower().find("methanotrophs".lower())
   object_pos = chunk_text.lower().find("methane".lower())
   ```

2. **Match to Sentences**: Use spaCy-provided character offsets

   ```python
   for sentence in chunk["sentences"]:
       if sentence["char_start"] <= subject_pos <= sentence["char_end"]:
           # Subject found in this sentence
       if sentence["char_start"] <= object_pos <= sentence["char_end"]:
           # Object found in this sentence
   ```

3. **Extract Source Span**: If both entities in same sentence

   ```python
   source_span = {
       "text_evidence": sentence["text"],
       "char_positions": {
           "start": sentence["document_start"],
           "end": sentence["document_end"]
       },
       "sentences": [sentence["text"]]
   }
   ```

4. **Calculate Confidence**:
   - Both entities in same sentence: confidence = 0.9-1.0
   - Entities in adjacent sentences: confidence = 0.7-0.8
   - Entities in different sentences: confidence = 0.5-0.6
   - Entity not found in text: confidence = 0.3-0.4 (chunk-level provenance)

**Why This Matters**:

Accurate sentence mapping enables:

- **Precise Citations**: Point to exact sentence that supports the relation
- **Verification**: Readers can validate extracted relations
- **Confidence Scoring**: Reliable quality metrics for downstream use
- **Debugging**: Identify extraction errors by examining source sentences
- **Legal/Scientific Rigor**: Meet citation standards for academic use

**Example with spaCy vs. Regex**:

Consider text: "Fig. 1 shows data. Methanotrophs oxidize methane."

**With spaCy**:

```python
Sentence 1: "Fig. 1 shows data." (chars 0-19)
Sentence 2: "Methanotrophs oxidize methane." (chars 20-51)
# Correctly identifies 2 sentences
# Relation mapped to sentence 2 with high confidence
```

**With Regex Fallback**:

```python
Sentence 1: "Fig." (chars 0-4)  # Incorrect split!
Sentence 2: "1 shows data." (chars 5-19)
Sentence 3: "Methanotrophs oxidize methane." (chars 20-51)
# Incorrectly identifies 3 sentences
# Relation may map to wrong sentence or fail mapping
```

**Output**:

- Text KG results file (`research_paper_kg_results_TIMESTAMP.json`)
- Contains:
  - All extracted triples (subject, predicate, object)
  - Source provenance (section, pages, chunk ID)
  - Sentence-level mappings with precise character offsets
  - Document offsets for each relation
  - Confidence scores based on sentence mapping quality
  - Summary statistics
- Processing report

**Location**: `output/text_triples/`

**Triple Structure**:

```json
{
  "subject": "Methanotrophs",
  "predicate": "use as primary carbon source",
  "object": "methane",
  "section": "1. Introduction",
  "pages": [2],
  "chunk_id": 19,
  "source_span": {
    "span_type": "single_sentence",
    "sentence_start": 0,
    "sentence_end": 0,
    "document_start": 1234,
    "document_end": 1345,
    "text_evidence": "Methanotrophs are bacteria that use methane as their primary carbon source.",
    "confidence": 0.95,
    "subject_positions": [{ "start": 0, "end": 13, "sentence_id": 0 }],
    "object_positions": [{ "start": 49, "end": 56, "sentence_id": 0 }]
  }
}
```

**LLM Configuration**:

- Model: `ollama_chat/mistral:7b` (default)
- Temperature: 0.0 (deterministic)
- API Base: `http://localhost:11434` (Ollama server)
- Can be configured to use OpenAI or other providers

**Extraction Features**:

- Entity recognition across multiple types
- Relation extraction with predicates
- Sentence-level source tracking
- Multi-sentence relation mapping
- Confidence scoring
- Fallback handling for unmapped relations

### Stage 4: Figure Detection

**Purpose**: Identify extractable visual content to determine if visual extraction should run

**Input**:

- Docling JSON file

**Process**:

- Analyzes document for figure elements
- Identifies captions and picture references
- Counts extractable figures
- Evaluates figure quality and relevance
- Determines extraction feasibility
- Provides skip reasons if extraction not recommended

**Decision Criteria**:

- At least one caption or picture must exist
- Figures must have associated metadata
- Images must be extractable from PDF
- Content must be informational (not decorative)

**Output**:

- Boolean decision: should_extract (True/False)
- Figure count
- Skip reasons if applicable
- No file output (in-memory decision)

### Stage 5: Visual KG Extraction

**Purpose**: Extract knowledge from figures using vision-language models

**Input**:

- Docling JSON file (for figure metadata)
- PDF file (for actual images)

**Process**:

1. **Figure Parsing**

   - Extract figure metadata from Docling JSON
   - Get captions and provenance information
   - Organize by page number

2. **Image Extraction**

   - Open PDF with PyMuPDF (fitz)
   - Extract embedded images from relevant pages
   - Convert to PIL Image format
   - Preserve image quality and dimensions

3. **Figure Matching**

   - Match Docling figures to PDF images
   - Pair captions with corresponding images
   - Handle multiple figures per page
   - Validate image-caption associations

4. **Visual Analysis**

   - Load Qwen3-VL-4B vision-language model
   - Process each figure with its caption
   - Prompt VLM to extract entities and relationships
   - Parse structured output (subject-predicate-object triples)
   - Add figure metadata and provenance

5. **Result Formatting**
   - Structure triples for database loading
   - Add figure IDs and page numbers
   - Include confidence scores
   - Format consistently with text triples

**Output**:

- Raw visual triples (`research_paper_visual_triples.json`)
- Formatted visual KG file (`research_paper_visual_kg_format_TIMESTAMP.json`)
- Contains:
  - Visual triples with full provenance
  - Figure IDs and page numbers
  - Caption information
  - Image metadata
  - Summary statistics

**Location**:

- Raw: `output/raw_visual_triples/` (cleaned up after formatting)
- Final: `output/visual_triples/`

**VLM Configuration**:

- Model: `Qwen/Qwen3-VL-4B-Instruct`
- Device: Auto-detected (CUDA/MPS/CPU)
- Precision: Float16 for efficiency
- Memory management: Cleanup after each paper

**Visual Triple Structure**:

```json
{
  "subject": "M. capsulatus",
  "predicate": "produces",
  "object": "methanol",
  "section": "Figure 3",
  "pages": [6],
  "figure_id": "page6_fig1",
  "caption": "Methanol production by M. capsulatus over time",
  "source_paper": "research_paper.pdf",
  "confidence": 0.9
}
```

### Stage 6: Output Organization & Reporting

**Purpose**: Structure results and generate processing reports

**Process**:

- Collects processing statistics
- Generates timestamped output files
- Creates processing report with:
  - Success/failure status
  - Processing duration
  - Entity and relation counts (text and visual)
  - Error messages if any
  - Database loading instructions
- Cleans up intermediate files (if enabled)
- Releases GPU resources
- Prints summary to console

**Output**:

- Processing report (`research_paper_processing_report.json`)
- Console summary

**Location**: `output/reports/`

**Report Structure**:

```json
{
  "processing_summary": {
    "pdf_file": "research_paper.pdf",
    "start_time": "2024-11-28T10:30:00",
    "end_time": "2024-11-28T10:35:30",
    "total_duration": 330.5,
    "success": true
  },
  "text_extraction": {
    "success": true,
    "entities": 450,
    "relations": 320,
    "output_file": "output/text_triples/research_paper_kg_results_20241128_103000.json"
  },
  "visual_extraction": {
    "attempted": true,
    "success": true,
    "entities": 45,
    "relations": 38,
    "output_file": "output/visual_triples/research_paper_visual_kg_format_20241128_103000.json"
  },
  "loading_instructions": {
    "text_kg": "python ../knowledge_graph/kg_data_loader.py output/text_triples/research_paper_kg_results_20241128_103000.json",
    "visual_kg": "python ../knowledge_graph/kg_data_loader.py output/visual_triples/research_paper_visual_kg_format_20241128_103000.json"
  },
  "errors": []
}
```

## Output Structure

### Directory Organization

```
output/
””€”€ docling_json/          # Structured document representations
”‚  OK”””€”€ paper.json
””€”€ text_chunks/           # Text chunks with provenance
”‚  OK”””€”€ paper.texts_chunks.jsonl
””€”€ text_triples/          # Final text-based knowledge graphs
”‚  OK”””€”€ paper_kg_results_TIMESTAMP.json
””€”€ raw_visual_triples/    # Intermediate visual extraction (cleaned up)
”‚  OK”””€”€ paper_visual_triples.json
””€”€ visual_triples/        # Final visual knowledge graphs
”‚  OK”””€”€ paper_visual_kg_format_TIMESTAMP.json
”””€”€ reports/              # Processing reports
   OK”””€”€ paper_processing_report.json
```

### File Naming Conventions

- Timestamps: `YYYYMMDD_HHMMSS` format
- Text KG: `{paper_name}_kg_results_{timestamp}.json`
- Visual KG: `{paper_name}_visual_kg_format_{timestamp}.json`
- Reports: `{paper_name}_processing_report.json`
- Chunks: `{paper_name}.texts_chunks.jsonl`

## Usage

### Basic Commands

```bash
# Process all papers in directory
python main.py --all --papers-dir ../papers

# Process single paper
python main.py "../papers/research_paper.pdf"

# Dry run (preview without processing)
python main.py --all --papers-dir ../papers --dry-run

# Force reprocess existing outputs
python main.py --all --papers-dir ../papers --force

# Custom output directory
python main.py --all --papers-dir ../papers --output-dir ./custom_output

# Keep intermediate files (no cleanup)
python main.py --all --papers-dir ../papers --no-cleanup
```

### Command-Line Options

| Option             | Description                      | Default  |
| ------------------ | -------------------------------- | -------- |
| `--all`            | Process all PDFs in directory    | False    |
| `--papers-dir DIR` | Directory containing PDFs        | `papers` |
| `--output-dir DIR` | Output directory                 | `output` |
| `--dry-run`        | Show what would be processed     | False    |
| `--force`          | Force reprocess existing outputs | False    |
| `--no-cleanup`     | Keep intermediate files          | False    |
| `--verbose`        | Detailed logging                 | True     |

### Batch Processing Features

**Duplicate Detection**:

- Uses glob patterns to find duplicates: `Copy of {name}.pdf`, `{name} (1).pdf`
- Automatically skips duplicates
- Reports skipped files

**Skip Existing**:

- Checks for existing output files with any timestamp
- Skips processing if outputs found (unless `--force` used)
- Reports skipped papers

**Progress Tracking**:

- Shows paper X of Y during batch processing
- Reports processing time per paper
- Displays summary statistics at end

**Error Handling**:

- Continues processing remaining papers if one fails
- Logs errors to reports
- Provides final error summary

## Configuration

### LLM Model Configuration

Text extraction uses configurable LLM backends. Edit `text_kg_extractor.py`:

```python
# Ollama (local, free)
model="ollama_chat/mistral:7b"
api_base="http://localhost:11434"

# OpenAI (cloud, paid)
model="gpt-4o-mini"
api_base="https://api.openai.com/v1"
# Set OPENAI_API_KEY environment variable
```

### Vision Model Configuration

Visual extraction uses Qwen3-VL. Edit `visual_kg_extractor.py`:

```python
# Default configuration
model_name="Qwen/Qwen3-VL-4B-Instruct"

# Alternative: Larger model for better accuracy (requires more memory)
model_name="Qwen/Qwen3-VL-7B-Instruct"

# Alternative: Smaller model for faster processing
model_name="Qwen/Qwen3-VL-2B-Instruct"
```

### Resource Management

**Memory Cleanup**:

- Automatic GPU memory cleanup between papers
- Optional intermediate file cleanup
- Garbage collection after model usage

**GPU Configuration**:

- Auto-detects CUDA/MPS/CPU
- Uses Float16 precision for efficiency
- Expandable segments for large models

## Data Loading

### Loading into Dgraph Database

After pipeline processing, load results into knowledge graph database:

```bash
# Load text triples
cd knowledge_graph
python kg_data_loader.py ../kg_gen_pipeline/output/text_triples/paper_kg_results_TIMESTAMP.json

# Load visual triples
python kg_data_loader.py ../kg_gen_pipeline/output/visual_triples/paper_visual_kg_format_TIMESTAMP.json

# Batch load all papers
python batch_load_table_triples.py
```

The loader handles:

- Case-insensitive entity deduplication
- Relation deduplication
- Provenance preservation
- Error handling

## Utilities

### Debug Tools

**Debug Docling JSON**:

```bash
python utils/debug_docling_json.py output/docling_json/paper.json
```

Shows document structure, sections, and figure metadata.

**Debug Provenance**:

```bash
python utils/debug_provenance.py output/text_chunks/paper.texts_chunks.jsonl
```

Displays provenance information for text chunks.

### Table Extraction

The pipeline includes specialized processing for extracting knowledge from tables, which often contain dense, structured information not captured in regular text extraction.

**Why Separate Table Processing**:

Tables contain structured data that requires different handling than prose text:

- Dense information in compact format (rows, columns, cells)
- Relationships encoded in table structure itself
- Often contain numerical data, measurements, and comparisons
- May have complex multi-level headers
- Context spans across cells rather than linear sentences

**Table Extraction Process**:

1. **Table Detection**: Docling identifies tables during PDF parsing
2. **Table Content Extraction**: Raw table text extracted from Docling JSON
3. **Table Chunking**: Table content split into processable segments
4. **Sentence Segmentation**: Table text segmented using spaCy (same as text chunking)
5. **LLM Extraction**: Relations extracted from table content
6. **Provenance Tracking**: Relations linked back to specific tables and pages

**Table-Only Extraction Script** (`extract_tables_only.py`):

This script processes tables WITHOUT reprocessing entire papers, useful for:

- Adding table-based relations to existing knowledge graphs
- Focusing extraction on structured data sources
- Supplementing text-based extraction with table information

**Process Flow**:

```
Existing Docling JSON
   OK†
Load table elements only
   OK†
Create chunks from table content
   OK†
Segment table text into sentences (using spaCy)
   OK†
Run LLM extraction on table chunks
   OK†
Output supplemental kg_format files (table relations only)
   OK†
Load alongside existing data
```

**Implementation Details**:

```python
# From extract_tables_only.py
class TableOnlyExtractor:
    def __init__(self):
        # Initialize spaCy for sentence segmentation
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            print("Loaded spaCy for sentence segmentation")
        except:
            print("Warning: spaCy not available, using basic sentence splitting")
            self.nlp = None

    def _segment_text_into_sentences(self, text: str):
        """Segment table text into sentences for span mapping."""
        if self.nlp:
            doc = self.nlp(text)
            for sent_idx, sent in enumerate(doc.sents):
                # Track sentence boundaries for provenance
                sentences.append({
                    "sentence_id": sent_idx,
                    "text": sent.text.strip(),
                    "char_start": sent.start_char,
                    "char_end": sent.end_char
                })
```

**Table-Specific Features**:

1. **Table ID Tracking**: Each relation marked with source table identifier
2. **Cell-Level Provenance**: Tracks which table cells contributed to relations
3. **Row/Column Context**: Preserves table structure information
4. **Multi-Table Processing**: Handles papers with multiple tables
5. **Deduplication**: Avoids extracting same relations from text and tables

**Commands**:

**Extract Tables from Single Paper**:

```bash
python extract_tables_only.py --paper "Research Paper Name"
```

Processes tables from one specific paper.

**Extract Tables from All Papers**:

```bash
python extract_tables_only.py
```

Processes all papers in the corpus for table extraction.

**Batch Table Extraction**:

```bash
python batch_extract_tables.py --papers-dir ../papers
```

Process multiple papers for table extraction with progress tracking.

**Add Table IDs to Relations**:

```bash
python add_table_ids_to_relations.py
```

Post-process to add table identifiers to relations for provenance.

**Output Structure**:

Table extraction creates supplemental output files:

```
output/
”””€”€ table_triples/
   OK”””€”€ research_paper_table_kg_TIMESTAMP.json
```

**Table Relation Format**:

```json
{
  "subject": "Temperature",
  "predicate": "affects",
  "object": "CH4 flux",
  "section": "Results",
  "pages": [8],
  "table_id": "Table_2",
  "source_span": {
    "text_evidence": "CH4 flux increased from 45 to 120 mg m-2 d-1 with temperature rise from 15Â°C to 25Â°C",
    "char_positions": { "start": 23, "end": 109 },
    "sentences": [
      "CH4 flux increased from 45 to 120 mg m-2 d-1 with temperature rise from 15Â°C to 25Â°C"
    ]
  },
  "confidence": 0.92
}
```

**Integration with Main Pipeline**:

Table triples can be loaded into the knowledge graph alongside text triples:

```bash
# Load text triples
python knowledge_graph/kg_data_loader.py paper_text_kg.json

# Load table triples separately
python knowledge_graph/kg_data_loader.py paper_table_kg.json
```

The knowledge graph deduplication system ensures relations extracted from both text and tables are merged appropriately.

**Performance Characteristics**:

- Table detection: < 1 second (already in Docling JSON)
- Table chunking: 1-2 seconds per table
- Table extraction: 5-15 seconds per table (depends on table size)
- Average paper: 2-5 tables, 30-90 seconds total table processing

**Use Cases**:

1. **Data-Heavy Papers**: Extract structured experimental results
2. **Comparison Tables**: Capture comparative relationships between entities
3. **Measurement Tables**: Extract quantitative relationships
4. **Summary Tables**: Capture aggregated information
5. **Supplemental Material**: Process supplementary tables separately

## Performance Characteristics

### Processing Time

**Per Paper Average**:

- PDF conversion: 10-30 seconds
- Text chunking: 5-10 seconds
- Text extraction: 2-5 minutes (depends on length and LLM)
- Figure detection: 1-2 seconds
- Visual extraction: 30-60 seconds per figure
- Total: 3-10 minutes per paper

**Factors Affecting Speed**:

- Paper length and complexity
- Number of figures
- LLM backend (local vs cloud)
- GPU availability for visual extraction
- Model size (7B vs 4B parameters)

### Resource Requirements

**Memory**:

- Text extraction: 2-4 GB RAM
- Visual extraction: 6-8 GB GPU memory (4B model)
- Recommended: 16 GB RAM, 8+ GB GPU

**Storage**:

- Per paper: 5-20 MB (all outputs)
- Docling JSON: 1-5 MB
- Text triples: 1-5 MB
- Visual triples: 500 KB - 2 MB

**Dependencies**:

- Python 3.8+
- PyTorch (for visual extraction)
- Ollama (for local LLM)
- Docling library
- KG-GEN library
- PyMuPDF (fitz)
- Transformers (Hugging Face)
- **spaCy** (`en_core_web_sm` model) - for sentence segmentation in text and table chunking
  - Install: `pip install spacy`
  - Download model: `python -m spacy download en_core_web_sm`
  - Used by: `text_chunker.py`, `extract_tables_only.py`
  - Fallback available if not installed (basic regex splitting)

## Known Issues and Limitations

### Sentence Segmentation

**Issue**: Sentence boundary detection critical for accurate provenance

**Background**:

The pipeline relies heavily on accurate sentence segmentation for:

- Mapping extracted relations to specific sentences
- Calculating character offsets for provenance tracking
- Creating source_span data for relation validation
- Enabling fine-grained citation of extraction sources

**spaCy vs. Regex Comparison**:

| Aspect            | spaCy (Primary)                       | Regex (Fallback)              |
| ----------------- | ------------------------------------- | ----------------------------- |
| Accuracy          | High - handles complex cases          | Moderate - simple rules       |
| Abbreviations     | Correctly handles "Dr.", "Fig.", etc. | May split incorrectly         |
| Quotes            | Preserves quoted sentences            | May break at internal periods |
| Scientific Text   | Trained on diverse corpus             | Generic patterns only         |
| Character Offsets | Precise start/end positions           | Approximate boundaries        |
| Performance       | Fast (NLP optimized)                  | Faster (simple regex)         |
| Dependency        | Requires model download               | No external dependencies      |

**Recommendation**: Always use spaCy for production extraction. The fallback is provided for convenience but may reduce relation mapping quality.

**Installation**:

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

**Verification**:

Check if spaCy is working correctly:

```python
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp("This is a test. Dr. Smith found Fig. 1 interesting.")
for sent in doc.sents:
    print(f"Sentence: {sent.text}")
# Should correctly identify 2 sentences, not 4
```

### Text Extraction

**Issue**: Some relations may not map to specific sentences

- **Cause**: LLM extracts relations that span multiple disconnected sentences
- **Workaround**: Falls back to chunk-level provenance with lower confidence score

**Issue**: Entity name variations cause duplicate entities

- **Cause**: "Methanotrophs" vs "methanotrophs" treated as different
- **Solution**: Database loader performs case-insensitive deduplication

### Visual Extraction

**Issue**: Some figures may not be extractable

- **Cause**: PDF image encoding, embedded vs vector graphics
- **Workaround**: Figure detection pre-filters non-extractable figures

**Issue**: Visual extraction requires significant GPU memory

- **Cause**: Vision-language models are large (4B+ parameters)
- **Solution**: Automatic memory cleanup between papers, use smaller models if needed

**Issue**: Not all visual relationships are captured accurately

- **Cause**: Complex diagrams, overlapping elements, unclear visual hierarchy
- **Limitation**: VLM accuracy varies with figure complexity

### Processing

**Issue**: Docling conversion may fail on some PDFs

- **Cause**: Unsupported PDF versions, encryption, complex layouts
- **Workaround**: Pipeline continues with remaining papers, logs errors

**Issue**: Papers with "Copy of" or "(1)" in filename are treated as duplicates

- **Cause**: Glob pattern duplicate detection
- **Solution**: Rename files or use `--force` flag

## Troubleshooting

### Common Issues

**"spaCy model not found" error**:

```bash
# Install spaCy and download English model
pip install spacy
python -m spacy download en_core_web_sm

# Verify installation
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy loaded successfully')"
```

**Warning: "spaCy not available, using basic sentence splitting"**:

- Not a critical error - pipeline will continue with regex fallback
- For production use, install spaCy for better accuracy
- May result in less precise sentence boundaries and provenance
- Relations may have lower confidence scores without accurate sentence mapping

**"Model not found" error**:

```bash
# Ensure Ollama is running and model is installed
ollama pull mistral:7b
```

**"CUDA out of memory" error**:

```python
# Use smaller vision model or CPU
model_name="Qwen/Qwen3-VL-2B-Instruct"
# Or force CPU in visual_kg_extractor.py
device_map="cpu"
```

**"Docling conversion failed"**:

- Check PDF is not encrypted
- Ensure PDF is valid format
- Try re-downloading the PDF

**"No figures detected" but paper has figures**:

- Check Docling JSON has picture/caption elements
- Some PDFs embed figures as vector graphics (not extractable)
- Use `utils/debug_docling_json.py` to inspect structure

**"No tables found" but paper has tables**:

- Check Docling JSON `tables` array
- Some PDFs have tables as images (not extractable as structured data)
- Tables with complex layouts may not be detected by Docling
- Use `utils/debug_docling_json.py` to inspect table extraction

**Table extraction produces no relations**:

- Verify table content is meaningful (not just formatting/layout tables)
- Check table text in Docling JSON is readable
- Some tables are purely numerical without textual relationships
- LLM may not identify extractable relations from certain table formats

**Sentence offsets incorrect in output**:

- Ensure spaCy is installed and loaded (check startup messages)
- Regex fallback provides approximate offsets only
- Character encoding issues in PDF may affect offset calculation
- Check source PDF text extraction quality

### Debug Mode

Enable verbose logging for detailed information:

```python
orchestrator = MasterKGOrchestrator(verbose=True)
```

## Future Enhancements

### Planned Features

- Table content extraction and KG generation
- Cross-paper entity linking
- Automated quality validation
- Incremental processing (only new papers)
- Parallel processing of multiple papers
- API endpoint for on-demand extraction
- Support for additional document formats (DOCX, HTML)

### Potential Improvements

- Better entity deduplication using embeddings
- Multi-modal fusion (combining text and visual extractions)
- Confidence calibration for relations
- Hierarchical entity type classification
- Temporal relation extraction
- Citation graph integration

## Related Documentation

- `README.md` - Project overview and setup
- `knowledge_graph/API_ENDPOINTS.md` - API documentation
- `Notes/TABLE_SUPPORT_IMPLEMENTATION.md` - Table extraction details
- `Notes/VISUAL_REVIEW_IMPLEMENTATION_PLAN.md` - Vision model architecture
- `Notes/FIGURE_TABLE_API_REFERENCE.md` - Visual element API guide
