# Knowledge Graph Visualization Plan

## Overview

This document outlines the plan for implementing an interactive knowledge graph visualization in the No-RAGrets UI. The visualization will allow users to explore relationships between entities across multiple scientific papers, discover connections, and navigate between related research.

## Goals

1. Provide a global view of all entities and relations across papers
2. Enable entity-based search and exploration
3. Allow users to discover unexpected connections between research
4. Support navigation from graph view to specific papers
5. Create an intuitive, interactive interface for knowledge discovery

## Endpoint Testing Results

### Working Endpoints

**1. Graph Statistics - `/api/graph/stats`**

- Status: Working correctly
- Returns:
  - `total_nodes`: 28,530 entities
  - `total_relations`: 17,451 relations
  - `total_papers`: 71 papers
  - `unique_predicates`: 6,408 relation types
- Use case: Display overview statistics, determine graph size

**2. Most Connected Entities - `/api/entities/most-connected?limit=N`**

- Status: Working correctly
- Returns: Array of entities with connection counts
- Top entities: Methane (121 connections), Methanotrophs (104 connections)
- Each entity includes:
  - `entity.id`: Unique identifier (e.g., "0x2a")
  - `entity.name`: Entity name
  - `entity.type`: Entity type (e.g., "biochemical_entity")
  - `total_connections`: Total number of relations
  - `outgoing_count`: Relations where entity is subject
  - `incoming_count`: Relations where entity is object
- Use case: Identify hub nodes, initial graph population

**3. Entity Search - `/api/entities/search?q=query&limit=N`**

- Status: Working correctly
- Returns: Array of matching entities
- Supports partial matching (e.g., "methane" finds "Methane", "Methane monooxygenase")
- Use case: User search functionality, finding specific entities

**4. Entity Connections - `/api/entities/{entity_name}/connections?max_relations=N`**

- Status: **WORKING CORRECTLY** (Backend fixed the validation issue)
- Returns: Object with `outgoing` and `incoming` arrays of relations
- Query Parameters:
  - `max_relations` (optional, default: 50): Maximum relations per direction
  - `direction` (optional, default: "both"): "incoming", "outgoing", or "both"
- Each relation includes:
  - `id`: Relation identifier
  - `predicate`: Relationship type (e.g., "has", "is", "produces")
  - `subject`: Full entity object (id, name, type, namespace)
  - `object`: Full entity object (id, name, type, namespace)
  - `section`: Document section where relation was found
  - `pages`: Array of page numbers
  - `source_paper`: Paper filename
  - `confidence`: Extraction confidence (if available)
  - `figure_id`, `table_id`: Source figure/table (if applicable)
- Example response for "Methane":
  - Outgoing: "Methane has 28-34 times higher global warming potential..."
  - Incoming: "High temperatures and pressures can be employed to promote reaction Methane"
- Use case: Expanding entity nodes to show all connections, building graph edges

### All Endpoints Operational

All four required endpoints are now fully functional and ready for integration into the graph visualization feature.

## Implementation Strategy

### Phase 1: Global Multi-Paper Knowledge Graph

**Description:** Show all entities and relations across all papers in one interactive network view.

**User Flow:**

1. User navigates to Graph View
2. System loads top 50 most-connected entities as initial graph
3. User can:
   - Search for specific entities using search bar
   - Filter by entity type (if type filtering is implemented)
   - Click on entity node to highlight it
   - Expand entity to show connections (once backend fixes connections endpoint)
   - Click on relation edge to see details (source paper, context)
   - Click "View in Paper" to navigate to PaperView with entity highlighted

**Visual Design:**

- Interactive force-directed graph using ReactFlow
- Node size proportional to connection count (hub nodes larger)
- Node colors based on entity type
- Edge labels showing relation types (predicates)
- Minimap for navigation of large graphs
- Zoom and pan controls
- Search overlay with autocomplete

**Initial Data Loading:**

```
1. Fetch /api/graph/stats -> Display statistics panel
2. Fetch /api/entities/most-connected?limit=50 -> Create initial nodes
3. For each top entity, optionally fetch /api/entities/{name}/connections
   to build initial edges between visible nodes
4. Apply force-directed layout algorithm
```

**Note:** Now that the connections endpoint works, we can build a fully connected graph from the start by fetching connections for the initial 50 entities and creating edges between them.

### Phase 2: Entity Search and Filtering

**Search Functionality:**

- Search bar at top of graph view
- Uses `/api/entities/search?q={query}` endpoint
- Autocomplete suggestions as user types
- Clicking search result centers and highlights entity in graph
- If entity not currently in graph, fetch and add it

**Filter Options:**

- Filter by entity type (when backend provides types)
- Filter by connection threshold (only show entities with N+ connections)
- Filter by paper source (show entities from specific papers)
- Toggle edge labels on/off for clarity

### Phase 3: Interactive Expansion

**Entity Interaction:**

- Click entity node -> Show info panel with:
  - Entity name and type
  - Total connections count
  - List of papers mentioning this entity
  - "Expand connections" button
  - "View in papers" button
- Double-click entity -> Expand to show direct connections
- Right-click entity -> Context menu with actions

