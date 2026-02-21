#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# setup_llama_cpp.sh
#
# Downloads MedGemma GGUF model + mmproj, installs llama-cpp-python,
# and configures .env to use the llama_cpp provider for local inference.
# ─────────────────────────────────────────────────────────────────────────────

REPO="lmstudio-community/medgemma-4b-it-GGUF"
QUANT="${1:-Q4_K_M}"                  # Override: ./setup_llama_cpp.sh Q6_K
MODEL_FILE="medgemma-4b-it-${QUANT}.gguf"
MMPROJ_FILE="mmproj-model-F16.gguf"

# Resolve project root (one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODEL_DIR="${PROJECT_ROOT}/models"
ENV_FILE="${PROJECT_ROOT}/.env"

echo "=== MedGemma llama-cpp-python Setup ==="
echo "  Repo:       ${REPO}"
echo "  Quant:      ${QUANT}"
echo "  Model file: ${MODEL_FILE}"
echo "  Dest:       ${MODEL_DIR}"
echo ""

# ── 1. Check prerequisites ──────────────────────────────────────────────────

if ! command -v huggingface-cli &>/dev/null; then
    echo "Installing huggingface_hub CLI..."
    pip install --quiet huggingface_hub
fi

# ── 2. Create models directory ───────────────────────────────────────────────

mkdir -p "${MODEL_DIR}"

# ── 3. Download model GGUF ──────────────────────────────────────────────────

MODEL_PATH="${MODEL_DIR}/${MODEL_FILE}"
if [ -f "${MODEL_PATH}" ]; then
    echo "Model already exists: ${MODEL_PATH}"
    echo "  Size: $(du -h "${MODEL_PATH}" | cut -f1)"
else
    echo "Downloading ${MODEL_FILE} (~2.5 GB for Q4_K_M)..."
    huggingface-cli download "${REPO}" "${MODEL_FILE}" \
        --local-dir "${MODEL_DIR}" \
        --local-dir-use-symlinks False
    echo "Downloaded: ${MODEL_PATH}"
fi

# ── 4. Download mmproj (vision projection model) ────────────────────────────

MMPROJ_PATH="${MODEL_DIR}/${MMPROJ_FILE}"
if [ -f "${MMPROJ_PATH}" ]; then
    echo "mmproj already exists: ${MMPROJ_PATH}"
    echo "  Size: $(du -h "${MMPROJ_PATH}" | cut -f1)"
else
    echo "Downloading ${MMPROJ_FILE} (~851 MB)..."
    huggingface-cli download "${REPO}" "${MMPROJ_FILE}" \
        --local-dir "${MODEL_DIR}" \
        --local-dir-use-symlinks False
    echo "Downloaded: ${MMPROJ_PATH}"
fi

# ── 5. Install llama-cpp-python if missing ───────────────────────────────────

if ! python -c "import llama_cpp" 2>/dev/null; then
    echo ""
    echo "Installing llama-cpp-python..."
    pip install llama-cpp-python
else
    echo "llama-cpp-python already installed."
fi

# ── 6. Configure .env ───────────────────────────────────────────────────────

echo ""
echo "Configuring ${ENV_FILE}..."

# Helper: set or update a key in .env
set_env() {
    local key="$1" value="$2"
    if [ ! -f "${ENV_FILE}" ]; then
        echo "${key}=${value}" > "${ENV_FILE}"
    elif grep -q "^${key}=" "${ENV_FILE}"; then
        # Update existing (macOS-compatible sed)
        sed -i '' "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}"
        echo "  Updated: ${key}=${value}"
    elif grep -q "^# *${key}=" "${ENV_FILE}"; then
        # Uncomment and set
        sed -i '' "s|^# *${key}=.*|${key}=${value}|" "${ENV_FILE}"
        echo "  Enabled: ${key}=${value}"
    else
        echo "${key}=${value}" >> "${ENV_FILE}"
        echo "  Added:   ${key}=${value}"
    fi
}

set_env "MEDGEMMA_MODEL" "llama_cpp/medgemma-4b-it-${QUANT}"
set_env "MEDGEMMA_LOCAL_PATH" "${MODEL_PATH}"
set_env "MEDGEMMA_MMPROJ_PATH" "${MMPROJ_PATH}"

# ── 7. Ensure models/ is gitignored ─────────────────────────────────────────

GITIGNORE="${PROJECT_ROOT}/.gitignore"
if ! grep -q "^models/" "${GITIGNORE}" 2>/dev/null; then
    echo "" >> "${GITIGNORE}"
    echo "# GGUF model weights (large binary files)" >> "${GITIGNORE}"
    echo "models/" >> "${GITIGNORE}"
    echo "  Added models/ to .gitignore"
fi

# ── 8. Verify ───────────────────────────────────────────────────────────────

echo ""
echo "=== Verification ==="
echo "  Model:  $(du -h "${MODEL_PATH}" | cut -f1)  ${MODEL_PATH}"
echo "  mmproj: $(du -h "${MMPROJ_PATH}" | cut -f1)  ${MMPROJ_PATH}"

python -c "
from llama_cpp import Llama
print('  llama-cpp-python: OK (import successful)')
" 2>/dev/null || echo "  llama-cpp-python: FAILED (import error)"

echo ""
echo "=== Done ==="
echo "Start the server with:"
echo "  cd ${PROJECT_ROOT}"
echo "  uv run uvicorn app.main:app --reload --app-dir src"
echo ""
echo "The llama_cpp provider will load the model on first request."
