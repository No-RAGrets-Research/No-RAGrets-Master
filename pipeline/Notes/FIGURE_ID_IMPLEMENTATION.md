# Figure ID Implementation Summary

## What We Built

Added complete support for querying relations by figure/table ID with the query:
**"Give me all relations from Figure 3 in this paper"**

## Changes Made

### 1. Schema (`knowledge_graph/schema.graphql`)

OK Added `figure_id` field to Relation type:

```graphql
figure_id: String @search(by: [term])
```

### 2. API (`knowledge_graph/api.py`)

OK Added new endpoint `/api/relations/by-figure`
OK Updated `RelationResponse` model to include `figure_id`

### 3. Data Loader (`knowledge_graph/kg_data_loader.py`)

OK Modified `create_relation()` to accept `figure_id` parameter
OK Updated GraphQL mutation to include `figure_id` field
OK Extracts `figure_id` from source_span when `span_type == 'visual_figure'`
OK Passes `figure_id` to database during relation creation

### 4. Documentation (`knowledge_graph/API_ENDPOINTS.md`)

OK Added full documentation for `/api/relations/by-figure` endpoint

## Data Flow (Already Working!)

Your visual extraction pipeline already creates `figure_id`:

1. **Visual Extraction** (`visual_kg_formatter.py`)

   - Line 87: Creates source_span with `figure_id`
   - Line 150: Sets `figure_id` for each chunk

2. **Data Loading** (NOW UPDATED: `kg_data_loader.py`)

   - Detects `span_type == 'visual_figure'`
   - Extracts `figure_id` from source_span
   - Stores in Dgraph relation

3. **API Query** (`api.py`)
   - `/api/relations/by-figure?paper_id=X&figure_id=Figure%203`
   - Returns all relations from that figure

## Usage

### Query by Figure:

```bash
curl "http://localhost:8001/api/relations/by-figure?paper_id=MyPaper.pdf&figure_id=Figure%203"
```

### Example Response:

```json
[
  {
    "id": "0x789",
    "subject": { "name": "CO2", "type": "chemical" },
    "predicate": "converts_to",
    "object": { "name": "methanol", "type": "chemical" },
    "figure_id": "Figure 3",
    "section": "Visual Analysis: Figure 3",
    "pages": [7]
  }
]
```

## Next Steps

1. **Re-load Visual Data** (if you already have visual extractions):

   ```bash
   cd knowledge_graph
   python kg_data_loader.py ../output/visual_results/your_paper_visual.json
   ```

2. **Test the Endpoint**:

   ```bash
   python test_figure_query.py
   ```

3. **New Extractions**: Any new papers processed with visual extraction will automatically get `figure_id` populated!

## Benefits of Separate Text/Visual Folders

OK **Easy filtering**: Know which relations came from figures vs text
OK **Quality tracking**: Monitor visual extraction vs text extraction separately
OK **Selective re-processing**: Re-run just visual or just text extraction
OK **Clear provenance**: Users can see "this came from Figure 3"
OK **Better debugging**: Isolate issues in visual vs text pipeline

## File Structure

```
output/
îîÄîÄ text_kg_results/    OKÜê Text extraction (no figure_id)
îÇ  OKîîîÄîÄ paper_text.json
îîîÄîÄ visual_kg_results/  OKÜê Visual extraction (has figure_id)
   OKîîîÄîÄ paper_visual.json
```

Both load into the same graph, but visual relations have `figure_id` field populated!
