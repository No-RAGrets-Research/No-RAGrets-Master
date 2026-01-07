# Knowledge Graph Database

A Dgraph-based knowledge graph database that transforms PDF extraction results into a searchable graph database with GraphQL API. Successfully tested with 900+ entities and 350+ relationships from scientific literature.

## Overview

This system converts knowledge graph extraction results from the `kg_gen_pipeline` into a dynamic, searchable graph database using Dgraph v25.0.0. It provides full-text search, graph traversal queries, and provenance tracking for research knowledge discovery.

### Key Features

- **Graph Traversal**: Navigate relationships between entities
- **Semantic Search**: Full-text search across entity names and relationships
- **Provenance Tracking**: Maintain links back to source documents and sections
- **GraphQL API**: Standard query interface for web applications
- **Real-time Updates**: Add and modify knowledge graph data dynamically

## Quick Start

### 1. Start the Database

```bash
# Start Dgraph services
docker compose up -d

# Check services are running
docker ps
```

This starts three containers:

- `dgraph-zero`: Cluster coordinator (ports 5080, 6080)
- `dgraph-alpha`: Database server with GraphQL endpoint (ports 8080, 9080)
- `dgraph-ratel`: Web UI for database management

### 2. Load the Schema

```bash
# Load GraphQL schema
python dgraph_manager.py
```

### 3. Load Knowledge Graph Data

**Basic Loading (with deduplication):**

```bash
# Load single file (safe to repeat)
python kg_data_loader.py kg_gen_pipeline/output/text_triples/paper_results.json

# Batch load ALL extracted data (safe to repeat)
python scripts/batch_load.py --base-dir .

# Load only specific types
python scripts/batch_load.py --types text
python scripts/batch_load.py --types visual
```

**Advanced Loading Options:**

```bash
# See what's being skipped (verbose mode)
python kg_data_loader.py --verbose paper_results.json
python scripts/batch_load.py --verbose --base-dir .

# Force overwrite existing data
python kg_data_loader.py --force-update paper_results.json
python scripts/batch_load.py --force-update --base-dir .

# Dry run to preview
python scripts/batch_load.py --dry-run --base-dir .

# Check current database status
python scripts/check_database.py
```

### 4. Access the Database

- **GraphQL API**: http://localhost:8080/graphql
- **Admin API**: http://localhost:8080/admin
- **Web UI (Ratel)**: http://localhost:8080/ratel

## Database Schema

### Core Types

**Node** - Entities in the knowledge graph:

```graphql
type Node {
  id: ID!
  name: String! @search(by: [term, trigram, fulltext])
  type: String @search(by: [term])
  namespace: String @search(by: [term])
  created_at: String
  updated_at: String
  outgoing: [Relation] @hasInverse(field: subject)
  incoming: [Relation] @hasInverse(field: object)
}
```

**Relation** - Relationships between entities:

```graphql
type Relation {
  id: ID!
  subject: Node! @hasInverse(field: outgoing)
  predicate: String! @search(by: [term, fulltext])
  object: Node! @hasInverse(field: incoming)

  # Provenance tracking
  section: String @search(by: [term])
  pages: [Int]
  bbox_data: String
  confidence: Float
  source_paper: String @search(by: [term])

  created_at: String
  extraction_method: String
}
```

**Paper** - Document metadata:

```graphql
type Paper {
  id: ID!
  title: String! @search(by: [term, fulltext])
  filename: String! @search(by: [exact])
  processed_at: String
  total_entities: Int
  total_relations: Int
  sections: [String]
}
```

## Query Examples

### Entity Search

Search for entities containing specific terms:

```graphql
query {
  queryNode(filter: { name: { anyoftext: "methanol" } }, first: 5) {
    id
    name
    type
    namespace
  }
}
```

### Relationship Exploration

Find relationships and connected entities:

```graphql
query {
  queryNode(filter: { name: { anyoftext: "Methanotrophs" } }) {
    name
    outgoing(first: 3) {
      predicate
      object {
        name
      }
    }
  }
}
```

### Relationship Analysis

Search for specific types of relationships:

```graphql
query {
  queryRelation(filter: { predicate: { anyoftext: "convert" } }) {
    predicate
    subject {
      name
    }
    object {
      name
    }
    source_paper
  }
}
```

