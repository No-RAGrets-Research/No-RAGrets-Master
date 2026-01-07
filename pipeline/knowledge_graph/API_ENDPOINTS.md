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

### Search Relations by Text

**GET** `/api/relations/by-text`

Search for relations by their source text evidence. Find relations where the extracted sentence or paragraph contains specific text.

**Query Parameters:**

- `q` (required): Text to search for in relation source spans
- `limit` (optional, default: 50): Maximum results

**Example:**

```bash
curl "http://localhost:8001/api/relations/by-text?q=methanol+production&limit=5"
```

**Response:**

```json
[
  {
    "id": "0x456",
    "predicate": "produces",
    "subject": {
      "id": "0x123",
      "name": "Methanotrophs",
      "type": "organism"
    },
    "object": {
      "id": "0x789",
      "name": "methanol",
      "type": "chemical"
    },
    "section": "3.3. Results",
    "pages": [5],
    "source_paper": "A. Priyadarsini et al. 2023",
    "confidence": 0.95
  }
]
```

**Use Case:** Find all relations extracted from sentences containing specific keywords or phrases.

---

### Search Relations by Location

**GET** `/api/relations/by-location`

Get all relations from a specific location in a paper. Filter by paper, section, and/or page number.

**Query Parameters:**

- `paper_id` (required): Paper filename or ID
- `section` (optional): Document section name
- `page` (optional): Page number
- `limit` (optional, default: 100): Maximum results

**Examples:**

```bash
# Get relations from a specific section
curl "http://localhost:8001/api/relations/by-location?paper_id=Paper.pdf&section=Methods"

# Get relations from a specific page
curl "http://localhost:8001/api/relations/by-location?paper_id=Paper.pdf&page=5"

# Get relations from page 3 of the Methods section
curl "http://localhost:8001/api/relations/by-location?paper_id=Paper.pdf&section=Methods&page=3"
```

**Response:** Array of RelationResponse objects

**Use Case:** Find what knowledge was extracted from a specific part of a document.

---

### Search Relations by Chunk

**GET** `/api/relations/by-chunk`

Get all relations extracted from a specific text chunk ID from document processing.

**Query Parameters:**

- `paper_id` (required): Paper filename or ID
- `chunk_id` (required): Chunk ID from document processing
- `limit` (optional, default: 100): Maximum results

**Example:**

```bash
curl "http://localhost:8001/api/relations/by-chunk?paper_id=Paper.pdf&chunk_id=19"
```

**Response:** Array of RelationResponse objects

**Use Case:** Find all relations from a specific chunk of text in the document processing pipeline.

---

### Search Relations by Figure

**GET** `/api/relations/by-figure`

Get all relations extracted from a specific figure or chart in a paper. FULLY OPERATIONAL

**Query Parameters:**

- `paper_id` (required): Paper filename or ID (use cleaned filename without "Copy of" or timestamps)
- `figure_id` (required): Figure identifier (e.g., "page5_fig1", "page6_fig1")
- `limit` (optional, default: 100): Maximum results

**Examples:**

```bash
# Get all relations from page 6, figure 1
curl "http://localhost:8001/api/relations/by-figure?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page6_fig1"

# Get relations from page 5, figure 1
curl "http://localhost:8001/api/relations/by-figure?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page5_fig1"

# Count relations in a figure
curl "http://localhost:8001/api/relations/by-figure?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page6_fig1" | jq 'length'
```

**Response:** Array of RelationResponse objects with figure_id field populated

**Example Response:**

```json
[
  {
    "id": "0x789",
    "predicate": "produces methanol after",
    "subject": {
      "id": "0x456",
      "name": "M. buryatense",
      "type": "biochemical_entity"
    },
    "object": {
      "id": "0x123",
      "name": "5 days of incubation",
      "type": "biochemical_entity"
    },
    "section": "Results",
    "pages": [6],
    "source_paper": "A. Priyadarsini et al. 2023.pdf",
    "figure_id": "page6_fig1",
    "table_id": null,
    "confidence": 1.0
  }
]
```

**Use Case:** "Give me all relations from Figure 3 in this paper" - find knowledge extracted from specific figures.

**Implementation Status:** The visual extraction pipeline automatically populates `figure_id` during relation creation. Relations are tagged with their source figure during ingestion and can be queried using this endpoint.

---

### Search Relations by Table

**GET** `/api/relations/by-table`

Get all relations extracted from a specific table in a paper.

**Current Status**: FULLY OPERATIONAL. The database contains table relations extracted from 132 tables across 37 papers (2,479 total relations). All table relations are merged with existing text-based relations, sharing the same entity nodes across the knowledge graph.

