#!/bin/bash
# Load all processed papers from kg_gen_pipeline into Dgraph
# Loads text triples, visual triples (figures), and table triples
# Skips papers that are already loaded

cd "$(dirname "$0")"

# Load text triples
echo "=========================================="
echo "STEP 1: Loading text triples"
echo "=========================================="

text_count=0
for file in ../kg_gen_pipeline/output/text_triples/*.json; do
    if [ -f "$file" ]; then
        echo ""
        echo "[$((++text_count))] Loading: $(basename "$file")"
        python kg_data_loader.py "$file"
    fi
done

echo ""
echo "Text triples loaded: $text_count files"

# Load visual triples (figures)
echo ""
echo "=========================================="
echo "STEP 2: Loading visual triples (figures)"
echo "=========================================="

visual_count=0
for file in ../kg_gen_pipeline/output/visual_triples/*.json; do
    if [ -f "$file" ]; then
        echo ""
        echo "[$((++visual_count))] Loading: $(basename "$file")"
        python kg_data_loader.py "$file"
    fi
done

echo ""
echo "Visual triples loaded: $visual_count files"

# Load table triples
echo ""
echo "=========================================="
echo "STEP 3: Loading table triples"
echo "=========================================="

table_count=0
for file in ../kg_gen_pipeline/output/table_triples/*.json; do
    if [ -f "$file" ]; then
        echo ""
        echo "[$((++table_count))] Loading: $(basename "$file")"
        python kg_data_loader.py "$file"
    fi
done

echo ""
echo "Table triples loaded: $table_count files"

# Summary
echo ""
echo "=========================================="
echo "LOADING COMPLETE"
echo "=========================================="
echo "Text triples:   $text_count files"
echo "Visual triples: $visual_count files"
echo "Table triples:  $table_count files"
echo "Total:          $((text_count + visual_count + table_count)) files"
echo "=========================================="
