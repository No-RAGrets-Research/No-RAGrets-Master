# Knowledge Graph System Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Database Layer](#database-layer)
4. [Data Model & Schema](#data-model--schema)
5. [Data Loading System](#data-loading-system)
6. [Pipeline Integration](#pipeline-integration)
7. [REST API](#rest-api)
8. [Query System](#query-system)
9. [LLM Review System](#llm-review-system)
10. [Deployment](#deployment)
11. [Usage Examples](#usage-examples)
12. [Configuration](#configuration)
13. [Troubleshooting](#troubleshooting)
14. [Related Documentation](#related-documentation)

---

## System Overview

The **Knowledge Graph System** is the backend infrastructure that stores, manages, and queries extracted scientific knowledge from PDF papers. It provides a high-performance graph database with a comprehensive REST API for knowledge retrieval and traversal.

### Purpose

- Store extracted entities, relations, and papers from the KG generation pipeline
- Accept triples from three extraction sources: text, visual (figures), and tables
- Provide efficient querying and traversal of the knowledge graph
- Enable deduplication of entities and relations across all sources
- Support comprehensive provenance tracking back to source documents (text sentences, figures, tables)
- Offer LLM-powered paper quality review
- Serve as the backend for frontend applications

### Key Features

- **Graph Database**: Dgraph with GraphQL and DQL query support
- **Case-Insensitive Deduplication**: Intelligent entity merging
- **Provenance Tracking**: Full source attribution (sections, pages, figures, tables)
- **REST API**: 20+ endpoints for search, traversal, and analytics
- **LLM Integration**: Multi-backend support (OpenAI, Ollama)
- **Batch Processing**: Scripts for loading large datasets
- **Docker Deployment**: Containerized for easy deployment

### Technology Stack

- **Database**: Dgraph v25.0.0+ (GraphQL + DQL)
- **API Framework**: FastAPI with CORS support
- **Language**: Python 3.8+
- **LLM**: OpenAI API or Ollama (local)
- **Container**: Docker Compose
- **Query Language**: GraphQL and DQL

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Apps                            │
│                    (Web UI, CLI tools, etc.)                    │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP/REST API
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Server                            │
│                         (api.py)                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Search     │  │  Traversal   │  │  Analytics   │         │
│  │  Endpoints   │  │  Endpoints   │  │  Endpoints   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Query      │  │   Dgraph     │  │  LLM Review  │         │
│  │   Builder    │  │   Manager    │  │   System     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────┬────────────────────────────────────────────────┘
                 │ GraphQL/DQL
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Dgraph Database                             │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              GraphQL Schema                           │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │      │
│  │  │   Node   │  │ Relation │  │  Paper   │          │      │
│  │  └──────────┘  └──────────┘  └──────────┘          │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Data Storage (Badger)                    │      │
│  └──────────────────────────────────────────────────────┘      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Data Loading Pipeline                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ KGDataLoader │  │ Batch Scripts│  │   Pipeline   │         │
│  │              │  │              │  │   Outputs    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **api.py** (2,212 lines)

The FastAPI application serving the REST API.

- **Port Management**: Auto-detects available ports (default: 8001)
- **CORS**: Enabled for web applications
- **Endpoints**: 20+ endpoints for search, traversal, analytics
- **Models**: Pydantic models for type-safe responses
- **Error Handling**: Comprehensive error responses with details

#### 2. **dgraph_manager.py** (102 lines)

Database connection and schema management.

- **Connection**: HTTP client for GraphQL/DQL endpoints
- **Schema Loading**: GraphQL mutation-based schema deployment
- **Health Checks**: Database availability monitoring
- **Query/Mutate**: Unified interface for database operations

#### 3. **kg_data_loader.py** (609 lines)

Data loading with intelligent deduplication.

- **Paper Creation**: Duplicate checking with force_update option
- **Node Creation**: Case-insensitive entity deduplication
- **Relation Creation**: Deduplication based on subject-predicate-object
- **Batch Loading**: Efficient bulk data insertion

#### 4. **query_builder.py** (246 lines)

Dynamic GraphQL query construction.

- **Entity Search**: Name, type, namespace filters
- **Relation Search**: Predicate, subject, object filters
- **Entity Connections**: Traversal with depth control
- **Pagination**: Configurable result limits

#### 5. **schema.graphql** (47 lines)

The database schema definition.

- **Node Type**: Entities with names, types, namespaces
- **Relation Type**: Subject-predicate-object triples with provenance
- **Paper Type**: Document metadata and content
- **Search Directives**: Full-text, term, exact, trigram search

#### 6. **llm_review/** (Directory)

LLM-powered paper quality assessment.

- **Multiple Rubrics**: Methodology, reproducibility, rigor, data quality, presentation, references
- **Synthesis**: Combined review from all rubrics
- **Multi-Backend**: OpenAI or Ollama support
- **Batch Processing**: Review multiple papers

---

## Database Layer

### Dgraph Overview

**Dgraph** is a distributed graph database that supports:

- **GraphQL**: Type-safe queries with schema validation
- **DQL** (Dgraph Query Language): Powerful graph queries with regex, filtering
- **Transactions**: ACID compliance for data integrity
- **Scalability**: Horizontal scaling with sharding
- **Real-time**: Sub-second query performance

### Why Dgraph?

1. **Native Graph Storage**: Optimized for connected data
2. **GraphQL First-Class**: No need for resolvers or custom backend
3. **Flexible Queries**: Both declarative (GraphQL) and imperative (DQL)
4. **Search Capabilities**: Full-text, trigram, exact, term search
5. **Performance**: Fast traversals even with millions of nodes

### Database Endpoints

```python
# GraphQL endpoint for queries and mutations
GRAPHQL_ENDPOINT = "http://localhost:8080/graphql"

# Admin endpoint for schema management
ADMIN_ENDPOINT = "http://localhost:8080/admin"

# Health check endpoint
HEALTH_ENDPOINT = "http://localhost:8080/health"
```

### Connection Management

```python
from dgraph_manager import DgraphManager

# Initialize connection
dgraph = DgraphManager(
    host="localhost",
    port=8080
)

# Check database health
is_healthy = dgraph.health_check()

# Load schema
dgraph.load_schema("schema.graphql")

# Execute query
result = dgraph.query(query_string, variables)

# Execute mutation
result = dgraph.mutate(mutation_string, variables)
```

---

## Data Model & Schema

### Complete GraphQL Schema

```graphql
type Node {
  id: ID!
  name: String! @search(by: [exact, term, trigram, fulltext])
  type: String @search(by: [exact, term])
  namespace: String @search(by: [exact])

  # Bidirectional relations
  outgoing: [Relation] @hasInverse(field: subject)
  incoming: [Relation] @hasInverse(field: object)
}

type Relation {
  id: ID!

  # Triple structure
  subject: Node! @hasInverse(field: outgoing)
  predicate: String! @search(by: [term, fulltext])
  object: Node! @hasInverse(field: incoming)

  # Provenance metadata
  source_paper: String @search(by: [exact])
  section: String @search(by: [term])
  pages: String
  bbox_data: String
  confidence: Float

  # Source attribution
  figure_id: String @search(by: [term])
  table_id: String @search(by: [term])
  source_span: String # JSON: {text_evidence, char_positions, sentences}
}

type Paper {
  id: ID!
  title: String! @search(by: [term, fulltext])
  filename: String! @search(by: [exact])
  stats: String
  sections: String
}
```

### Entity Types (Node.type)

The knowledge graph supports multiple entity types:

| Type          | Description          | Example                 |
| ------------- | -------------------- | ----------------------- |
| `ENTITY`      | Generic entities     | "Climate Change"        |
| `CHEMICAL`    | Chemical compounds   | "Methane", "CO2"        |
| `ORGANISM`    | Biological organisms | "Methanotrophs"         |
| `PROCESS`     | Processes/activities | "Oxidation", "Emission" |
| `LOCATION`    | Geographic locations | "Arctic", "Wetlands"    |
| `MEASUREMENT` | Numeric measurements | "100 ppm", "25°C"       |
| `METHOD`      | Techniques/methods   | "Gas Chromatography"    |

### Relation Types (Relation.predicate)

Common predicates in the graph:

| Predicate    | Description          | Example                            |
| ------------ | -------------------- | ---------------------------------- |
| `causes`     | Causal relationships | Methane → causes → Warming         |
| `contains`   | Compositional        | Atmosphere → contains → Methane    |
| `oxidizes`   | Chemical reactions   | Methanotrophs → oxidizes → Methane |
| `emits`      | Emission sources     | Wetlands → emits → Methane         |
| `located_in` | Geographic           | Methanotrophs → located_in → Soil  |
| `measures`   | Measurement methods  | GC → measures → Methane            |
| `affects`    | General influence    | Temperature → affects → Emission   |

### Provenance Fields

Every relation includes detailed provenance tracking its source:

**Text-Based Relations**:

- `source_span`: JSON with text evidence, character positions, sentences
- `section`: Document section (Introduction, Methods, Results, etc.)
- `pages`: Page numbers where relation appears
- `confidence`: Mapping quality score (0.0-1.0)
- `figure_id`: null
- `table_id`: null

**Visual-Based Relations**:

- `figure_id`: Figure identifier (e.g., "Figure_3")
- `bbox_data`: Bounding box coordinates in PDF
- `pages`: Page number of figure
- `section`: Section containing the figure
- `confidence`: VLM extraction confidence
- `source_span`: null
- `table_id`: null

**Table-Based Relations**:

- `table_id`: Table identifier (e.g., "Table_2")
- `source_span`: JSON with table text evidence and positions
- `section`: Section containing the table
- `pages`: Page number of table
- `confidence`: Extraction quality score
- `figure_id`: null

**Example (Text-Based)**:

```json
{
  "source_paper": "Smith_2023_Methane.pdf",
  "section": "Results",
  "pages": "5-6",
  "confidence": 0.85,
  "figure_id": "Figure_3",
  "table_id": null,
  "source_span": "{
    \"text_evidence\": \"Methanotrophs oxidize methane in wetland soils, reducing atmospheric emissions.\",
    \"char_positions\": {\"start\": 2450, \"end\": 2534},
    \"sentences\": [\"Methanotrophs oxidize methane in wetland soils, reducing atmospheric emissions.\"]
  }",
  "bbox_data": "{\"x0\": 72, \"y0\": 450, \"x1\": 540, \"y1\": 470}"
}
```

---

## Data Loading System

### KGDataLoader Class

The `kg_data_loader.py` module provides intelligent data loading with deduplication.

#### Initialization

```python
from kg_data_loader import KGDataLoader

loader = KGDataLoader(
    dgraph_url="http://localhost:8080",
    default_namespace="climate_science"
)
```

#### Loading Papers

```python
# Create a new paper
paper_id = loader.create_paper(
    filename="Smith_2023_Methane.pdf",
    title="Methane Cycling in Wetlands",
    stats='{"pages": 12, "figures": 8, "tables": 3}',
    sections='["Abstract", "Introduction", "Methods", "Results", "Discussion"]',
    force_update=False  # Skip if already exists
)

print(f"Created paper with ID: {paper_id}")
```

#### Loading Nodes (Entities)

```python
# Create a node with case-insensitive deduplication
node_id = loader.create_node(
    name="Methane",  # Will match "methane", "METHANE", etc.
    node_type="CHEMICAL",
    namespace="climate_science"
)

# Creates new node only if no case-insensitive match exists
# Returns existing node UID if found
```

##### Case-Insensitive Matching Logic

The loader uses **DQL with regular expressions** for case-insensitive matching:

```python
def _escape_regex(text: str) -> str:
    """Escape special regex characters for safe DQL regexp matching."""
    special_chars = r'\.[]{}()*+?^$|'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# DQL query with case-insensitive regex
dql_query = f"""{{
  nodes(func: has(Node.name)) @filter(
    regexp(Node.name, /^{self._escape_regex(name)}$/i) AND
    eq(Node.type, "{node_type}") AND
    eq(Node.namespace, "{namespace}")
  ) {{ uid Node.name }}
}}"""
```

**Key Features**:

- `/^..$/i` flag for case-insensitive matching
- Regex escaping for special characters
- Exact match boundaries (^ and $)
- Type and namespace filtering

#### Loading Relations

```python
# Create a relation with automatic deduplication
relation_id = loader.create_relation(
    subject_name="Methanotrophs",
    subject_type="ORGANISM",
    predicate="oxidizes",
    object_name="Methane",
    object_type="CHEMICAL",
    namespace="climate_science",

    # Provenance
    source_paper="Smith_2023_Methane.pdf",
    section="Results",
    pages="5-6",
    confidence=0.85,
    source_span='{"text_evidence": "...", "char_positions": {...}}',
    figure_id="Figure_3"
)
```

##### Relation Deduplication

Relations are deduplicated based on:

1. **Subject UID** (resolved from subject_name)
2. **Predicate** (exact string match)
3. **Object UID** (resolved from object_name)

If a relation with the same subject-predicate-object already exists, the existing UID is returned.

### Batch Loading Scripts

#### load_all_papers.sh

Load all papers from the pipeline outputs:

```bash
cd knowledge_graph
./load_all_papers.sh
```

This script:

1. Finds all `*_full_output.json` files
2. Loads each paper with `kg_data_loader.py`
3. Skips already-loaded papers (unless `--force`)
4. Reports success/failure for each paper

#### batch_load_table_triples.py

Load table-extracted triples in batches:

```bash
python batch_load_table_triples.py \
    --input_dir ../output_kg_tables \
    --batch_size 100 \
    --namespace climate_science
```

Features:

- Batch processing for performance
- Progress tracking with tqdm
- Error handling per batch
- Resumable (skips completed batches)

#### reset_database.py

**WARNING - DANGER**: Completely wipes the database:

```bash
python reset_database.py --confirm
```

Use with caution! This deletes:

- All nodes
- All relations
- All papers
- Cannot be undone

---

## Pipeline Integration

The Knowledge Graph System is designed to consume outputs from the KG Generation Pipeline, which extracts knowledge from three distinct sources: text, visual elements (figures), and tables. This section explains how each extraction type integrates with the knowledge graph.

### Overview: Three Extraction Sources

The pipeline produces three types of triples, each with unique characteristics:

```
PDF Document
    ↓
KG Generation Pipeline
    ├─ Text Extraction → Text Triples
    ├─ Visual Extraction → Visual Triples
    └─ Table Extraction → Table Triples
    ↓
Knowledge Graph System
    └─ Unified Storage with Source Attribution
```

### Text-Based Extraction

**Source**: Document body text (Introduction, Methods, Results, Discussion, etc.)

**Process**:

1. Text chunked into sections and paragraphs (using spaCy for sentence segmentation)
2. LLM (Mistral 7B) extracts entities and relations from text chunks
3. Relations mapped back to specific sentences using character offsets
4. Output: Text triples with sentence-level provenance

**Provenance Fields**:

```json
{
  "subject": "Methanotrophs",
  "predicate": "oxidize",
  "object": "Methane",
  "source_paper": "Smith_2023.pdf",
  "section": "Results",
  "pages": "5-6",
  "confidence": 0.92,
  "source_span": {
    "text_evidence": "Methanotrophs oxidize methane in wetland soils...",
    "char_positions": { "start": 2450, "end": 2534 },
    "sentences": ["Methanotrophs oxidize methane in wetland soils..."]
  },
  "figure_id": null,
  "table_id": null
}
```

**Characteristics**:

- **Volume**: Highest volume of triples (hundreds to thousands per paper)
- **Coverage**: Captures narrative relationships, context, interpretations
- **Confidence**: High when both entities in same sentence (0.9-1.0)
- **Use Cases**: Understanding research context, finding causal relationships, literature connections

### Visual-Based Extraction

**Source**: Figures, charts, diagrams, flowcharts in documents

**Process**:

1. Docling detects figures during PDF parsing
2. Figure images extracted from PDF using PyMuPDF
3. Vision-language model (Qwen3-VL) analyzes figure content
4. VLM extracts entities and relationships from visual elements
5. Output: Visual triples with figure-specific provenance

**Provenance Fields**:

```json
{
  "subject": "Temperature",
  "predicate": "correlates_with",
  "object": "CH4 flux",
  "source_paper": "Smith_2023.pdf",
  "section": "Results",
  "pages": "8",
  "confidence": 0.88,
  "figure_id": "Figure_3",
  "table_id": null,
  "bbox_data": "{\"x0\": 72, \"y0\": 300, \"x1\": 540, \"y1\": 600}",
  "source_span": null
}
```

**Characteristics**:

- **Volume**: Lower volume (typically 5-20 relations per figure)
- **Coverage**: Captures visual patterns, trends, comparisons, spatial relationships
- **Confidence**: Depends on figure complexity and clarity
- **Use Cases**: Understanding data trends, visual comparisons, experimental results
- **Unique Information**: Often contains quantitative relationships not explicitly stated in text

### Table-Based Extraction

**Source**: Tables with structured data (measurements, comparisons, results)

**Process**:

1. Docling detects and extracts table structure during PDF parsing
2. Table content linearized into readable text
3. Table text chunked and segmented (using spaCy, same as text extraction)
4. LLM extracts relations from table content
5. Output: Table triples with table-specific provenance

**Provenance Fields**:

```json
{
  "subject": "Site A",
  "predicate": "has_CH4_flux",
  "object": "120 mg m-2 d-1",
  "source_paper": "Smith_2023.pdf",
  "section": "Results",
  "pages": "7",
  "confidence": 0.95,
  "table_id": "Table_2",
  "figure_id": null,
  "source_span": {
    "text_evidence": "Site A showed CH4 flux of 120 mg m-2 d-1",
    "char_positions": { "start": 45, "end": 87 },
    "sentences": ["Site A showed CH4 flux of 120 mg m-2 d-1"]
  }
}
```

**Characteristics**:

- **Volume**: Medium volume (10-100 relations per table)
- **Coverage**: Captures structured data, measurements, comparisons, experimental conditions
- **Confidence**: Very high (0.9-1.0) due to structured format
- **Use Cases**: Extracting measurements, comparing experimental results, finding numerical data
- **Unique Information**: Dense, structured information often not repeated in text

### Loading Strategy

**Sequential Loading**:

The knowledge graph loads data from all three sources independently:

```bash
# 1. Load text triples (primary extraction)
python kg_data_loader.py paper_text_kg.json

# 2. Load visual triples (supplemental)
python kg_data_loader.py paper_visual_kg.json

# 3. Load table triples (supplemental)
python kg_data_loader.py paper_table_kg.json
```

**Automatic Deduplication**:

The loader prevents duplicate relations across sources:

1. **Entity Deduplication**: Case-insensitive matching ensures "Methane" from text = "methane" from table
2. **Relation Deduplication**: Subject-predicate-object matching prevents duplicate triples
3. **Provenance Preservation**: If same relation found in multiple sources, first occurrence retained

**Example Deduplication**:

If both text and table extract "Wetlands → emits → Methane":

- First occurrence stored with full provenance
- Second occurrence skipped (existing relation UID returned)
- Result: Single relation in graph, avoiding redundancy

### Source Attribution

The schema tracks which source each relation came from:

```python
# Query relations by source type
def get_relations_by_source(source_type):
    if source_type == "text":
        # Relations with source_span but no figure_id or table_id
        return relations.filter(source_span != null, figure_id == null, table_id == null)
    elif source_type == "visual":
        # Relations with figure_id
        return relations.filter(figure_id != null)
    elif source_type == "table":
        # Relations with table_id
        return relations.filter(table_id != null)
```

### Complementary Information

The three extraction types provide complementary views of the same research:

**Example: Methane Research Paper**

**Text Extraction**:

- "Methanotrophs oxidize methane in wetland soils" (narrative)
- "Temperature affects methane emission rates" (causal relationship)

**Visual Extraction** (Figure 3 - scatter plot):

- "Temperature correlates_with CH4 flux" (visual trend)
- "R² = 0.87" (quantitative correlation)

**Table Extraction** (Table 2 - site measurements):

- "Site A has_CH4_flux 120 mg m-2 d-1" (precise measurement)
- "Site B has_CH4_flux 45 mg m-2 d-1" (comparative data)

Together, these create a rich, multi-faceted knowledge graph that captures:

- **Narrative** (text)
- **Trends** (visuals)
- **Data** (tables)

### Integration Benefits

**Comprehensive Coverage**: No information source overlooked

**Source Verification**: Cross-reference claims across text, figures, and tables

**Structured Data Access**: Query specific measurement values from tables

**Visual Context**: Understand trends and patterns from figures

**Unified Querying**: Single API to search across all extraction types

**Provenance Tracking**: Know exactly where each relation came from (text sentence, figure ID, or table ID)

### Query Examples by Source

**Find text-based relations**:

```graphql
{
  queryRelation(
    filter: {
      source_span: { regexp: "/.*/" }
      AND: [{ figure_id: { eq: null } }, { table_id: { eq: null } }]
    }
  ) {
    subject {
      name
    }
    predicate
    object {
      name
    }
    section
  }
}
```

**Find visual relations**:

```graphql
{
  queryRelation(filter: { figure_id: { regexp: "/Figure_.*/" } }) {
    subject {
      name
    }
    predicate
    object {
      name
    }
    figure_id
    pages
  }
}
```

**Find table relations**:

```graphql
{
  queryRelation(filter: { table_id: { regexp: "/Table_.*/" } }) {
    subject {
      name
    }
    predicate
    object {
      name
    }
    table_id
    section
  }
}
```

### Performance Characteristics

**Text Triples**:

- Load time: 5-15 seconds per paper
- Typical volume: 100-500 relations
- Deduplication: ~10-15% duplicates across papers

**Visual Triples**:

- Load time: 2-5 seconds per paper
- Typical volume: 10-50 relations (2-5 figures × 5-10 relations each)
- Deduplication: ~5% duplicates

**Table Triples**:

- Load time: 3-10 seconds per paper
- Typical volume: 20-100 relations (2-5 tables × 10-20 relations each)
- Deduplication: ~20% duplicates (tables often repeat text information)

---

## REST API

The FastAPI server (`api.py`) provides 20+ endpoints for querying the knowledge graph.

### Starting the API

```bash
cd knowledge_graph
python api.py
```

**Auto Port Detection**: If port 8001 is busy, the API automatically finds the next available port (8002, 8003, etc.).

### API Categories

1. **Search & Discovery**: Find entities, relations, papers
2. **Graph Traversal**: Navigate entity connections
3. **Provenance**: Track extraction sources
4. **Analytics**: Graph statistics and patterns
5. **Paper Management**: Load, search, query papers
6. **LLM Review**: Quality assessment of papers

### Quick Reference

| Endpoint                           | Method | Purpose                                |
| ---------------------------------- | ------ | -------------------------------------- |
| `/api/entities/search`             | GET    | Search entities by name                |
| `/api/relations/search`            | GET    | Search relations by predicate/entities |
| `/api/entities/{name}/connections` | GET    | Get entity's connections               |
| `/api/papers/search`               | GET    | Search papers by title/filename        |
| `/api/graph/stats`                 | GET    | Graph statistics                       |
| `/api/review/paper`                | POST   | Review paper quality with LLM          |

For complete API documentation, see: **[API_ENDPOINTS.md](knowledge_graph/API_ENDPOINTS.md)**

### Example: Search Entities

```bash
curl "http://localhost:8001/api/entities/search?q=methane&type=CHEMICAL&limit=10"
```

Response:

```json
[
  {
    "id": "0x1234",
    "name": "Methane",
    "type": "CHEMICAL",
    "namespace": "climate_science"
  }
]
```

### Example: Get Entity Connections

```bash
curl "http://localhost:8001/api/entities/Methane/connections?limit=50"
```

Response:

```json
{
  "entity": {
    "id": "0x1234",
    "name": "Methane",
    "type": "CHEMICAL",
    "namespace": "climate_science"
  },
  "outgoing": [
    {
      "id": "0x5678",
      "subject": { "id": "0x1234", "name": "Methane" },
      "predicate": "causes",
      "object": { "id": "0x9012", "name": "Global Warming" },
      "source_paper": "Smith_2023.pdf",
      "section": "Introduction",
      "confidence": 0.92
    }
  ],
  "incoming": [
    {
      "id": "0x3456",
      "subject": { "id": "0x7890", "name": "Wetlands" },
      "predicate": "emits",
      "object": { "id": "0x1234", "name": "Methane" },
      "source_paper": "Jones_2022.pdf",
      "section": "Results"
    }
  ],
  "stats": {
    "total_outgoing": 87,
    "total_incoming": 8,
    "total_connections": 95
  }
}
```

### Malformed Relation Filtering

**Data Quality Note**: The API automatically filters out malformed relations (missing required fields) to prevent 500 errors. This means:

- Relations with `null` predicates are skipped
- Relations with missing subject/object are skipped
- Connection counts may be lower than raw database counts

---

## Query System

### GraphQLQueryBuilder

The `query_builder.py` module constructs dynamic GraphQL queries based on filters.

#### Entity Search

```python
from query_builder import GraphQLQueryBuilder

builder = GraphQLQueryBuilder()

# Build entity search query
query = builder.build_entity_search(
    search_term="methane",
    type_filter="CHEMICAL",
    namespace="climate_science",
    limit=10
)

print(query)
```

Generated query:

```graphql
query SearchEntities(
  $searchTerm: String!
  $typeFilter: String
  $namespace: String
) {
  queryNode(
    filter: {
      name: { allofterms: $searchTerm }
      AND: [{ type: { eq: $typeFilter } }, { namespace: { eq: $namespace } }]
    }
    first: 10
  ) {
    id
    name
    type
    namespace
  }
}
```

#### Relation Search

```python
# Build relation search query
query = builder.build_relation_search(
    predicate="oxidizes",
    subject_name="Methanotrophs",
    object_name="Methane",
    section="Results",
    limit=20
)
```

#### Entity Connections

```python
# Build entity traversal query
query = builder.build_entity_connections(
    entity_name="Methane",
    max_depth=2,
    limit=50
)
```

### Direct DQL Queries

For advanced queries, use DQL directly:

```python
from dgraph_manager import DgraphManager

dgraph = DgraphManager()

# Case-insensitive search with regex
dql_query = """{
  results(func: has(Node.name)) @filter(
    regexp(Node.name, /methane/i)
  ) {
    uid
    Node.name
    Node.type
    outgoing: Node.outgoing {
      uid
      Relation.predicate
      Relation.object {
        uid
        Node.name
      }
    }
  }
}"""

result = dgraph.query(dql_query)
```

---

## LLM Review System

The `llm_review/` directory provides automated paper quality assessment using LLMs.

### Architecture

```
llm_review/
├── main.py               # Orchestration script
├── prompts/
│   ├── rubric1_methodology.txt
│   ├── rubric2_reproducibility.txt
│   ├── rubric3_rigor.txt
│   ├── rubric4_data.txt
│   ├── rubric5_presentation.txt
│   ├── rubric6_references.txt
│   └── synthesizer.txt
└── utils/
    ├── llm_runner.py      # LLM client (OpenAI/Ollama)
    ├── text_loader.py     # PDF text extraction
    ├── result_merger.py   # Combine rubric outputs
    └── vision_runner.py   # Image analysis
```

### Review Workflow

1. **Load Paper**: Extract text from PDF using Docling
2. **Apply Rubrics**: Run 6 specialized quality rubrics
3. **Merge Results**: Combine rubric outputs
4. **Synthesize**: Generate final evidence-based summary

### LLM Backend Support

#### OpenAI

```bash
# .env configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

#### Ollama (Local)

```bash
# .env configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b
```

### Running Reviews

#### Command Line

```bash
cd knowledge_graph/llm_review

# Place PDFs in papers/ directory
cp ../../papers/*.pdf papers/

# Run review
python main.py
```

#### Via API

```bash
curl -X POST "http://localhost:8001/api/review/paper" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_filename": "Smith_2023_Methane.pdf"
  }'
```

### Review Rubrics

1. **Methodology**: Research design, methods appropriateness
2. **Reproducibility**: Detail level, code/data availability
3. **Rigor**: Statistical analysis, controls, validation
4. **Data Quality**: Sample sizes, measurement accuracy
5. **Presentation**: Clarity, figures, tables, writing
6. **References**: Citation quality, literature coverage

### Output Structure

```
outputs/
└── Smith_2023_Methane/
    ├── rubric1_methodology_output.md
    ├── rubric2_reproducibility_output.md
    ├── rubric3_rigor_output.md
    ├── rubric4_data_output.md
    ├── rubric5_presentation_output.md
    ├── rubric6_references_output.md
    ├── merged_results.md
    └── final_summary.md
```

---

## Deployment

### Docker Compose Setup

The knowledge graph runs in Docker containers for easy deployment.

#### docker-compose.yaml

```yaml
version: "3.9"

services:
  zero:
    image: dgraph/dgraph:v25.0.0
    container_name: dgraph_zero
    volumes:
      - dgraph_zero_data:/dgraph
    ports:
      - "5080:5080"
      - "6080:6080"
    restart: on-failure
    command: dgraph zero --my=zero:5080

  alpha:
    image: dgraph/dgraph:v25.0.0
    container_name: dgraph_alpha
    volumes:
      - dgraph_alpha_data:/dgraph
    ports:
      - "8080:8080"
      - "9080:9080"
    restart: on-failure
    command: dgraph alpha --my=alpha:7080 --zero=zero:5080 --security whitelist=0.0.0.0/0
    depends_on:
      - zero

  ratel:
    image: dgraph/ratel:latest
    container_name: dgraph_ratel
    ports:
      - "8000:8000"
    restart: on-failure

volumes:
  dgraph_zero_data:
  dgraph_alpha_data:
```

#### Starting the Database

```bash
cd knowledge_graph
docker-compose up -d
```

#### Stopping the Database

```bash
docker-compose down
```

#### Viewing Logs

```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f alpha
```

### Port Mapping

| Service      | Internal Port | External Port | Purpose              |
| ------------ | ------------- | ------------- | -------------------- |
| Dgraph Zero  | 5080          | 5080          | Cluster coordination |
| Dgraph Alpha | 8080          | 8080          | GraphQL/DQL queries  |
| Dgraph Ratel | 8000          | 8000          | Web UI (optional)    |
| FastAPI      | 8001          | 8001          | REST API             |

### Health Checks

```bash
# Check Dgraph health
curl http://localhost:8080/health

# Check API health
curl http://localhost:8001/health
```

### Data Persistence

Data is stored in Docker volumes:

- `dgraph_zero_data`: Zero node data (cluster state)
- `dgraph_alpha_data`: Alpha node data (graph data)

To backup:

```bash
docker run --rm -v dgraph_alpha_data:/source -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/dgraph_backup_$(date +%Y%m%d).tar.gz -C /source .
```

---

## Usage Examples

### Complete Workflow: Load and Query

#### 1. Start Services

```bash
# Start database
cd knowledge_graph
docker-compose up -d

# Wait for database to be ready
sleep 5

# Start API
python api.py
```

#### 2. Load Schema

```bash
python -c "
from dgraph_manager import DgraphManager
dgraph = DgraphManager()
dgraph.load_schema('schema.graphql')
print('Schema loaded successfully')
"
```

#### 3. Load Data

```bash
# Load a single paper
python -c "
from kg_data_loader import KGDataLoader
loader = KGDataLoader()

# Create paper
paper_id = loader.create_paper(
    filename='Smith_2023.pdf',
    title='Methane Cycling in Wetlands'
)

# Create entities
methane_id = loader.create_node('Methane', 'CHEMICAL', 'climate_science')
wetlands_id = loader.create_node('Wetlands', 'LOCATION', 'climate_science')

# Create relation
rel_id = loader.create_relation(
    subject_name='Wetlands',
    subject_type='LOCATION',
    predicate='emits',
    object_name='Methane',
    object_type='CHEMICAL',
    namespace='climate_science',
    source_paper='Smith_2023.pdf',
    section='Results',
    confidence=0.92
)

print(f'Loaded paper {paper_id}, relation {rel_id}')
"
```

#### 4. Query via API

```bash
# Search for entities
curl "http://localhost:8001/api/entities/search?q=methane"

# Get connections
curl "http://localhost:8001/api/entities/Methane/connections"

# Search relations
curl "http://localhost:8001/api/relations/search?predicate=emits"

# Get graph stats
curl "http://localhost:8001/api/graph/stats"
```

### Batch Loading from Pipeline

```bash
# Load all pipeline outputs
cd knowledge_graph
./load_all_papers.sh

# Check loading progress
tail -f load_all_papers.log
```

### Export Data

```python
from dgraph_manager import DgraphManager
import json

dgraph = DgraphManager()

# Export all relations
query = """
{
  queryRelation {
    id
    subject { name type }
    predicate
    object { name type }
    source_paper
    confidence
  }
}
"""

result = dgraph.query(query)
relations = result['data']['queryRelation']

# Save to file
with open('exported_relations.json', 'w') as f:
    json.dump(relations, f, indent=2)

print(f"Exported {len(relations)} relations")
```

---

## Configuration

### Environment Variables

Create a `.env` file in `knowledge_graph/`:

```bash
# Database Configuration
DGRAPH_HOST=localhost
DGRAPH_PORT=8080

# API Configuration
API_PORT=8001
API_HOST=0.0.0.0
CORS_ORIGINS=["http://localhost:3000"]

# LLM Configuration
LLM_PROVIDER=openai  # or "ollama"
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.1:8b

# Data Loading
DEFAULT_NAMESPACE=climate_science
BATCH_SIZE=100
```

### Loading from Environment

```python
import os
from dotenv import load_dotenv

load_dotenv()

dgraph_host = os.getenv("DGRAPH_HOST", "localhost")
dgraph_port = int(os.getenv("DGRAPH_PORT", "8080"))
api_port = int(os.getenv("API_PORT", "8001"))
```

### Schema Customization

Modify `schema.graphql` to add custom types or fields:

```graphql
# Add a custom field to Node
type Node {
  id: ID!
  name: String! @search(by: [exact, term, trigram, fulltext])
  type: String @search(by: [exact, term])
  namespace: String @search(by: [exact])

  # Custom fields
  description: String @search(by: [fulltext])
  aliases: [String] @search(by: [term])

  outgoing: [Relation] @hasInverse(field: subject)
  incoming: [Relation] @hasInverse(field: object)
}
```

After modifying schema:

```bash
python -c "
from dgraph_manager import DgraphManager
dgraph = DgraphManager()
dgraph.load_schema('schema.graphql')
"
```

---

## Troubleshooting

### Database Issues

#### Problem: Cannot connect to Dgraph

**Symptoms**:

```
ConnectionError: Could not connect to http://localhost:8080
```

**Solutions**:

1. Check if containers are running:
   ```bash
   docker ps
   ```
2. Restart containers:
   ```bash
   docker-compose restart
   ```
3. Check logs:
   ```bash
   docker-compose logs alpha
   ```

#### Problem: Schema loading fails

**Symptoms**:

```
Error: Schema mutation failed
```

**Solutions**:

1. Verify Dgraph version (must be v25.0.0+):
   ```bash
   docker exec dgraph_alpha dgraph version
   ```
2. Check schema syntax:
   ```bash
   # Validate GraphQL schema
   npm install -g graphql-schema-linter
   graphql-schema-linter schema.graphql
   ```

### Data Loading Issues

#### Problem: Case-insensitive deduplication not working

**Symptoms**: Multiple nodes with same name but different cases (e.g., "Methane", "methane")

**Solutions**:

1. Check DQL regex escaping:
   ```python
   from kg_data_loader import KGDataLoader
   loader = KGDataLoader()
   escaped = loader._escape_regex("CO2")
   print(escaped)  # Should be: CO2
   ```
2. Test DQL query directly:
   ```bash
   curl -X POST http://localhost:8080/query -d '{
     nodes(func: has(Node.name)) @filter(regexp(Node.name, /^methane$/i)) {
       uid Node.name
     }
   }'
   ```

#### Problem: Duplicate relations

**Symptoms**: Same relation appears multiple times

**Solutions**:

1. Check relation deduplication logic in `kg_data_loader.py`
2. Verify subject/object UIDs are resolved correctly
3. Run deduplication script:
   ```bash
   python scripts/deduplicate_relations.py
   ```

### API Issues

#### Problem: 500 errors for entity connections

**Symptoms**:

```json
{ "detail": "Internal Server Error" }
```

**Solutions**:

1. Check for malformed relations in database
2. Verify API filtering is enabled:
   ```python
   # In api.py, check for this code:
   valid_outgoing = [
       rel for rel in outgoing
       if rel is not None and rel.get("predicate") and rel.get("subject") and rel.get("object")
   ]
   ```
3. Check API logs:
   ```bash
   # Restart API with verbose logging
   python api.py --log-level DEBUG
   ```

#### Problem: Port already in use

**Symptoms**:

```
OSError: [Errno 48] Address already in use
```

**Solutions**:

1. API auto-detects available ports, but if still failing:

   ```bash
   # Find process using port 8001
   lsof -i :8001

   # Kill process
   kill -9 <PID>
   ```

2. Use custom port:
   ```bash
   API_PORT=8002 python api.py
   ```

### Performance Issues

#### Problem: Slow queries

**Symptoms**: API responses take >5 seconds

**Solutions**:

1. Add indexes to frequently queried fields in schema:
   ```graphql
   type Node {
     name: String! @search(by: [exact, term, hash]) # Add hash for exact lookups
   }
   ```
2. Limit result sizes:
   ```bash
   curl "http://localhost:8001/api/entities/search?q=methane&limit=10"
   ```
3. Use pagination for large result sets
4. Check Dgraph logs for slow queries:
   ```bash
   docker-compose logs alpha | grep "slow query"
   ```

#### Problem: High memory usage

**Symptoms**: Docker containers using >4GB RAM

**Solutions**:

1. Limit Dgraph memory in `docker-compose.yaml`:
   ```yaml
   alpha:
     image: dgraph/dgraph:v25.0.0
     deploy:
       resources:
         limits:
           memory: 2G
   ```
2. Run garbage collection:
   ```bash
   docker exec dgraph_alpha dgraph admin --alpha=localhost:9080 --gql_run_backup
   ```

### Data Quality Issues

#### Problem: Missing provenance

**Symptoms**: Relations have null source_paper or section

**Solutions**:

1. Check pipeline extraction logs
2. Verify source data includes provenance:
   ```bash
   jq '.relations[] | select(.source_paper == null)' output.json
   ```
3. Re-run pipeline with provenance tracking enabled

#### Problem: Broken references

**Symptoms**: Relations pointing to non-existent nodes

**Solutions**:

1. Run integrity check:
   ```bash
   python scripts/check_graph_integrity.py
   ```
2. Fix broken relations:
   ```bash
   python scripts/fix_broken_relations.py
   ```

---

## Related Documentation

- **[KG_GENERATION_PIPELINE.md](KG_GENERATION_PIPELINE.md)**: Complete pipeline documentation (extraction, processing)
- **[API_ENDPOINTS.md](knowledge_graph/API_ENDPOINTS.md)**: Comprehensive API reference
- **[README.md](README.md)**: Project overview and quick start
- **[DEDUPLICATION.md](knowledge_graph/DEDUPLICATION.md)**: Case-insensitive deduplication details

### External Resources

- **Dgraph Documentation**: https://dgraph.io/docs/
- **GraphQL Spec**: https://spec.graphql.org/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **DQL Reference**: https://dgraph.io/docs/query-language/

---

## Summary

The **Knowledge Graph System** is a production-ready backend for storing and querying extracted scientific knowledge. Key takeaways:

**Graph Database**: Dgraph with GraphQL + DQL for flexible querying  
**Intelligent Deduplication**: Case-insensitive entity matching with DQL regex  
**Rich Provenance**: Full source attribution for every relation  
**REST API**: 20+ endpoints for search, traversal, analytics  
**LLM Integration**: Multi-backend paper quality review  
**Docker Deployment**: Containerized for easy deployment  
**Batch Processing**: Scripts for loading large datasets  
**Data Quality**: API-level filtering of malformed data

For questions or issues, see the [Troubleshooting](#troubleshooting) section or file a GitHub issue.