**Query Parameters:**

- `paper_id` (required): Paper filename or ID (use cleaned filename without "Copy of" or timestamps)
- `table_id` (required): Table identifier in format `page{N}_table{M}` where M is 0-based index matching Docling's table array
- `limit` (optional, default: 100): Maximum results

**Table ID Format:**

- Uses 0-based indexing matching Docling's `self_ref` field
- Format: `page{pageNumber}_table{doclingIndex}`
- Example: Docling `#/tables/0` on page 3 becomes `page3_table0`
- Example: Docling `#/tables/2` on page 5 becomes `page5_table2`

**Examples:**

```bash
# Get all relations from first table on page 3 (Docling index 0)
curl "http://localhost:8001/api/relations/by-table?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&table_id=page3_table0"

# Get relations from third table on page 5 (Docling index 2)
curl "http://localhost:8001/api/relations/by-table?paper_id=paper.pdf&table_id=page5_table2"

# Count relations in a table
curl "http://localhost:8001/api/relations/by-table?paper_id=paper.pdf&table_id=page3_table0" | jq 'length'
```

**Response:** Array of RelationResponse objects with table_id field populated

**Example Response:**

```json
[
  {
    "id": "0xb727",
    "predicate": "is produced by",
    "subject": {
      "id": "0xa3b0",
      "name": "Methanol",
      "type": "biochemical_entity",
      "namespace": "extracted"
    },
    "object": {
      "id": "0xa3c1",
      "name": "Methylocella tundrae",
      "type": "biochemical_entity",
      "namespace": "extracted"
    },
    "section": "Visual Analysis: Table page3_table0",
    "pages": [3],
    "source_paper": "A. Priyadarsini et al. 2023.pdf",
    "figure_id": null,
    "table_id": "page3_table0",
    "confidence": null
  }
]
```

**Use Case:** "Give me all relations from Table 2 in this paper" - find knowledge extracted from specific tables.

**Implementation Details:**

- Backend API endpoint: Fully functional
- Database schema: Supports table_id field
- Data loader: Handles table relations with proper node merging
- Pipeline: Extracts relations from tables using Docling JSON structure
- Node reconciliation: Table entities merge with existing text-based entities (same "Methanol" node used across all sources)
- Table indexing: 0-based matching Docling's internal array indexing

**Frontend Integration:**

```javascript
// Extract table reference from Docling JSON
const tableRef = table.self_ref; // "#/tables/2"
const tableIndex = parseInt(tableRef.split("/").pop()); // 2
const pageNo = table.prov[0].page_no; // 5
const tableId = `page${pageNo}_table${tableIndex}`; // "page5_table2"

// Query API
fetch(`/api/relations/by-table?paper_id=${paperId}&table_id=${tableId}`);
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
      "subject": {
        "id": "0x123",
        "name": "ATP",
        "type": "chemical",
        "namespace": "extracted",
        "created_at": null
      },
      "object": {
        "id": "0x457",
        "name": "cellular processes",
        "type": "process",
        "namespace": "extracted",
        "created_at": null
      },
      "section": "Introduction",
      "pages": [2],
      "source_paper": "sample_paper.pdf",
      "confidence": 0.95,
      "figure_id": null,
      "table_id": null
    }
  ],
  "incoming": [
    {
      "id": "0x789",
      "predicate": "produces",
      "subject": {
        "id": "0x788",
        "name": "mitochondria",
        "type": "organelle",
        "namespace": "extracted",
        "created_at": null
      },
      "object": {
        "id": "0x123",
        "name": "ATP",
        "type": "chemical",
        "namespace": "extracted",
        "created_at": null
      },
      "section": "Results",
      "pages": [5],
      "source_paper": "sample_paper.pdf",
      "confidence": 0.98,
      "figure_id": null,
      "table_id": null
    }
  ]
}
```

**Note:** Both `outgoing` and `incoming` relations include complete `subject` and `object` information, allowing you to see the full triple structure regardless of direction.

**Data Quality:** This endpoint automatically filters out malformed relations (those missing required fields like `predicate`, `subject`, or `object`) that exist in the database. The response contains only valid, complete relations. See the Known Data Quality Issues section in the README for details.

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

### Search Papers

**GET** `/api/papers/search`

Search for papers by title or filename using fulltext search.

**Query Parameters:**

- `q` (required): Search term for paper titles or filenames
- `limit` (optional, default: 10): Maximum results to return

**Example:**

```bash
curl "http://localhost:8001/api/papers/search?q=priyadarsini&limit=5"
```

**Response:**

