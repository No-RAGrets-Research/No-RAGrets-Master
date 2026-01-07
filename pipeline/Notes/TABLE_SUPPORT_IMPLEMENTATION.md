# Table Support Implementation

**Date**: November 23, 2025  
**Status**: ✅ IMPLEMENTED

## Overview

Added table support to the knowledge graph system, following the same pattern as figures. Tables and figures now have separate ID fields and dedicated API endpoints for click-to-lookup functionality.

## Changes Made

### 1. Schema Updates (`schema.graphql`)

Added `table_id` field to Relation type:

```graphql
type Relation {
  # ... existing fields ...
  figure_id: String @search(by: [term]) # Figure ID (e.g., "page6_fig1")
  table_id: String @search(by: [term]) # Table ID (e.g., "page5_table2")
  # ... remaining fields ...
}
```

### 2. Data Loader Updates (`kg_data_loader.py`)

#### Updated `create_relation()` method signature (line 151):

```python
def create_relation(self, subject_id: str, predicate: str, object_id: str,
                   section: str, pages: list, source_paper: str,
                   bbox_data: str = None, source_span: str = None,
                   figure_id: str = None, table_id: str = None) -> bool:
```

#### Updated mutation query to include table_id (lines 197-233):

- Added `$tableId: String` parameter to mutation
- Added `table_id: $tableId` to input
- Added `'tableId': table_id` to variables

#### Updated chunk processing to extract table_id (lines 380-403):

```python
# Extract figure_id and table_id from source_span if available
figure_id = None
table_id = None
if source_span_data:
    if source_span_data.get('span_type') == 'visual_figure':
        figure_id = source_span_data.get('figure_id')
    elif source_span_data.get('span_type') == 'visual_table':
        table_id = source_span_data.get('table_id')

success = self.create_relation(
    subject_id, predicate, object_id,
    section, pages, filename,
    bbox_json, source_span_json, figure_id, table_id
)
```

#### Updated all_relations processing (lines 463-491):

```python
if source_span_data:
    # ... existing cross_chunk handling ...
    elif source_span_data.get('span_type') == 'visual_figure':
        figure_id = source_span_data.get('figure_id')
        section = f"Visual Analysis: Figure {figure_id or 'Unknown'}"
        if 'page_number' in source_span_data:
            pages = [source_span_data['page_number']]
    elif source_span_data.get('span_type') == 'visual_table':
        table_id = source_span_data.get('table_id')
        section = f"Visual Analysis: Table {table_id or 'Unknown'}"
        if 'page_number' in source_span_data:
            pages = [source_span_data['page_number']]

success = self.create_relation(
    subject_id, predicate, object_id,
    section, pages, filename,
    bbox_json, source_span_json, figure_id, table_id
)
```

### 3. API Updates (`api.py`)

#### Updated RelationResponse model (line 83):

```python
class RelationResponse(BaseModel):
    # ... existing fields ...
    figure_id: Optional[str] = None  # e.g., "page6_fig1"
    table_id: Optional[str] = None  # e.g., "page5_table2"
```

#### Updated by-figure endpoint to return table_id (line 377):

```python
@app.get("/api/relations/by-figure", response_model=List[RelationResponse])
async def search_relations_by_figure(
    paper_id: str = Query(..., description="Paper filename or ID"),
    figure_id: str = Query(..., description="Figure ID (e.g., 'page6_fig1')"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all relations extracted from a specific figure."""
    # ... query includes both figure_id and table_id fields ...
```

#### Added new by-table endpoint (line 428):

