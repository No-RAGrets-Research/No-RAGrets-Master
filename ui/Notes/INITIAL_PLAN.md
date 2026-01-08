# No-RAGrets UI - Initial Development Plan

## Project Overview

An interactive web application for exploring scientific research papers through their knowledge graph representations. Users can view PDFs, click on sentences or figures to discover relationships, and trace how concepts connect across multiple papers.

## Core Features

### 1. Interactive PDF Viewer

- **Display PDFs** with full navigation (zoom, pan, page controls)
- **Clickable text selection** - Click/select any sentence to explore its entities and relationships
- **Figure/image highlighting** - Click on figures to see extracted visual knowledge
- **Relation highlighting** - Visual overlays showing bounding boxes of extracted relations
- **Multi-paper view** - Option to view multiple papers side-by-side

### 2. Knowledge Graph Visualization

- **Force-directed graph** showing entities (nodes) and relationships (edges)
- **Interactive navigation** - Click nodes to explore connections
- **Filtering** - Filter by entity type, relation type, paper source
- **Zoom/pan controls** for exploring large graphs
- **Highlight paths** between selected entities
- **Color coding** by entity type (chemical, organism, process, etc.)

### 3. Cross-Paper Relationship Explorer

- **Entity tracking** - See which papers mention the same entity
- **Relationship comparison** - Compare how different papers describe the same relationship
- **Paper similarity** - Find papers with overlapping concepts
- **Timeline view** - Show how knowledge evolved across publication dates (if available)
- **Batch highlighting** - Click an entity to highlight all mentions across all loaded papers

### 4. Provenance Tracking & Context

- **Click-to-explore** - Click any sentence in PDF to see:
  - Extracted entities in that sentence
  - Relations extracted from that text
  - Character-level highlighting of subject/object positions
- **Source tracing** - Click any relation in graph to jump to source PDF location
- **Section context** - Show which paper section (Methods, Results, etc.) a relation came from
- **Confidence scores** - Display extraction confidence for relations
- **Visual provenance** - Show PDF page with highlighted bounding box

### 5. LLM Analysis Integration (Future Feature)

- **Custom prompt interface** - Input box for custom analysis prompts
- **Rubric-based evaluation** - Run LLM checks against configurable rubrics
- **Sentence analysis** - Analyze selected text with LLM for:
  - Quality assessment
  - Fact verification
  - Methodology evaluation
  - Custom criteria
- **Batch processing** - Run analysis across multiple selected sentences/sections
- **Results overlay** - Display LLM analysis results inline with PDF

## Technical Stack

### Frontend Framework

- **React 18** with **TypeScript** for type safety
- **Vite** for fast development and building
- **React Router** for navigation

### PDF Rendering

- **react-pdf** or **PDF.js** for PDF viewing
- Custom overlay layer for relation highlighting
- Text selection and coordinate mapping

### Graph Visualization

- **React Flow** or **D3.js** for interactive graph rendering
- Force-directed layout algorithms
- Custom node/edge components

### UI Components

- **Tailwind CSS** for styling
- **shadcn/ui** or **Material-UI** for component library
- **Framer Motion** for animations
- **React Split** for resizable panels

### State Management

- **Zustand** or **Redux Toolkit** for global state
- React Query for API data fetching and caching

### API Integration

- **Axios** for HTTP requests
- TypeScript API client with full type definitions
- WebSocket support for real-time updates (optional)

## Project Structure