**Connection Expansion:**

- Fetch `/api/entities/{name}/connections?max_relations=50`
- Add connected entities to graph if not present
- Add relation edges with predicates as labels
- Animate new nodes appearing with smooth transitions
- Limit expansion to prevent overcrowding (user can expand further)
- Cache fetched connections to avoid redundant API calls

**Relation Details:**

- Click edge -> Show panel with:
  - Subject entity (with link to expand/focus)
  - Predicate (relation type)
  - Object entity (with link to expand/focus)
  - Source paper(s) with section names
  - Page numbers where relation appears
  - Original text context from section
  - Figure/table reference (if relation from visual element)
  - "View in paper" button to navigate to source

### Phase 4: Paper Navigation Integration

**From Graph to Paper:**

- Info panels include "View in Paper" button
- Clicking navigates to PaperView
- Pass entity name as URL parameter or state
- PaperView highlights all occurrences of entity
- User can return to graph with browser back button

**From Paper to Graph:**

- Add "Explore in Graph" button to PaperView
- Clicking navigates to GraphView
- Centers graph on selected entity from paper
- Shows connections relevant to that entity

## Technical Implementation

### Components to Create

**1. GraphView.tsx (Page)**

- Main container for graph visualization
- Manages graph state (nodes, edges, layout)
- Handles data fetching from API
- Coordinates between child components

**2. KnowledgeGraphCanvas.tsx (Component)**

- ReactFlow wrapper component
- Renders nodes and edges
- Handles zoom, pan, selection
- Custom node and edge components

**3. GraphControls.tsx (Component)**

- Search bar with autocomplete
- Filter controls
- Statistics display
- Layout algorithm selector
- Zoom controls

**4. EntityInfoPanel.tsx (Component)**

- Displays selected entity details
- Shows connections list
- Action buttons (expand, view in paper)
- Connection statistics

**5. RelationInfoPanel.tsx (Component)**

- Displays selected relation details
- Shows source paper and context
- Navigate to paper button

### Data Management

**State Management (Zustand):**

```typescript
interface GraphStore {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  searchQuery: string;
  filters: GraphFilters;
  stats: GraphStats;

  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNodes: (nodes: Node[]) => void;
  addEdges: (edges: Edge[]) => void;
  selectNode: (id: string) => void;
  selectEdge: (id: string) => void;
  setSearchQuery: (query: string) => void;
  updateFilters: (filters: Partial<GraphFilters>) => void;
}
```

**Data Fetching (React Query):**

- Cache graph statistics (stale after 5 minutes)
- Cache most-connected entities (stale after 5 minutes)
- Cache entity search results (stale after 2 minutes)
- Cache entity connections (stale after 5 minutes, per entity)
- Invalidate cache when new papers are added
- Prefetch connections for visible nodes on hover

### API Service Functions

**Create `src/services/api/graph.ts`:**

```typescript
// Get graph statistics
export const getGraphStats = async (): Promise<GraphStats> => {
  const response = await apiClient.get("/api/graph/stats");
  return response.data;
};

// Already exists in entities.ts:
// - getMostConnectedEntities(params?: MostConnectedParams)
// - searchEntities(params: EntitySearchParams)
// - getEntityConnections(entityName: string, params?: EntityConnectionsParams) ✓ WORKING
```

### ReactFlow Configuration

**Node Types:**

- Entity nodes with custom styling
- Size based on connection count
- Color based on entity type
- Label with entity name

**Edge Types:**

- Directed edges with arrows
- Labels showing predicate
- Click handlers for details
- Curved paths to avoid overlaps

**Layout Algorithm:**

- Force-directed layout (default)
- Hierarchical layout (optional)
- Circular layout (optional)
- Manual layout (user can drag nodes)

### Performance Considerations

**Large Graph Handling:**

- Lazy loading: Start with top N entities
- Progressive disclosure: Expand on demand
- Virtual rendering: ReactFlow handles off-screen nodes
- Pagination: Limit connections shown per entity
- Debounced search: Wait for user to stop typing
- Cached results: React Query caching strategy

**Optimization:**

- Memoize expensive calculations
- Use React.memo for node/edge components
- Throttle layout recalculations
- Web workers for complex graph algorithms (if needed)

## UI/UX Design

### Layout Structure

```
+---------------------------------------------------+
|  [Search Bar]  [Filters]  [Stats]  [Controls]   |
+---------------------------------------------------+
|                                    |              |
|                                    |   Entity     |
|         Graph Canvas               |   Info       |
|         (ReactFlow)                |   Panel      |
|                                    |   (sidebar)  |
|                                    |              |
+---------------------------------------------------+
|  Minimap  |  [Zoom Controls]                     |
+-----------+--------------------------------------  +
```

### Visual Style

**Colors:**

- Background: Light gray (light mode) / Dark gray (dark mode)
- Entity nodes: Gradient based on type
- Selected node: Highlight with glow effect
- Edges: Semi-transparent lines
- Selected edge: Bright color with animation

**Interactions:**

