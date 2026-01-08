# Quick Reference: Table and Figure Lookup API

## Endpoints

### Get Relations from a Figure

```
GET /api/relations/by-figure?paper_id={paper}&figure_id={id}
```

**Example**:

```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=paper.pdf&figure_id=page6_fig1"
```

### Get Relations from a Table

```
GET /api/relations/by-table?paper_id={paper}&table_id={id}
```

**Example**:

```bash
curl "http://localhost:8001/api/relations/by-table?paper_id=paper.pdf&table_id=page5_table2"
```

## ID Format

| Type   | Format             | Example        |
| ------ | ------------------ | -------------- |
| Figure | `page{N}_fig{M}`   | `page6_fig1`   |
| Table  | `page{N}_table{M}` | `page5_table2` |

## Frontend Integration

### Converting Docling References

```javascript
// Docling figure reference
const figRef = {
  self_ref: "#/figures/1", // 1-indexed
  page: 5,
};
const figureId = `page${figRef.page}_fig${figRef.self_ref.split("/")[2]}`;
// Result: "page5_fig1"

// Docling table reference
const tableRef = {
  self_ref: "#/tables/2", // 1-indexed
  page: 5,
};
const tableId = `page${tableRef.page}_table${tableRef.self_ref.split("/")[2]}`;
// Result: "page5_table2"
```

### API Query Functions

```javascript
async function getFigureRelations(paperId, figureId) {
  const response = await fetch(
    `/api/relations/by-figure?paper_id=${paperId}&figure_id=${figureId}`
  );
  return response.json();
}

async function getTableRelations(paperId, tableId) {
  const response = await fetch(
    `/api/relations/by-table?paper_id=${paperId}&table_id=${tableId}`
  );
  return response.json();
}
```

### Response Format

Both endpoints return the same structure:

```json
[
  {
    "id": "0x123",
    "subject": {
      "id": "0x456",
      "name": "methane",
      "type": "chemical",
      "namespace": "compound"
    },
    "predicate": "converted_to",
    "object": {
      "id": "0x789",
      "name": "methanol",
      "type": "chemical",
      "namespace": "compound"
    },
    "section": "Visual Analysis: Figure page6_fig1",
    "pages": [6],
    "source_paper": "paper.pdf",
    "confidence": 0.95,
    "figure_id": "page6_fig1",
    "table_id": null
  }
]
```

## Implementation Status

OK **Ready to use** - Backend fully supports both figures and tables  
OK **Waiting for data** - Visual extraction pipeline needs to generate `visual_table` spans

### What Works Now

- Schema includes `table_id` field
- API endpoints are live
- Frontend can query by figure or table
- Data loader handles both span types

### What's Needed

The visual extraction pipeline must:

1. Detect table references
2. Set `span_type: "visual_table"`
3. Generate `table_id: "page{N}_table{M}"`