```
no-ragrets-ui/
””€”€ public/
”‚  OK”””€”€ papers/                 # Static PDF files (symlinked or copied)
””€”€ src/
”‚  OK””€”€ components/
”‚  OK”‚  OK””€”€ pdf-viewer/
”‚  OK”‚  OK”‚  OK””€”€ PDFViewer.tsx          # Main PDF viewer component
”‚  OK”‚  OK”‚  OK””€”€ PDFHighlighter.tsx     # Overlay for highlighting relations
”‚  OK”‚  OK”‚  OK””€”€ TextSelector.tsx       # Handle text selection
”‚  OK”‚  OK”‚  OK”””€”€ FigureMarker.tsx       # Mark and click figures
”‚  OK”‚  OK””€”€ graph/
”‚  OK”‚  OK”‚  OK””€”€ KnowledgeGraph.tsx     # Main graph visualization
”‚  OK”‚  OK”‚  OK””€”€ GraphNode.tsx          # Custom node component
”‚  OK”‚  OK”‚  OK””€”€ GraphEdge.tsx          # Custom edge component
”‚  OK”‚  OK”‚  OK”””€”€ GraphControls.tsx      # Zoom, filter, layout controls
”‚  OK”‚  OK””€”€ explorer/
”‚  OK”‚  OK”‚  OK””€”€ EntityPanel.tsx        # Entity details sidebar
”‚  OK”‚  OK”‚  OK””€”€ RelationPanel.tsx      # Relation details sidebar
”‚  OK”‚  OK”‚  OK””€”€ CrossPaperView.tsx     # Cross-paper comparison
”‚  OK”‚  OK”‚  OK”””€”€ ProvenancePanel.tsx    # Source provenance details
”‚  OK”‚  OK””€”€ llm/
”‚  OK”‚  OK”‚  OK””€”€ LLMAnalyzer.tsx        # LLM analysis interface
”‚  OK”‚  OK”‚  OK””€”€ PromptEditor.tsx       # Custom prompt input
”‚  OK”‚  OK”‚  OK””€”€ RubricConfig.tsx       # Rubric configuration
”‚  OK”‚  OK”‚  OK”””€”€ AnalysisResults.tsx    # Display analysis results
”‚  OK”‚  OK””€”€ layout/
”‚  OK”‚  OK”‚  OK””€”€ MainLayout.tsx         # App shell
”‚  OK”‚  OK”‚  OK””€”€ Sidebar.tsx            # Navigation sidebar
”‚  OK”‚  OK”‚  OK”””€”€ ResizablePanels.tsx    # Split view layout
”‚  OK”‚  OK”””€”€ common/
”‚  OK”‚      OK””€”€ SearchBar.tsx          # Entity/relation search
”‚  OK”‚      OK””€”€ PaperList.tsx          # Paper selection
”‚  OK”‚      OK”””€”€ FilterPanel.tsx        # Filtering controls
”‚  OK””€”€ services/
”‚  OK”‚  OK””€”€ api/
”‚  OK”‚  OK”‚  OK””€”€ client.ts              # Axios instance configuration
”‚  OK”‚  OK”‚  OK””€”€ entities.ts            # Entity API calls
”‚  OK”‚  OK”‚  OK””€”€ relations.ts           # Relation API calls
”‚  OK”‚  OK”‚  OK””€”€ papers.ts              # Paper API calls
”‚  OK”‚  OK”‚  OK””€”€ provenance.ts          # Provenance API calls
”‚  OK”‚  OK”‚  OK”””€”€ analytics.ts           # Analytics API calls
”‚  OK”‚  OK””€”€ llm/
”‚  OK”‚  OK”‚  OK”””€”€ analyzer.ts            # LLM integration service
”‚  OK”‚  OK”””€”€ pdf/
”‚  OK”‚      OK”””€”€ coordinator.ts         # PDF coordinate mapping
”‚  OK””€”€ types/
”‚  OK”‚  OK””€”€ entities.ts                # Entity type definitions
”‚  OK”‚  OK””€”€ relations.ts               # Relation type definitions
”‚  OK”‚  OK””€”€ papers.ts                  # Paper type definitions
”‚  OK”‚  OK”””€”€ api.ts                     # API response types
”‚  OK””€”€ hooks/
”‚  OK”‚  OK””€”€ useEntitySearch.ts         # Entity search hook
”‚  OK”‚  OK””€”€ useRelationSearch.ts       # Relation search hook
”‚  OK”‚  OK””€”€ useEntityConnections.ts    # Entity connections hook
”‚  OK”‚  OK””€”€ usePaperData.ts            # Paper data hook
”‚  OK”‚  OK”””€”€ useLLMAnalysis.ts          # LLM analysis hook
”‚  OK””€”€ store/
”‚  OK”‚  OK””€”€ index.ts                   # Store configuration
”‚  OK”‚  OK””€”€ paperStore.ts              # Selected paper state
”‚  OK”‚  OK””€”€ graphStore.ts              # Graph state
”‚  OK”‚  OK”””€”€ selectionStore.ts          # User selection state
”‚  OK””€”€ utils/
”‚  OK”‚  OK””€”€ coordinates.ts             # PDF coordinate transformations
”‚  OK”‚  OK””€”€ graphLayout.ts             # Graph layout algorithms
”‚  OK”‚  OK”””€”€ formatting.ts              # Data formatting utilities
”‚  OK””€”€ App.tsx                        # Root component
”‚  OK””€”€ main.tsx                       # Entry point
”‚  OK”””€”€ index.css                      # Global styles
””€”€ package.json
””€”€ tsconfig.json
””€”€ vite.config.ts
””€”€ tailwind.config.js
”””€”€ README.md
```