```json
[
  {
    "id": "0x2",
    "title": "A. Priyadarsini et al. 2023",
    "filename": "A. Priyadarsini et al. 2023.pdf",
    "processed_at": null,
    "total_entities": 656,
    "total_relations": 369,
    "sections": [
      "1. Introduction",
      "2. Methods",
      "3. Results",
      "4. Discussion",
      "5. Conclusions"
    ]
  }
]
```

**Use Case:** Find papers by author name, title keywords, or filename patterns. This searches the actual paper documents, not entity names that may reference papers.

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

### Delete Paper

**DELETE** `/api/papers/{paper_id}`

Delete a paper and all its associated relations from the knowledge graph.

**Path Parameters:**

- `paper_id` (required): Paper UID (e.g., "0xa82e")

**Example:**

```bash
curl -X DELETE "http://localhost:8001/api/papers/0xa82e"
```

**Response:**

```json
{
  "message": "Successfully deleted paper and 156 associated relations",
  "paper_id": "0xa82e",
  "filename": "extraction_summary.pdf",
  "relations_deleted": 156
}
```

**Warning:** This is a destructive operation that cannot be undone. Use with caution.

**Use Cases:**

- Remove papers that didn't process correctly
- Clean up test data
- Remove non-research documents (e.g., extraction summaries)
- Maintain data quality in the knowledge graph

---

### Get Paper Relations

**GET** `/api/papers/{paper_id}/relations`

Get all relations extracted from a specific paper with full details.

**Path Parameters:**

- `paper_id` (required): Paper identifier or title

**Query Parameters:**

- `section` (optional): Filter by document section
- `limit` (optional, default: 1000): Maximum relations to return

**Example:**

```bash
curl "http://localhost:8001/api/papers/A.%20Priyadarsini%20et%20al.%20202320251115/relations?limit=5"
```

**Response:**

```json
[
  {
    "id": "0x5",
    "predicate": "provides",
    "subject": {
      "id": "0x3",
      "name": "ScienceDirect",
      "type": "biochemical_entity",
      "namespace": "extracted"
    },
    "object": {
      "id": "0x4",
      "name": "Contents",
      "type": "biochemical_entity",
      "namespace": "extracted"
    },
    "section": "Front Matter",
    "pages": [1],
    "source_paper": "Copy of A. Priyadarsini et al. 202320251115.pdf",
    "confidence": null
  }
]
```

**Note:** Use URL encoding for paper IDs with spaces or special characters (e.g., `%20` for spaces).

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

### Get Batch Source Spans

**GET** `/api/relations/source-spans`

Get source spans for multiple relations in a single request. This is significantly faster than making individual requests for each relation.

**Query Parameters:**

- `ids` (required): Comma-separated list of relation UIDs (e.g., "0x5,0x7,0x13")
- Maximum 500 IDs per request

**Example:**

```bash
curl "http://localhost:8001/api/relations/source-spans?ids=0x5,0x7,0x13"
```

**Response:**

```json
{
  "results": [
    {
      "relation_id": "0x5",
      "subject": "ScienceDirect",
      "predicate": "provides",
      "object": "Contents",
      "source_span": {
        "span_type": "single_sentence",
        "text_evidence": "Contents lists available at ScienceDirect",
        "confidence": 1.0,
        "location": {
          "chunk_id": 0,
          "sentence_range": [0, 0],
          "document_offsets": {
            "start": 24,
            "end": 65
          }
        },
        "subject_positions": [
          {
            "start": 28,
            "end": 41,
            "sentence_id": 0,
            "matched_text": "ScienceDirect"
          }
        ],
        "object_positions": [
          {
            "start": 0,
            "end": 8,
            "sentence_id": 0,
            "matched_text": "Contents"
          }
        ]
      }
    }
  ],
  "metadata": {
    "requested": 3,
    "found": 3,
    "not_found": [],
    "processing_time_ms": 10.14
  }
}
```

**Performance:** ~125x faster than individual requests. Batch of 20 relations processes in ~8ms vs 1000ms for sequential calls.

**Notes:**

- Duplicate IDs are automatically removed
- Returns partial results if some IDs are not found (tracked in `metadata.not_found`)
- Maximum 500 IDs per request to prevent timeouts

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

## 6. Paper Review Endpoints

The Paper Review system provides AI-powered quality assessment of scientific papers using specialized evaluation rubrics. It supports both OpenAI and Ollama (local) LLM providers.

### Configuration

Configure the LLM provider using environment variables in `.env`:

