# No-RAGrets-Master

The master repository for the No-RAGrets scientific literature analysis platform.

## Project Structure

```
No-RAGrets-Master/
├── data/            # Shared data directory
│   ├── papers/              # Source PDFs (47 papers, single source of truth)
│   └── docling_json/        # Processed paper data from Docling
├── pipeline/        # Production: Knowledge graph extraction & paper quality assessment
├── ui/              # Production: React frontend for graph visualization & analysis
├── reviewer/        # Production: AI-powered paper review system with rubrics
└── archive/         # Development iterations & experiments
    ├── baseline_model/          # Traditional ML approach for paper evaluation
    ├── image_extraction/        # Image extraction method comparisons
    ├── llm_to_kg/              # End-to-end Graph-RAG pipeline (Qwen models)
    ├── kg_infrastructure/       # Dgraph database setup
    ├── Milos/                   # Token classification experiments
    ├── paper_similarity/        # Paper similarity analysis
    └── relation_llm_judgement/  # LLM-based relation evaluation
```

## Getting Started

### Prerequisites

- Python 3.11+ (Python 3.12 recommended)
- Node.js 18+ and npm
- Docker Desktop (required for Dgraph database)
- Git

### Quick Setup

1. Clone the repository

   ```bash
   git clone <repository-url>
   cd No-RAGrets-Master
   ```

2. Set up the Pipeline (Backend)

   ```bash
   cd pipeline
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .  # Install pipeline package in editable mode
   ```

3. Set up the UI (Frontend)

   ```bash
   cd ui/no-ragrets-ui
   npm install
   ```

4. Start Docker Desktop

   Ensure Docker Desktop is running before starting the database.

5. Start Dgraph Database

   ```bash
   cd pipeline/knowledge_graph
   docker compose up -d
   ```

### Running the Applications

1. Start the Pipeline API Server

   ```bash
   cd pipeline
   source venv/bin/activate
   python -m uvicorn knowledge_graph.api:app --reload --port 8001
   ```

   API documentation available at http://localhost:8001/docs

2. Start the UI Development Server

   ```bash
   cd ui/no-ragrets-ui
   npm run dev
   ```

   Access the UI at http://localhost:5173

### Environment Configuration

The pipeline supports both OpenAI and Ollama as LLM providers. Set environment variables:

- `LLM_PROVIDER`: Set to "openai" or "ollama" (default: openai)
- `OPENAI_API_KEY`: Your OpenAI API key (required if using OpenAI)
- `OLLAMA_BASE_URL`: Ollama endpoint (default: http://localhost:11434/v1)
- `OLLAMA_MODEL`: Model to use with Ollama (default: llama3.1:8b)

The UI is pre-configured in `ui/no-ragrets-ui/.env` to connect to the API at http://localhost:8001.

## Production Applications

### Pipeline

Automated system that converts PDFs to knowledge graphs using Docling, extracts entities and relationships with Qwen models, and stores data in Dgraph. Provides REST API endpoints for querying the knowledge graph and performing AI-powered paper quality assessment.

Key features:

- PDF to structured JSON conversion via Docling
- Entity and relationship extraction using Qwen 2.5-1.5B and Qwen3-VL-4B
- Graph database storage and querying with Dgraph
- RESTful API for frontend integration

See [pipeline/README.md](pipeline/README.md) for detailed documentation.

### UI

Interactive React interface built with Vite, TypeScript, and Tailwind CSS for exploring knowledge graphs, viewing entity relationships, and performing AI rubric reviews. Features real-time graph visualization and cross-paper analysis.

Key features:

- Interactive graph visualization with D3.js
- Entity and relationship browsing
- Cross-paper analysis
- PDF viewer integration
- AI-powered paper review interface

See [ui/README.md](ui/README.md) for detailed documentation.

### Reviewer

Specialized paper review system with 5 evaluation dimensions (Relevance, Novelty, Feasibility, Impact, Presentation) and 3-tier assessment framework (Abstract, Full Text, Figures). Generates comprehensive review reports with scoring and detailed feedback.

See [reviewer/README.md](reviewer/README.md) for detailed documentation.

## Data Organization

All papers and processed data are stored in the centralized `data/` directory:

- `data/papers/`: 47 source PDF files (68MB)
- `data/docling_json/`: Processed documents from Docling pipeline (33MB)

The UI accesses papers via symlinks in `ui/no-ragrets-ui/public/` pointing to the centralized data directory.

## Archive

The archive contains experimental iterations and development prototypes that inform the production systems. These are preserved for reference and potential future integration.

## Troubleshooting

### API Import Errors

If you see module import errors, ensure you installed the pipeline package in editable mode:

````bash
cd pipeline
source venv/bin/activate
pip install -e .
```bash
open -a Docker
# Wait 15 seconds for Docker to start
docker compose up -d
````

### Port Already in Use

If port 8001 or 5173 is in use, kill the process:

```bash
lsof -ti:8001 | xargs kill -9  # For API
lsof -ti:5173 | xargs kill -9  # For UI
```
