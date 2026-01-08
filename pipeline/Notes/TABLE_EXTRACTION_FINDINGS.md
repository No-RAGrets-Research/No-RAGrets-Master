# Table Extraction Investigation Findings

## Summary

The table support infrastructure is **100% complete and ready**, but **no table data exists** because the extraction pipeline doesn't convert table elements into text chunks.

---

## What We Found

###OKOK Tables Exist in Docling JSON

- **88 tables found** across 47 papers
- Each table has:
  - `self_ref`: `"#/tables/0"`, `"#/tables/1"`, etc.
  - `page_no`: Page number
  - `bbox`: Bounding box coordinates
  - `text`: Table content (sometimes null)

**Example from A. Priyadarsini et al. 2023:**

```json
{
  "self_ref": "#/tables/0",
  "prov": {
    "page_no": 3,
    "bbox": {
      "l": 36.63742446899414,
      "t": 732.8916511535645,
      "r": 558.4600219726562,
      "b": 68.733642578125,
      "coord_origin": "BOTTOMLEFT"
    }
  }
}
```

###OKOK Tables NOT in Text Chunks

**Problem:** Text chunks (`.texts_chunks.jsonl` files) only reference text elements, not tables.

All chunks have provenance like:

```json
"provenance": [
  {
    "docling_ref": "#/texts/1",   //OKÜê References text, not tables
    "label": "text",
    "pages": [...]
  }
]
```

**Never:**

```json
"provenance": [
  {
    "docling_ref": "#/tables/0",  //OKÜê This doesn't exist in chunks
    "label": "table",
    "pages": [...]
  }
]
```

### Result: Zero Table Relations

- Text triples contain **13,857 relations** total
- **0 relations from tables** (all are from regular text)
- Backend API returns empty arrays for all `/api/relations/by-table` queries

---

## Why This Matters

The backend is ready to handle table relations:

1.OKOK **Schema**: `table_id` field exists in Dgraph
2.OKOK **API**: `/api/relations/by-table` endpoint works
3.OKOK **Data Loader**: Checks for `docling_ref: "#/tables/X"` and extracts `table_id`
4.OKOK **Documentation**: Complete with examples

**Missing piece:** The chunking step that converts Docling JSONOKÜí text chunks **skips tables entirely**.

---

## The Fix Required

### Where to Fix

The extraction pipeline step that reads Docling JSON and creates text chunks needs to:

1. **Iterate through tables** (not just texts)
2. **Extract table content** as text
3. **Create chunks with table provenance**:

   ```json
   {
     "chunk": "[Table page3_table1]\n<table content as text>",
     "provenance": [{
       "docling_ref": "#/tables/0",
       "label": "table",
       "pages": [{
         "page_no": 3,
         "bbox": {...}
       }]
     }],
     "section": "Results"
   }
   ```

4. **Pass through relation extraction** (LLM extracts triples from table text)

5. **Data loader automatically tags** relations with `table_id` when it sees `docling_ref: "#/tables/X"`

### Estimated Impact

Based on script analysis:

- **88 tables** across 47 papers
- Could generate **hundreds of additional relations**
- Example: Paper with 8 tables likely has significant tabular data (measurements, comparisons, etc.)

---

## Alternative Approaches

### Option 1: Fix Pipeline & Re-extract (Proper Solution)

**Pros:**

- Clean, sustainable
- Captures all table content
- Future papers automatically include tables

**Cons:**

- Requires re-running extraction for all 47 papers
- Time-consuming (days of LLM calls)
- Expensive (API costs)

### Option 2: Quick Retroactive Script (Attempted, Failed)

**What we tried:** Script to retroactively add `table_id` to existing relations

**Why it failed:** Relations don't exist yet. Can't tag what isn't there.

**Script result:**

```
Files processed: 47
Total relations: 13,857
Relations with table_id: 0
Percentage: 0.0%
```

### Option 3: Selective Re-extraction (Recommended)

**Compromise approach:**

1. Fix the chunking pipeline to handle tables
2. **Only re-extract papers with important tables**
   - Papers with many tables (8+ tables)
   - Key papers for your research
   - High-value content (experimental results, comparisons)
3. Leave other papers as-is for now
4. Future papers automatically get table extraction

**Papers to prioritize** (based on table count):

- Methane Biocatalysis - Selecting the Right Microbe: **8 tables**
- Sheets et al. 2017: **8 tables**
- Joseph et al. 2022: **8 tables**
- Adegbola thesis: **17 tables** (thesis - likely comprehensive tables)
- Jovanovic et al 2021 (part II): **6 tables**

---

## Code Location

### Chunking Code (Needs Fix)

Look for the script that:

- Reads `kg_gen_pipeline/output/docling_json/*.json`
- Writes `kg_gen_pipeline/output/text_chunks/*.texts_chunks.jsonl`

Current behavior:

```python
# Pseudocode of current chunking
for text_element in docling_json['texts']:
    create_chunk(text_element)

# Missing:
for table_element in docling_json['tables']:
    create_chunk(table_element)  #OKÜê ADD THIS
```

### Backend (Already Complete)

- `knowledge_graph/schema.graphql`: `table_id` field
- `knowledge_graph/kg_data_loader.py`: Handles `docling_ref: "#/tables/X"`
- `knowledge_graph/api.py`: `/api/relations/by-table` endpoint

---

## Test Plan (Once Fixed)

### 1. After Pipeline Fix

```bash
# Re-extract one paper with tables
cd kg_gen_pipeline
./extract_single_paper.py "A. Priyadarsini et al. 2023.pdf"

# Verify chunks now include tables
cat output/text_chunks/*.jsonl | grep -c '"#/tables/'
# Should return > 0
```

### 2. Check Relations Have Table IDs

```bash
# Check text triples include table_id
cat output/text_triples/*.json | grep -c '"table_id"'
# Should return > 0
```

### 3. Load to Dgraph

```bash
cd ../knowledge_graph
python kg_data_loader.py \
  --file ../kg_gen_pipeline/output/text_triples/Copy\ of\ A.\ Priyadarsini\ et\ al.\ 2023_kg_results_*.json
```

### 4. Test API

```bash
# Query by table_id
curl "http://localhost:8001/api/relations/by-table?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&table_id=page3_table1"

# Should return relations with:
{
  "table_id": "page3_table1",
  "section": "Visual Analysis: Table page3_table1",
  ...
}
```

---

## Next Steps

### Immediate

1. **Find the chunking script** in kg_gen_pipeline
2. **Add table processing** to create chunks with `docling_ref: "#/tables/X"`
3. **Test with one paper** (A. Priyadarsini has 3 tables)

### Short-term

1. **Re-extract 5-10 key papers** with most tables
2. **Load to Dgraph** and verify table relations work
3. **Update frontend** to use table click-to-lookup

### Long-term

1. **Gradually re-extract remaining papers** as needed
2. **All future papers** automatically include table extraction

---

## Summary

**Status:** Backend infrastructure is complete and waiting for data.

**Blocker:** Chunking pipeline doesn't extract tables from Docling JSON.

**Fix:** Update chunking step to process `docling_json['tables']` in addition to `docling_json['texts']`.

**Recommendation:** Fix pipeline + selective re-extraction of high-value papers.