```bash
# Use Ollama (free, local)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434

# Or use OpenAI (paid, cloud)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

The system uses six specialized rubrics to evaluate different aspects of papers:

1. **Methodology** - Research design, experimental approach, validation methods
2. **Reproducibility** - Code availability, data sharing, procedural details
3. **Rigor** - Statistical analysis, controls, bias mitigation
4. **Data** - Dataset quality, labeling, metrics, documentation
5. **Presentation** - Clarity, organization, figures, writing quality
6. **References** - Citation completeness, literature coverage, attribution

---

### Complete Paper Review

**POST** `/api/review`

Perform a complete 6-rubric evaluation of a paper plus meta-synthesis. This processes all rubrics sequentially and generates a consolidated review with improvement recommendations.

**Request Body:**

```json
{
  "text": "Paper content as markdown text...",
  "pdf_filename": "optional_paper.pdf"
}
```

**Note:** Provide either `text` (paper content directly) or `pdf_filename` (will be loaded from `papers/` directory and converted via Docling).

**Example with text:**

```bash
curl -X POST http://localhost:8002/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "text": "# Abstract\n\nThis paper studies methanol production..."
  }'
```

**Example with PDF:**

```bash
curl -X POST http://localhost:8002/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_filename": "A. Priyadarsini et al. 2023.pdf"
  }'
```

**Response:**

```json
{
  "rubric_responses": [
    {
      "rubric_name": "rubric1_methodology",
      "response": "Tier 2-3: Adequate methodology with some gaps...\n\nStrengths:\n- Clear experimental design\n- Appropriate controls\n\nWeaknesses:\n- Missing statistical power analysis\n- Limited validation details\n\nRecommendations:\n- Add quantitative validation metrics\n- Include power calculations"
    },
    {
      "rubric_name": "rubric2_reproducibility",
      "response": "Tier 2: Partially reproducible...\n..."
    }
  ],
  "merged_text": "Combined evaluation text from all 6 rubrics...",
  "final_summary": "META-SYNTHESIS:\n\nOverall Assessment: Tier 2-3\n\nKey Strengths:\n- Novel approach to methanol production\n- Clear experimental design\n\nCritical Gaps:\n- Missing code and data availability\n- Insufficient statistical details\n\nImprovement Checklist:\n[ ] Add GitHub repository with code\n[ ] Include statistical power analysis\n[ ] Provide supplementary data files\n...",
  "metadata": {
    "provider": "ollama",
    "model": "llama3.1:8b"
  }
}
```

**Performance:**

- Ollama (llama3.1:8b): ~3 minutes total (30-40 seconds per rubric)
- OpenAI (gpt-4o-mini): ~30-60 seconds total

**Use Cases:**

- Comprehensive paper quality assessment
- Pre-submission review and improvement
- Literature review quality filtering
- Research proposal evaluation

---

### Single Rubric Evaluation

**POST** `/api/review/rubric/{rubric_name}`

Evaluate a paper using a single rubric. This is much faster than the complete review and useful for iterative development or focused assessment.

**Path Parameters:**

- `rubric_name` (required): Rubric to apply. Accepted values:
  - `methodology` or `rubric1` - Research methodology evaluation
  - `reproducibility` or `rubric2` - Reproducibility assessment
  - `rigor` or `rubric3` - Scientific rigor analysis
  - `data` or `rubric4` - Data quality evaluation
  - `presentation` or `rubric5` - Presentation quality
  - `references` or `rubric6` - Reference completeness

**Request Body:**

```json
{
  "text": "Paper content as markdown text...",
  "pdf_filename": "optional_paper.pdf"
}
```

**Example - Methodology rubric:**

```bash
curl -X POST http://localhost:8002/api/review/rubric/methodology \
  -H "Content-Type: application/json" \
  -d '{
    "text": "# Methods\n\nWe cultured M. tundrae in 5L bioreactors..."
  }' | jq -r '.response'
```

**Example - Data quality rubric:**

```bash
curl -X POST http://localhost:8002/api/review/rubric/data \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_filename": "research_paper.pdf"
  }' | jq '.'
```

**Response:**

```json
{
  "rubric_name": "rubric4_data",
  "response": "Tier 2: Adequate data quality with some gaps...\n\nStrengths:\n- Clear dataset description\n- Appropriate sample size\n\nWeaknesses:\n- Missing data availability statement\n- No information about data labeling process\n- Insufficient statistical context\n\nRecommendations:\n- Add data repository link (e.g., Zenodo, Figshare)\n- Document labeling methodology\n- Include statistical distributions\n- Provide train/test split details",
  "metadata": {
    "provider": "ollama",
    "model": "llama3.1:8b"
  }
}
```

**Performance:**

- Ollama (llama3.1:8b): ~30 seconds per rubric
- OpenAI (gpt-4o-mini): ~5-10 seconds per rubric

**Output Options with jq:**

```bash
# View just the evaluation text
curl ... | jq -r '.response'