```python
@app.get("/api/relations/by-table", response_model=List[RelationResponse])
async def search_relations_by_table(
    paper_id: str = Query(..., description="Paper filename or ID"),
    table_id: str = Query(..., description="Table ID (e.g., 'page5_table2')"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all relations extracted from a specific table.

    Find relations that were extracted from a specific table
    by matching the table_id field.

    Examples:
    - table_id="page5_table2"
    - table_id="page7_table1"
    """
    try:
        query = f"""
        {{
            queryRelation(filter: {{
                source_paper: {{ eq: "{paper_id}" }},
                table_id: {{ anyofterms: "{table_id}" }}
            }}, first: {limit}) {{
                id
                subject {{ id name type namespace }}
                predicate
                object {{ id name type namespace }}
                source_paper
                section
                pages
                confidence
                figure_id
                table_id
                source_span
            }}
        }}
        """
        response = dgraph.query(query)
        # ... error handling and return ...
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## ID Format Convention

### Figures

- **Format**: `page{N}_fig{M}`
- **Examples**: `page6_fig1`, `page3_fig2`
- **Detection**: `span_type == 'visual_figure'`

### Tables

- **Format**: `page{N}_table{M}`
- **Examples**: `page5_table2`, `page7_table1`
- **Detection**: `span_type == 'visual_table'`

## Frontend Integration Guide

### For Figures

```javascript
// Docling gives you: self_ref: "#/figures/1", page: 5
const pageNumber = 5;
const figureIndex = 1; // from self_ref split
const figureId = `page${pageNumber}_fig${figureIndex}`;

// Query the API
const response = await fetch(
  `/api/relations/by-figure?paper_id=${paperId}&figure_id=${figureId}`
);
```

### For Tables

```javascript
// Docling gives you: self_ref: "#/tables/2", page: 5
const pageNumber = 5;
const tableIndex = 2; // from self_ref split
const tableId = `page${pageNumber}_table${tableIndex}`;

// Query the API
const response = await fetch(
  `/api/relations/by-table?paper_id=${paperId}&table_id=${tableId}`
);
```

## Testing Requirements

To test table support with actual data, you need:

1. **Visual extraction pipeline** must populate:

   - `span_type: "visual_table"` in source_span
   - `table_id: "page{N}_table{M}"` in source_span
   - `page_number: N` in source_span

2. **Sample test data** structure:

```json
{
  "chunks": [
    {
      "relations": [
        {
          "subject": "entity1",
          "predicate": "relation_type",
          "object": "entity2",
          "source_span": {
            "span_type": "visual_table",
            "table_id": "page5_table2",
            "page_number": 5
          }
        }
      ]
    }
  ]
}
```

3. **API Test**:

```bash
# After loading data with table relations
curl "http://localhost:8001/api/relations/by-table?paper_id=paper.pdf&table_id=page5_table2"
```

## Current Limitations

1. **No existing table data**: Current visual extraction pipeline only populates `visual_figure`, not `visual_table`
2. **Visual extraction needs update**: The visual KG extraction process needs to:
   - Detect table references in addition to figures
   - Set `span_type: "visual_table"` for table extractions
   - Generate table_id in the format `page{N}_table{M}`

## Next Steps (If Tables Are Needed)

If you want to start extracting relations from tables:

1. **Update visual extraction pipeline** to:

   - Parse table references from documents
   - Set span_type to "visual_table"
   - Generate table_id from table position

2. **Test with sample data**: Create a test JSON file with visual_table relations

3. **Reload affected papers**: Reprocess papers with table data

## Verification

- ✅ Schema updated with table_id field
- ✅ Data loader extracts table_id from visual_table spans
- ✅ API model includes table_id field
- ✅ New /api/relations/by-table endpoint added
- ✅ By-figure endpoint returns table_id field
- ✅ Schema loaded successfully to Dgraph
- ⏸️ **Waiting for visual extraction pipeline to generate table data**

## Summary

The backend now **fully supports tables** with the same functionality as figures:

- Separate `table_id` field in database
- Dedicated `/api/relations/by-table` endpoint
- ID format follows `page{N}_table{M}` convention
- Frontend can query by paper_id + table_id

**The implementation is complete and ready to use as soon as the visual extraction pipeline starts generating `visual_table` span types with `table_id` values.**
