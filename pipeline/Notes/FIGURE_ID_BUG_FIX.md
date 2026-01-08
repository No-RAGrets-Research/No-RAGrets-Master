# Figure ID Bug Fix - Summary

## Issue Discovered
When querying relations from the database, the `figure_id` field was always `null`, even though the data loader appeared to be processing visual triples correctly.

## Root Cause
In `knowledge_graph/kg_data_loader.py`, the variable `source_span_data` was not initialized before the `if/elif` block that processes relations. This caused a `NameError` when trying to extract `figure_id` from the source_span for relations in list format (as opposed to dict format).

### Problematic Code (Lines 341-358)
```python
for relation in chunk.get('relations', []):
    # Handle both old format (list) and new format (dict with source_span)
    if isinstance(relation, list) and len(relation) >= 3:
        subject, predicate, obj = relation[0], relation[1], relation[2]
        source_span_json = None
    elif isinstance(relation, dict):
        subject = relation.get('subject')
        predicate = relation.get('predicate') 
        obj = relation.get('object')
        
        # Extract source span data if available
        source_span_data = relation.get('source_span')  #OK† Only defined here!
        source_span_json = json.dumps(source_span_data) if source_span_data else None
```

Later, at line 367, the code tried to access `source_span_data`:
```python
# Extract figure_id from source_span if available
figure_id = None
if source_span_data and source_span_data.get('span_type') == 'visual_figure':  #OK† Error!
    figure_id = source_span_data.get('figure_id')
```

If the relation was in list format, `source_span_data` was never defined, causing the extraction logic to fail silently or raise an error.

## Solution
Initialize `source_span_data` and `source_span_json` to `None` at the beginning of each loop iteration, before the `if/elif` block:

```python
for relation in chunk.get('relations', []):
    # Initialize variables
    source_span_data = None
    source_span_json = None
    
    # Handle both old format (list) and new format (dict with source_span)
    if isinstance(relation, list) and len(relation) >= 3:
        subject, predicate, obj = relation[0], relation[1], relation[2]
    elif isinstance(relation, dict):
        subject = relation.get('subject')
        predicate = relation.get('predicate') 
        obj = relation.get('object')
        
        # Extract source span data if available
        source_span_data = relation.get('source_span')
        source_span_json = json.dumps(source_span_data) if source_span_data else None
```

The same fix was applied to the `all_relations` processing section (around line 413).

## Files Modified
- `knowledge_graph/kg_data_loader.py` - Added initialization of `source_span_data` and `source_span_json` variables

## Verification

### Before Fix
```bash
$ curl "http://localhost:8001/api/papers/A.%20Priyadarsini%20et%20al.%202023.pdf/relations?limit=100" | \
  jq '[.[] | select(.figure_id != null)] | length'
0  # No relations with figure_id
```

### After Fix
```bash
$ curl "http://localhost:8001/api/relations/by-figure?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page6_fig1" | \
  jq '{count: length, sample: .[0] | {subject: .subject.name, predicate, object: .object.name, figure_id}}'

{
  "count": 9,
  "sample": {
    "subject": "M. buryatense",
    "predicate": "produces methanol after",
    "object": "5 days of incubation",
    "figure_id": "page6_fig1"
  }
}
```

### Data Loader Output Now Shows Figure IDs
```bash
$ python kg_data_loader.py ../kg_gen_pipeline/output/raw_visual_triples/Copy\ of\ A.\ Priyadarsini\ et\ al.\ 2023_visual_triples_kg_format.json

Created relation: represents --[), (2,]--> , (with span) [from page5_fig1]
Created relation: represents --[), (1,]--> , (with span) [from page5_fig1]
Created relation: has --[), (3,]--> , (with span) [from page5_fig1]
Created relation: M. buryatense --[produces methanol after]--> 5 days of incubation (with span) [from page6_fig1]
Created relation: M. capsulatus --[produces methanol after]--> 5 days of incubation (with span) [from page6_fig1]
```

## API Endpoint Usage

The `/api/relations/by-figure` endpoint now works correctly:

```bash
# Get all relations from a specific figure
curl "http://localhost:8001/api/relations/by-figure?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page6_fig1"

# Count relations from a figure
curl "http://localhost:8001/api/relations/by-figure?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page6_fig1" | jq 'length'
```

## Impact
-OKOK Visual triples now correctly store `figure_id` in the database
-OKOK The `/api/relations/by-figure` endpoint can filter relations by figure/table
-OKOK Users can now query "which relations came from this specific figure?"
-OKOK Supports distinguishing between text-extracted and visually-extracted knowledge

## Status
**RESOLVED** - The data loader now correctly extracts and stores `figure_id` for all visual triple relations.
