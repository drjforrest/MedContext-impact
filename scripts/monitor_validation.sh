#!/bin/bash
# Monitor validation progress

TERMINAL_FILE="${1:?Usage: $0 <terminal_file> <output_dir> <pid>}"

#!/bin/bash
# Monitor validation progress

TERMINAL_FILE="${1:?Usage: $0 <terminal_file> <output_dir> <pid>}"
OUTPUT_DIR="${2:?Usage: $0 <terminal_file> <output_dir> <pid>}"
PID="${3:?Usage: $0 <terminal_file> <output_dir> <pid>}"

# Validate PID is numeric
if ! [[ "$PID" =~ ^[0-9]+$ ]]; then
    echo "Error: PID must be a numeric value (got: '$PID')" >&2
    exit 1
fi

echo "==================================="
echo "Phase 1 Validation Monitor"
echo "==================================="
echo ""
echo "PID: $PID"
echo "Expected runtime: ~26 minutes"
echo "Started: $(date)"
echo ""

# Check if process is running
if ps -p "$PID" > /dev/null 2>&1; then
    echo "✓ Validation process is running"
else
    echo "✗ Validation process not found"
    exit 1
fi

# Show last few lines of output
echo ""
echo "--- Latest output ---"
tail -20 "$TERMINAL_FILE" 2>/dev/null || echo "No output yet"

# Check for any results files
echo ""
echo "--- Output files ---"
ls -lh "$OUTPUT_DIR"/*.json 2>/dev/null || echo "No output files yet"

echo ""
echo "To monitor in real-time:"
echo "  tail -f $TERMINAL_FILE"
echo ""
echo "To check status again:"
echo "  bash scripts/monitor_validation.sh"
