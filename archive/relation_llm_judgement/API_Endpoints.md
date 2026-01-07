# Knowledge Graph API Endpoints

This document describes all available REST API endpoints for the Knowledge Graph system.

**Base URL**: `http://localhost:8001/api` (or configured port)

**Interactive Documentation**:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

---

## 1. Search & Discovery Endpoints

### Search Entities

**GET** `/api/entities/search`

Search for entities (nodes) by name, type, or namespace.

**Query Parameters:**

- `q` (required): Search term for entity names
- `type` (optional): Filter by entity type (e.g., "chemical", "organism")
- `namespace` (optional): Filter by namespace
- `limit` (optional, default: 20): Maximum results to return

**Example:**

```bash
curl "http://localhost:8001/api/entities/search?q=methanol&limit=10"
```

**Response:**

```json
[
  {
    "id": "0x123",
    "name": "methanol",
    "type": "chemical",
    "namespace": "default",
    "created_at": "2024-11-15T10:30:00Z"
  }
]
```

---

### Search Relations

**GET** `/api/relations/search`

Search for relationships (triples) by predicate, subject, object, or section.

**Query Parameters:**

- `predicate` (optional): Filter by relationship type (e.g., "converts", "produces")
- `subject` (optional): Filter by subject entity name
- `object` (optional): Filter by object entity name
- `section` (optional): Filter by document section
- `limit` (optional, default: 20): Maximum results

**Example:**

```bash
curl "http://localhost:8001/api/relations/search?predicate=convert&limit=5"
```

**Response:**

```json
[
  {
    "id": "0x456",
    "predicate": "convert",
    "subject": {
      "id": "0x123",
      "name": "Methanotrophs",
      "type": "organism"
    },
    "object": {
      "id": "0x789",
      "name": "methane",
      "type": "chemical"
    },
    "section": "3.3. Methanol production",
    "pages": [5],
    "source_paper": "A. Priyadarsini et al. 2023",
    "confidence": 0.95
  }
]
```

---

## 2. Graph Traversal Endpoints

### Get Entity Connections

**GET** `/api/entities/{entity_name}/connections`

Get all relationships (incoming and/or outgoing) for a specific entity.

**Path Parameters:**

- `entity_name` (required): Name of the entity to explore

**Query Parameters:**

- `direction` (optional, default: "both"): Direction of relationships
  - Values: "incoming", "outgoing", "both"
- `max_relations` (optional, default: 50): Maximum relations per direction

**Example:**

```bash
curl "http://localhost:8001/api/entities/ATP/connections?direction=both"
```

**Response:**

```json
{
  "outgoing": [
    {
      "id": "0x456",
      "predicate": "powers",
      "object": {
        "name": "cellular processes",
        "type": "process"
      }
    }
  ],
  "incoming": [
    {
      "id": "0x789",
      "predicate": "produces",
      "subject": {
        "name": "mitochondria",
        "type": "organelle"
      }
    }
  ]
}
```

---

### Find Path Between Entities

**GET** `/api/entities/{entity_name}/path-to/{target_entity}`

Find connection paths between two entities in the graph.

**Path Parameters:**

- `entity_name` (required): Source entity
- `target_entity` (required): Target entity

**Query Parameters:**

- `max_depth` (optional, default: 3): Maximum path length

**Example:**

```bash
curl "http://localhost:8001/api/entities/methane/path-to/methanol?max_depth=2"
```

**Note:** This endpoint is a placeholder. Path-finding algorithm implementation is in progress.

---

## 3. Document & Provenance Endpoints

### List Papers

**GET** `/api/papers`

Get all papers loaded in the knowledge graph.

**Example:**

```bash
curl "http://localhost:8001/api/papers"
```

**Response:**

```json
[
  {
    "id": "0xabc",
    "title": "Methanol production from methanotrophs",
    "filename": "A. Priyadarsini et al. 2023.pdf",
    "processed_at": "2024-11-15T12:00:00Z",
    "total_entities": 450,
    "total_relations": 320,
    "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"]
  }
]
```

---

### Get Paper Entities

**GET** `/api/papers/{paper_id}/entities`

Get all entities extracted from a specific paper.

**Path Parameters:**

- `paper_id` (required): Paper identifier

