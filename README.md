# No-RAGrets-Master

The master repository for the No-RAGrets scientific literature analysis platform.

## Project Structure

```
No-RAGrets-Master/
├── data/            # Shared data directory
│   ├── papers/              # Source PDFs (49 papers, single source of truth)
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

- Python 3.8+
- Node.js 18+ and npm
- Docker Desktop (optional, for Dgraph database)
- Git

### Quick Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd No-RAGrets-Master
   ```

2. **Set up the Pipeline (Backend)**

   ```bash
   cd pipeline
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env      # Configure your LLM provider
   ```

3. **Set up the UI (Frontend)**

   ```bash
   cd ui/no-ragrets-ui
   npm install
   cp .env.example .env      # Configure API base URL
   ```

4. **Configure Environment Variables**

   Edit `.env` files to set your LLM provider (OpenAI or Ollama) and API keys.
   See individual application READMEs for detailed configuration options.

### Running the Applications

**Pipeline API Server:**

```bash
cd pipeline
source venv/bin/activate
python -m uvicorn knowledge_graph.api.main:app --reload --port 8001
```

**UI Development Server:**

```bash
cd ui/no-ragrets-ui
npm run dev
```

Access the UI at `http://localhost:5173`

## Production Applications

### Pipeline

Automated system that converts PDFs to knowledge graphs, extracts entities/relationships, and provides AI-powered quality assessment. See [pipeline/README.md](pipeline/README.md).

### UI

Interactive React interface for exploring knowledge graphs, entity relationships, and performing AI rubric reviews. See [ui/README.md](ui/README.md).

### Reviewer

Specialized paper review system with 5 evaluation dimensions and 3-tier assessment framework. See [reviewer/README.md](reviewer/README.md).

## Archive

The archive contains experimental iterations and development prototypes that inform the production systems. These are preserved for reference and potential future integration.