## API Integration

### Endpoints to Implement

1. **Search & Discovery**

   - `GET /api/entities/search` - Search entities
   - `GET /api/relations/search` - Search relations

2. **Graph Traversal**

   - `GET /api/entities/{name}/connections` - Get entity connections
   - `GET /api/entities/{name}/path-to/{target}` - Find paths between entities

3. **Document & Provenance**

   - `GET /api/papers` - List all papers
   - `GET /api/papers/{id}/entities` - Get paper entities
   - `GET /api/relations/{id}/provenance` - Get relation provenance
   - `GET /api/relations/{id}/source-span` - Get exact text span
   - `GET /api/relations/{id}/section-image` - Get highlighted PDF image

4. **Analytics**
   - `GET /api/graph/stats` - Graph statistics
   - `GET /api/entities/most-connected` - Hub entities
   - `GET /api/predicates/frequency` - Relation type frequencies

## Development Phases

### Phase 1: Foundation (Week 1)

- [ ] Set up React + TypeScript + Vite project
- [ ] Configure Tailwind CSS and component library
- [ ] Create basic layout with resizable panels
- [ ] Implement TypeScript API client with all endpoint types
- [ ] Create basic routing structure

### Phase 2: PDF Viewer (Week 1-2)

- [ ] Integrate PDF.js or react-pdf
- [ ] Implement PDF navigation (pages, zoom, pan)
- [ ] Add text selection capability
- [ ] Create overlay system for highlighting
- [ ] Map PDF coordinates to API bbox data
- [ ] Implement figure click detection

### Phase 3: Knowledge Graph (Week 2-3)

- [ ] Set up React Flow or D3.js
- [ ] Create custom node components (colored by entity type)
- [ ] Create custom edge components (labeled with predicates)
- [ ] Implement force-directed layout
- [ ] Add zoom, pan, and filter controls
- [ ] Connect to entity/relation APIs

### Phase 4: Entity Explorer (Week 3-4)

- [ ] Build entity detail panel
- [ ] Build relation detail panel
- [ ] Implement provenance display
- [ ] Add cross-paper entity tracking
- [ ] Create paper list and selection UI
- [ ] Implement search functionality

### Phase 5: Integration & Interaction (Week 4-5)

- [ ] Click sentence in PDFOK†’ highlight entitiesOK†’ show in graph
- [ ] Click node in graphOK†’ show in all PDFs where it appears
- [ ] Click relationOK†’ jump to source PDF with highlight
- [ ] Cross-paper highlighting for same entities
- [ ] Real-time state synchronization between components

### Phase 6: LLM Analysis (Week 5-6)

- [ ] Create LLM analysis interface
- [ ] Implement custom prompt editor
- [ ] Add rubric configuration system
- [ ] Connect to LLM service (Claude, GPT, or local model)
- [ ] Display analysis results inline
- [ ] Add batch processing capability

### Phase 7: Polish & Optimization (Week 6-7)

