#!/bin/bash
# Quick validation test with n=10 to verify fixes

cd /Users/drjforrest/dev/projects/hero-counterforce/medcontext || exit

echo "=== Running Quick Validation Test (n=10) ==="
echo "This will verify the fixes are working correctly"
echo ""

# Use the local quantized model (Q)
MEDGEMMA_PROVIDER=local \
LOCAL_MEDGEMMA_URL=http://localhost:1234 \
MEDGEMMA_MODEL=local/medgemma-1.5-4b-it \
uv run python -m app.validation.run_validation \
  --data-dir data/med-mmhl \
  --output-dir validation_results/test_n10_fixes \
  --limit 10 \
  --seed 42 \
  2>&1 | tee logs/test_n10_fixes.log

echo ""
echo "=== Validation Complete ==="
echo "Check validation_results/test_n10_fixes/ for results"
