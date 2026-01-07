# Figure ID Endpoint Verification Summary

## Date: November 21, 2025

## Verification Status: ✅ WORKING CORRECTLY

The `/api/relations/by-figure` endpoint has been tested and verified to be working correctly.

## Test Results

### Test 1: Query relations from Figure 5 (page5_fig1)
```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=Copy%20of%20A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page5_fig1"
```

**Result:** ✅ SUCCESS
- Returned 14 relations
- All relations correctly tagged with `figure_id: "page5_fig1"`
- Section correctly set to "Figure 5 Analysis"
- Page number correctly set to [5]

### Test 2: Query relations from Figure 6 (page6_fig1)
```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=Copy%20of%20A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page6_fig1"
```

**Result:** ✅ SUCCESS
- Returned 6 relations
- All relations correctly tagged with `figure_id: "page6_fig1"`
- Section correctly set to "Figure 6 Analysis"
- Page number correctly set to [6]

**Example relation from Figure 6:**
```json
{
  "subject": "M. buryatense",
  "predicate": "produces methanol after",
  "object": "5 days of incubation",
  "figure_id": "page6_fig1",
  "section": "Figure 6 Analysis",
  "pages": [6]
}
```

### Test 3: Query non-existent figure
```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=Copy%20of%20A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page99_fig1"
```

**Result:** ✅ SUCCESS
- Returned empty array `[]`
- Correctly handles missing figures without error

## Data Flow Verification

### 1. Visual Extraction Pipeline ✅
The visual extraction creates proper `figure_id` in source_span:
```json
"source_span": {
  "span_type": "visual_figure",
  "figure_id": "page5_fig1",
  "page_number": 5,
  "caption_evidence": "Fig. 1. (a) Genomic DNA extraction...",
  "bbox_coordinates": {...}
}
```

### 2. Data Loader ✅
The `kg_data_loader.py` correctly:
- Detects `span_type == 'visual_figure'`
- Extracts `figure_id` from `source_span`
- Passes `figure_id` to the GraphQL mutation
- Stores in database

**Evidence from loader output:**
```
Created relation: M. buryatense --[produces methanol after]--> 5 days of incubation (with span) [from page6_fig1]
```

### 3. API Endpoint ✅
The endpoint correctly:
- Queries by both `paper_id` and `figure_id`
- Returns all matching relations
- Includes full relation details with nested subject/object entities

## Usage Examples

### Basic Query
```bash
# Get all relations from a specific figure
curl "http://localhost:8001/api/relations/by-figure?paper_id=MyPaper.pdf&figure_id=Figure%203"
```

### With jq for pretty output
```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=MyPaper.pdf&figure_id=page5_fig1" | jq '.'
```

### Count relations from a figure
```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=MyPaper.pdf&figure_id=page6_fig1" | jq '. | length'
```

### Get specific fields
```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=MyPaper.pdf&figure_id=page5_fig1" | \
  jq '.[] | {subject: .subject.name, predicate, object: .object.name, figure_id}'
```

## How to Load Visual Data

To populate `figure_id` for existing visual extractions:

```bash
cd knowledge_graph

# Load a single visual extraction file
python kg_data_loader.py ../kg_gen_pipeline/output/raw_visual_triples/YOUR_PAPER_visual_triples_kg_format.json

# Load all visual extractions
for file in ../kg_gen_pipeline/output/raw_visual_triples/*.json; do
    python kg_data_loader.py "$file"
done
```

## API Documentation

The endpoint is documented in `knowledge_graph/API_ENDPOINTS.md`:

**Endpoint:** `GET /api/relations/by-figure`

**Parameters:**
- `paper_id` (required): Paper filename or ID
- `figure_id` (required): Figure ID (e.g., "Figure 3", "page5_fig1", "Table 2")
- `limit` (optional): Maximum number of results (default: 100)

**Returns:** Array of RelationResponse objects with `figure_id` populated

## Verified Components

✅ Schema (`schema.graphql`) - has `figure_id: String @search(by: [term])`
✅ API endpoint (`api.py`) - `/api/relations/by-figure` implemented
✅ Data loader (`kg_data_loader.py`) - extracts and stores `figure_id`
✅ Visual extraction pipeline - creates `figure_id` in source_span
✅ Database storage - `figure_id` persisted and queryable

## Next Steps

The endpoint is ready for production use. To use with your papers:

1. **For new papers:** Visual extractions will automatically include `figure_id`
2. **For existing papers:** Re-load visual extraction files using `kg_data_loader.py`
3. **Query by figure:** Use the `/api/relations/by-figure` endpoint

## Example Use Cases

1. **"Show me all relations from Figure 3"**
   - Query: `?paper_id=MyPaper.pdf&figure_id=Figure%203`

2. **"What data was extracted from this table?"**
   - Query: `?paper_id=MyPaper.pdf&figure_id=Table%202`

3. **"Compare text vs visual extractions"**
   - Text relations: don't have `figure_id`
   - Visual relations: have `figure_id` populated

## Conclusion

The figure ID endpoint is **fully functional** and ready to use. It correctly:
- Filters relations by figure/table
- Returns accurate provenance information
- Handles edge cases (missing figures, etc.)
- Integrates with the existing visual extraction pipeline
