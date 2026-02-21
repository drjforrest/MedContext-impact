#!/bin/bash
# Full validation run with n=163

cd /Users/drjforrest/dev/projects/hero-counterforce/medcontext || exit

echo "=== Starting Full Validation (n=163) ==="
echo "Started at: $(date)"
echo ""

# Create output directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="validation_results/med_mmhl_n163_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo ""

# Run validation using local quantized model
python -m app.validation.run_validation \
  --data-dir data/med-mmhl \
  --output-dir "$OUTPUT_DIR" \
  --limit 163 \
  --seed 42 \
  2>&1 | tee "logs/validation_n163_${TIMESTAMP}.log"

echo ""
echo "=== Validation Complete ==="
echo "Finished at: $(date)"
echo "Results in: $OUTPUT_DIR"