**Query Parameters:**

- `section` (optional): Filter by document section
- `limit` (optional, default: 100): Maximum entities

**Example:**

```bash
curl "http://localhost:8001/api/papers/A.%20Priyadarsini%20et%20al.%202023/entities?section=Methods"
```

---

### Get Relation Provenance

**GET** `/api/relations/{relation_id}/provenance`

Get detailed provenance information for a specific relation, including which paper it came from, what section, page numbers, and bounding box coordinates.

**Path Parameters:**

- `relation_id` (required): Relation UID (e.g., "0x456")

**Example:**

```bash
curl "http://localhost:8001/api/relations/0x456/provenance"
```

**Response:**

```json
{
  "relation_id": "0x456",
  "section": "3.3. Methanol production",
  "pages": [5],
  "bbox_data": {
    "l": 72.5,
    "t": 200.3,
    "r": 300.8,
    "b": 215.6,
    "coord_origin": "BOTTOMLEFT"
  },
  "source_paper": "A. Priyadarsini et al. 2023",
  "extraction_method": "llm_extraction_v1"
}
```

---

### Get Relation Source Span

**GET** `/api/relations/{relation_id}/source-span`

Get the exact text span where a relation was extracted, including the sentence text and character positions of subject and object.

**Path Parameters:**

- `relation_id` (required): Relation UID

**Example:**

```bash
curl "http://localhost:8001/api/relations/0x456/source-span"
```

**Response:**

```json
{
  "relation_id": "0x456",
  "subject": "Methanotrophs",
  "predicate": "convert",
  "object": "methane to methanol",
  "source_span": {
    "span_type": "single_sentence",
    "text_evidence": "Methanotrophs convert methane to methanol using methane monooxygenase enzymes.",
    "confidence": 1.0,
    "location": {
      "chunk_id": 19,
      "sentence_range": [2, 2],
      "document_offsets": {
        "start": 11680,
        "end": 11706
      }
    },
    "subject_positions": [
      {
        "start": 0,
        "end": 13,
        "sentence_id": 2,
        "matched_text": "Methanotrophs"
      }
    ],
    "object_positions": [
      {
        "start": 22,
        "end": 41,
        "sentence_id": 2,
        "matched_text": "methane to methanol"
      }
    ]
  }
}
```

---

### Get Section Image with Highlighted Relation

**GET** `/api/relations/{relation_id}/section-image`

Generate a PDF page image with the relation's bounding box highlighted.

**Path Parameters:**

- `relation_id` (required): Relation UID

**Example:**

```bash
curl "http://localhost:8001/api/relations/0x456/section-image" --output relation.png
```

**Response:** PNG image with highlighted text region

---

## 4. Analytics Endpoints

### Get Graph Statistics

**GET** `/api/graph/stats`

Get comprehensive statistics about the knowledge graph.

**Example:**

```bash
curl "http://localhost:8001/api/graph/stats"
```

**Response:**

```json
{
  "total_nodes": 25858,
  "total_relations": 45632,
  "total_papers": 47,
  "unique_predicates": 324,
  "most_connected_entities": []
}
```

---

### Get Most Connected Entities

**GET** `/api/entities/most-connected`

Get entities with the highest number of relationships.

**Query Parameters:**

- `limit` (optional, default: 10): Number of top entities

**Example:**

```bash
curl "http://localhost:8001/api/entities/most-connected?limit=5"
```

**Response:**

```json
[
  {
    "entity": {
      "id": "0x123",
      "name": "methanol",
      "type": "chemical"
    },
    "total_connections": 156,
    "outgoing_count": 89,
    "incoming_count": 67
  }
]
```

---

### Get Predicate Frequency

**GET** `/api/predicates/frequency`

Get frequency distribution of all relationship types.

**Example:**

```bash
curl "http://localhost:8001/api/predicates/frequency"
```

**Response:**

```json
{
  "total_unique_predicates": 324,
  "predicate_frequencies": [
    {
      "predicate": "produces",
      "count": 1234
    },
    {
      "predicate": "converts",
      "count": 987
    }
  ]
}
```

---

## 5. Utility Endpoints

### Health Check

**GET** `/api/health`

Check API and database health status.

**Example:**