### Document Overview

Get statistics about loaded papers:

```graphql
query {
  queryPaper {
    title
    filename
    total_entities
    total_relations
    sections
  }
}
```

## Components

### Core Files

- **`schema.graphql`** - GraphQL schema defining Node, Relation, and Paper types
- **`dgraph_manager.py`** - Database connection and schema management utility
- **`kg_data_loader.py`** - Data loader that imports KG extraction results into Dgraph
- **`docker-compose.yaml`** - Docker Compose configuration for Dgraph deployment

### Database Management

**dgraph_manager.py** provides:

- Database connection management
- Schema loading and validation
- Health checks and status monitoring

**kg_data_loader.py** features:

- Smart deduplication prevents duplicate data
- Entity caching for efficient processing
- Provenance data preservation
- Verbose mode to see what's being skipped
- Force update mode to overwrite existing data
- Error handling and progress reporting

## Integration with Pipeline

The database integrates seamlessly with the extraction pipeline:

1. **Input**: JSON results from `kg_gen_pipeline/output/text_triples/`
2. **Processing**: Schema-aware loading with provenance tracking
3. **Output**: Searchable graph database with GraphQL API
4. **Access**: Ready for web interfaces, analytics, and knowledge discovery

### Data Flow

```
kg_gen_pipeline/output/text_triples/*.json
    ↓ kg_data_loader.py
Dgraph Database (Nodes + Relations + Papers)
    ↓ GraphQL API
Search Interface / Analytics / Applications
```

## Deduplication and Data Management

### Smart Deduplication

The loader automatically prevents duplicates:

- **Papers**: Checked by filename - existing papers are skipped
- **Nodes**: Checked by name/type/namespace - reuses existing entities
- **Relations**: Checked by subject/predicate/object/source - prevents duplicate relationships

### Visibility Options

```bash
# See what's being skipped
python kg_data_loader.py --verbose paper.json
python scripts/batch_load.py --verbose --base-dir .

# Check current database contents
python scripts/check_database.py
```

### Update Options

```bash
# Overwrite existing data with new versions
python kg_data_loader.py --force-update paper.json
python scripts/batch_load.py --force-update --base-dir .

# Safe default: preserve existing, add new
python kg_data_loader.py paper.json  # Default behavior
```

**Key Benefits:**

- Safe to run loading scripts multiple times
- No accidental data duplication
- Option to see what's being preserved vs added
- Choice to update existing data when needed

## Persistent Database Hosting

### Current Setup: Local Persistent Storage

Your current Docker Compose setup already provides persistence through Docker volumes. Data survives container restarts and prevents duplicates with proper deduplication.

**Current Benefits:**

- Data persists between container restarts
- No data loss when updating Dgraph versions
- Fast local access for development
- Automatic deduplication prevents duplicate loading

### Option 1: Enhanced Local Setup

**Backup and Restore Tools:**

```bash
# Create backup before major changes
python scripts/backup_restore.py backup --name "before_major_update"

# List all backups
python scripts/backup_restore.py list

# Restore from backup
python scripts/backup_restore.py restore backup_name
```

**One-Time Load Everything:**

```bash
# Load ALL your extracted data at once (with deduplication)
python scripts/batch_load.py --base-dir .

# This loads ~47 papers worth of text + visual triples
# Safe to run multiple times - no duplicates created
```

**Benefits:**

- Load all data once, never reload
- Backup/restore for safety
- Fast local queries
- No hosting costs
- Safe re-running with deduplication

### Option 2: Cloud Database Hosting

**A. Dgraph Cloud (Recommended for Production)**

1. **Sign up**: https://cloud.dgraph.io/
2. **Create cluster**: Free tier available
3. **Update connection**:
   ```python
   # In dgraph_manager.py, update endpoint
   DGRAPH_ENDPOINT = "https://your-cluster.grpc.cloud.dgraph.io:443"
   ```
4. **Load data**: Same scripts work with cloud endpoint

**Benefits:**

- Always available
- Automatic backups
- Scaling on demand
- Multi-user access

**B. Self-Hosted Cloud (AWS/GCP/Azure)**

Deploy using Docker on cloud VM:

