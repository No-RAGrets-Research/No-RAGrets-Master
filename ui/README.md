# No-RAGrets UI

A React-based frontend for scientific paper analysis with interactive knowledge graph visualization and AI-powered content reviews.

## Overview

No-RAGrets UI provides an interactive interface for exploring scientific research papers through knowledge graphs and entity-relation analysis. The application enables researchers to visualize connections between concepts across multiple papers, trace fact provenance, and perform AI-powered content reviews.

## Features

### Interactive Knowledge Graph

- Visual graph exploration using ReactFlow with grid layout
- Real-time entity search with autocomplete (1+ character trigger)
- Node interactions to load entity connections and analytics
- Edge interactions to view relation provenance across multiple papers
- Entity statistics showing paper appearances and top relations
- Multi-source tracking for relations (see which papers support each fact)
- Smoothstep edge routing with labeled backgrounds for readability
- Connection limiting (top 3 per hub entity) to prevent visual clutter
- Clickable navigation to source papers

### Document Analysis

- PDF rendering with entity and relation highlighting
- Figure and table extraction with base64 encoding
- Text selection and annotation
- Triple extraction (subject-predicate-object relationships)
- Annotated view with entity/relation overlays
- Provenance tracking showing exact sections and pages

### Entity & Relation Exploration

- Browse 28,530+ extracted entities across 49 papers
- Explore 17,451+ relations in the knowledge graph
- Filter by entity types (Chemical, Process, Method, etc.)
- View entity connections (outgoing and incoming relations)
- Track relation confidence scores
- Cross-reference facts across multiple papers

### AI Rubric Reviews

Six evaluation criteria for scientific content:

- **Methodology**: Research design and experimental approach
- **Reproducibility**: Clarity and completeness of methods
- **Rigor**: Statistical analysis and controls
- **Data Quality**: Collection, presentation, and analysis
- **Presentation**: Clarity, organization, and effectiveness
- **References**: Citation quality and relevance

Supports review of:

- Selected text passages
- Figures (using vision models)
- Tables (structure analysis)

## Technology Stack

### Frontend

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router** - Navigation and routing
- **React Query (TanStack Query)** - Server state management
- **Zustand** - Client state management
- **ReactFlow 11.11.4** - Graph visualization
- **PDF.js** - PDF rendering
- **Lucide React** - Icon library

### Backend Integration

- FastAPI REST API communication via Axios
- GraphQL-style entity and relation queries
- Support for Ollama (local) and OpenAI (cloud) vision models
- Docling JSON document format
- Neo4j knowledge graph storage

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API server running (default: `http://localhost:8001`)

### Installation

```bash
cd no-ragrets-ui
npm install
```

### Configuration

Create a `.env` file in `no-ragrets-ui/`:

```env
VITE_API_BASE_URL=http://localhost:8001
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

Production build will be in `no-ragrets-ui/dist/`

## Project Structure

```
no-ragrets-ui/
├── src/
│   ├── components/       # React components
│   │   ├── annotated-view/   # Document viewer with annotations
│   │   ├── entities/         # Entity display components
│   │   ├── graph/            # Knowledge graph visualization
│   │   ├── layout/           # App shell and navigation
│   │   ├── pdf-viewer/       # PDF rendering components
│   │   ├── relations/        # Relation display components
│   │   ├── review/           # Rubric review modals
│   │   └── ui/               # Reusable UI components
│   ├── pages/            # Route pages
│   │   ├── GraphView.tsx     # Interactive knowledge graph
│   │   ├── PaperView.tsx     # Individual paper analysis
│   │   └── Home.tsx          # Landing page
│   ├── services/         # API client functions
│   │   └── api/          # Organized by resource
│   │       ├── papers.ts     # Paper endpoints
│   │       ├── entities.ts   # Entity endpoints
│   │       ├── relations.ts  # Relation endpoints
│   │       └── review.ts     # Review endpoints
│   ├── types/            # TypeScript type definitions
│   ├── hooks/            # Custom React hooks
│   │   ├── usePaperData.ts   # Paper data queries
│   │   ├── useGraphData.ts   # Graph data queries
│   │   └── useRelationSearch.ts  # Relation queries
│   ├── utils/            # Helper functions
│   └── config.ts         # App configuration
├── public/
│   ├── papers/           # PDF files
│   └── docling_json/     # Docling format documents
└── package.json
```

## Key User Workflows

### Exploring the Knowledge Graph

1. Start at the Graph View to see the top 12 hub entities
2. Use the search bar to find specific entities (autocomplete activates at 1+ characters)
3. Click nodes to load entity connections and view analytics
4. Click edges to see relation provenance across multiple papers
5. Navigate to source papers by clicking paper names

### Analyzing Individual Papers

1. Browse available papers from the home page or graph view
2. Select a paper to open the detailed view
3. Toggle between reference PDF view and annotated view
4. In annotated view, select text, figures, or tables to see extracted relations
5. Use rubric review to evaluate content quality

### Tracing Fact Provenance

1. In the graph view, click an edge connecting two entities
2. View the relation details panel showing all papers where this relation appears
3. See section names, page numbers, and confidence scores for each source
4. Click "View in Paper" for any source to navigate to that specific paper

## API Integration

The frontend communicates with a FastAPI backend. See `API_Endpoints.md` for complete API documentation.

Key endpoints:

- `/api/papers` - Document management and metadata
- `/api/entities` - Entity search and retrieval
- `/api/entities/{entity_id}/connections` - Entity connections with relations
- `/api/relations` - Relation queries
- `/api/relations/search` - Advanced relation filtering
- `/api/triples` - Triple extraction
- `/api/stats` - Graph statistics (total entities, relations, papers)
- `/api/review/rubric/{rubricName}` - Text review
- `/api/review/figure` - Figure review with vision models
- `/api/review/table` - Table structure review

## Development Notes

### Graph Performance

The graph view implements several performance optimizations:

- Limits connections to top 3 per hub entity to prevent overwhelming display
- Uses debounced search (200ms) to reduce API calls
- Implements edge deduplication by source-predicate-target ID
- Aggregates multiple sources per relation into single edges
- Grid layout with randomization for better node distribution

### Multi-Source Relation Tracking

Relations that appear in multiple papers are tracked with full provenance:

- Each edge stores an array of sources (paper, section, pages, confidence)
- Edge IDs include the predicate to properly group same relations
- Clicking edges shows all paper sources with individual navigation buttons
- Enables cross-paper fact verification and trust assessment

### Timeout Configuration

Vision model endpoints have extended timeouts:

- Text reviews: 60 seconds
- Table reviews: 120 seconds
- Figure reviews: 180 seconds

### Image Extraction

Figures are extracted client-side as base64 PNG data URLs and sent to the backend, avoiding duplicate PDF processing.

### Document Format

Uses Docling JSON format with extracted figures, tables, and structured content. The backend processes PDFs into this format for frontend consumption.

## Database Statistics

Current knowledge graph contains:

- 49 scientific papers
- 28,530 unique entities
- 17,451 relations
- Multiple entity types (Chemical, Process, Method, Material, etc.)

## Future Enhancements

Potential improvements and features:

- Advanced graph filtering by entity type, confidence, or date range
- Entity clustering and community detection
- Temporal analysis showing how concepts evolve across papers
- Export functionality for graphs and provenance data
- Collaborative annotation and review features
- Integration with external knowledge bases

## Contributing

This project is part of the No-RAGrets Research organization. For issues or contributions, please refer to the repository guidelines.

## License

See LICENSE file for details.