# View full JSON structure
curl ... | jq '.'

# View just the metadata
curl ... | jq '.metadata'

# Check which rubric was used
curl ... | jq -r '.rubric_name'
```

**Use Cases:**

- Fast iteration during rubric development
- Focused assessment of specific paper aspects
- Debugging evaluation logic
- Quick quality checks during paper writing

---

### Rubric Descriptions

Each rubric evaluates papers on a 3-tier scale:

**Tier 1 (Exemplary):** Best practices, comprehensive documentation, high reproducibility

**Tier 2 (Adequate):** Acceptable quality with some gaps, partial documentation

**Tier 3 (Needs Improvement):** Significant gaps, poor documentation, limited reproducibility

#### Rubric 1: Methodology

Evaluates research design, experimental approach, and validation methods. Checks for:

- Clear problem statement and hypotheses
- Appropriate experimental design
- Valid methodology for research questions
- Proper controls and baselines
- Statistical power and sample size justification

#### Rubric 2: Reproducibility

Assesses whether others could replicate the research. Checks for:

- Code availability and documentation
- Data availability and accessibility
- Detailed procedural descriptions
- Environment and dependency specifications
- Random seed documentation

#### Rubric 3: Rigor

Evaluates scientific rigor and robustness. Checks for:

- Statistical analysis appropriateness
- Multiple trials and replication
- Bias identification and mitigation
- Uncertainty quantification
- Limitations discussion

#### Rubric 4: Data

Assesses dataset quality and documentation. Checks for:

- Dataset size and representativeness
- Data labeling methodology
- Statistical distributions and characteristics
- Train/test/validation splits
- Data availability statements

#### Rubric 5: Presentation

Evaluates clarity and organization. Checks for:

- Logical structure and flow
- Clear figures and tables
- Appropriate technical writing
- Accessible language for target audience
- Proper formatting and style

#### Rubric 6: References

Assesses citation quality and completeness. Checks for:

- Comprehensive literature coverage
- Proper attribution of prior work
- Recent and relevant citations
- Balanced perspective on field
- Citation format consistency

---

### Development Workflow

**Fast iteration with single rubrics:**

```bash
# Test methodology rubric (30 seconds)
curl -X POST http://localhost:8002/api/review/rubric/methodology \
  -H "Content-Type: application/json" \
  -d @paper_excerpt.json | jq -r '.response'

# Test data rubric (30 seconds)
curl -X POST http://localhost:8002/api/review/rubric/data \
  -H "Content-Type: application/json" \
  -d @paper_excerpt.json | jq -r '.response'
```

**Complete evaluation when ready:**

```bash
# Full review (3 minutes)
curl -X POST http://localhost:8002/api/review \
  -H "Content-Type: application/json" \
  -d @full_paper.json > review_output.json

# View synthesis
jq -r '.final_summary' review_output.json

# View specific rubric
jq '.rubric_responses[] | select(.rubric_name == "rubric1_methodology") | .response' review_output.json
```

**Switch between providers:**

```bash
# Use Ollama for free local development
echo "LLM_PROVIDER=ollama" > .env

# Use OpenAI for production (faster, more consistent)
echo "LLM_PROVIDER=openai" > .env
echo "OPENAI_API_KEY=sk-..." >> .env

# Restart API server to apply changes
```

---

### 6.2 Figure Review Endpoints (Vision Models)

The Figure Review system uses vision-capable AI models (GPT-4o, LLaVA) to assess the quality of scientific figures including charts, graphs, diagrams, and images.

#### Vision Model Configuration

Add vision model settings to your `.env` file:

```bash
# Vision Model for Figure Analysis
VISION_PROVIDER=openai
VISION_MODEL=gpt-4o

