#!/bin/bash
# Monitor validation progress

TERMINAL_FILE="/Users/drjforrest/.cursor/projects/Users-drjforrest-dev-projects-hero-counterforce-medcontext/terminals/18174.txt"
OUTPUT_DIR="validation_results/med_mmhl_n163_quantized_4b"

echo "==================================="
echo "Phase 1 Validation Monitor"
echo "==================================="
echo ""
echo "PID: 39838"
echo "Expected runtime: ~26 minutes"
echo "Started: $(date)"
echo ""

# Check if process is running
if ps -p 39838 > /dev/null 2>&1; then
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
