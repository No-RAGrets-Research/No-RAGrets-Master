y# Annotated View Implementation Plan (Updated with Docling + New API Endpoints)

## Vision

Create a dual-mode paper viewer:

1. **Reference Mode**: Clean PDF viewing (current implementation)
2. **Annotated Mode**: Interactive HTML document with click-to-explore relations

**Key Insight**: Use pre-processed docling JSON for document structure, then lazy-load relations via new API endpoints when user clicks.

---

## Architecture Overview

```
Docling JSON (local)OK†’ Parse & Render HTMLOK†’ User ClicksOK†’ API LookupOK†’ Display Relations
                             OK†OK                                             OK†
                      Interactive Document                            Sidebar Details
```

### Major Architectural Change

**OLD Approach:**

- Extract text from PDF using PDF.js
- Fetch all relations upfront
- Match relations to extracted text
- Slow, complex, redundant work

**NEW Approach:**

- Load docling JSON (already has complete structure)
- Render document immediately
- Only fetch relations when user clicks
- Fast, simple, efficient

### Benefits

- No PDF text extraction (docling already did it)
- No upfront relation fetching (lazy load on click)
- No coordinate conversions
- No alignment issues
- Instant document rendering
- Perfect document structure (sections, figures, tables)
- Efficient API usage (only fetch what's needed)
- Figures included (docling has pictures array)

---

## Data Flow

### 1. Input Sources

**From Docling JSON (local file):**

```typescript
{
  "schema_name": "DoclingDocument",
  "name": "A. Priyadarsini et al. 2023",
  "body": {
    "children": [
      { "$ref": "#/texts/0" },
      { "$ref": "#/pictures/0" },
      { "$ref": "#/texts/1" },
      // ...
    ]
  },
  "texts": [
    {
      "self_ref": "#/texts/0",
      "text": "Methanotrophs convert methane to methanol...",
      "label": "text", // or "section_header", "caption", etc.
      "prov": [
        {
          "page_no": 3,
          "bbox": { "l": 37.5, "t": 200.3, "r": 300.8, "b": 215.6 },
          "charspan": [0, 145]
        }
      ]
    }
  ],
  "pictures": [
    {
      "self_ref": "#/pictures/0",
      "prov": [{ "page_no": 5, "bbox": {...} }]
      // May include image data or reference
    }
  ],
  "tables": [...]
}
```

**From New API Endpoints (on-demand):**

```typescript
// When user clicks text
GET /api/relations/by-chunk?paper_id=Paper.pdf&chunk_id=19
GET /api/relations/by-text?q=Methanotrophs+convert+methane
GET /api/relations/by-location?paper_id=Paper.pdf&page=3

// When user clicks figure
GET /api/relations/by-figure?paper_id=Paper.pdf&figure_id=page5_fig1

// For batch details
GET /api/relations/source-spans?ids=0x1,0x2,0x3  // max 500 ids

// For visual helpers
GET /api/relations/{id}/section-image  // highlighted image snippet
GET /api/relations/{id}/provenance     // bbox data
```

### 2. Rendering Process

```typescript
// Step 1: Load docling JSON (local, instant)
const docling = await fetch(`/docling_json/${paperName}.json`).then((r) =>
  r.json()
);

// Step 2: Parse document structure
const document = parseDoclingDocument(docling);
// Returns: { texts, pictures, tables, body_order }

// Step 3: Render HTML immediately
<DoclingRenderer document={document}>
  {document.body_order.map((item, idx) => {
    if (item.type === "text") {
      return (
        <TextBlock
          key={idx}
          text={item.text}
          label={item.label} // text, section_header, caption
          page={item.page_no}
          onClick={() => handleTextClick(item)}
        />
      );
    }
    if (item.type === "picture") {
      return (
        <FigureBlock
          key={idx}
          picture={item}
          onClick={() => handleFigureClick(item)}
        />
      );
    }
  })}
</DoclingRenderer>;

// Step 4: On click, fetch relations
async function handleTextClick(textBlock) {
  // Try chunk_id first (if available and mapped)
  let relations = await api.getRelationsByChunk(paperId, textBlock.chunk_id);

  // Fallback: text search
  if (!relations || relations.length === 0) {
    relations = await api.getRelationsByText(textBlock.text);
  }

  // Show in sidebar
  setSidebarRelations(relations);
  setSelectedTextBlock(textBlock);
}

async function handleFigureClick(picture) {
  // New endpoint - fully operational!
  const figureId = `page${picture.page_no}_fig${picture.index}`;
  const relations = await api.getRelationsByFigure(paperId, figureId);

  setSidebarRelations(relations);
  setSelectedFigure(picture);
}
```

---

## Component Architecture

### Mode Toggle

```
PaperView
””€ ViewModeToggle
”‚ OK””€ "Reference" button
”‚ OK”””€ "Annotated" button
”‚
””€ {mode === 'reference' && <ReferenceView />}
””€ {mode === 'annotated' && <AnnotatedView />}
”‚
”””€ SidePanel (shared between both modes)
```

### Reference View (Keep Current)

```jsx
<ReferenceView>
  <PDFViewer file={pdfUrl} onPageChange={setCurrentPage} zoom={zoom} />
  {/* Clean PDF viewing, no changes needed */}
</ReferenceView>
```

### Annotated View (NEW - Docling-based)

```jsx
<AnnotatedView paperFilename={paperFilename}>
  <DoclingRenderer
    doclingData={doclingData}
    onTextClick={handleTextClick}
    onFigureClick={handleFigureClick}
    selectedBlock={selectedBlock}
  >
    {/* Renders document structure from docling JSON */}
    {/* - Text blocks (clickable sentences) */}
    {/* - Section headers */}
    {/* - Figures (clickable) */}
    {/* - Tables */}
    {/* - Captions */}
  </DoclingRenderer>
</AnnotatedView>
```

### Click Handler Flow

```typescript
// User clicks text block
const handleTextClick = async (textBlock: DoclingText) => {
  setLoading(true);

  // Try chunk-based lookup (fastest, most accurate)
  let relations = [];
  if (textBlock.chunk_id) {
    relations = await api.getRelationsByChunk(paperId, textBlock.chunk_id);
  }

  // Fallback: text-based search
  if (relations.length === 0) {
    relations = await api.getRelationsByText(textBlock.text);
  }

  // Fallback: location-based search
  if (relations.length === 0) {
    relations = await api.getRelationsByLocation(paperId, textBlock.page_no);
    // Filter to only relations whose bbox intersects this text block
    relations = filterByBboxIntersection(relations, textBlock.bbox);
  }

  // Update UI
  setSelectedBlock(textBlock);
  setSidebarRelations(relations);
  setLoading(false);
};

// User clicks figure
const handleFigureClick = async (figure: DoclingPicture) => {
  setLoading(true);

  // New endpoint - fully operational!
  const figureId = `page${figure.page_no}_fig${figure.index}`;
  const relations = await api.getRelationsByFigure(paperId, figureId);

  // Update UI
  setSelectedFigure(figure);
  setSidebarRelations(relations);
  setLoading(false);
};
```

---

## Implementation Phases (UPDATED)

### Phase 1: Docling Renderer (2-3 days)

**Goal**: Render document from docling JSON

**Tasks:**

1. Create docling JSON loader utility

   ```typescript
   async function loadDoclingData(
     paperFilename: string
   ): Promise<DoclingDocument>;
   ```

2. Create DoclingRenderer component

   - Parse body order (texts, pictures, tables)
   - Render text blocks with proper styling
   - Render section headers (h1, h2, h3 based on level)
   - Render figures as placeholders
   - Apply reading order from docling

3. Style with Tailwind prose
   - Typography for readability
   - Proper spacing between elements
   - Page indicators
   - Section dividers

**Deliverable**: Can render complete document from docling JSON (no interactions yet)

**Verification:**

- Document structure matches PDF
- All text appears in correct order
- Sections are clearly delineated
- Figures show as placeholders

---

---

## Sidebar Integration Strategy (Hybrid Approach)

### Current Sidebar State

The sidebar currently displays:

- Entity counts by type
- Relations for the current page
- Selected relation detail (when relation is clicked)

### New Behavior with Click-to-Explore

**Default State (No Selection):**

- Show page-level relations (current behavior)
- Display entity counts
- Standard view mode

**Active Selection State (Text/Figure/Table Clicked):**

1. **Add "Selected Content" section at top of sidebar:**

   - Show what was selected (snippet of text or "Figure X from page Y")
   - Display loading spinner while fetching
   - Show count: "N relations found in selection"
   - Include clear selection button (X icon)

2. **Display selection-specific relations:**

   - Replace or prepend to page relations
   - Group by relation type if many results
   - Each relation remains clickable for detail view

3. **Empty results handling:**

   - Show message: "No relations found in this selection"
   - Keep the selection highlighted
   - Allow user to clear selection and return to page view

4. **Clear selection action:**
   - Click X buttonOK†’ deselectOK†’ return to page view
   - Click elsewhere in documentOK†’ new selectionOK†’ fetch new relations
   - Switch pagesOK†’ auto-clear selection

### Visual Layout

```
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚ SIDEBAR                        OK”‚
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”¤
”‚                                OK”‚
”‚ [IF SELECTION ACTIVE]          OK”‚
”‚OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”OK”‚
”‚OK”‚ Selected Content         [X]”‚OK”‚
”‚OK”‚ "Methanotrophs convert..." OK”‚OK”‚
”‚OK”‚ Page 3                     OK”‚OK”‚
”‚OK”‚                            OK”‚OK”‚
”‚OK”‚ [Loading...] or            OK”‚OK”‚
”‚OK”‚ 5 relations found          OK”‚OK”‚
”‚OK”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜OK”‚
”‚                                OK”‚
”‚ Selection Relations:           OK”‚
”‚OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”OK”‚
”‚OK”‚ SubjectOK†’ PredicateOK†’ Object”‚OK”‚
”‚OK”‚ ...                        OK”‚OK”‚
”‚OK”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜OK”‚
”‚                                OK”‚
”‚OK”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€OK”‚
”‚                                OK”‚
”‚ [IF NO SELECTION]              OK”‚
”‚ Page Relations:                OK”‚
”‚OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”OK”‚
”‚OK”‚ All relations on page N    OK”‚OK”‚
”‚OK”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜OK”‚
”‚                                OK”‚
”‚ Entity Counts:                 OK”‚
”‚OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”OK”‚
”‚OK”‚ GENE: 42                   OK”‚OK”‚
”‚OK”‚ PROTEIN: 28                OK”‚OK”‚
”‚OK”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
```

### API Lookup Strategy

**For Text Blocks:**

1. **Primary**: Chunk-based lookup (if chunk_id available in provenance)

   - `GET /api/relations/by-chunk?paper_id={paperId}&chunk_id={chunkId}`
   - Fastest and most accurate

2. **Fallback 1**: Text search

   - `GET /api/relations/by-text?q={encodedText}`
   - Good for direct text matches

3. **Fallback 2**: Location + bbox filtering
   - `GET /api/relations/by-location?paper_id={paperId}&page={pageNum}`
   - Filter results by bbox intersection with text block
   - Most comprehensive but slowest

**For Figures:**

- Construct figure ID: `page{N}_fig{M}` (e.g., "page5_fig1")
- `GET /api/relations/by-figure?paper_id={paperId}&figure_id={figureId}`
- Backend handles figure-to-relation mapping

**For Tables:**

- Similar to figures: construct table ID
- `GET /api/relations/by-table?paper_id={paperId}&table_id={tableId}` (if endpoint exists)
- Or use location-based approach with bbox filtering

---

## Implementation Phases (UPDATED)

### Phase 1: Docling Renderer (COMPLETED)

**Status**: DONE

**Completed Tasks:**

- Created docling JSON loader utility
- Implemented DoclingRenderer component with text/figure/table rendering
- Added proper styling with Tailwind prose
- Figures render with lazy-loaded images from PDF
- Tables render with full HTML structure
- Document displays in clean, centered, paper-like layout

**Deliverable**: Complete document rendering from docling JSON

---

### Phase 2: Click-to-Lookup Integration (NEXT - 2-3 days)

**Goal**: Add click handlers and API integration

**Tasks:**

1. Make text blocks clickable

   - Add hover effects
   - Track selected block state
   - Visual feedback on click

2. Implement API lookup functions

   ```typescript
   // Primary: chunk-based (if available)
   getRelationsByChunk(paperId: string, chunkId: number): Promise<Relation[]>

   // Fallback: text search
   getRelationsByText(text: string): Promise<Relation[]>

   // Fallback: location-based + bbox filtering
   getRelationsByLocation(paperId: string, page: number): Promise<Relation[]>

   // For figures
   getRelationsByFigure(paperId: string, figureId: string): Promise<Relation[]>
   ```

3. Connect to existing sidebar

   - Pass relations to existing RelationDetail component
   - Sync selected state
   - Handle loading states

   - Show snippet of selected content in sidebar header
   - Smooth transitions when switching selections

4. Handle edge cases
   - Empty results: Show "No relations found" message
   - Multiple clicks: Cancel previous requests
   - Page navigation: Clear selection automatically

**Deliverable**: Hybrid sidebar that shows selection-specific or page-level relations

**Verification:**

- Clicking text/figure/table fetches and displays relations in sidebar
- Selection is clearly indicated in both document and sidebar
- Can clear selection and return to page view
- Loading states display appropriately
- Empty results handled gracefully
- Multiple rapid clicks don't cause UI issues

---

### Phase 3: Advanced Interactions (Future - 2-3 days)

**Goal**: Fine-grained clickability at sentence level

**Tasks:**

1. Parse text blocks into sentences

   ```typescript
   function splitIntoSentences(text: string): Sentence[];
   // Use charspan boundaries from docling
   ```

2. Make individual sentences clickable

   - Hover highlights sentence
   - Click selects sentence
   - Visual boundary indicators

3. Refine API lookups for sentences

   - Use sentence text for more precise lookup
   - Filter relations by sentence_range if available
   - Handle multi-sentence relations

4. Add sentence-level highlighting
   - Highlight clicked sentence
   - Dim other sentences slightly
   - Smooth transitions

**Deliverable**: Can click individual sentences, not just blocks

**Verification:**

- Sentence boundaries are accurate
- Clicking sentence shows relevant relations
- Highlighting is smooth and clear
- Works with multi-sentence paragraphs

---

### Phase 5: Polish & Features (ongoing)

**Tasks:**

- Search within document (matches docling text)
- Virtual scrolling for long papers (react-window)
- Export annotated view (markdown, HTML)
- Add user notes/comments (stored locally)
- Cross-paper comparison view
- Table interaction (click table cells)
- Citation linking (click referencesOK†’ jump to bibliography)
- Keyboard navigation (arrow keys to move between sentences)

---

## Technical Details

### Docling JSON Data Structure

```typescript
interface DoclingDocument {
  schema_name: "DoclingDocument";
  version: string; // e.g., "1.8.0"
  name: string;
  origin: {
    mimetype: string;
    binary_hash: string;
    filename: string;
  };
  furniture: {
    self_ref: string;
    children: Array<{ $ref: string }>;
    name: string;
    label: string;
  };
  body: {
    self_ref: string;
    children: Array<{ $ref: string }>; // Pointers like "#/texts/0", "#/pictures/0"
    name: string;
    label: string;
  };
  texts: DoclingText[];
  pictures: DoclingPicture[];
  tables: DoclingTable[];
  key_value_items?: any[];
}

interface DoclingText {
  self_ref: string; // "#/texts/42"
  text: string; // Actual text content
  label: "text" | "section_header" | "caption" | "page_header" | "page_footer";
  prov: DoclingProvenance[];
}

interface DoclingPicture {
  self_ref: string; // "#/pictures/5"
  prov: DoclingProvenance[];
  label?: "figure" | "image";
  data?: {
    width?: number;
    height?: number;
    mimetype?: string;
    image?: string; // Base64 or URL
  };
}

interface DoclingTable {
  self_ref: string; // "#/tables/2"
  prov: DoclingProvenance[];
  label?: "table";
  data?: {
    grid: any[][]; // Table cells
  };
}

interface DoclingProvenance {
  page_no: number; // 1-indexed page number
  bbox: {
    l: number; // Left (normalized 0-1)
    t: number; // Top (normalized 0-1)
    r: number; // Right (normalized 0-1)
    b: number; // Bottom (normalized 0-1)
    coord_origin: string; // "TOPLEFT"
  };
  charspan?: [number, number]; // Character range in original text
}
```

### Rendering Pipeline

```typescript
// 1. Load docling JSON
async function loadDoclingData(
  paperFilename: string
): Promise<DoclingDocument> {
  const response = await fetch(`/docling_json/${paperFilename}.json`);
  return response.json();
}

// 2. Parse document structure
function parseDoclingDocument(docling: DoclingDocument): ParsedDocument {
  const { body, texts, pictures, tables } = docling;

  // Resolve $ref pointers
  const items = body.children.map((ref) => {
    const path = ref.$ref; // e.g., "#/texts/0"
    const [type, index] = path.split("/").slice(1); // ["texts", "0"]

    if (type === "texts") return { type: "text", data: texts[parseInt(index)] };
    if (type === "pictures")
      return { type: "picture", data: pictures[parseInt(index)] };
    if (type === "tables")
      return { type: "table", data: tables[parseInt(index)] };

    return null;
  });

  return {
    items: items.filter(Boolean),
    texts,
    pictures,
    tables,
  };
}

// 3. Render item
function renderDoclingItem(item: DoclingItem) {
  switch (item.type) {
    case "text":
      return renderTextBlock(item.data as DoclingText);
    case "picture":
      return renderPicture(item.data as DoclingPicture);
    case "table":
      return renderTable(item.data as DoclingTable);
  }
}

// 4. Make text clickable
function renderTextBlock(textBlock: DoclingText) {
  const isHeader = textBlock.label === "section_header";
  const Tag = isHeader ? "h2" : "p";

  return (
    <Tag
      className={cn(
        "cursor-pointer hover:bg-blue-50 rounded px-2 py-1 transition-colors",
        isHeader && "text-2xl font-bold mt-6 mb-3",
        textBlock.label === "caption" && "text-sm italic text-gray-600"
      )}
      onClick={() => handleTextClick(textBlock)}
    >
      {textBlock.text}
    </Tag>
  );
}

// 5. Handle clicks
async function handleTextClick(textBlock: DoclingText) {
  setLoading(true);

  // Try endpoints in order of speed/accuracy
  let relations: Relation[] = [];

  // 1. Try chunk-based lookup (fastest)
  if (textBlock.chunk_id) {
    relations = await api.getRelationsByChunk(paperId, textBlock.chunk_id);
  }

  // 2. Fallback: text search
  if (relations.length === 0) {
    relations = await api.getRelationsByText(textBlock.text);
  }

  // 3. Fallback: location-based
  if (relations.length === 0 && textBlock.prov.length > 0) {
    const page = textBlock.prov[0].page_no;
    const allPageRelations = await api.getRelationsByLocation(paperId, page);

    // Filter to only relations that spatially overlap this text
    relations = allPageRelations.filter((rel) =>
      doesBboxIntersect(rel.bbox, textBlock.prov[0].bbox)
    );
  }

  setSidebarRelations(relations);
  setSelectedTextBlock(textBlock);
  setLoading(false);
}

// 6. Handle figure clicks
async function handleFigureClick(picture: DoclingPicture) {
  setLoading(true);

  // Construct figure ID from page and index
  const figureId = `page${picture.prov[0].page_no}_fig${picture.index}`;

  // Use new by-figure endpoint (fully operational!)
  const relations = await api.getRelationsByFigure(paperId, figureId);

  setSidebarRelations(relations);
  setSelectedFigure(picture);
  setLoading(false);
}

// 7. Spatial intersection helper
function doesBboxIntersect(bbox1: BBox, bbox2: BBox): boolean {
  return !(
    bbox1.r < bbox2.l ||
    bbox1.l > bbox2.r ||
    bbox1.b < bbox2.t ||
    bbox1.t > bbox2.b
  );
}
```

### API Service Functions (New)

Add these to `src/services/api/relations.ts`:

```typescript
export async function getRelationsByText(query: string): Promise<Relation[]> {
  const response = await fetch(
    `${API_BASE}/api/relations/by-text?q=${encodeURIComponent(query)}`
  );
  if (!response.ok) throw new Error("Failed to fetch relations by text");
  return response.json();
}

export async function getRelationsByChunk(
  paperId: string,
  chunkId: number
): Promise<Relation[]> {
  const response = await fetch(
    `${API_BASE}/api/relations/by-chunk?paper_id=${paperId}&chunk_id=${chunkId}`
  );
  if (!response.ok) throw new Error("Failed to fetch relations by chunk");
  return response.json();
}

export async function getRelationsByLocation(
  paperId: string,
  page?: number,
  section?: string
): Promise<Relation[]> {
  const params = new URLSearchParams();
  params.set("paper_id", paperId);
  if (page !== undefined) params.set("page", page.toString());
  if (section) params.set("section", section);

  const response = await fetch(
    `${API_BASE}/api/relations/by-location?${params.toString()}`
  );
  if (!response.ok) throw new Error("Failed to fetch relations by location");
  return response.json();
}

export async function getRelationsByFigure(
  paperId: string,
  figureId: string
): Promise<Relation[]> {
  const response = await fetch(
    `${API_BASE}/api/relations/by-figure?paper_id=${paperId}&figure_id=${figureId}`
  );
  if (!response.ok) throw new Error("Failed to fetch relations by figure");
  return response.json();
}

export async function getRelationSectionImage(
  relationId: string
): Promise<Blob> {
  const response = await fetch(
    `${API_BASE}/api/relations/${relationId}/section-image`
  );
  if (!response.ok) throw new Error("Failed to fetch section image");
  return response.blob();
}

export async function getRelationProvenance(
  relationId: string
): Promise<ProvenanceData> {
  const response = await fetch(
    `${API_BASE}/api/relations/${relationId}/provenance`
  );
  if (!response.ok) throw new Error("Failed to fetch provenance");
  return response.json();
}
```

---

## UI/UX Design

### Mode Toggle

```
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚ OK””€”€”€”€”€”€”€”€”€”€”€”€” OK””€”€”€”€”€”€”€”€”€”€”€”€”€”€” OK”‚
”‚ OK”‚  ReferenceOK”‚ OK”‚  Annotated  OK”‚ OK”‚OK† Tabs
”‚ OK”””€”€”€”€”€”€”€”€”€”€”€”€”˜ OK”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜ OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
```

### Reference View (unchanged)

```
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚          [Clean PDF View]           OK”‚
”‚                                     OK”‚
”‚   Page 1 of 47    [- 100% +]      OK”‚
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
```

### Annotated View (NEW - Docling-rendered)

```
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚  Abstract                           OK”‚
”‚ OK”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€ OK”‚
”‚  Methanotrophs convert methane to   OK”‚OK† Click text block
”‚  methanol using MMO enzymes...      OK”‚  OK†’ fetch relations
”‚                                     OK”‚  OK†’ show in sidebar
”‚  3.3 Methanol Production            OK”‚
”‚ OK”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€ OK”‚
”‚  The conversion process requires... OK”‚
”‚                                     OK”‚
”‚  [Figure 1: MMO structure]          OK”‚OK† Click figure
”‚  OK†‘ Clickable figure placeholder    OK”‚  OK†’ fetch figure relations
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
```

### Interaction States

**Hover over text block:**

```
””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”
”‚  Methanotrophs convert methane to   OK”‚OK† Light blue highlight
”‚  methanol using MMO enzymes...      OK”‚   Cursor: pointer
”””€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”˜
```

**Click text block:**

```
1. Text block turns blue (selected state)
2. Loading spinner in sidebar
3. Relations appear in sidebar after ~200-500ms
4. Sidebar highlights matching relation type
```

**Click figure:**

```
1. Figure border turns blue
2. Sidebar shows figure-specific relations
3. Option to view section-image (highlighted PNG)
```

---

## Benefits of This Approach

### For Users

OK **Instant loading** - No API calls until user clicks (0ms initial load)  
OK **Complete document structure** - Sections, figures, tables, captions from docling  
OK **Efficient exploration** - Only fetch relations for content you interact with  
OK **Clean reading experience** - Proper typography, semantic HTML  
OK **Click-to-discover** - Explore relations by clicking any text or figure  
OK **Natural interactions** - Hover, click, scroll just like any webpage

### For Development

OK **Simple architecture** - No PDF extraction, no text matching, no coordinate conversion  
OK **Reliable data** - Docling pre-processed, no runtime parsing errors  
OK **Fast API** - New endpoints optimized for lookup patterns  
OK **Easy to test** - Standard React components, no canvas complexity  
OK **Better performance** - Local JSON parsing vs slow API calls  
OK **Maintainable** - Clear separation: render doclingOK†’ handle clicksOK†’ fetch relations

### For API Efficiency

OK **Lazy loading** - Only fetch relations when user clicks (vs all upfront)  
OK **Targeted queries** - New endpoints allow precise lookups (by-chunk, by-figure, by-text)  
OK **Reduced load** - 1-2 API calls per click vs 1000+ on page load  
OK **Graceful fallbacks** - Try chunkOK†’ textOK†’ location in sequence  
OK **Batch operations** - source-spans endpoint supports 500 IDs when needed

### For Future Features

OK **Cross-paper comparison** - Side-by-side docling views  
OK **Custom annotations** - User highlights stored separately  
OK **Export** - Markdown, HTML with relations embedded  
OK **Mobile-friendly** - Responsive HTML, no canvas  
OK **Knowledge graph** - Click entityOK†’ visualize connections  
OK **Search** - Full-text search in docling JSON (instant)

---

## Migration Strategy

### Phase 0: Preserve Current Work

- Reference view (PDF viewer) stays unchangedOK
- Sidebar components reused (RelationDetail, EntityBreakdown)OK
- API service layer extended with new endpoints

### Phase 1: Build Docling Foundation

- Load docling JSON from `/docling_json/{filename}.json`
- Parse body structure (resolve $refs)
- Render basic text blocks (no clicks yet)
- Verify document structure matches PDF

### Phase 2: Add Interactivity

- Make text blocks clickable
- Implement click handlers (chunkOK†’ textOK†’ location fallbacks)
- Connect to existing sidebar
- Add loading states

### Phase 3: Complete Features

- Render figures as clickable elements
- Add figure-relation lookup
- Render tables
- Polish typography and spacing

### Phase 4: Production Ready

- Virtual scrolling for long documents
- Search within document
- Keyboard navigation
- Accessibility improvements

---

## Key Decisions

### Use Docling JSON Instead of PDF Extraction

**Rationale:**

- Docling already parsed and structured the documents
- Pre-computed text, bbox, page_no for every element
- Includes figures, tables, captions that PDF.js struggles with
- 47 matching JSON files ready to use
- Zero API calls needed for document rendering

### Lazy-Load Relations via New Endpoints

**Rationale:**

- User only views ~5-10% of document content
- Fetching all 1000 relations wastes time/bandwidth
- New endpoints (by-chunk, by-text, by-figure) enable efficient lookup
- 200-500ms response time acceptable for on-demand fetching
- Graceful fallbacks if chunk_id unavailable

### Fallback Hierarchy for Lookups

**Priority order:**

1. **by-chunk** (fastest, most accurate if chunk_id available)
2. **by-text** (flexible, works for any text)
3. **by-location + bbox filtering** (broadest, but needs filtering)

**Rationale:**

- Chunk IDs from pipeline are most reliable
- Text search catches everything chunk lookup misses
- Location-based is safety net for edge cases

### Click Text Blocks, Not Sentences (Initially)

**Rationale:**

- Simpler to implement (one click handler per text block)
- Docling text blocks are already semantic units (paragraphs)
- Sentence splitting can be added in Phase 4 if needed
- Reduces initial complexity

### Render Figures as Placeholders (Initially)

**Rationale:**

- Docling doesn't always embed images (file size)
- Can use section-image endpoint for highlighted PNGs
- Placeholders sufficient to show figure location + relations
- Actual image rendering is Phase 3 enhancement

---

## Success Metrics

### Phase 1 Complete (Docling Renderer)

- [ ] Can load docling JSON for any paper
- [ ] Document structure renders correctly (texts, sections, figures)
- [ ] Typography is readable (Tailwind prose)
- [ ] Page numbers and section headers display
- [ ] Rendering takes <100ms for typical paper

### Phase 2 Complete (Click-to-Lookup)

- [ ] Clicking text block fetches relations (chunk/text/location fallbacks)
- [ ] Relations appear in sidebar within 500ms
- [ ] Selected text block visually highlighted
- [ ] Loading states show clearly
- [ ] No race conditions with multiple clicks

### Phase 3 Complete (Figures + Tables)

- [ ] Figures render as clickable elements
- [ ] Clicking figure shows figure-specific relations
- [ ] Figure captions display correctly
- [ ] Tables render in basic form
- [ ] Can export section-image for visual confirmation

### Phase 4 Complete (Production Ready)

- [ ] Works with all 47 papers
- [ ] Virtual scrolling for papers >50 pages
- [ ] Search within document (matches docling text)
- [ ] Keyboard navigation works
- [ ] Mobile responsive
- [ ] Accessible (ARIA labels, screen reader support)

### Performance Benchmarks

- [ ] Initial render: <100ms (just parse JSON)
- [ ] Click-to-relations: <500ms (API lookup)
- [ ] Mode toggle: <50ms (already loaded)
- [ ] Scroll performance: 60fps
- [ ] Memory usage: <200MB for typical paper

---

## Implementation Notes

### Docling JSON Quirks

- Some papers may have empty `pictures` array (text-only papers)
- Charspan values are optional (not all texts have them)
- Labels vary: `text`, `section_header`, `caption`, `page_header`, `page_footer`
- Body order defines reading sequence (not page order necessarily)

### API Endpoint Considerations

- **by-chunk**: Requires chunk_id from pipeline (may not be in docling JSON)
- **by-text**: Works but can be slow for long passages
- **by-figure**: Fully operational, use `page{N}_fig{M}` format
- **by-location**: Returns all relations on page (needs bbox filtering)
- **source-spans**: Batch endpoint (max 500 IDs) for bulk fetching

### Error Handling

- Docling JSON missingOK†’ graceful error, offer PDF view only
- API endpoint failsOK†’ show toast, try next fallback
- No relations foundOK†’ show "No relations extracted from this section"
- Malformed doclingOK†’ log error, render what's parseable

### State Management

```typescript
// Annotated view state
const [doclingData, setDoclingData] = useState<DoclingDocument | null>(null);
const [selectedBlock, setSelectedBlock] = useState<
  DoclingText | DoclingPicture | null
>(null);
const [sidebarRelations, setSidebarRelations] = useState<Relation[]>([]);
const [loading, setLoading] = useState(false);
```

### Component Structure

```
<AnnotatedView>
  <DoclingRenderer>
    {items.map(item => (
      {item.type === 'text' && <TextBlock onClick={handleTextClick} />}
      {item.type === 'picture' && <FigurePlaceholder onClick={handleFigureClick} />}
      {item.type === 'table' && <TableView />}
    ))}
  </DoclingRenderer>
</AnnotatedView>
```

---

## Next Steps

1. **Finalize this plan**OKOK (current step - update complete)
2. **Create docling JSON loader** - Utility function to load and parse
3. **Build DoclingRenderer component** - Display texts, figures, tables
4. **Add API service functions** - getRelationsByText, getRelationsByChunk, etc.
5. **Implement click handlers** - Connect renderer to API lookups
6. **Integrate with sidebar** - Reuse existing RelationDetail component
7. **Test with A. Priyadarsini paper** - Validate full flow
8. **Expand to all 47 papers** - Ensure consistency
9. **Add figure support** - Render figure placeholders, click-to-lookup
10. **Polish and optimize** - Virtual scrolling, search, accessibility

---

## Comparison: Old vs New Approach

| Aspect             | Old (PDF Extraction)                     | New (Docling + Lazy Lookup)          |
| ------------------ | ---------------------------------------- | ------------------------------------ |
| Initial load time  | 5+ minutes (fetch 1000 source-spans)     | <100ms (parse local JSON)            |
| Data source        | PDF + API source-spans                   | Docling JSON (pre-processed)         |
| Text extraction    | PDF.js getTextContent() - error-prone    | Docling texts[] - reliable           |
| Relation fetching  | All upfront (slow, wasteful)             | Lazy on click (fast, efficient)      |
| Document structure | Must reconstruct from bbox               | Already in docling body order        |
| Figures            | Hard to extract from PDF                 | Docling pictures[] array             |
| Tables             | Very difficult with PDF.js               | Docling tables[] with grid data      |
| API calls on load  | 1000+ (source-spans in batches)          | 0 (only on user interaction)         |
| Complexity         | High (extract, match, sort, reconstruct) | Low (parse, render, handle clicks)   |
| Maintenance        | Fragile (bbox coord conversions)         | Robust (semantic HTML)               |
| User experience    | Long wait before interaction             | Instant rendering, explore on demand |
| Extensibility      | Hard (canvas-based)                      | Easy (standard HTML/React)           |

---