# Or use local Ollama with vision models (free)
VISION_PROVIDER=ollama_vision
VISION_MODEL=llava
VISION_BASE_URL=http://localhost:11434/v1
```

**Cost Considerations:**

- GPT-4o: ~$0.03-0.10 per paper (depends on number of figures)
- LLaVA (Ollama): Free, but slower and requires local GPU
- Hybrid approach: Use Ollama for text reviews, GPT-4o for figures

#### Figure Quality Assessment Criteria

Vision models evaluate figures on a 3-tier scale:

**Tier 1 (Exemplary):**

- Professional publication-quality appearance
- All axes clearly labeled with units
- Complete and informative legends
- Appropriate chart types for data
- High resolution, accessible colors
- Readable text at all sizes

**Tier 2 (Adequate with Issues):**

- Generally clear with minor issues
- Most axes labeled, some missing units
- Legend present but could be better
- Acceptable but not optimal chart type
- Some readability or color issues

**Tier 3 (Needs Improvement):**

- Difficult to interpret
- Missing axis labels or units
- No legend or inadequate legend
- Inappropriate chart type
- Low resolution or poor contrast
- Unreadable text

---

### Review All Figures in Paper

**POST** `/api/review/figures`

Evaluate all figures in a scientific paper using vision models. Assesses visual clarity, labels, legends, chart types, resolution, and accessibility.

**Request Body:**

```json
{
  "pdf_filename": "A. Priyadarsini et al. 2023.pdf"
}
```

**Note:** `pdf_filename` is required (figures cannot be extracted from plain text).

**Example:**

```bash
curl -X POST http://localhost:8002/api/review/figures \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "A. Priyadarsini et al. 2023.pdf"}' \
  | jq '.'
```

**Response:**

```json
{
  "figure_count": 2,
  "figure_reviews": [
    {
      "figure_id": "page5_fig0",
      "page": 5,
      "caption": "Fig. 1. (a) Genomic DNA extraction from rice field soil samples...",
      "assessment": "Tier 2: Adequate figure quality with some issues...\n\nOverall Impression:\nThe figure presents a clear workflow diagram but has some readability issues...\n\nStrengths:\n- Clear logical flow from left to right\n- Good use of color to distinguish steps\n- Informative labels on each box\n\nIssues:\n- Text size is too small in some panels\n- No scale bar in microscopy images\n- Color contrast could be improved for colorblind accessibility\n\nRecommendations:\n- Increase font size to at least 8pt\n- Add scale bars to all microscopy images\n- Use colorblind-friendly palette (e.g., viridis)\n- Increase line weight for better visibility"
    },
    {
      "figure_id": "page6_fig0",
      "page": 6,
      "caption": "Fig. 2. Methanol production in M. buryatense, M. capsulatus...",
      "assessment": "Tier 2-3: Adequate data presentation with notable issues...\n\nOverall Impression:\nThe bar chart effectively shows comparative data but lacks important details...\n\nStrengths:\n- Clear bar chart format appropriate for comparison\n- Error bars present showing variability\n- Legend identifies different organisms\n\nIssues:\n- Y-axis missing units (mg/L? mM?)\n- No statistical significance indicators\n- Color scheme not ideal for print/colorblind readers\n- Caption could be more descriptive\n\nRecommendations:\n- Add units to Y-axis label\n- Include significance markers (*, **, ***)\n- Use patterns (stripes, dots) in addition to colors\n- Expand caption to explain experimental conditions"
    }
  ],
  "metadata": {
    "provider": "openai",
    "model": "gpt-4o"
  }
}
```

**Performance:**

- GPT-4o: ~10-20 seconds per figure
- LLaVA (Ollama): ~60-120 seconds per figure

**Use Cases:**

- Pre-submission figure quality check
- Reviewer feedback preparation
- Accessibility compliance verification
- Publication-ready figure validation

---

### Review Single Figure

**POST** `/api/review/figure/{figure_id}`

Evaluate a specific figure in a paper. Useful for iterative improvement of individual figures.

**Path Parameters:**

- `figure_id` (required): Figure identifier (e.g., "page5_fig0", "page6_fig0")

**Request Body:**

```json
{
  "pdf_filename": "A. Priyadarsini et al. 2023.pdf"
}
```

**Figure ID Format:**

- Format: `page{N}_fig{M}` where M is 0-based
- First figure on page 5: `page5_fig0`
- Second figure on page 5: `page5_fig1`
- First figure on page 6: `page6_fig0`

**Example:**

```bash
# Review just the first figure on page 5
curl -X POST http://localhost:8002/api/review/figure/page5_fig0 \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "A. Priyadarsini et al. 2023.pdf"}' \
  | jq -r '.assessment'
```

**Response:**

```json
{
  "figure_id": "page5_fig0",
  "page": 5,
  "caption": "Fig. 1. (a) Genomic DNA extraction from rice field soil samples...",
  "assessment": "Tier 2: Adequate figure quality with some issues...\n\n[Full assessment text]",
  "metadata": {
    "provider": "openai",
    "model": "gpt-4o"
  }
}
```

**Output with jq:**

```bash
# Just the assessment text
curl -X POST http://localhost:8002/api/review/figure/page5_fig0 \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "paper.pdf"}' \
  | jq -r '.assessment'

# Check figure ID and page
curl ... | jq '{figure_id, page, caption}'

