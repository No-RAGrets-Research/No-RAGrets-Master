# Knowledge Graph Extraction Pipeline

A comprehensive pipeline for extracting structured knowledge graphs from scientific research papers using advanced NLP and computer vision models.

## Overview

This pipeline converts PDF research papers into structured knowledge graphs through automated text and visual content analysis. It supports batch processing of paper collections with intelligent duplicate detection and comprehensive output organization.

### Pipeline Stages

1. **PDF Conversion** - Convert PDFs to structured Docling JSON format
2. **Text Chunking** - Break documents into processable text chunks with provenance tracking
3. **Text KG Extraction** - Extract entities and relations from text using LLM models
4. **Figure Detection** - Identify and extract figures, charts, and diagrams
5. **Visual KG Extraction** - Extract knowledge from images using Qwen-VL vision models
6. **Output Organization** - Structure results for database loading or further analysis

## Quick Start

### Basic Usage

```bash
# Process all papers in the papers directory
python main.py --all --papers-dir ../papers

# Process a single paper
python main.py "../papers/research_paper.pdf"

# See what would be processed without running
python main.py --all --papers-dir ../papers --dry-run

# Force reprocess existing outputs
python main.py --all --papers-dir ../papers --force
```

### Command Options

```bash
python main.py --help
```

**Key Options:**

- `--all` - Process all PDF files in specified directory
- `--papers-dir DIR` - Directory containing PDF files (default: papers)
- `--output-dir DIR` - Output directory (default: output)
- `--dry-run` - Show what would be processed without running
- `--force` - Force reprocessing even if outputs exist
- `--no-cleanup` - Keep all intermediate files

## Pipeline Components

### Core Processing (`core/`)

**`pipeline_orchestrator.py`** - Main batch processing orchestrator

- Discovers papers in directory
- Manages sequential processing workflow
- Handles duplicate detection using glob patterns
- Provides progress reporting and error handling

**`pdf_converter.py`** - PDF to Docling JSON conversion

- Extracts structured document layout
- Preserves text, tables, figures, and metadata
- Handles various PDF formats and layouts

**`text_chunker.py`** - Text chunking with provenance

- Creates processable text segments
- Maintains document structure and page references
- Tracks source locations for traceability

**`text_kg_extractor.py`** - Text knowledge graph extraction

- Extracts entities and relationships using LLM
- Processes text chunks with context preservation
- Generates structured triple format output

**`visual_kg_extractor.py`** - Visual knowledge graph extraction

- Processes figures, charts, and diagrams
- Uses Qwen-VL vision-language models
- Extracts knowledge from visual content

**`visual_kg_formatter.py`** - Visual triple formatting

- Formats visual extraction results for database loading
- Ensures consistency with text extraction format
- Handles visual-specific metadata

**`figure_detection.py`** - Figure identification and processing

- Detects extractable visual content
- Handles various image formats and layouts
- Prepares figures for vision model processing

### Utilities (`utils/`)

**`debug_docling_json.py`** - Debug document structure

- Inspect Docling JSON format and content
- Troubleshoot PDF conversion issues
- Analyze document layout and extraction

**`debug_provenance.py`** - Debug paper provenance

- Trace knowledge extraction back to source
- Verify chunk-to-source mapping
- Analyze extraction accuracy

### Testing (`tests/`)

**`run_tests.py`** - Main test runner

- Comprehensive test suite execution
- Unit and integration test categories
- Validation of pipeline components

**Unit Tests (`tests/unit/`)**:

- `test_chunker.py` - Text chunking functionality
- `test_kg_extractor.py` - Knowledge extraction validation

**Integration Tests (`tests/integration/`)**:

- `test_pipeline.py` - End-to-end pipeline testing
- `test_steps.py` - Step-by-step validation

## Output Structure

After processing, results are organized in the `output/` directory:

```
output/
├── docling_json/           # Structured PDF content
│   └── paper_name.json
├── text_chunks/            # Text chunks with provenance
│   └── paper_name.texts_chunks.jsonl
├── text_triples/           # Knowledge graphs from text
│   └── paper_name_kg_results_timestamp.json
├── visual_triples/         # Knowledge graphs from figures
│   └── paper_name_visual_kg_format_timestamp.json
└── reports/                # Processing summaries
    ├── paper_name_kg_summary_timestamp.json
    └── paper_name_processing_report.json
```

### Output File Types

**Docling JSON** - Structured document content with:

- Text content organized by sections
- Table data in structured format
- Figure locations and metadata
- Document layout information

**Text Chunks** - JSONL format with:

- Individual text segments
- Page and section provenance
- Chunk index and metadata
- Source document references

**Text Triples** - Knowledge graph results with:

- Subject-predicate-object triples
- Supporting text evidence
- Provenance information
- Confidence scores

**Visual Triples** - Visual knowledge extraction with:

- Entities and relations from figures
- Image-specific metadata
- Visual evidence references
- Figure source information

**Reports** - Processing summaries with:

- Extraction statistics
- Processing timing
- Error logs and warnings
- Success/failure status