```bash
curl "http://localhost:8001/api/health"
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-11-17T15:30:00Z",
  "database": "dgraph",
  "api_version": "1.0.0"
}
```

---

### API Root

**GET** `/`

Get API information and endpoint overview.

**Example:**

```bash
curl "http://localhost:8001/"
```

**Response:**

```json
{
  "message": "Knowledge Graph API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "search": "/api/entities/search, /api/relations/search",
    "traversal": "/api/entities/{name}/connections",
    "provenance": "/api/papers, /api/relations/{id}/provenance",
    "analytics": "/api/graph/stats, /api/entities/most-connected"
  }
}
```

---

## Understanding the Data Model

### Entity (Node)

Represents a named entity extracted from scientific papers:

- `id`: Unique identifier (Dgraph UID like "0x123")
- `name`: Entity name (e.g., "ATP", "methanol")
- `type`: Entity type/category (e.g., "chemical", "organism", "process")
- `namespace`: Grouping/classification namespace
- `created_at`: When entity was first added to graph

**Note:** Entities are deduplicated - same name+type+namespace = same node. Entities themselves have NO provenance fields.

---

### Relation (Triple)

Represents a relationship between two entities:

- `id`: Unique identifier
- `predicate`: Relationship type (e.g., "converts", "produces")
- `subject`: Source entity (Node)
- `object`: Target entity (Node)
- **Provenance fields** (Relations track where they came from):
  - `source_paper`: Which paper this relation was extracted from
  - `section`: Document section (e.g., "Methods", "Results")
  - `pages`: Page numbers where relation appears
  - `bbox_data`: Bounding box coordinates on the PDF page
  - `source_span`: Detailed text span with character positions
  - `confidence`: Extraction confidence score

**Important:** Each relation is paper-specific. The same triple appearing in multiple papers creates separate relation instances, each with its own provenance.

---

### Provenance Architecture

**Nodes (Entities)** are shared across papers:

- "ATP" appears once in the graph, no matter how many papers mention it
- No `source_paper` field on nodes
- Only metadata: name, type, namespace, created_at

**Relations (Triples)** track provenance:

- Each relation knows exactly which paper, section, page, and text span it came from
- Same knowledge in different papers = different relation instances
- To find all papers mentioning "ATP": query all relations where ATP is subject or object

**Why this design?**

- The atomic unit of knowledge with provenance is the triple, not the entity
- This preserves exact source tracking while eliminating entity duplication
- Enables queries like "find all mentions of ATP across papers" by traversing relations

---

## Running the API

Start the API server:

```bash
cd knowledge_graph
python api.py
```

The API will automatically:

1. Check for available ports (8000, 8001, etc.)
2. Connect to Dgraph at `localhost:8080`
3. Start the FastAPI server
4. Display the URL for accessing the API

Access interactive documentation:

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

---

## Example Workflows

### 1. Find All Papers Mentioning an Entity

```bash
# Step 1: Search for the entity
curl "http://localhost:8001/api/entities/search?q=ATP&limit=1"
# Get entity name from response

# Step 2: Get all connections
curl "http://localhost:8001/api/entities/ATP/connections?max_relations=1000"
# Each relation has a source_paper field

# Step 3: Deduplicate source papers from all relations
```

---

### 2. Explore a Specific Relation's Context

```bash
# Step 1: Search for relations
curl "http://localhost:8001/api/relations/search?subject=methane&predicate=convert"
# Get relation ID from response

# Step 2: Get source span (exact sentence)
curl "http://localhost:8001/api/relations/0x456/source-span"
# See the exact text and character positions

# Step 3: Get PDF context (visual)
curl "http://localhost:8001/api/relations/0x456/section-image" --output context.png
# See the highlighted region in the PDF
```

---

### 3. Analyze Knowledge Graph Structure

```bash
# Get overall statistics
curl "http://localhost:8001/api/graph/stats"

# Find hub entities
curl "http://localhost:8001/api/entities/most-connected?limit=20"

# Analyze relationship types
curl "http://localhost:8001/api/predicates/frequency"
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- **200 OK**: Successful request
- **404 Not Found**: Entity/relation not found
- **422 Unprocessable Entity**: Invalid query parameters
- **500 Internal Server Error**: Database or server error

Error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```