# Get metadata
curl ... | jq '.metadata'
```

**Use Cases:**

- Iterative figure improvement workflow
- Quick quality check during paper writing
- Focused feedback on problematic figures
- Testing different figure versions

---

### Figure Review Workflow

**1. Initial Assessment (All Figures):**

```bash
# Get overview of all figures
curl -X POST http://localhost:8002/api/review/figures \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "my_paper.pdf"}' \
  > figure_review.json

# Check how many figures found
jq '.figure_count' figure_review.json

# List all figure IDs
jq -r '.figure_reviews[].figure_id' figure_review.json
```

**2. Focused Improvement (Single Figure):**

```bash
# Review specific figure after making changes
curl -X POST http://localhost:8002/api/review/figure/page5_fig0 \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "my_paper_v2.pdf"}' \
  | jq -r '.assessment'
```

**3. Compare Before/After:**

```bash
# Save assessments
curl -X POST http://localhost:8002/api/review/figure/page5_fig0 \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "paper_v1.pdf"}' \
  | jq -r '.assessment' > fig_v1.txt

curl -X POST http://localhost:8002/api/review/figure/page5_fig0 \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "paper_v2.pdf"}' \
  | jq -r '.assessment' > fig_v2.txt

# Compare
diff fig_v1.txt fig_v2.txt
```

---

### Integration with Text Review

Combine text and figure reviews for comprehensive paper assessment:

```bash
# Step 1: Text-only review (fast with Ollama)
curl -X POST http://localhost:8002/api/review \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "paper.pdf"}' \
  > text_review.json

# Step 2: Figure review (GPT-4o for quality)
curl -X POST http://localhost:8002/api/review/figures \
  -H "Content-Type: application/json" \
  -d '{"pdf_filename": "paper.pdf"}' \
  > figure_review.json

# Step 3: Combine insights
echo "TEXT REVIEW SUMMARY:"
jq -r '.final_summary' text_review.json

echo -e "\nFIGURE REVIEW SUMMARY:"
jq -r '.figure_reviews[] | "\n\(.figure_id) (Page \(.page)):\n\(.assessment)\n"' figure_review.json
```

**Hybrid Configuration Example:**

```bash
# .env for cost-effective review
LLM_PROVIDER=ollama          # Free for text
OLLAMA_MODEL=llama3.1:8b
VISION_PROVIDER=openai       # Paid for figures (better quality)
VISION_MODEL=gpt-4o
OPENAI_API_KEY=sk-...

# Cost: ~$0.00 for text + ~$0.05-0.15 for figures = ~$0.05-0.15 per paper
# Time: ~3 min for text + ~30 sec for figures = ~3.5 min total
```

---

### 6.3 Simplified Visual Review Endpoints (Frontend-Based)

These new endpoints accept data directly from the frontend, eliminating backend PDF processing complexity. The frontend extracts figures as base64 data URLs and tables as Docling JSON objects, then sends them for review.

**Key Benefits:**

- No backend PDF extraction needed
- Faster processing (no temp files)
- Cleaner separation of concerns
- Frontend already has all the data

#### Review Figure (Base64 Image)

**POST** `/api/review/figure`

Review a figure using base64-encoded image data from the frontend.

**Request Body:**

```json
{
  "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "rubric": "presentation"
}
```

**Parameters:**

- `image_data` (required): Base64-encoded image (with or without `data:image/png;base64,` prefix)
- `rubric` (required): Rubric name to apply
  - `methodology` - Research design and experimental approach
  - `reproducibility` - Replication and documentation
  - `rigor` - Statistical analysis and robustness
  - `data` - Data quality and documentation
  - `presentation` - Clarity, organization, visual quality (most common for figures)
  - `references` - Citation completeness

**Example:**

```bash
curl -X POST http://localhost:8001/api/review/figure \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...",
    "rubric": "presentation"
  }'
```

**Response:**

```json
{
  "review": "### RUBRIC 5 – Presentation & Documentation\n\nTier 2: Adequate with Issues\n\nStrengths:\n- Clear bar chart format\n- Color differentiation visible\n\nWeaknesses:\n- Missing axis labels\n- No legend present\n- Units not specified\n\nRecommendations:\n- Add X and Y axis labels with units\n- Include legend identifying each bar\n- Consider accessibility (colorblind-friendly palette)",
  "rubric": "rubric5_presentation",
  "metadata": {
    "provider": "qwen",
    "model": "qwen3-vl:4b"
  }
}
```

**Frontend Integration Example:**

```javascript
// Frontend already has image as data URL
const imageUrl = figureElement.imageUrl; // "data:image/png;base64,..."

