# UI Architecture and Implementation Details

This document provides a comprehensive explanation of how the No-RAGrets UI works, including all views, data flow, and architectural decisions.

## Table of Contents

1. [Overview](#overview)
2. [Application Views](#application-views)
3. [Data Architecture](#data-architecture)
4. [PDF and Docling File System](#pdf-and-docling-file-system)
5. [Component Architecture](#component-architecture)
6. [State Management](#state-management)
7. [Performance Optimizations](#performance-optimizations)
8. [Routing and Navigation](#routing-and-navigation)
9. [Environment Configuration](#environment-configuration)
10. [Error Handling and Edge Cases](#error-handling-and-edge-cases)
11. [Entity Type System](#entity-type-system)
12. [Dark Mode Implementation](#dark-mode-implementation)
13. [Known Limitations and Requirements](#known-limitations-and-requirements)
14. [Development Guidelines](#development-guidelines)

## Overview

The No-RAGrets UI is a React-based single-page application that provides three primary views for exploring scientific research papers through knowledge graphs and entity-relation analysis. The application is designed for fast, responsive interaction with minimal server requests by leveraging local file caching and intelligent state management.

### Core Architecture Principles

- **Client-side file serving**: PDF and Docling JSON files are served statically from the public directory
- **Lazy loading**: Data is fetched only when needed, with aggressive caching
- **Progressive enhancement**: Basic functionality works immediately, with enhanced features loading asynchronously
- **Separation of concerns**: Backend handles analysis and extraction, frontend handles visualization and interaction

## Application Views

### 1. Home View (`Home.tsx`)

**Purpose**: Entry point providing navigation to papers and the knowledge graph.

**Key Features**:

- Welcome message and application overview
- Quick navigation cards to Graph View and Papers
- Statistics dashboard showing total papers, entities, and relations
- Recent papers list with metadata (title, authors, year)

**Data Flow**:

```
User loads Home → usePapers hook fetches paper list → React Query caches result
                → useGraphStats hook fetches statistics → Display in UI
```

**Implementation Details**:

- Uses React Query for automatic caching and background refetching
- Statistics are fetched from `/api/stats` endpoint once and cached for 10 minutes
- Paper list is cached for 10 minutes to reduce server load
- Navigation uses React Router for client-side routing (no page reloads)

### 2. Graph View (`GraphView.tsx`)

**Purpose**: Interactive visualization of the knowledge graph showing entities and their relationships.

**Key Features**:

#### Initial Graph Display

- Loads top 12 hub entities (highest connection counts) on mount
- For each hub entity, displays its top 3 connections
- Uses grid layout with randomization to prevent overlapping
- Implements edge deduplication and multi-source tracking

**Loading Process**:

```
Component mount → fetchEntitiesAndConnections()
                → GET /api/entities/curated (12 hub entities)
                → For each entity: GET /api/entities/{id}/connections
                → Aggregate results → Build nodes and edges → Render graph
```

#### Search Functionality

- Real-time autocomplete search with 200ms debounce
- Triggers on 1+ character input (aggressive for fast discovery)
- Returns top 15 matching entities sorted by relevance
- Clicking a result navigates to that entity in the graph

**Search Flow**:

```
User types → 200ms debounce → GET /api/entities/search?query={text}&limit=15
          → Display dropdown → User clicks result → Load entity connections
```

#### Node Interactions

- Click a node to load that entity's full connection graph
- Fetches up to 20 relations (outgoing + incoming)
- Populates entity analytics panel with statistics
- Shows which papers contain this entity

**Node Click Flow**:

```
User clicks node → handleNodeClick()
                 → GET /api/entities/{id}/connections?max_relations=20
                 → Build edges with multi-source tracking
                 → Update graph display
                 → Populate entity analytics panel
```

**Entity Analytics Panel**:

- Entity name, type, and total connections
- Breakdown of outgoing vs incoming relations
- "Appears in X papers" count with list
- Top predicate (most common relation type)
- Expandable papers list sorted by relation count
- Each paper is clickable to navigate to PaperView

#### Edge Interactions

- Click an edge to see relation provenance
- Shows all papers where this relation appears
- Displays section, page numbers, and confidence scores
- Individual "View in Paper" buttons for each source

**Edge Click Flow**:

```
User clicks edge → handleEdgeClick()
                 → Extract edge.data.sources array
                 → Populate relation details panel
                 → Display all papers with this relation
```

**Relation Details Panel**:

- Subject → Predicate → Object triple display
- "Appears in X papers" count
- List of all sources with:
  - Paper filename
  - Section name
  - Page numbers
  - Confidence score (if available)
  - Navigation button to that paper

#### Multi-Source Edge Tracking

**Implementation**:
The graph implements sophisticated edge deduplication while preserving provenance:

```typescript
// Edge ID includes predicate to group same relations
const edgeId = `${sourceId}-${predicate}-${targetId}`;

// Check if edge already exists
if (edgeMap.has(edgeId)) {
  // Append new source to existing edge
  existingEdge.data.sources.push({
    paper: relation.source_paper,
    section: relation.section,
    pages: relation.pages || [],
    confidence: relation.confidence,
  });
} else {
  // Create new edge with first source
  edgeMap.set(edgeId, {
    id: edgeId,
    source: sourceId,
    target: targetId,
    data: {
      subject: subjectName,
      predicate: predicate,
      object: objectName,
      sources: [{ paper, section, pages, confidence }],
    },
  });
}
```

**Benefits**:

- Clean graph: One visual edge per unique relation
- Complete provenance: All paper sources tracked
- Trust indicators: Relations in multiple papers are well-established
- Cross-paper verification: Compare how different studies describe same relationship

#### Graph Rendering

- Uses ReactFlow 11.11.4 for visualization
- Custom node styling with entity type colors
- Smoothstep edges with labeled backgrounds for readability
- Interactive zoom, pan, and selection
- Background grid with dots
- MiniMap for navigation
- Controls for zoom/fit view

**ReactFlow Configuration**:

```typescript
<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onNodeClick={handleNodeClick}
  onEdgeClick={handleEdgeClick}
  fitView
  elevateEdgesOnSelect={true}
>
  <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
  <Controls />
  <MiniMap />
</ReactFlow>
```

#### Performance Optimizations

- Connection limiting: Top 3 connections per hub entity to prevent clutter
- Debounced search: 200ms delay to reduce API calls
- Edge deduplication: Prevents duplicate visual edges
- Lazy loading: Only loads data when nodes/edges are clicked
- React Query caching: Repeated requests use cached data

### 3. Paper View (`PaperView.tsx`)

**Purpose**: Detailed analysis of individual research papers with PDF viewing, entity/relation exploration, and AI-powered reviews.

**URL Pattern**: `/papers/:id` where `id` is the encoded paper filename

**Two View Modes**:

#### Reference View (Default)

Shows the original PDF with entity and relation highlighting.

**Components**:

- `PDFViewer`: Renders PDF using PDF.js
- Bounding box overlays for entity mentions
- Clickable highlights navigate to entities
- Page navigation and zoom controls

**PDF Loading Flow**:

```
PaperView loads → Fetch paper metadata from API
                → PDFViewer component mounts
                → Loads PDF from /papers/{filename}
                → PDF.js renders pages client-side
                → No server processing required
```

#### Annotated View

Shows parsed document structure with interactive entity/relation extraction.

**Components**:

- `AnnotatedView`: Displays Docling JSON structure
- Text sections, figures, and tables rendered separately
- Click/select content to extract relations
- Real-time relation display for selections

**Docling Loading Flow**:

```
AnnotatedView mounts → componentDidMount()
                     → fetch(/docling_json/{filename}.json)
                     → Parse Docling structure locally
                     → Render sections, figures, tables
                     → User selects content
                     → POST /api/relations/extract (only selected content)
                     → Display relations in sidebar
```

**Content Selection**:

- **Text**: Click paragraph to select, double-click to deselect
- **Figures**: Click image to select
- **Tables**: Click table to select
- Selected content highlighted with blue border
- Relation extraction happens server-side only for selection
- Previous selections are cleared when new content selected

**Relation Display**:

- Shows relations only for selected content (not entire page)
- Title changes to "Relations in Selection"
- Displays subject-predicate-object triples
- Each relation clickable to see full provenance
- Clear selection button to reset

#### Entity Panel (Right Sidebar)

**Always Visible**:

- Paper statistics (total entities, total relations)
- Entity type filter buttons (ALL, CHEMICAL, PROCESS, METHOD, etc.)
- Filtered entity list with type badges
- Relation details for selected relation

**Entity List**:

- Click entity type filter to show only that type
- Each entity shows its name and type
- Scroll through all entities in paper
- Click entity to see its relations

**Relation Details**:

- Appears when clicking a relation in the list
- Shows subject → predicate → object
- Displays confidence score
- Section and page information
- Text snippet showing context

#### Rubric Review System

**Purpose**: AI-powered evaluation of selected content against academic quality criteria.

**Six Rubrics**:

1. **Methodology**: Research design, experimental approach, hypothesis
2. **Reproducibility**: Method clarity, detail sufficiency, replicability
3. **Rigor**: Statistical analysis, controls, sample size, bias mitigation
4. **Data Quality**: Collection methods, presentation, analysis appropriateness
5. **Presentation**: Clarity, organization, visual effectiveness, coherence
6. **References**: Citation quality, relevance, recency, diversity

**Review Flow**:

```
User selects content → Click "Review" button
                     → Choose rubric from dropdown
                     → System determines content type (text/figure/table)
                     → Routes to appropriate API endpoint:
                        - Text: POST /api/review/rubric/{rubricName}
                        - Figure: POST /api/review/figure
                        - Table: POST /api/review/table
                     → Display results in modal
```

**Content Type Handling**:

- **Text**: Sends text string, uses LLM for evaluation
- **Figure**: Extracts image as base64 PNG, sends to vision model
- **Table**: Sends table structure data, uses specialized analysis

**Review Modal**:

- Shows loading state during analysis
- Displays score (0-100)
- Provides detailed feedback
- Lists strengths and weaknesses
- Offers improvement recommendations
- Retry button if review fails
- Close button to return to document

**Timeout Configuration**:

- Text reviews: 60 seconds
- Table reviews: 120 seconds
- Figure reviews: 180 seconds (vision models are slower)

## Data Architecture

### API Communication

**Base Client** (`services/api/client.ts`):

```typescript
const apiClient = axios.create({
  baseURL: config.apiBaseUrl, // http://localhost:8001
  timeout: 30000, // 30 seconds default
  headers: {
    "Content-Type": "application/json",
  },
});
```

**Extended Timeouts for Vision**:

```typescript
const visionClient = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 180000, // 3 minutes for figure processing
});
```

### React Query Integration

**Configuration**:

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

**Custom Hooks**:

1. **usePapers**: Fetches all papers, cached for 10 minutes
2. **usePaper**: Fetches single paper by ID
3. **usePaperEntities**: Fetches entities for a paper with filtering
4. **useGraphStats**: Fetches graph statistics
5. **useEntitySearch**: Searches entities with debouncing
6. **useEntityConnections**: Fetches connections for an entity
7. **useRelationProvenance**: Fetches all occurrences of a relation

**Cache Benefits**:

- Repeated navigation doesn't refetch data
- Background updates keep data fresh
- Optimistic updates for better UX
- Automatic garbage collection of unused queries

## PDF and Docling File System

### Architecture Decision: Static File Serving

**Why Static Files?**

Instead of fetching PDFs and Docling files through the API, they are served directly from the public directory. This provides significant benefits:

1. **Performance**: No server processing, files sent directly by Vite/nginx
2. **Scalability**: Web server handles file serving efficiently
3. **Caching**: Browser caches files, subsequent loads are instant
4. **Reduced backend load**: API server focuses on analysis, not file serving
5. **Simpler deployment**: Files can be CDN-hosted in production

### Directory Structure

```
public/
├── papers/                    # PDF files
│   ├── A. Priyadarsini et al. 2023.pdf
│   ├── B. Sharma et al. 2022.pdf
│   └── ... (49 papers total)
└── docling_json/             # Pre-processed Docling files
    ├── A. Priyadarsini et al. 2023.json
    ├── B. Sharma et al. 2022.json
    └── ... (49 JSON files)
```

### PDF Loading Process

**Client-Side Flow**:

```
User navigates to paper → PaperView component mounts
                        → PDFViewer requests /papers/{filename}
                        → Vite dev server serves file directly
                        → Browser caches PDF
                        → PDF.js parses PDF client-side
                        → Renders pages to canvas elements
```

**Benefits**:

- **Instant loading**: No API round-trip, direct file transfer
- **Browser caching**: Second visit loads from cache (0ms)
- **Client-side rendering**: PDF.js does all processing in browser
- **No backend burden**: API doesn't handle large file transfers
- **Offline capability**: Service worker can cache PDFs for offline access

**Implementation**:

```typescript
// PDFViewer.tsx
const pdfUrl = `/papers/${filename}`;

useEffect(() => {
  const loadPdf = async () => {
    const loadingTask = pdfjsLib.getDocument(pdfUrl);
    const pdf = await loadingTask.promise;
    // Render pages...
  };
  loadPdf();
}, [pdfUrl]);
```

### Docling JSON Loading Process

**What is Docling?**

Docling is a document parsing format that extracts structured content from PDFs:

- Text sections with hierarchy
- Figures with captions and base64 image data
- Tables with structure and captions
- Metadata (authors, title, year)
- Layout information

**File Structure Example**:

```json
{
  "title": "Carbon Capture Research",
  "authors": ["Smith, J.", "Doe, A."],
  "year": 2023,
  "sections": [
    {
      "type": "section",
      "level": 1,
      "text": "Introduction",
      "content": [
        {
          "type": "paragraph",
          "text": "Carbon dioxide emissions..."
        }
      ]
    }
  ],
  "figures": [
    {
      "id": "fig_1",
      "caption": "CO2 capture process",
      "image_data": "data:image/png;base64,iVBORw0KGgo..."
    }
  ],
  "tables": [
    {
      "id": "table_1",
      "caption": "Efficiency comparison",
      "data": [
        ["Method", "Efficiency"],
        ["Method A", "85%"]
      ]
    }
  ]
}
```

**Loading Flow**:

```
AnnotatedView mounts → fetch(/docling_json/{filename}.json)
                     → Parse JSON locally (instant)
                     → Extract sections, figures, tables
                     → Render structure in DOM
                     → Images already base64-encoded (no additional fetches)
```

**Benefits Over API Fetching**:

1. **Speed**: JSON parse is ~10-100x faster than API request

   - API: 50-200ms (network + processing)
   - Static file: 5-20ms (cache hit)

2. **Reliability**: No server errors, no timeouts

3. **Offline**: Files can be cached for offline access

4. **Bandwidth**: One-time download, then cached forever

5. **Scalability**: No backend processing per request

**Implementation**:

```typescript
// AnnotatedView.tsx
useEffect(() => {
  const loadDocling = async () => {
    const response = await fetch(`/docling_json/${paperFilename}.json`);
    const data = await response.json();

    // Process sections
    setSections(data.sections);

    // Process figures (images already embedded)
    setFigures(data.figures);

    // Process tables
    setTables(data.tables);
  };

  loadDocling();
}, [paperFilename]);
```

### Pre-processing vs On-Demand

**Backend Pre-processing**:

- PDFs are processed once during ingestion
- Docling extraction happens server-side with specialized tools
- Results saved as JSON files in public directory
- Entity and relation extraction stored in Neo4j database

**Frontend Benefits**:

- No waiting for extraction
- Immediate visualization
- Consistent results (same extraction every time)
- Can work offline after initial load

**Workflow**:

```
Backend Pipeline (one-time):
Upload PDF → Docling extraction → Entity/relation extraction
          → Save JSON to public/docling_json/
          → Save entities/relations to Neo4j
          → Copy PDF to public/papers/

Frontend (every visit):
Load paper → Fetch from /papers/ (cached)
          → Fetch from /docling_json/ (cached)
          → Display immediately
```

### Image Extraction for Reviews

**Figure Review Process**:
When user reviews a figure, the image is extracted client-side:

```typescript
// AnnotatedView.tsx
const extractImageData = (figureElement: HTMLElement) => {
  const imgElement = figureElement.querySelector("img");
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  canvas.width = imgElement.naturalWidth;
  canvas.height = imgElement.naturalHeight;

  ctx.drawImage(imgElement, 0, 0);

  return canvas.toDataURL("image/png"); // base64 PNG
};
```

**Benefits**:

- No server-side image extraction
- Uses already-loaded Docling image data
- Sends only the selected figure (not entire PDF)
- Fast and efficient

## Component Architecture

### Layout Components

**AppLayout** (`components/layout/AppLayout.tsx`):

- Top-level application shell
- Navigation bar with logo and links
- Dark mode toggle
- Route outlet for page content
- Responsive design

**Navigation**:

```typescript
<nav>
  <Link to="/">Home</Link>
  <Link to="/graph">Graph</Link>
  <Link to="/papers">Papers</Link>
</nav>
```

### Graph Components

**Custom Node Component**:

```typescript
const CustomNode = ({ data }) => {
  return (
    <div className="px-4 py-2 rounded-lg border-2 bg-white">
      <div className="font-semibold">{data.label}</div>
      <div className="text-xs text-gray-500">{data.type}</div>
    </div>
  );
};
```

**Edge Configuration**:

```typescript
const defaultEdgeOptions = {
  type: "smoothstep",
  animated: false,
  style: { stroke: "#94a3b8", strokeWidth: 2 },
  labelStyle: { fill: "#1f2937", fontWeight: 500 },
  labelBgStyle: { fill: "#f1f5f9" },
};
```

### PDF Components

**PDFViewer**:

- Page-by-page rendering using PDF.js
- Canvas-based display
- Zoom and pan controls
- Page navigation
- Bounding box overlays for entity highlights

**Page Rendering**:

```typescript
const renderPage = async (pageNum: number) => {
  const page = await pdf.getPage(pageNum);
  const viewport = page.getViewport({ scale: zoom });

  const canvas = document.createElement("canvas");
  canvas.width = viewport.width;
  canvas.height = viewport.height;

  const context = canvas.getContext("2d");
  await page.render({ canvasContext: context, viewport }).promise;

  return canvas;
};
```

### Annotated View Components

**AnnotatedView**:

- Main container for Docling content
- Section rendering with hierarchy
- Figure rendering with captions
- Table rendering with structure
- Selection handling
- Relation extraction trigger

**Content Rendering**:

```typescript
{
  sections.map((section) => (
    <section key={section.id}>
      <h2>{section.title}</h2>
      {section.paragraphs.map((p) => (
        <p onClick={() => handleSelect(p)}>{p.text}</p>
      ))}
    </section>
  ));
}

{
  figures.map((fig) => (
    <figure onClick={() => handleSelect(fig)}>
      <img src={fig.image_data} alt={fig.caption} />
      <figcaption>{fig.caption}</figcaption>
    </figure>
  ));
}
```

### Entity and Relation Components

**EntityTypeBadge**:

- Color-coded badge for entity types
- Consistent styling across application
- Type icons

**RelationDetail**:

- Triple display (subject-predicate-object)
- Confidence score visualization
- Source paper information
- Clickable navigation

## State Management

### Local Component State

Used for UI-specific state that doesn't need to be shared:

- Modal open/closed states
- Dropdown visibility
- Form inputs
- Loading indicators
- Selection state

**Example**:

```typescript
const [showInfoPanel, setShowInfoPanel] = useState(true);
const [selectedEntity, setSelectedEntity] = useState(null);
const [searchQuery, setSearchQuery] = useState("");
```

### React Query State

Used for server data:

- Paper lists and details
- Entities and relations
- Graph statistics
- Search results

**Benefits**:

- Automatic caching and invalidation
- Loading and error states
- Background refetching
- Optimistic updates
- Request deduplication

### Zustand (if needed)

For global application state:

- User preferences
- Theme settings
- Filter configurations

## Performance Optimizations

### 1. Static File Serving

**Impact**: 10-100x faster than API requests

- PDFs: Browser cache hit = 0ms load time
- Docling JSON: Parse cached file = 5-20ms
- No server processing overhead

### 2. React Query Caching

**Impact**: Eliminates redundant API calls

- First load: API request (100-200ms)
- Subsequent loads: Cache hit (1-2ms)
- Background updates keep data fresh

### 3. Debounced Search

**Impact**: 5-10x fewer API calls during typing

```typescript
const debouncedSearch = useCallback(
  debounce((query) => {
    performSearch(query);
  }, 200),
  []
);
```

### 4. Connection Limiting

**Impact**: Prevents overwhelming graph display

- Top 3 connections per hub entity
- Expandable on demand via node clicks
- Keeps initial graph readable

### 5. Edge Deduplication

**Impact**: Cleaner graph with same information

- Single edge for repeated relations
- Sources aggregated in edge data
- Reduces visual clutter by 30-50%

### 6. Lazy Loading

**Impact**: Faster initial page load

- Graph loads only visible nodes initially
- Entity details loaded on click
- Relations loaded only for selections
- Review models loaded on demand

### 7. Code Splitting

**Impact**: Smaller initial bundle

```typescript
const PaperView = lazy(() => import("./pages/PaperView"));
const GraphView = lazy(() => import("./pages/GraphView"));
```

### 8. Memoization

**Impact**: Prevents unnecessary re-renders

```typescript
const nodeElements = useMemo(
  () => createNodesFromEntities(entities),
  [entities]
);

const edgeElements = useMemo(
  () => createEdgesFromRelations(relations),
  [relations]
);
```

## Routing and Navigation

### React Router Configuration

The application uses React Router v6 for client-side routing with the following structure:

**Route Definitions** (`App.tsx`):

```typescript
<BrowserRouter>
  <Routes>
    <Route path="/" element={<AppLayout />}>
      <Route index element={<Home />} />
      <Route path="graph" element={<GraphView />} />
      <Route path="papers/:id" element={<PaperView />} />
      <Route path="*" element={<NotFound />} />
    </Route>
  </Routes>
</BrowserRouter>
```

### Navigation Patterns

**Programmatic Navigation**:

```typescript
const navigate = useNavigate();

// Navigate to paper
navigate(`/papers/${encodeURIComponent(paperFilename)}`);

// Navigate to graph
navigate("/graph");

// Navigate back
navigate(-1);
```

**URL Parameter Handling**:

```typescript
// Extract paper ID from URL
const { id } = useParams<{ id: string }>();
const decodedId = decodeURIComponent(id || "");

// Match paper by ID or filename
const paper = papers?.find(
  (p) => p.id === decodedId || p.filename === decodedId
);
```

**State Preservation**:

- React Query cache persists across navigation
- Graph view state (zoom, pan) resets on navigation
- Paper view scroll position preserved via browser
- Search state cleared on view change

**Navigation Performance**:

- Client-side routing (no page reloads)
- Instant transitions between views
- Lazy-loaded components for code splitting
- Prefetching for cached data

## Environment Configuration

### Configuration File Structure

**`config.ts`**:

```typescript
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "http://localhost:8001",
  apiTimeout: 30000,
  visionTimeout: 180000,
  searchDebounce: 200,
  cacheTime: 10 * 60 * 1000,
  maxConnectionsPerEntity: 3,
  maxRelationsPerFetch: 20,
};
```

### Environment Variables

**`.env` File**:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8001

# Optional: Enable verbose logging
VITE_ENABLE_DEBUG=false

# Optional: Analytics
VITE_ANALYTICS_ID=
```

**Development** (`.env.development`):

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_ENABLE_DEBUG=true
```

**Production** (`.env.production`):

```env
VITE_API_BASE_URL=https://api.noragrets.example.com
VITE_ENABLE_DEBUG=false
```

### Configuration Access

**In Components**:

```typescript
import { config } from "../config";

// Use configuration
const response = await fetch(`${config.apiBaseUrl}/api/papers`);
```

**Vite Environment Variables**:

- Prefixed with `VITE_` to be exposed to client
- Accessed via `import.meta.env.VITE_*`
- Type-safe through TypeScript declarations

## Error Handling and Edge Cases

### API Error Handling

**React Query Error Handling**:

```typescript
const { data, error, isError, refetch } = usePapers();

if (isError) {
  return (
    <div className="error-container">
      <p>Error: {error.message}</p>
      <button onClick={() => refetch()}>Retry</button>
    </div>
  );
}
```

**Axios Interceptors**:

```typescript
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ECONNABORTED") {
      // Timeout error
      console.error("Request timeout");
    } else if (error.response?.status === 404) {
      // Not found
      console.error("Resource not found");
    } else if (error.response?.status >= 500) {
      // Server error
      console.error("Server error");
    }
    return Promise.reject(error);
  }
);
```

### Common Edge Cases

**1. Paper Not Found**:

```typescript
// PaperView.tsx
if (!paper) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <p className="text-gray-600">Paper not found</p>
        <Link to="/">Return to Home</Link>
      </div>
    </div>
  );
}
```

**2. Missing PDF File**:

```typescript
// PDFViewer.tsx
try {
  const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
  setPdf(pdf);
} catch (error) {
  console.error("Failed to load PDF:", error);
  setError("Unable to load PDF. File may be missing or corrupted.");
}
```

**3. Missing Docling File**:

```typescript
// AnnotatedView.tsx
try {
  const response = await fetch(`/docling_json/${paperFilename}.json`);
  if (!response.ok) {
    throw new Error("Docling file not found");
  }
  const data = await response.json();
  setDoclingData(data);
} catch (error) {
  console.error("Failed to load Docling data:", error);
  setFallbackMessage("Annotated view not available for this paper");
}
```

**4. Empty Search Results**:

```typescript
// GraphView.tsx
if (searchResults.length === 0 && searchQuery.length > 0) {
  return (
    <div className="text-sm text-gray-500 p-2">
      No entities found matching "{searchQuery}"
    </div>
  );
}
```

**5. Network Timeout**:

```typescript
// Handled by React Query retry logic
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // Retry once on failure
      retryDelay: 1000, // Wait 1 second before retry
    },
  },
});
```

**6. Invalid Entity ID**:

```typescript
// Handle invalid node clicks gracefully
const handleNodeClick = useCallback((event, node) => {
  if (!node?.id) {
    console.warn("Invalid node clicked");
    return;
  }
  // Proceed with valid node
}, []);
```

**7. Malformed Relation Data**:

```typescript
// Validate edge data before using
if (
  edge.data?.subject &&
  edge.data?.predicate &&
  edge.data?.object &&
  edge.data?.sources
) {
  setSelectedRelation({ ...edge.data });
} else {
  console.warn("Malformed edge data:", edge);
}
```

### Loading States

**Skeleton Loading**:

```typescript
if (isLoading) {
  return (
    <div className="animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  );
}
```

**Progressive Loading**:

- Graph: Shows loading animation while fetching entities
- PDF: Renders pages as they load (not all at once)
- Docling: Shows skeleton while parsing JSON
- Search: Shows spinner in input field during search

## Entity Type System

### Entity Types and Colors

The application uses a consistent color-coding system for entity types across all views:

**Type Definitions**:

```typescript
type EntityType =
  | "CHEMICAL"
  | "PROCESS"
  | "METHOD"
  | "MATERIAL"
  | "EQUIPMENT"
  | "MEASUREMENT"
  | "PROPERTY"
  | "LOCATION"
  | "ORGANIZATION"
  | "OTHER";
```

**Color Mapping**:

```typescript
const entityColors = {
  CHEMICAL: {
    bg: "bg-blue-100 dark:bg-blue-900",
    text: "text-blue-700 dark:text-blue-300",
    border: "border-blue-300 dark:border-blue-700",
  },
  PROCESS: {
    bg: "bg-green-100 dark:bg-green-900",
    text: "text-green-700 dark:text-green-300",
    border: "border-green-300 dark:border-green-700",
  },
  METHOD: {
    bg: "bg-purple-100 dark:bg-purple-900",
    text: "text-purple-700 dark:text-purple-300",
    border: "border-purple-300 dark:border-purple-700",
  },
  MATERIAL: {
    bg: "bg-orange-100 dark:bg-orange-900",
    text: "text-orange-700 dark:text-orange-300",
    border: "border-orange-300 dark:border-orange-700",
  },
  EQUIPMENT: {
    bg: "bg-red-100 dark:bg-red-900",
    text: "text-red-700 dark:text-red-300",
    border: "border-red-300 dark:border-red-700",
  },
  // ... other types
};
```

**EntityTypeBadge Component**:

```typescript
export const EntityTypeBadge = ({ type }: { type: EntityType }) => {
  const colors = entityColors[type] || entityColors.OTHER;

  return (
    <span
      className={`
      px-2 py-1 rounded text-xs font-medium
      ${colors.bg} ${colors.text} ${colors.border} border
    `}
    >
      {type}
    </span>
  );
};
```

**Usage Across Views**:

- **Graph View**: Node colors based on entity type
- **Paper View**: Entity list filtered by type with badges
- **Search Results**: Type indicators in dropdown
- **Relation Details**: Subject/object type badges

### Predicate Types

Common predicates in the knowledge graph:

- `has` - General possession or property
- `contains` - Composition relationship
- `produces` - Output relationship
- `requires` - Dependency relationship
- `improves` - Enhancement relationship
- `reduces` - Reduction relationship
- `increases` - Augmentation relationship
- `affects` - General influence

## Dark Mode Implementation

### Theme System

**Theme State Management**:

```typescript
// Using Tailwind's dark mode with class strategy
const [isDark, setIsDark] = useState(() => {
  const saved = localStorage.getItem("theme");
  return (
    saved === "dark" ||
    (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)
  );
});

useEffect(() => {
  if (isDark) {
    document.documentElement.classList.add("dark");
    localStorage.setItem("theme", "dark");
  } else {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("theme", "light");
  }
}, [isDark]);
```

**Tailwind Configuration**:

```javascript
// tailwind.config.js
module.exports = {
  darkMode: "class", // Use class-based dark mode
  theme: {
    extend: {
      colors: {
        // Custom dark mode colors
      },
    },
  },
};
```

**Component Styling**:

```typescript
// Dual-theme classes
className = "bg-white dark:bg-gray-800 text-gray-900 dark:text-white";

// Border colors
className = "border-gray-200 dark:border-gray-700";

// Hover states
className = "hover:bg-gray-50 dark:hover:bg-gray-700";
```

**Dark Mode Toggle**:

```typescript
<button onClick={() => setIsDark(!isDark)}>
  {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
</button>
```

**Benefits**:

- Respects system preferences by default
- Persists user choice in localStorage
- Smooth transitions between themes
- Consistent colors across all components
- Accessible contrast ratios in both modes

## Known Limitations and Requirements

### Browser Requirements

**Minimum Browser Versions**:

- Chrome/Edge: 90+
- Firefox: 88+
- Safari: 14+
- Opera: 76+

**Required Features**:

- ES2020+ JavaScript support
- CSS Grid and Flexbox
- Local Storage
- Canvas API (for PDF rendering)
- Fetch API
- Web Workers (for PDF.js)

### Scale Limitations

**Current Constraints**:

- Maximum graph display: 50-100 nodes before performance degrades
- PDF rendering: Memory usage increases with page count (50+ pages may be slow)
- Search: Limited to 15 results to maintain responsiveness
- Connection limit: 20 relations per entity fetch to prevent overload

**File Size Limits**:

- PDFs: Recommended max 50MB (browser memory constraints)
- Docling JSON: Recommended max 10MB per file
- Base64 images in Docling: Recommended max 5MB per image

**Data Constraints**:

- Backend must return paginated results for large datasets
- Graph view optimized for 12 hub entities with 3 connections each
- Entity list in paper view: All entities loaded (may be slow for papers with 1000+ entities)

### Known Issues

**1. Large PDF Performance**:

- PDFs with 100+ pages render slowly
- Canvas memory usage can exceed browser limits
- Mitigation: Lazy load pages, render on-demand

**2. Image-Heavy Docling Files**:

- Large base64 images in JSON slow down parsing
- Multiple large images cause memory pressure
- Mitigation: Compress images during Docling extraction

**3. Graph Layout**:

- Grid layout with randomization can occasionally overlap nodes
- Manual repositioning not persistent (resets on reload)
- Mitigation: Use zoom and pan to adjust view

**4. Search Latency**:

- First search after page load may be slower (cold start)
- Very long entity names may be truncated in results
- Mitigation: Backend indexing, client-side caching

**5. Cross-Origin Limitations**:

- PDFs must be served from same origin or with CORS headers
- Base64 images bypass this, but increase JSON size
- Mitigation: Proper CORS configuration in production

### Device Support

**Desktop**:

- Fully supported on Windows, macOS, Linux
- Optimized for screens 1920x1080 and above
- Minimum resolution: 1366x768

**Tablet**:

- Partial support (iPad Pro, large Android tablets)
- Graph interactions may be challenging with touch
- PDF viewing works well

**Mobile**:

- Limited support (small screens)
- Graph view not recommended on phones
- Paper view readable but cramped
- Consider responsive design improvements for mobile

## Development Guidelines

### Adding New Features

**1. New Entity Type**:

```typescript
// types/entities.ts
export type EntityType = "CHEMICAL" | "NEW_TYPE"; // Add here

// Add to color mapping
const entityColors = {
  NEW_TYPE: {
    bg: "bg-teal-100 dark:bg-teal-900",
    text: "text-teal-700 dark:text-teal-300",
    border: "border-teal-300 dark:border-teal-700",
  },
};
```

**2. New API Endpoint**:

```typescript
// services/api/newResource.ts
export const getNewResource = async (id: string): Promise<NewResource> => {
  const response = await apiClient.get(`/api/new-resource/${id}`);
  return response.data;
};

// hooks/useNewResource.ts
export const useNewResource = (id: string) => {
  return useQuery({
    queryKey: ["newResource", id],
    queryFn: () => getNewResource(id),
    staleTime: 5 * 60 * 1000,
  });
};
```

**3. New Graph Feature**:

```typescript
// Update GraphView.tsx
// Add state for new feature
const [newFeature, setNewFeature] = useState(false);

// Add UI controls
<button onClick={() => setNewFeature(!newFeature)}>Toggle Feature</button>;

// Update graph rendering
useEffect(() => {
  if (newFeature) {
    // Apply new feature logic
  }
}, [newFeature, nodes, edges]);
```

### Code Conventions

**Component Organization**:

```
ComponentName.tsx
  - Imports
  - Type definitions (interfaces, types)
  - Component function
  - Helper functions
  - Export
```

**Naming Conventions**:

- Components: PascalCase (`PaperView`, `EntityBadge`)
- Hooks: camelCase with `use` prefix (`usePapers`, `useGraphData`)
- Utilities: camelCase (`formatDate`, `encodeFilename`)
- Constants: UPPER_SNAKE_CASE (`MAX_CONNECTIONS`, `API_TIMEOUT`)
- Types: PascalCase (`EntityType`, `PaperMetadata`)

**TypeScript Guidelines**:

- Prefer interfaces for object shapes
- Use type for unions and primitives
- Avoid `any` - use `unknown` if type is truly unknown
- Export types that are used across files
- Use strict mode (enabled in tsconfig.json)

**Styling Guidelines**:

- Use Tailwind utility classes
- Avoid inline styles unless dynamic
- Group related utilities (layout, colors, spacing)
- Use dark mode variants: `dark:bg-gray-800`
- Extract repeated patterns to components

**API Integration**:

- All API calls through services layer
- Use React Query for data fetching
- Handle loading, error, and success states
- Implement retry logic for transient failures
- Add timeout configuration for slow endpoints

### Testing Strategy

**Unit Tests** (if implemented):

- Test utility functions in isolation
- Test custom hooks with React Testing Library
- Mock API responses for predictable tests

**Integration Tests** (if implemented):

- Test complete user flows (search, click, navigate)
- Test error scenarios (network failures, missing data)
- Test cross-view navigation

**Manual Testing Checklist**:

- Load each view and verify data displays
- Test search with various queries
- Click nodes and edges in graph
- Navigate between papers
- Toggle between reference and annotated views
- Test dark mode switch
- Verify PDF rendering on different papers
- Test rubric reviews on text, figures, tables
- Check responsive behavior at different screen sizes
- Test error states (disconnect network, invalid URLs)

### Debugging Tips

**React DevTools**:

- Inspect component hierarchy
- View props and state
- Track re-renders with Profiler

**React Query DevTools**:

- View cached queries
- See loading/error states
- Inspect query keys and data
- Force refetch or invalidate cache

**Browser DevTools**:

- Network tab: Monitor API calls, check response times
- Console: View error logs, debug messages
- Application tab: Inspect localStorage, check cache
- Performance tab: Profile rendering, identify bottlenecks

**Common Debug Scenarios**:

1. **Graph not loading**: Check `/api/entities/curated` response
2. **Paper not found**: Verify filename encoding/decoding
3. **PDF not rendering**: Check `/papers/` directory, console errors
4. **Slow search**: Check debounce timing, backend response time
5. **Relations not showing**: Verify edge data structure, check sources array

## Summary

The No-RAGrets UI achieves high performance through architectural decisions that prioritize client-side processing and aggressive caching:

1. **Static file serving** eliminates server bottlenecks for PDFs and Docling files
2. **Pre-processing** moves expensive operations to ingestion time
3. **React Query caching** prevents redundant API calls
4. **Intelligent loading** fetches only what's needed, when it's needed
5. **Multi-source tracking** provides complete provenance without graph clutter

This architecture enables instant page loads, responsive interactions, and seamless navigation across 49 papers, 28,530 entities, and 17,451 relations.
