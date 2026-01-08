# No-RAGrets Truth Experiments and Pipelines

An automated pipeline that converts scientific research papers (PDFs) into structured knowledge graphs and provides AI-powered quality assessment. The system extracts entities, relationships, and concepts from text and visual content (figures, tables, diagrams), then enables comprehensive paper review using specialized evaluation rubrics.

**Key Features**: Batch paper processing, text and visual knowledge extraction, provenance tracking, graph database integration, and AI-powered paper review with vision models.

## Overview

This system provides two major capabilities:

1. **Knowledge Graph Generation**: Automatically converts scientific papers into structured knowledge graphs capturing entities (chemicals, processes, organisms) and their relationships from both text and visual elements.

2. **Paper Quality Review**: AI-powered evaluation of papers using specialized rubrics for methodology, reproducibility, rigor, data quality, presentation, and references. Supports both text and visual content assessment.

### What It Does

**Knowledge Extraction**:

- Identifies entities and relationships from text, figures, tables, and diagrams
- Batch processes entire paper collections with duplicate detection
- Maintains provenance links to source documents and page locations
- Outputs structured data for graph database loading

**Paper Review**:

- Evaluates papers using 6 specialized quality rubrics
- Assesses figures using vision models (GPT-4o, Qwen-VL)
- Analyzes tables using structured data evaluation
- Provides tier-based assessments with actionable recommendations
- Supports both OpenAI (cloud) and Ollama (local) model providers

## Prerequisites

Before setting up the system, ensure you have the following:

**Required**:

- Python 3.8+
- Virtual environment tool (venv)
- Git

**Optional** (depending on use case):

- Docker Desktop (for Dgraph database)
- Ollama (for local/free LLM models)
- OpenAI API key (for cloud LLM models)

### Install Python Dependencies

1. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the root directory (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` to configure your LLM providers:

```bash
# For OpenAI (cloud, paid)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
VISION_PROVIDER=openai
VISION_MODEL=gpt-4o

# For Ollama (local, free)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434/v1
VISION_PROVIDER=qwen
VISION_MODEL=qwen3-vl:4b
VISION_BASE_URL=http://localhost:11434/v1

# Hybrid approach (Ollama for text, OpenAI for figures)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
VISION_PROVIDER=openai
VISION_MODEL=gpt-4o
OPENAI_API_KEY=sk-your-key-here
```

**Note**: After changing `.env`, restart the API server to apply changes.

## Quick Start

### 1. Set Up Environment

```bash
# Navigate to the pipeline directory
cd pipeline

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and preferences
```

### 2. Add Your Papers

Place PDF research papers in the `papers/` directory:

```bash
# Copy your research papers
cp ~/Downloads/*.pdf papers/
```

### 3. Process Papers into Knowledge Graphs

```bash
cd kg_gen_pipeline

# Process all papers in the papers directory
python main.py --all --papers-dir ../papers

# Or process a single paper
python main.py "../papers/your_paper.pdf"

# See what would be processed without running
python main.py --all --papers-dir ../papers --dry-run
```

### 4. Start the API Server (for Paper Review)

```bash
cd knowledge_graph
python api.py
```

The API server will start on http://localhost:8001 (or next available port).

**Access Documentation**:

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### 5. View Results

**Knowledge Graph Results** are in `kg_gen_pipeline/output/`:

- `text_triples/` - Entities and relationships from text
- `visual_triples/` - Knowledge from figures and diagrams
- `text_chunks/` - Document sections with source tracking
- `reports/` - Processing summaries

**Paper Review** via API endpoints (see API documentation for details).

## Knowledge Graph Extraction

### Adding Papers to the System

1. **Place PDF files** in the `papers/` directory:

```bash
# Copy individual papers
cp ~/Downloads/research_paper.pdf papers/

# Copy multiple papers
cp ~/research_files/*.pdf papers/
```

2. **Process papers** through the extraction pipeline:

```bash
cd kg_gen_pipeline

# Process all papers at once (recommended)
python main.py --all --papers-dir ../papers

# Process specific papers
python main.py "../papers/research_paper.pdf"
```

### Processing Pipeline Workflow

The system processes papers through these stages:

1. **PDF to Docling JSON**: Extract structured content with document layout
2. **JSON to Text Chunks**: Create sections with provenance tracking
3. **Text to Knowledge Graph**: Extract entities and relationships using LLM
4. **Figures to Visual KG**: Extract knowledge from images using vision models
5. **Tables to Structured KG**: Extract knowledge from tables using Docling structure
6. **Results to Formatted Output**: Organize for database loading

### Pipeline Commands

```bash
# Show available options
python main.py --help

# Process papers with custom output location
python main.py --all --papers-dir ../papers --output-dir custom_output

# Skip cleanup of intermediate files
python main.py --all --papers-dir ../papers --no-cleanup

# Force reprocess even if outputs exist
python main.py --all --papers-dir ../papers --force
```

### Processing Output Structure

Each paper generates organized outputs:

```
output/
├── docling_json/           # Structured PDF content
├── text_chunks/            # Text chunks with provenance
├── text_triples/           # Knowledge graphs from text
├── visual_triples/         # Knowledge graphs from figures and tables
└── reports/                # Processing summaries
```

## Paper Review System

The system provides comprehensive AI-powered paper quality assessment using specialized evaluation rubrics.

### Review Capabilities

**Text Review** (6 rubrics):

1. **Methodology** - Research design and experimental approach
2. **Reproducibility** - Code/data availability and replication details
3. **Rigor** - Statistical analysis and robustness
4. **Data** - Dataset quality and documentation
5. **Presentation** - Clarity, organization, writing quality
6. **References** - Citation completeness and literature coverage

**Visual Review**:

- **Figures** - Assessed using vision models for clarity, labels, legends, chart types
- **Tables** - Evaluated using structured data analysis for completeness and formatting

### API Endpoints

**Complete Paper Review**:

```bash
# Review entire paper with all 6 rubrics + synthesis
curl -X POST http://localhost:8001/api/review \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "paper.pdf"}'
```

**Single Rubric Review**:

```bash
# Review with specific rubric only
curl -X POST http://localhost:8001/api/review/rubric/methodology \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "paper.pdf"}'
```

**Figure Review** (base64 image from frontend):

```bash
# Review figure using vision model
curl -X POST http://localhost:8001/api/review/figure \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "data:image/png;base64,iVBORw0K...",
    "rubric": "presentation"
  }'
```

**Table Review** (Docling JSON from frontend):

```bash
# Review table using structured data
curl -X POST http://localhost:8001/api/review/table \
  -H "Content-Type: application/json" \
  -d '{
    "table_data": {
      "caption": {"text": "Table 1. Results"},
      "text": "Sample | Result\nA | 125\nB | 98"
    },
    "rubric": "data"
  }'
```

### Review Architecture

**Text-Based Review**:

- Uses `LLM_PROVIDER` setting from `.env`
- Models: OpenAI (gpt-4o-mini) or Ollama (llama3.1:8b)
- Cost: $0.00-0.02 per paper (OpenAI) or free (Ollama)
- Speed: 30-60 seconds (OpenAI) or 3-5 minutes (Ollama)

**Figure Review**:

- Uses `VISION_PROVIDER` setting from `.env`
- Models: OpenAI (gpt-4o) or Ollama (qwen3-vl:4b, llava)
- Cost: $0.03-0.10 per paper (OpenAI) or free (Ollama)
- Speed: 5-10 seconds per figure (OpenAI) or 30-60 seconds (Ollama)

**Table Review**:

- Uses text model (`LLM_PROVIDER`) not vision model
- Analyzes structured Docling table data
- Same cost/speed as text review

### Switching Between Providers

**Use OpenAI** (faster, more consistent, paid):

```bash
# Edit .env
LLM_PROVIDER=openai
VISION_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Restart API server
cd knowledge_graph
# Stop server (Ctrl+C in terminal)
python api.py
```

**Use Ollama** (free, local, slower):

```bash
# Install Ollama from https://ollama.ai

# Pull models
ollama pull llama3.1:8b
ollama pull qwen3-vl:4b

# Edit .env
LLM_PROVIDER=ollama
VISION_PROVIDER=qwen

# Restart API server
```

**Hybrid Approach** (recommended):

```bash
# Edit .env
LLM_PROVIDER=ollama          # Free for text
VISION_PROVIDER=openai       # Paid for figures (better quality)

# Cost: ~$0.03-0.10 per paper (figures only)
# Speed: 3 min for text + 30 sec for figures
```

## Database Integration

### Loading Data into Dgraph

After processing papers, load results into a graph database:

```bash
cd knowledge_graph

# Start Dgraph database
docker compose up -d

# Load schema
python load_schema.py

# Load KG results (text triples)
python kg_data_loader.py ../kg_gen_pipeline/output/text_triples/paper_results.json

# Load visual triples (figures and tables)
python batch_load_table_triples.py
```

**Note on Paper Counts**: The knowledge graph may contain fewer papers than PDFs in the `papers/` directory. Some papers may have been skipped during processing due to Docling compatibility issues or manual curation choices. Check the processing reports in `kg_gen_pipeline/output/reports/` for details on which papers were successfully processed.

### Database Interfaces

- **Dgraph Native**: http://localhost:8080
- **Admin Interface**: http://localhost:8080/admin
- **Ratel UI**: http://localhost:8080/ratel

### Querying the Knowledge Graph

The API provides endpoints for searching entities, relations, papers, and provenance:

```bash
# Search for entities (extracted concepts like "Methane", "GHG")
curl "http://localhost:8001/api/entities/search?q=methanol&limit=10"

# Search for papers by title or filename
curl "http://localhost:8001/api/papers/search?q=priyadarsini&limit=10"

# Get entity connections (outgoing and incoming relations)
curl "http://localhost:8001/api/entities/Methane/connections?max_relations=100"

# Search relations by predicate
curl "http://localhost:8001/api/relations/search?predicate=produces&limit=5"

# Get relations from specific figure
curl "http://localhost:8001/api/relations/by-figure?paper_id=paper.pdf&figure_id=page5_fig0"

# Get relations from specific table
curl "http://localhost:8001/api/relations/by-table?paper_id=paper.pdf&table_id=page3_table0"

# List all papers in the knowledge graph
curl "http://localhost:8001/api/papers"
```

**Note**: The entity connections endpoint automatically filters out malformed relations in the database. See the Known Data Quality Issues section for details.

See `knowledge_graph/API_ENDPOINTS.md` for complete API documentation.

## Project Structure

### Debug and Utilities

The pipeline includes debugging tools for troubleshooting:

```bash
# Debug Docling JSON structure
python utils/debug_docling_json.py path/to/paper.json

# Debug paper provenance information
python utils/debug_provenance.py path/to/paper.json
```

### Testing the Pipeline

Run the test suite to verify pipeline functionality:

```bash
cd kg_gen_pipeline

# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --unit
python tests/run_tests.py --integration
```

### Pipeline Components

The organized pipeline consists of:

**Core Processing (`core/`)**:

- `pipeline_orchestrator.py` - Main batch processing orchestrator
- `pdf_converter.py` - PDF to Docling JSON conversion
- `text_chunker.py` - Text chunking with provenance
- `text_kg_extractor.py` - Text knowledge graph extraction
- `visual_kg_extractor.py` - Visual knowledge graph extraction
- `visual_kg_formatter.py` - Format visual triples for database

**Utilities (`utils/`)**:

- `debug_docling_json.py` - Debug document structure
- `debug_provenance.py` - Debug paper provenance

## Database Integration

### Loading Data into Dgraph

After processing papers, load the results into a graph database:

```bash
cd knowledge_graph

# Start Dgraph database
docker compose up -d

# Load schema
python dgraph_manager.py

# Load KG results
python kg_data_loader.py ../kg_gen_pipeline/output/text_triples/paper_results.json
```

### Database Interfaces

**Dgraph Native Interface**: http://localhost:8080  
**Admin Interface**: http://localhost:8080/admin  
**Web UI (Ratel)**: http://localhost:8080/ratel

Example DQL query:

```dql
{
  entities(func: alloftext(name, "methanol")) {
    uid
    name
    type
    namespace
  }
}
```

## Output Formats

### Knowledge Graph JSON Structure

Each processed paper generates knowledge graph results in structured JSON:

```json
{
  "paper_info": {
    "title": "Paper Title",
    "file_path": "/path/to/paper.pdf"
  },
  "kg_results": [
    {
      "subject": "methanol",
      "predicate": "is_produced_by",
      "object": "Methylosinus trichosporium",
      "text_evidence": "Supporting text from paper",
      "provenance": {
        "chunk_index": 5,
        "page_number": 3
      }
    }
  ]
}
```

### Processing Reports

Each processing run generates detailed reports:

- **Processing status** - Success/failure per paper
- **Statistics** - Entities and relations extracted
- **Timing information** - Processing duration
- **Error logs** - Issues encountered during processing

## Project Structure

```
├── papers/                      # PDF research papers (input)
├── .env                         # Environment configuration (create from .env.example)
├── .env.example                 # Example environment configuration
├── kg_gen_pipeline/             # Knowledge extraction pipeline
│   ├── main.py                  # Primary entry point
│   ├── core/                    # Core processing components
│   │   ├── pipeline_orchestrator.py  # Batch processing
│   │   ├── pdf_converter.py           # PDF to Docling conversion
│   │   ├── text_chunker.py            # Text chunking with provenance
│   │   ├── text_kg_extractor.py       # Text knowledge extraction
│   │   ├── visual_kg_extractor.py     # Visual knowledge extraction
│   │   └── visual_kg_formatter.py     # Visual triple formatting
│   ├── utils/                   # Utilities
│   └── output/                  # Processing results
│       ├── docling_json/              # Structured documents
│       ├── text_chunks/               # Text chunks with provenance
│       ├── text_triples/              # Text knowledge graphs
│       ├── visual_triples/            # Visual knowledge graphs
│       └── reports/                   # Processing summaries
├── knowledge_graph/             # Database and API
│   ├── api.py                         # REST API server
│   ├── dgraph_manager.py              # Database management
│   ├── kg_data_loader.py              # Load text triples
│   ├── batch_load_table_triples.py    # Load visual triples
│   ├── docker-compose.yaml            # Dgraph setup
│   ├── schema.graphql                 # Database schema
│   ├── API_ENDPOINTS.md               # Complete API documentation
│   ├── llm_review/                    # Paper review system
│   │   ├── prompts/                   # 6 evaluation rubrics
│   │   └── utils/                     # Review utilities
│   │       ├── llm_runner.py          # Text model interface
│   │       ├── vision_runner.py       # Vision model interface
│   │       ├── text_loader.py         # Load papers
│   │       └── figure_extractor.py    # Extract figures
│   └── scripts/                       # Helper scripts
└── requirements.txt             # Python dependencies
```

## Advanced Usage

### Debug and Utilities

The pipeline includes debugging tools:

```bash
# Debug Docling JSON structure
python utils/debug_docling_json.py path/to/paper.json

# Debug paper provenance information
python utils/debug_provenance.py path/to/paper.json
```

### Testing

Run tests to verify functionality:

```bash
cd kg_gen_pipeline

# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --unit
python tests/run_tests.py --integration
```

## Configuration Details

### LLM Provider Options

**OpenAI** (Cloud, Paid):

- Best quality and consistency
- Fastest processing
- Cost: ~$0.01-0.02 per paper (text) + $0.03-0.10 (figures)
- Requires API key from https://platform.openai.com

**Ollama** (Local, Free):

- Free to use
- Slower processing
- Requires local installation and model downloads
- Install from https://ollama.ai

**Hybrid** (Recommended):

- Ollama for text review (free)
- OpenAI for figure review (paid, better quality)
- Cost: ~$0.03-0.10 per paper (figures only)

### Vision Model Options

**For Figures**:

- `gpt-4o` (OpenAI) - Best quality, $0.03-0.10 per paper
- `qwen3-vl:4b` (Ollama) - Free, requires 32x32 minimum image size
- `llava` (Ollama) - Free, general purpose vision model

**For Tables**:

- Uses text models (LLM_PROVIDER), not vision models
- Analyzes structured Docling table data
- More accurate and cheaper than vision analysis

## Troubleshooting

### Processing Issues

If papers fail to process:

```bash
# Check which papers would be processed
python main.py --all --papers-dir ../papers --dry-run

# Run with verbose output
python main.py --all --papers-dir ../papers --verbose

# Process individual paper to isolate issues
python main.py "../papers/problematic_paper.pdf"
```

### Common Issues

**Missing Dependencies**:

```bash
pip install -r requirements.txt
```

**Environment Variables Not Loading**:

- After editing `.env`, restart the API server
- `reload=True` in uvicorn only reloads code, not environment variables

**Vision Model Empty Responses**:

- Check if using correct provider in `.env`
- Restart API server after changing `.env`
- For Qwen: Ensure images are at least 32x32 pixels

**Memory Issues**:

```bash
# Process papers individually for large files
python main.py "../papers/large_paper.pdf"
```

**Ollama Connection Issues**:

```bash
# Check Ollama is running
ollama list

# Start Ollama if needed (runs automatically on macOS)
# Or check http://localhost:11434
```

### Database Issues

If using Dgraph:

```bash
# Check Docker status
docker ps

# Restart containers
cd knowledge_graph
docker compose down
docker compose up -d

# View logs
docker compose logs
```

### Known Data Quality Issues

The knowledge graph database currently contains malformed data that causes GraphQL query errors:

**Symptoms**:

- 500 Internal Server Error when querying entity connections
- GraphQL errors: "Non-nullable field 'predicate' was not present in result from Dgraph"
- Null values appearing in relation arrays at specific indices
- Affects high-connection entities: Methane (121 connections), Methanotrophs (104), M. capsulatus (15), Methane monooxygenase (14), etc.

**Root Cause**:

- Database contains relations with missing required fields (predicates)
- Dangling reverse edges pointing to deleted or incomplete relation objects
- GraphQL layer returns null for these malformed relations, causing serialization errors

**Current Workaround**:

- Frontend implements error handling to filter out null/malformed relations
- API endpoint `/api/entities/{entity_name}/connections` may return partial data with errors

**Permanent Fix Options**:

1. Re-run data pipeline from scratch with validated data
2. Implement data validation in the loading process
3. Clean up dangling edges and orphaned relations in database
4. Add GraphQL schema validation before loading data

**Related Scripts**:

- `knowledge_graph/fix_broken_relations.py` - Deletes relations with missing subject/object nodes
- `knowledge_graph/fix_malformed_relations.py` - Finds relations missing required fields
- `knowledge_graph/fix_dangling_edges.py` - Identifies dangling reverse edges

Note: Direct database deletion attempts showed 0 malformed relations via DQL queries, but GraphQL still reports errors, indicating a schema/indexing mismatch between DQL and GraphQL layers.

### API Issues

**Server Won't Start**:

```bash
# Check port availability
lsof -ti:8001

# Kill existing process
kill $(lsof -ti:8001)

# Start server
cd knowledge_graph
python api.py
```

**Wrong Model Provider**:

- Edit `.env` file with correct provider settings
- Restart API server (Ctrl+C then `python api.py`)
- Verify provider in API response metadata

## Documentation

Detailed documentation available:

- `knowledge_graph/API_ENDPOINTS.md` - Complete REST API reference
- `VISUAL_REVIEW_IMPLEMENTATION_PLAN.md` - Vision model architecture
- `TABLE_SUPPORT_IMPLEMENTATION.md` - Table extraction details
- `FIGURE_TABLE_API_REFERENCE.md` - Visual element API guide

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

## License

This project is licensed under the terms specified in the LICENSE file.