// Send to API
const response = await fetch("/api/review/figure", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    image_data: imageUrl,
    rubric: "presentation",
  }),
});

const result = await response.json();
console.log(result.review); // Display review to user
```

**Performance:**

- Qwen (local): ~10-30 seconds per figure
- OpenAI GPT-4o: ~5-10 seconds per figure

---

#### Review Table (Docling JSON)

**POST** `/api/review/table`

Review a table using Docling table object from the frontend.

**Request Body:**

```json
{
  "table_data": {
    "caption": {
      "text": "Table 1. Methanol production results"
    },
    "text": "Organism | Methanol (mg/L) | Growth Rate\nM. tundrae | 125 | 0.45",
    "data": {
      "headers": ["Organism", "Methanol (mg/L)", "Growth Rate"],
      "rows": [
        ["M. tundrae", "125", "0.45"],
        ["M. capsulatus", "98", "0.38"]
      ]
    }
  },
  "rubric": "data"
}
```

**Parameters:**

- `table_data` (required): Docling table object with caption, text, data, and/or grid
- `rubric` (required): Rubric name to apply
  - `methodology` - Experimental design
  - `reproducibility` - Replication details
  - `rigor` - Statistical completeness
  - `data` - Data quality and documentation (most common for tables)
  - `presentation` - Clarity and formatting
  - `references` - Citation context

**Example:**

```bash
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

**Response:**

```json
{
  "review": "### RUBRIC 4 – Data Quality\n\nTier 2: Adequate with Gaps\n\nStrengths:\n- Clear tabular format\n- Numeric data present\n- Caption identifies content\n\nWeaknesses:\n- Missing units for measurements\n- No error bars or standard deviations\n- Sample size not specified\n- No statistical significance indicators\n\nRecommendations:\n- Add units to all numeric columns\n- Include error estimates (±SD or ±SEM)\n- Specify n for each measurement\n- Add significance markers if comparing groups",
  "rubric": "rubric4_data",
  "metadata": {
    "provider": "ollama",
    "model": "llama3.1:8b"
  }
}
```

**Frontend Integration Example:**

```javascript
// Frontend already has Docling table object
const doclingTable = {
  caption: table.caption,
  text: table.text,
  data: table.data,
  grid: table.grid,
};

// Send to API
const response = await fetch("/api/review/table", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    table_data: doclingTable,
    rubric: "data",
  }),
});

const result = await response.json();
console.log(result.review); // Display review to user
```

**Performance:**

- Ollama (text model): ~20-40 seconds per table
- OpenAI (text model): ~3-5 seconds per table

**Note:** Tables use text models (cheaper and faster than vision models) since Docling already provides structured text representation.

---

### Comparison: Old vs New Endpoints

**Old Figure Endpoint** (Backend PDF Extraction):

```bash
POST /api/review/figure/{figure_id}/rubric/{rubric_name}
{"pdf_filename": "paper.pdf"}
```

- Requires backend to extract figures from PDF
- Temp file management
- Complex file path resolution

**New Figure Endpoint** (Frontend Base64):

```bash
POST /api/review/figure
{"image_data": "data:image/png;base64,...", "rubric": "presentation"}
```

- Frontend sends image directly
- No temp files
- Simple and fast

**Advantage:** The new architecture leverages work the frontend already does (extracting figures from PDFs for display), eliminating redundant backend processing.

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
  - `figure_id`: Figure identifier (e.g., "page6_fig1") - identifies relations from figures (OPERATIONAL: data exists in database)
  - `table_id`: Table identifier (e.g., "page3_table0") - identifies relations from tables (OPERATIONAL: 2,479 relations from 132 tables across 37 papers)

**Visual Element Tracking**:

- Figure relations: Populated in database with format "page{N}\_fig{M}"
- Table relations: Populated in database with format "page{N}\_table{M}" where M is 0-based Docling index
- Table indexing matches Docling's self_ref format (e.g., "#/tables/0" becomes "page3_table0")

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

---

## Future Endpoints (Planned)

### Entity Normalization (sameAs)

- **GET** `/api/entities/{name}/canonical` - Get canonical form of entity
- **GET** `/api/entities/{name}/variants` - Get all variant names
- **POST** `/api/entities/normalize` - Batch normalize entity names

### Advanced Analytics

- **GET** `/api/graph/communities` - Detect entity communities/clusters
- **GET** `/api/entities/{name}/context` - Get entity context (co-occurring entities)
- **GET** `/api/papers/similarity` - Find similar papers by entity overlap

### Semantic Search

- **POST** `/api/search/semantic` - Vector similarity search for entities
- **POST** `/api/relations/search/semantic` - Semantic search for relations