- Hover: Show tooltip with entity name and connection count
- Click: Select and show info panel
- Double-click: Expand connections
- Right-click: Context menu
- Drag: Reposition node (manual layout)
- Scroll: Zoom in/out

### Accessibility

- Keyboard navigation support
- Screen reader labels for nodes and edges
- High contrast mode
- Adjustable text sizes
- Focus indicators

## Future Enhancements

### Advanced Features (Post-MVP)

1. **Paper-to-Paper Navigation Graph**

   - Show papers as nodes connected by shared entities
   - Visual representation of research relationships
   - Timeline view (if paper dates available)

2. **Subgraph Extraction**

   - Select multiple entities
   - Extract and save subgraph
   - Export as image or data file

3. **Path Finding**

   - Find shortest path between two entities
   - Visualize connection chains
   - Highlight path in graph

4. **Clustering**

   - Automatic grouping of related entities
   - Visual clusters/communities
   - Cluster labels

5. **Temporal Analysis**

   - Animate graph growth over time
   - Show when entities/relations were added
   - Track research evolution

6. **Collaborative Features**
   - Share graph views (URL with state)
   - Annotate entities and relations
   - Save favorite views

## Success Metrics

**Functionality:**

- Graph renders with 50+ entities within 2 seconds
- Search returns results within 500ms
- Smooth interactions (60fps) with 100+ nodes
- All entity types visually distinguishable

**User Experience:**

- Users can find specific entities easily
- Users can understand entity relationships
- Navigation between graph and papers is seamless
- Interface is intuitive without training

## Dependencies

**Required:**

- ReactFlow (already installed)
- Zustand (already installed)
- React Query (already installed)
- Lucide icons (already installed)

**Optional:**

- d3-force (for custom layout algorithms)
- elkjs (for advanced layouts)

## Timeline Estimate

**Phase 1: Basic Graph (3-4 days)**

- Day 1: Set up GraphView component and ReactFlow integration
- Day 2: Implement data fetching and initial node rendering
- Day 3: Add basic interactions (click, hover, select)
- Day 4: Polish styling and add controls

**Phase 2: Search and Filters (2-3 days)**

- Day 1: Implement search functionality with autocomplete
- Day 2: Add filter controls and statistics panel
- Day 3: Testing and refinement

**Phase 3: Expansion (2-3 days)**

- Day 1: Entity info panel with connection expansion (fully operational now)
- Day 2: Relation details panel with context from connections API
- Day 3: Animation, transitions, and performance optimization

**Phase 4: Integration (1-2 days)**

- Day 1: Navigation between graph and paper views
- Day 2: Testing full user flow and bug fixes

**Total: 8-12 days for full implementation**

## Implementation Steps

### Phase 1: UI Layout and Skeleton (Step 1 - IN PROGRESS)

1. Create GraphView page component with visual placeholder layout

   - Top toolbar with mock search, filters, and stats display
   - Central graph canvas area with "Graph will render here" message
   - Collapsible right sidebar for entity/relation info panels
   - Bottom controls area for minimap and zoom
   - All sections clearly labeled and styled for visualization

2. Create placeholder components:
   - GraphControls component (top toolbar)
   - GraphCanvas component (ReactFlow container)
   - EntityInfoPanel component (sidebar)
   - RelationInfoPanel component (sidebar)

### Phase 2: Data Integration

3. Add API service function for graph stats in src/services/api/graph.ts
4. Fetch and display real graph statistics in toolbar
5. Fetch most-connected entities from API
6. Transform entity data into ReactFlow node format
7. Fetch connections for initial entities
8. Transform connections into ReactFlow edge format

### Phase 3: ReactFlow Integration

9. Install and configure ReactFlow in GraphCanvas
10. Render nodes from entity data
11. Render edges from connection data
12. Apply force-directed layout algorithm
13. Add zoom and pan controls
14. Add minimap component

### Phase 4: Interactivity

15. Implement node click to show EntityInfoPanel
16. Implement edge click to show RelationInfoPanel
17. Add node hover tooltips
18. Implement search functionality with entity highlighting
19. Add filter controls (connection threshold, entity type)
20. Implement connection expansion on node double-click

### Phase 5: Navigation

21. Add "View in Paper" button to info panels
22. Implement navigation to PaperView with entity highlight
23. Add "Explore in Graph" button to PaperView
24. Implement bidirectional navigation flow

## Implementation Status

**Backend API Status:**

- All 4 required endpoints are now fully operational and tested
- Ready to begin frontend implementation immediately
- No blockers remaining

**Ready to Implement:**

- Phase 1: Basic graph rendering with ReactFlow
- Phase 2: Search and filtering
- Phase 3: Interactive expansion (connections API working)
- Phase 4: Paper navigation integration

## Notes

- The graph will be read-only (no entity/relation creation from UI)
- Backend currently has 71 papers with 28,530 entities and 17,451 relations
- Most papers are about methanotrophs and methane-related biochemistry
- Hub entities include: Methane (121 connections), Methanotrophs (104 connections), Methane monooxygenase (14 connections)
- Graph statistics can be displayed in a stats panel for context
- Connection expansion will show rich metadata: section names, page numbers, source papers, predicates
