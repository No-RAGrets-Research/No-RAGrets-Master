#!/bin/bash
# Monitor table extraction progress

LOG_FILE="table_extraction.log"

echo "Table Extraction Progress Monitor"
echo "=================================="
echo ""

# Count papers processed
papers_done=$(grep -c "^\[.*Processing:" "$LOG_FILE" 2>/dev/null || echo "0")
echo "Papers processed: $papers_done / 49"

# Show current paper
current=$(tail -50 "$LOG_FILE" | grep "Processing:" | tail -1)
if [ ! -z "$current" ]; then
    echo "Current: $current"
fi

# Count tables processed
tables_done=$(grep -c "✓ Extracted.*relations" "$LOG_FILE" 2>/dev/null || echo "0")
echo "Tables completed: $tables_done"

# Show recent completions
echo ""
echo "Recent completions:"
tail -100 "$LOG_FILE" | grep "✓ Extracted" | tail -3

echo ""
echo "Last 10 lines:"
tail -10 "$LOG_FILE"