## Advanced Usage

### Batch Processing Options

```bash
# Process papers with custom output location
python main.py --all --papers-dir ../papers --output-dir custom_output

# Process only papers not already processed
python main.py --all --papers-dir ../papers

# Keep all intermediate files for debugging
python main.py --all --papers-dir ../papers --no-cleanup
```

### Single Paper Processing

```bash
# Process specific paper
python main.py "../papers/biochemistry/enzyme_study.pdf"

# Process with existing Docling JSON
python main.py paper.pdf --docling-json existing.json
```

### Debugging and Troubleshooting

```bash
# Debug document structure
python utils/debug_docling_json.py output/docling_json/paper.json

# Debug provenance tracking
python utils/debug_provenance.py output/docling_json/paper.json

# Run tests
python tests/run_tests.py

# Run specific test category
python tests/run_tests.py --unit
python tests/run_tests.py --integration
```

## Configuration

### Model Configuration

The pipeline uses several models that can be configured:

**Text Processing**:

- Default LLM: Configurable in `text_kg_extractor.py`
- Chunk size: Adjustable in `text_chunker.py`

**Visual Processing**:

- Vision model: Qwen-VL-4B (configurable in `visual_kg_extractor.py`)
- Figure processing: Adjustable thresholds in `figure_detection.py`

### Processing Parameters

Key parameters that can be adjusted:

- **Chunk overlap**: Text chunking overlap size
- **Extraction prompts**: LLM prompts for knowledge extraction
- **Visual processing**: Figure detection and processing thresholds
- **Output formats**: Triple formatting and metadata inclusion

## Database Integration

### Loading Results into Dgraph

After processing papers, results can be loaded into a graph database:

```bash
# Navigate to knowledge graph directory
cd ../knowledge_graph

# Start Dgraph database
docker compose up -d

# Load schema
python dgraph_manager.py

# Load KG results
python kg_data_loader.py ../kg_gen_pipeline/output/text_triples/results.json
```

### Database Setup

**Prerequisites**:

- Docker Desktop installed and running
- Dgraph containers started

**Access Points**:

- GraphQL API: http://localhost:8080/graphql
- Admin Interface: http://localhost:8080/admin
- Web UI (Ratel): http://localhost:8080/ratel

## Troubleshooting

### Common Issues

**Processing Failures**:

```bash
# Check which papers would be processed
python main.py --all --papers-dir ../papers --dry-run

# Process individual paper to isolate issues
python main.py "../papers/problematic_paper.pdf"
```

**Memory Issues**:

- Process papers individually instead of batch processing
- Reduce chunk size in text processing
- Close other applications to free memory

**Vision Model Issues**:

```bash
# Check MPS availability (macOS)
python -c "import torch; print(torch.backends.mps.is_available())"

# Check CUDA availability (Linux/Windows)
python -c "import torch; print(torch.cuda.is_available())"
```

**Missing Dependencies**:

```bash
# Reinstall requirements
pip install -r ../requirements.txt

# Check specific package versions
pip list | grep transformers
pip list | grep torch
```

### Debug Output

Enable verbose output for troubleshooting:

- Check processing logs in `output/reports/`
- Use debug utilities in `utils/` directory
- Run tests to validate component functionality

## Development

### Adding New Components

1. **Create new processor** in `core/` directory
2. **Update orchestrator** to include new processing step
3. **Add tests** in appropriate test directory
4. **Update documentation** with new functionality

### Modifying Existing Components

**Text Processing**:

- Edit `core/text_chunker.py` for chunking strategies
- Modify `core/text_kg_extractor.py` for extraction models

**Visual Processing**:

- Edit `core/visual_kg_extractor.py` for vision models
- Modify `core/figure_detection.py` for detection algorithms

**Output Formatting**:

- Update formatters for different output requirements
- Modify report generation for additional metrics

### Testing Changes

```bash
# Run full test suite
python tests/run_tests.py

# Run specific tests
python tests/run_tests.py --unit
python tests/run_tests.py --integration

# Add new tests
# - Create test files in tests/unit/ or tests/integration/
# - Follow existing test patterns
# - Include both positive and negative test cases
```

## Pipeline Architecture

### Processing Flow

```
PDF Input → Docling JSON → Text Chunks → Text KG → Formatted Output
              ↓              ↓            ↓
          Figure Detection → Visual KG → Formatted Output
                                ↓
                          Combined Results
```

### Data Flow

1. **Input**: PDF files from specified directory
2. **Conversion**: PDF → structured Docling JSON
3. **Text Path**: JSON → chunks → text triples
4. **Visual Path**: JSON → figures → visual triples
5. **Output**: Organized results ready for database loading

### Error Handling

- **Paper-level isolation**: Errors in one paper don't affect others
- **Graceful degradation**: Continue processing if non-critical components fail
- **Comprehensive logging**: Detailed error reporting and troubleshooting info
- **Recovery mechanisms**: Skip problematic papers, continue with batch

This pipeline provides a robust, scalable solution for converting research papers into structured knowledge graphs suitable for database storage and analysis.
