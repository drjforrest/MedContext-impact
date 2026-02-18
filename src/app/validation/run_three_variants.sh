#!/bin/bash
set -euo pipefail

# Three-Variant MedGemma Validation on Med-MMHL (n=163, seed=42)
#
# Compares 3 MedGemma 4B variants:
#   1. IT  (Instruction-Tuned) — results already exist in validation_results/med_mmhl_n163_4b_it/
#   2. PT  (Pre-Trained)       — via HuggingFace Inference API
#   3. Q   (Quantized GGUF)    — via LM Studio (must be running at localhost:1234)
#
# Usage:
#   ./src/app/validation/run_three_variants.sh          # Run PT + Q variants
#   ./src/app/validation/run_three_variants.sh --all     # Re-run all 3 variants
#   ./src/app/validation/run_three_variants.sh --pt      # Run only PT variant
#   ./src/app/validation/run_three_variants.sh --q       # Run only Q variant

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
DATA_DIR="${REPO_ROOT}/data/med-mmhl"
RESULTS_BASE="${REPO_ROOT}/validation_results"

RUN_IT=false
RUN_PT=false
RUN_Q=false

if [[ $# -eq 0 ]]; then
    # Default: run PT + Q (IT already exists)
    RUN_PT=true
    RUN_Q=true
elif [[ "$1" == "--all" ]]; then
    RUN_IT=true
    RUN_PT=true
    RUN_Q=true
elif [[ "$1" == "--pt" ]]; then
    RUN_PT=true
elif [[ "$1" == "--q" ]]; then
    RUN_Q=true
else
    echo "Usage: $0 [--all|--pt|--q]"
    exit 1
fi

echo "============================================================"
echo "MedGemma 3-Variant Validation (Med-MMHL n=163, seed=42)"
echo "============================================================"
echo ""

# Variant 1: IT (Instruction-Tuned) via HuggingFace
if [[ "$RUN_IT" == true ]]; then
    echo "--- Variant 1: MedGemma 4B IT (Instruction-Tuned) ---"
    MEDGEMMA_MODEL=google/medgemma-1.1-4b-it \
    uv run python -m app.validation.run_validation \
        --data-dir "$DATA_DIR" \
        --output-dir "${RESULTS_BASE}/med_mmhl_n163_4b_it" \
        --limit 163 --seed 42 \
        2>&1 | tee "${RESULTS_BASE}/med_mmhl_n163_4b_it_run.log"
    echo ""
else
    if [[ -f "${RESULTS_BASE}/med_mmhl_n163_4b_it/raw_predictions.json" ]]; then
        echo "--- Variant 1: MedGemma 4B IT --- SKIPPED (results exist) ---"
    else
        echo "WARNING: IT results not found at ${RESULTS_BASE}/med_mmhl_n163_4b_it/"
        echo "  Run with --all to generate them."
    fi
fi

# Variant 2: PT (Pre-Trained) via HuggingFace
if [[ "$RUN_PT" == true ]]; then
    echo ""
    echo "--- Variant 2: MedGemma 4B PT (Pre-Trained) ---"
    MEDGEMMA_MODEL=google/medgemma-1.1-4b-pt \
    uv run python -m app.validation.run_validation \
        --data-dir "$DATA_DIR" \
        --output-dir "${RESULTS_BASE}/med_mmhl_n163_4b_pt" \
        --limit 163 --seed 42 \
        2>&1 | tee "${RESULTS_BASE}/med_mmhl_n163_4b_pt_run.log"
fi

# Variant 3: Q (Quantized GGUF) via LM Studio
if [[ "$RUN_Q" == true ]]; then
    echo ""
    echo "--- Variant 3: MedGemma 4B Quantized (LM Studio) ---"

    # Check if LM Studio is running
    if ! curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
        echo "ERROR: LM Studio not reachable at localhost:1234"
        echo "  Start LM Studio and load a MedGemma GGUF model first."
        echo "  Skipping Q variant."
    else
        MEDGEMMA_MODEL=google/medgemma-1.1-4b-it.gguf \
        LOCAL_MEDGEMMA_URL=http://localhost:1234 \
        uv run python -m app.validation.run_validation \
            --data-dir "$DATA_DIR" \
            --output-dir "${RESULTS_BASE}/med_mmhl_n163_4b_quantized" \
            --limit 163 --seed 42 \
            2>&1 | tee "${RESULTS_BASE}/med_mmhl_n163_4b_quantized_run.log"
    fi
fi

echo ""
echo "============================================================"
echo "Validation complete. Run comparison with:"
echo "  uv run python -m app.validation.compare_variants"
echo "============================================================"
