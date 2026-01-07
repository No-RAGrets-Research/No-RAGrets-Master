# Docling Reference Backfill - Bug Fix and Success

**Date:** December 7, 2025  
**Status:** ✅ Completed Successfully

## Overview

Successfully backfilled `docling_ref` values into 14,900 existing relations in the knowledge graph database. This enables the frontend to scroll directly to specific document elements without relying on fuzzy text matching.

## Critical Bug Discovery

### The Problem

The initial backfill script (`knowledge_graph/backfill_docling_refs.py`) claimed to successfully update all 14,900 relations, but database verification revealed that **no data was actually persisted**. All `docling_ref` fields remained `null`.

### Root Cause

The `update_relation_source_span()` method used **invalid RDF mutation syntax** instead of the **GraphQL mutation format** required by Dgraph's GraphQL endpoint.

**Broken Code (Lines 205-212):**

```python
mutation = f"""
{{
    set {{
        <{relation_id}> <source_span> {json.dumps(updated_source_span)} .
    }}
}}
"""
result = self.dgraph.mutate(mutation)
return True  # Always returned True even though mutation failed
```

**Issues:**

- Used RDF triple syntax (`<uid> <predicate> value .`)
- Dgraph's GraphQL endpoint silently ignored these mutations
- Method always returned `True`, masking the failure
- First backfill run (14,900 "updates") actually wrote 0 records

## The Fix

### Solution

Rewrote the mutation to use proper **GraphQL mutation format** with typed mutations and variables.

**Fixed Code (Lines 205-221):**

```python
mutation = """
mutation updateRelationSourceSpan($id: ID!, $source_span: String!) {
    updateRelation(input: {filter: {id: [$id]}, set: {source_span: $source_span}}) {
        numUids
    }
}
"""
variables = {"id": relation_id, "source_span": updated_source_span}
result = self.dgraph.mutate(mutation, variables)
num_uids = result.get("data", {}).get("updateRelation", {}).get("numUids", 0)
return num_uids > 0  # Now actually checks if update succeeded
```

**Improvements:**

- Uses GraphQL `updateRelation` mutation with proper schema types
- Parameterized query with variables for safety
- Checks `numUids > 0` to verify actual database updates
- Returns `False` if mutation fails

## Verification Process

### 1. Initial Testing (Bug Discovery)

```bash
# Test API endpoint
curl "http://localhost:8001/api/relations/0x5/source-span"
# Result: "docling_ref": null ❌

# Query database directly
# Result: No relations with docling_ref found ❌
```

### 2. After Fix - Database Verification

```bash
# Sample query results (offset 5000):
0x45ae: docling_ref=#/texts/209 ✅
0x45b1: docling_ref=#/texts/209 ✅
0x45b4: docling_ref=#/texts/209 ✅
0x45b7: docling_ref=#/texts/209 ✅
0x45b9: docling_ref=#/texts/209 ✅
0x45be: docling_ref=#/texts/247 ✅
0x45c2: docling_ref=#/texts/247 ✅
0x45c5: docling_ref=#/texts/247 ✅
0x45cb: docling_ref=#/texts/247 ✅
0x45ce: docling_ref=#/texts/247 ✅
```

### 3. After Fix - API Verification

**Single Endpoint:**

```bash
curl "http://localhost:8001/api/relations/0x45ae/source-span"
```

```json
{
  "relation_id": "0x45ae",
  "subject": "Salts",
  "predicate": "facilitate",
  "object": "migration of volatile components",
  "source_span": {
    "span_type": "multi_sentence",
    "text_evidence": "The large amount of salts...",
    "confidence": 0.8,
    "location": {...},
    "docling_ref": "#/texts/209" ✅
  }
}
```

**Batch Endpoint:**

```bash
curl "http://localhost:8001/api/relations/source-spans?ids=0x45ae,0x45b1,0x45b4"
```

All 3 relations returned with valid `docling_ref` values ✅

## Results

### Final Statistics

- **Total Relations:** 14,900
- **Successfully Updated:** 14,900 (100%)
  - Text relations: 11,878
  - Figure relations: 846
  - Table relations: 2,176
- **Errors:** 0
- **Processing Time:** ~5-10 minutes

### Docling Reference Formats

- **Text elements:** `#/texts/209`
- **Figure elements:** `#/pictures/0`
- **Table elements:** `#/tables/0`

## Frontend Integration

The API now returns `docling_ref` in all source span responses, enabling direct DOM selection:

```javascript
// Fetch relation source span
const response = await fetch(`/api/relations/${relationId}/source-span`);
const data = await response.json();
const doclingRef = data.source_span.docling_ref; // e.g., "#/texts/209"

// Direct DOM selection - no fuzzy text matching needed!
const element = document.querySelector(`[data-docling-ref="${doclingRef}"]`);
element?.scrollIntoView({ behavior: "smooth", block: "center" });
```

## Key Learnings

1. **Dgraph GraphQL Requirements:** GraphQL endpoints require typed mutations, not RDF syntax
2. **Silent Failures:** Invalid mutations may be silently ignored without errors
3. **Verification is Critical:** Always verify database state after "successful" operations
4. **Port Configuration:**
   - Port 8000 = Dgraph Ratel UI
   - Port 8001 = FastAPI server
5. **File Naming:** Text chunks and visual triples have "Copy of " prefix, docling_json files don't

## Files Modified

- `knowledge_graph/backfill_docling_refs.py` (Lines 205-221)
  - Fixed mutation syntax from RDF to GraphQL format
  - Added proper error checking

## System Status

✅ **Fully Operational**

- Database: All 14,900 relations have `docling_ref`
- API: Successfully returns `docling_ref` in responses
- Frontend: Ready for direct DOM selection implementation
- Future Relations: Automatically get `docling_ref` during extraction (no future backfill needed)