- [ ] Performance optimization (virtualization, lazy loading)
- [ ] Add animations and transitions
- [ ] Improve error handling and loading states
- [ ] Add keyboard shortcuts
- [ ] Create user guide/tutorial
- [ ] Write documentation

## User Workflows

### Workflow 1: Explore a Paper's Knowledge

1. User selects a paper from the list
2. PDF loads in main viewer
3. User clicks a sentence about "methanol production"
4. Sidebar shows entities: "methanol", "Methylosinus trichosporium", "methane monooxygenase"
5. Graph updates to show these entities and their connections
6. User clicks an entity node to see all its relationships

### Workflow 2: Find Cross-Paper Connections

1. User searches for "ATP" in search bar
2. System shows ATP node with connection count
3. User clicks "Show in all papers"
4. All papers mentioning ATP are highlighted
5. User can jump between papers seeing different contexts
6. Graph shows ATP's relationships from all papers combined

### Workflow 3: Trace a Specific Relationship

1. User searches for relations with predicate "converts"
2. System shows list of conversion relationships
3. User clicks "methaneOK†’ methanol" relation
4. PDF automatically opens to exact page and highlights the sentence
5. Character-level highlighting shows subject and object positions
6. Provenance panel shows confidence score and extraction method

### Workflow 4: LLM Analysis

1. User selects a paragraph in PDF about a methodology
2. User clicks "Analyze with LLM" button
3. User types prompt: "Evaluate the rigor of this experimental design"
4. LLM processes the text and returns analysis
5. Results displayed in overlay with highlights
6. User can save analysis or try different prompts

## Configuration

### Environment Variables

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_PDF_DIRECTORY=/papers
VITE_LLM_API_URL=http://localhost:8000  # Future LLM service
VITE_LLM_API_KEY=your_api_key_here
```

### Features Toggles

```typescript
export const features = {
  llmAnalysis: false, // Enable LLM analysis (Phase 6)
  crossPaperView: true, // Enable cross-paper features
  visualKnowledge: true, // Enable figure/visual extraction
  advancedGraph: true, // Enable advanced graph features
  pathFinding: false, // Path between entities (when API ready)
};
```

## Testing Strategy

### Unit Tests

- Component rendering tests
- API service tests with mocked responses
- Utility function tests (coordinate mapping, formatting)

### Integration Tests

- PDF viewer interaction tests
- Graph interaction tests
- API integration tests
- State management tests

### E2E Tests (Cypress or Playwright)

- Complete user workflows
- Multi-component interactions
- Error scenarios

## Performance Considerations

1. **PDF Rendering**: Only render visible pages, lazy load others
2. **Graph Rendering**: Virtualize large graphs, limit visible nodes
3. **API Calls**: Cache responses, debounce search, batch requests
4. **State Management**: Optimize re-renders, use selectors
5. **Large Datasets**: Implement pagination, infinite scroll

## Future Enhancements

- **Collaborative annotations** - Share highlights and notes
- **Export capabilities** - Export subgraphs, analysis reports
- **Advanced filtering** - Complex multi-criteria filtering
- **Timeline visualization** - Show knowledge evolution over time
- **Mobile responsive** - Tablet and mobile support
- **Offline mode** - Cache papers and data for offline use
- **AI-powered insights** - Automatic pattern detection
- **Citation network** - Show paper citation relationships

## Success Metrics

- Users can find entities across papers in < 3 clicks
- PDF-to-graph navigation is seamless and instant
- Cross-paper relationship discovery is intuitive
- LLM analysis provides actionable insights
- System handles 50+ papers without performance degradation

---

## Next Steps

1. **Create Vite + React + TypeScript project**
2. **Set up project structure** following the layout above
3. **Install dependencies** (React, TypeScript, Tailwind, React Flow/D3, PDF.js)
4. **Create TypeScript types** matching the API response schemas
5. **Build API client** with all endpoint integrations
6. **Start with basic layout** and routing
7. **Implement PDF viewer** as the foundation
8. **Build incrementally** following the phase plan

Let's build an amazing research exploration tool! ðŸ€
