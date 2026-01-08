# Data Loader Fixes Summary

## Date: November 21, 2025

## Issues Fixed

### 1.OKOK Faulty Node Deduplication Logic
**Problem:** When using `--force-update`, the loader was updating timestamps on existing nodes, which are shared across papers. This caused unnecessary modifications to nodes that should remain immutable.

**Fix:** Modified `create_node()` to always reuse existing nodes without modification during force_update. Nodes are now truly shared entities across papers.

**Code Change:**
```python
# Before:
if self.force_update:
    # Update existing node timestamp
    update_mutation = """
    mutation UpdateNode($nodeId: [ID!], $updatedAt: String) {
      updateNode(input: { filter: { id: $nodeId }, set: { updated_at: $updatedAt } }) {
        node { id }
      }
    }"""
    # ...

# After:
# Always reuse existing nodes - they are shared across papers
# Don't modify them during force_update
if self.verbose:
    print(f"REUSED: Node already exists: {name}")
return existing_node['id']
```

### 2.OKOK Removed Timestamps from Papers
**Problem:** Papers had `processed_at` timestamps which would change on reload, breaking relation queries.

**Fix:** Removed `processed_at` field from paper creation entirely.

**Code Change:**
```python
# Before:
mutation CreatePaper($title: String!, $filename: String!, $processedAt: String!,
                   $totalEntities: Int, $totalRelations: Int, $sections: [String]) {
  addPaper(input: [{
    title: $title,
    filename: $filename,
    processed_at: $processedAt,  #OKOK Removed this
    # ...

# After:
mutation CreatePaper($title: String!, $filename: String!,
                   $totalEntities: Int, $totalRelations: Int, $sections: [String]) {
  addPaper(input: [{
    title: $title,
    filename: $filename,
    # No processed_at field
```

### 3.OKOK Fixed "Copy of" Prefix in Filenames
**Problem:** PDF filenames had "Copy of " prefix which was inconsistent and should be removed.

**Fix:** Updated filename parsing to remove "Copy of " prefix and clean up timestamps.

**Code Change:**
```python
# Before:
filename = results_path.stem.replace('_kg_results_', '').split('_')[0] + '.pdf'
title = filename.replace('Copy of ', '').replace('.pdf', '').replace('_', ' ')

# After:
clean_stem = results_path.stem.replace('_kg_results_', '').replace('_visual_triples_kg_format', '')
clean_stem = clean_stem.split('_20')[0]  # Remove timestamps like _20251115

filename = (clean_stem + '.pdf').replace('Copy of ', '')  # Remove "Copy of " prefix
title = filename.replace('.pdf', '').replace('_', ' ')
```

## Impact

These fixes ensure:
-OKOK Nodes remain immutable and shared across papers
-OKOK Papers can be reloaded without timestamp conflicts
-OKOK Filenames are clean and consistent
-OKOK Relations correctly reference their source papers

## Reloading Instructions

### Option 1: Reset and Reload All Data

```bash
cd knowledge_graph

# 1. Reset the database (deletes all data)
python reset_database.py

# 2. Reload all visual triples
for file in ../kg_gen_pipeline/output/raw_visual_triples/*.json; do
    echo "Loading: $file"
    python kg_data_loader.py "$file"
done

# 3. Reload all text triples (if you have them)
for file in ../kg_gen_pipeline/output/text_triples/*.json; do
    echo "Loading: $file"
    python kg_data_loader.py "$file"
done
```

### Option 2: Force Update Individual Papers

If you want to reload specific papers without resetting everything:

```bash
cd knowledge_graph

# Reload a specific paper (will delete and recreate that paper's data)
python kg_data_loader.py --force-update ../kg_gen_pipeline/output/raw_visual_triples/YOUR_PAPER.json
```

### Option 3: Scripted Full Reload

```bash
#!/bin/bash
cd knowledge_graph

echo "ðŸ”„ Resetting database..."
python reset_database.py

echo "ðŸŠ Loading visual triples..."
visual_count=0
for file in ../kg_gen_pipeline/output/raw_visual_triples/*.json; do
    if [ -f "$file" ]; then
        echo " OK†’ $(basename "$file")"
        python kg_data_loader.py "$file"
        ((visual_count++))
    fi
done

echo "ðŸOK Loading text triples..."
text_count=0  
for file in ../kg_gen_pipeline/output/text_triples/*.json; do
    if [ -f "$file" ]; then
        echo " OK†’ $(basename "$file")"
        python kg_data_loader.py "$file"
        ((text_count++))
    fi
done

echo ""
echo "OK Reload complete!"
echo "   Visual files loaded: $visual_count"
echo "   Text files loaded: $text_count"
```

## Verification

After reloading, verify the fixes worked:

```bash
# Check that papers don't have "Copy of" prefix
curl "http://localhost:8001/api/papers" | jq '.[].filename' | head -5

# Verify figure_id endpoint still works
curl "http://localhost:8001/api/relations/by-figure?paper_id=A.%20Priyadarsini%20et%20al.%202023.pdf&figure_id=page5_fig1" | jq '. | length'

# Count total relations in database
curl "http://localhost:8001/api/graph/stats" | jq '.total_relations'
```

## Expected Behavior After Fixes

1. **Node Reuse:** When loading multiple papers, entities like "CO2" or "methanol" will be created once and reused across all papers
2. **Clean Filenames:** Papers will have filenames like "A. Priyadarsini et al. 2023.pdf" instead of "Copy of A. Priyadarsini et al. 202320251115.pdf"
3. **Stable References:** Relations will correctly reference their source papers without timestamp issues
4. **Force Update:** Using `--force-update` will cleanly delete and recreate paper data without corrupting shared nodes
