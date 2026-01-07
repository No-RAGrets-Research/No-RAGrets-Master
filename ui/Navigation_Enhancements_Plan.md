# Navigation Enhancements Plan

## Overview

Plan to create bidirectional navigation between Graph View and Paper View, creating a highly interconnected exploration experience.

---

## 1. Relation → Paper Navigation (PRIORITY: HIGH - Implement First)

### Goal

Click "View Paper" on a relation in the knowledge graph and navigate directly to the exact location in the paper where that relation was extracted.

### Current Behavior

- "View Paper" button opens the paper but user must manually find the relation

### Proposed Behavior

- Click relation in graph → Navigate to paper with provenance data
- Paper opens in **Annotated View** (not PDF mode)
- Auto-scroll to specific page and text block
- Auto-select and highlight the text containing the relation
- Sidebar immediately shows the selected relation

### Technical Approach

- Relations already have provenance data (page numbers, bounding boxes, text references)
- Pass relation provenance through React Router navigation state
- Example URL: `/papers/paper123?page=5&highlight=text_42` or with state object
- PaperView component detects incoming navigation state on mount
- Triggers auto-selection of the corresponding text block
- Scrolls annotated view to correct position

### Implementation Requirements

- [ ] Extend "View Paper" button to pass relation data in navigation state
- [ ] Add useEffect in PaperView to detect incoming navigation state
- [ ] Implement auto-scroll logic in AnnotatedView
- [ ] Auto-trigger text block selection based on provenance
- [ ] Ensure sidebar displays the relation immediately

### UX Flow

```
Graph View: User clicks relation "methanotroph → produces → methane"
  ↓
Navigate to: /papers/Priyadarsini-2023.pdf (with relation ID in state)
  ↓
Paper View opens: Automatically in Annotated mode
  ↓
Auto-scroll: Jumps to page 3, paragraph 5
  ↓
Auto-highlight: Text block highlighted with blue border
  ↓
Sidebar shows: Selected relation details and context
  ↓
User sees: Exact sentence/paragraph where relation was extracted
```

### Value

- **Validation**: Quickly verify relation extraction accuracy
- **Context**: See full paragraph context around relation
- **Trust**: Users can inspect source evidence directly
- **Exploration**: Jump between graph patterns and source text seamlessly

---

## 2. Paper → Graph Navigation (PRIORITY: MEDIUM - Implement Second)

### Goal

Click "View in Graph" from an entity or relation in the paper view and navigate to the knowledge graph focused on that specific item.

### Current Behavior

- No way to jump from paper to graph for a specific entity/relation

### Proposed Behavior

- Add "View in Graph" button next to entities/relations in paper sidebar
- Navigate to `/graph?focus=entity_123` or `/graph?relation=rel_456`
- Graph loads centered on that entity/relation
- Node highlighted with different color or pulsing animation
- Info panel auto-opens showing details
- Related nodes are visible in immediate neighborhood

### Technical Approach

- Add "View in Graph" button in RelationDetail component
- Add button next to entity names in sidebar
- Navigate with query params: `/graph?focus=<entity_id>`
- GraphView reads URL params on mount
- Fetch entity connections via API
- Center graph on focused node
- Apply visual highlighting
- Auto-open info panel with entity details

### Implementation Requirements

- [ ] Add "View in Graph" buttons to paper sidebar components
- [ ] Implement URL param handling in GraphView
- [ ] Add API call to fetch connections for specific entity
- [ ] Implement graph centering/focusing logic
- [ ] Add visual highlighting for focused node (color/pulse animation)
- [ ] Auto-open info panel with entity details

### UX Flow

```
Paper View: Reading about "Methylococcus capsulatus"
  ↓
User clicks: "View in Graph" button next to entity
  ↓
Navigate to: /graph?focus=entity_methylococcus_123
  ↓
Graph View opens: Methylococcus node at center with connections
  ↓
Visual highlight: Node pulses or has distinct color
  ↓
Info panel auto-opens: Shows entity details, connected papers, relations
  ↓
User explores: Can see all papers mentioning this entity, related entities
```

### Value

- **Cross-paper context**: See how entity appears across multiple papers
- **Discovery**: Find related entities and concepts
- **Comparison**: Compare how different papers discuss same entity
- **Bidirectional flow**: Complete the loop between micro (paper) and macro (graph) views

---

## 3. Search Page Decision (PRIORITY: LOW - Decide Last)

### Current State

- Dedicated SearchView page with simple entity text search
- GraphView also has search functionality built in
- Some redundancy in functionality

### Options

#### Option A: Keep SearchView, Enhance It

**Enhancements:**

- Search returns both entities AND relations (not just entities)
- Click result → navigate to graph focused on that item
- Click result → navigate to source papers
- Becomes a "quick navigation hub"

**Pros:**

- Fast text-based lookup without loading graph
- Lighter weight for quick searches
- List format easier to scan than graph nodes

**Cons:**

- Maintenance overhead for separate view
- Feature duplication with GraphView search

#### Option B: Merge into GraphView (RECOMMENDED)

**Implementation:**

- Add prominent "search results panel" to GraphView sidebar
- Default state: Show "most connected entities" or "recent papers"
- When searching: Show list of matching entities/relations in sidebar
- Click result: Focus and highlight in graph
- Keep both list and visual views in one place

**Pros:**

- Best of both worlds: quick text search + visual context
- Single view to maintain
- More intuitive - search and results in same view
- Reduces app complexity

**Cons:**

- Graph might load slower than dedicated search page
- More complex GraphView component

#### Option C: Remove Completely

**Implementation:**

- Remove SearchView and `/search` route
- Update sidebar navigation
- Rely entirely on GraphView search
- Simplify to 3 main views: Dashboard, Graph, Papers

**Pros:**

- Simplest option
- Least code to maintain

**Cons:**

- Loses quick text-based search capability
- GraphView must always load for any search

### Recommendation

**Option B: Merge into GraphView**

- Implement after completing #1 and #2
- Observe usage patterns first
- Provides best user experience with integrated search + visualization
- Reduces maintenance while keeping functionality

---

## Implementation Priority

1. **FIRST: Relation → Paper Navigation**

   - Highest value
   - Clear use case for validation
   - Relatively straightforward implementation

2. **SECOND: Paper → Graph Navigation**

   - Completes bidirectional flow
   - Enables cross-paper exploration
   - Builds on patterns from #1

3. **LAST: Search Page Decision**
   - Observe how #1 and #2 change usage patterns
   - Make informed decision based on actual user flow
   - Can be implemented iteratively

---

## Expected Impact

### User Experience

- Fluid navigation between macro (graph) and micro (paper) views
- Seamless validation of extracted knowledge
- Enhanced discoverability of cross-paper patterns
- Reduced friction in exploration workflow

### Use Cases Enabled

1. **Validation workflow**: Graph → Relation → Paper source → Verify accuracy
2. **Discovery workflow**: Paper → Entity → Graph → Find related papers
3. **Comparison workflow**: Graph → Entity → Multiple papers → Compare mentions
4. **Deep dive workflow**: Graph pattern → Paper evidence → Related graph patterns

### Success Metrics

- Reduced time to validate relations
- Increased cross-paper exploration
- Higher engagement with both graph and paper views
- Reduced need for manual navigation/searching
