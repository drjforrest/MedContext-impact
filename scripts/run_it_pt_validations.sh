#!/bin/bash
# Run IT and PT validations with current code
# Q (quantized) already has fresh results from overnight_n163

cd /Users/drjforrest/dev/projects/hero-counterforce/medcontext

echo "=== Running MedGemma 4B IT (Instruction-Tuned) ==="
MEDGEMMA_PROVIDER=huggingface \
MEDGEMMA_HF_MODEL=google/medgemma-1.5-4b-it \
uv run python -m app.validation.run_validation \
  --data-dir data/med-mmhl \
  --output-dir validation_results/med_mmhl_n163_4b_it \
  --limit 163 \
  2>&1 | tee logs/validation_it_$(date +%Y%m%d_%H%M%S).log

echo ""
echo "=== Running MedGemma 4B PT (Pre-trained) ==="
MEDGEMMA_PROVIDER=huggingface \
MEDGEMMA_HF_MODEL=google/medgemma-1.5-4b-pt \
uv run python -m app.validation.run_validation \
  --data-dir data/med-mmhl \
  --output-dir validation_results/med_mmhl_n163_4b_pt \
  --limit 163 \
  2>&1 | tee logs/validation_pt_$(date +%Y%m%d_%H%M%S).log

echo ""
echo "=== All validations complete ==="
echo "Running comparison..."
uv run python -m app.validation.compare_variants \
  --it validation_results/med_mmhl_n163_4b_it \
  --pt validation_results/med_mmhl_n163_4b_pt \
  --q validation_results/overnight_n163