```bash
# On cloud VM
git clone your-repo
cd knowledge_graph
docker compose up -d

# Configure firewall for ports 8080, 9080
# Use cloud VM's IP address for remote access
```

### Option 3: Production Docker Setup

Enhanced docker-compose with backups:

```yaml
# Add to your docker-compose.yaml
services:
  backup:
    image: dgraph/dgraph:latest
    volumes:
      - dgraph-data:/dgraph
      - ./backups:/backups
    command: |
      sh -c "
        while true; do
          sleep 86400  # Daily backups
          dgraph export -a alpha:8080 -f /backups/backup_$(date +%Y%m%d)
        done
      "
```

### Option 4: Hybrid Approach

**Development**: Local persistent Docker
**Production**: Cloud hosted with regular sync

```bash
# Export from local
python scripts/backup_restore.py backup --name "prod_sync"

# Import to cloud
python scripts/sync_to_cloud.py --backup prod_sync
```

### Recommended Approach for Your Use Case

**For Research & Development:**

1. Keep current local Docker setup (already persistent!)
2. Load all data once with batch loader
3. Set up regular backups
4. Develop queries and analysis locally

**When ready for production/sharing:** 5. Deploy to Dgraph Cloud for team access 6. Sync data from local to cloud

### Quick Setup Commands

```bash
# 1. Start database (if not running)
cd knowledge_graph
docker compose up -d

# 2. Load ALL your data (one-time, safe to repeat)
python scripts/batch_load.py --base-dir .
# This processes ~47 papers, ~2000+ entities, ~1500+ relations

# 3. Create backup
python scripts/backup_restore.py backup --name "full_dataset"

# 4. Query the data
# Visit http://localhost:8080/graphql
```

**Result**: Persistent database with all your research data, ready for queries with no duplicates!

## Troubleshooting

### Docker Issues

Check if containers are running:

```bash
docker ps

# Should show dgraph-zero, dgraph-alpha, and dgraph-ratel
```

Restart if needed:

```bash
docker compose down
docker compose up -d
```

View logs:

```bash
docker compose logs dgraph-alpha
docker compose logs dgraph-zero
```

### Database Connection Issues

Test database connectivity:

```bash
# Check if Dgraph is accessible
curl http://localhost:8080/health

# Should return {"version": "..."}
```

### Schema Loading Issues

If schema fails to load:

```bash
# Manual schema loading via curl
curl -X POST localhost:8080/admin/schema \
  -H "Content-Type: application/json" \
  -d @schema.graphql
```

### Data Loading Issues

Common issues and solutions:

**JSON Format Errors**: Ensure input files are valid JSON from the extraction pipeline
**Memory Issues**: Process large datasets in smaller batches
**Connection Timeouts**: Increase timeout values in `kg_data_loader.py`

## Performance Notes

### Tested Scale

Successfully tested with:

- **Papers**: 1-50+ documents
- **Entities**: 900+ nodes
- **Relations**: 350+ relationships
- **Search Performance**: Sub-second response times

### Optimization Tips

- Use specific search terms rather than broad queries
- Filter by entity type when possible
- Limit result sets with `first: N` parameter
- Use indexes effectively with search directives

## Advanced Usage

### Batch Processing

Load multiple papers:

```bash
# Load all text triples from pipeline output
for file in ../kg_gen_pipeline/output/text_triples/*_kg_results_*.json; do
    python kg_data_loader.py "$file"
done
```

### Custom Queries

Access the GraphQL interface at http://localhost:8080/graphql for interactive query building.

Use DQL (Dgraph Query Language) for advanced queries via Ratel UI at http://localhost:8080/ratel.

### API Integration

The GraphQL endpoint can be integrated with:

- Web applications for knowledge exploration
- Analytics dashboards for research insights
- Search interfaces for document discovery
- Data visualization tools

## Development

### Adding New Entity Types

1. Update `schema.graphql` with new type definitions
2. Reload schema with `python dgraph_manager.py`
3. Modify `kg_data_loader.py` if needed for new data formats

### Extending Relationships

1. Add new predicate types to the schema
2. Update extraction pipeline to generate new relationship types
3. Test with sample data before batch processing

This knowledge graph database provides a robust foundation for research knowledge discovery and analysis, ready for production use with comprehensive querying capabilities.
