# Visual Papers Migration Summary

**Date:** November 26, 2025

## Problem

The knowledge graph was reporting **71 papers** instead of the expected **49 papers**. Investigation revealed 22 duplicate papers with filenames ending in `_visual_kg_format.pdf`.

## Root Cause

The visual extraction pipeline created these files as intermediate format files:

- `raw_visual_triples/*.json` → `visual_triples/*_visual_kg_format_*.json`
- The `load_all_papers.sh` script loaded ALL JSON files from `visual_triples/`
- Bug in `kg_data_loader.py` line 272: tried to clean `_visual_triples_kg_format` but actual suffix was `_visual_kg_format`
- Result: Visual extractions were loaded as separate papers instead of being merged with text-based extractions

## Solution Implemented

### 1. Fixed kg_data_loader.py (Line 272)

Added cleaning for the correct suffix:

```python
clean_stem = clean_stem.replace('_visual_kg_format', '')
```

### 2. Created migrate_visual_papers.py

Script that:

- Found all 22 `_visual_kg_format.pdf` papers
- Updated their 1,073 relations to point to correct paper names
- Deleted the duplicate paper entries

### 3. Migration Results

**Before:**

- Total papers: 71
- Regular papers: 49
- Visual format papers: 22
- Visual relations: 1,073 (orphaned in separate papers)

**After:**

- Total papers: 49 ✓
- Regular papers: 49 (merged with visual data)
- Visual format papers: 0 ✓
- Visual relations: 1,073 (properly attributed to parent papers)

**Migrated Papers:**

- A. Priyadarsini et al. 2023 (10 relations)
- Ahmadi & Lackner 2024 (168 relations)
- Burrows et al 1984 (63 relations)
- Cantera et al. 2016 (42 relations)
- Chen et al. 2021 (38 relations)
- Chen et al. 2023 (14 relations)
- Duan et al. 2011 (12 relations)
- Hou et al. 1984 (2 relations)
- Hwang et al. 2015 (38 relations)
- Jiang et al. 2023 (9 relations)
- Jovanovic et al 2021 (part II) (62 relations)
- Jovanovic et al. 2021 (part I) (81 relations)
- Kim et al. 2010 (70 relations)
- Kulkarni et al. 2021 (124 relations)
- Markowska & Michalkiewicz 2009 (15 relations)
- Sahoo et al. 2022 (28 relations)
- Sahoo et al. 2023 (84 relations)
- Sheets et al. 2017 (92 relations)
- Soo et al. 2018 (19 relations)
- Takeguchi et al. 1997 (63 relations)
- Xin et al. 2004 (0 relations)
- Yu et al. 2009 (39 relations)

## Prevention

The fix in `kg_data_loader.py` ensures future visual extractions will be correctly attributed to their parent papers. When `load_all_papers.sh` loads visual triple files, they will automatically:

1. Have the `_visual_kg_format` suffix stripped
2. Merge relations with the existing paper instead of creating duplicates

## Verification

```bash
# Check paper count (should be 49)
curl -s http://localhost:8001/api/graph/stats | jq '.total_papers'

# Verify no visual_kg_format papers remain
curl -s http://localhost:8001/api/papers | jq '[.[] | select(.filename | contains("_visual_kg_format"))] | length'

# Check visual relations are properly attributed
curl -s "http://localhost:8001/api/relations/search?section=Figure&limit=5" | jq '[.[] | .source_paper]'
```

## Files Modified

1. **knowledge_graph/kg_data_loader.py**

   - Added: `clean_stem = clean_stem.replace('_visual_kg_format', '')` at line 273

2. **knowledge_graph/migrate_visual_papers.py** (NEW)

   - One-time migration script for cleaning up existing duplicates

3. **knowledge_graph/test_filename_cleaning.py** (NEW)
   - Test script to verify filename cleaning prevents duplicates

## Prevention - How It Works Going Forward

The fix in `kg_data_loader.py` ensures future visual extractions will be correctly attributed to their parent papers **from the first load** - no migration needed.

### First-Time Load Behavior (With Fix)

When loading papers for the first time into a fresh database:

1. **Text triples load first**: `paper_kg_results_*.json`

   - Cleaned filename: `paper.pdf`
   - Creates new paper: `paper.pdf`
   - Loads text relations

2. **Visual triples load next**: `paper_visual_kg_format_*.json`

   - Cleaned filename: `paper.pdf` ✅ (suffix stripped by fix)
   - **Checks if paper exists**: YES (found from step 1)
   - **Skips creating duplicate** (line 56 in kg_data_loader.py)
   - **Merges visual relations into existing paper** ✅

3. **Table triples load last**: `paper_tables_only_kg_format_*.json`
   - Cleaned filename: `paper.pdf` ✅
   - **Checks if paper exists**: YES
   - **Merges table relations into existing paper** ✅

**Result**: One unified paper with all relations (text + visual + tables) from the start.

### What the Fix Does

```python
# Line 273 in kg_data_loader.py
clean_stem = clean_stem.replace('_visual_kg_format', '')
```

This ensures that when `load_all_papers.sh` processes files in sequence:

- Text file: `Paper_kg_results_20251115.json` → `Paper.pdf`
- Visual file: `Paper_visual_kg_format_20251115.json` → `Paper.pdf` (same!)
- Table file: `Paper_tables_only_kg_format_20251116.json` → `Paper.pdf` (same!)

All three map to the same paper name, so they automatically merge during the initial load.

### No Migration Needed for New Data

The `migrate_visual_papers.py` script was only needed **once** to fix the existing database that had duplicates. For any new papers processed and loaded:

- First load will automatically merge all extraction types
- No separate migration step required
- Papers are correctly unified from the start

## Status

✅ Migration completed successfully
✅ All 22 duplicate papers removed
✅ All 1,073 visual relations preserved and correctly attributed
✅ Future runs will not create duplicates
✅ First-time loads will automatically merge text + visual + table data
