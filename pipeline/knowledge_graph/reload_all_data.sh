#!/bin/bash
# reload_all_data.sh - Reset database and reload all KG data
# Usage: ./reload_all_data.sh

set -e  # Exit on error

cd "$(dirname "$0")"  # Change to script directory

echo "=========================================="
echo "Knowledge Graph Data Reload Script"
echo "=========================================="
echo ""

# Check if Dgraph is running
echo "🔍 Checking Dgraph status..."
python -c "from dgraph_manager import DgraphManager; dm = DgraphManager(); exit(0 if dm.health_check() else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Dgraph is not running!"
    echo "   Start it with: docker compose up -d"
    exit 1
fi
echo "✅ Dgraph is running"
echo ""

# Confirm reset
echo "⚠️  WARNING: This will DELETE all data and reload from scratch!"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled"
    exit 0
fi
echo ""

# Reset database
echo "🔄 Resetting database..."
python reset_database.py
if [ $? -ne 0 ]; then
    echo "❌ Database reset failed"
    exit 1
fi
echo "✅ Database reset complete"
echo ""

# Load visual triples
echo "=========================================="
echo "📊 Loading Visual Triples"
echo "=========================================="
visual_count=0
visual_failed=0

for file in ../kg_gen_pipeline/output/raw_visual_triples/*.json; do
    if [ -f "$file" ]; then
        basename=$(basename "$file")
        echo "→ Loading: $basename"
        
        if python kg_data_loader.py "$file" > /dev/null 2>&1; then
            ((visual_count++))
            echo "  ✅ Success"
        else
            ((visual_failed++))
            echo "  ❌ Failed"
        fi
    fi
done

echo ""
echo "Visual triples loaded: $visual_count"
if [ $visual_failed -gt 0 ]; then
    echo "Visual triples failed: $visual_failed"
fi
echo ""

# Load text triples
echo "=========================================="
echo "📝 Loading Text Triples"
echo "=========================================="
text_count=0
text_failed=0

if [ -d "../kg_gen_pipeline/output/text_triples" ]; then
    for file in ../kg_gen_pipeline/output/text_triples/*.json; do
        if [ -f "$file" ]; then
            basename=$(basename "$file")
            echo "→ Loading: $basename"
            
            if python kg_data_loader.py "$file" > /dev/null 2>&1; then
                ((text_count++))
                echo "  ✅ Success"
            else
                ((text_failed++))
                echo "  ❌ Failed"
            fi
        fi
    done
else
    echo "⚠️  Text triples directory not found, skipping..."
fi

echo ""
echo "Text triples loaded: $text_count"
if [ $text_failed -gt 0 ]; then
    echo "Text triples failed: $text_failed"
fi
echo ""

# Summary
echo "=========================================="
echo "🎉 Reload Complete!"
echo "=========================================="
echo "Visual files loaded: $visual_count"
echo "Text files loaded: $text_count"
echo "Total files loaded: $((visual_count + text_count))"

if [ $((visual_failed + text_failed)) -gt 0 ]; then
    echo "Total files failed: $((visual_failed + text_failed))"
fi

echo ""
echo "📊 Database Statistics:"
curl -s "http://localhost:8001/api/graph/stats" | python -m json.tool 2>/dev/null || echo "Could not fetch stats (API may not be running)"

echo ""
echo "✅ Done! Database is ready for use."
