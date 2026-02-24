#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# verify_vps_llama_cpp.sh
#
# Verify VPS is properly configured for llama-cpp local inference
# Run from local machine: ./scripts/verify_vps_llama_cpp.sh
# ─────────────────────────────────────────────────────────────────────────────

VPS_HOST="${VPS_HOST:-Contabo-admin}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_pass() { echo -e "${GREEN}✓${NC} $1"; }
check_fail() { echo -e "${RED}✗${NC} $1"; }
check_warn() { echo -e "${YELLOW}!${NC} $1"; }

echo "=== MedContext VPS llama-cpp Verification ==="
echo "VPS: $VPS_HOST"
echo ""

ALL_GOOD=true

ssh "$VPS_HOST" << 'ENDSSH'
set -euo pipefail

# Colors for remote output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_pass() { echo -e "${GREEN}✓${NC} $1"; }
check_fail() { echo -e "${RED}✗${NC} $1"; ALL_GOOD=false; }
check_warn() { echo -e "${YELLOW}!${NC} $1"; }

ALL_GOOD=true

# ── 1. Check working directory ──────────────────────────────────────────────
echo "1. Checking project directory..."
if [ -L /var/www/medcontext/medcontext ]; then
    TARGET=$(readlink -f /var/www/medcontext/medcontext)
    check_pass "Project directory exists (symlink to $TARGET)"
    cd /var/www/medcontext/medcontext
elif [ -d /var/www/medcontext/medcontext ]; then
    check_pass "Project directory exists"
    cd /var/www/medcontext/medcontext
else
    check_fail "Project directory not found: /var/www/medcontext/medcontext"
    exit 1
fi
echo ""

# ── 2. Check Python environment ─────────────────────────────────────────────
echo "2. Checking Python environment..."

if [ -d ".venv" ]; then
    check_pass "Virtual environment exists"
else
    check_fail "Virtual environment not found - run: uv venv"
    ALL_GOOD=false
fi

# Check llama-cpp-python installation
if .venv/bin/python -c "import llama_cpp" 2>/dev/null; then
    VERSION=$(.venv/bin/python -c "import llama_cpp; print(llama_cpp.__version__)" 2>/dev/null || echo "unknown")
    check_pass "llama-cpp-python is installed (version: $VERSION)"
else
    check_fail "llama-cpp-python is NOT installed"
    echo "  Install with: uv pip install llama-cpp-python"
    ALL_GOOD=false
fi
echo ""

# ── 3. Check GGUF model files ───────────────────────────────────────────────
echo "3. Checking GGUF model files..."

if [ -d "models" ]; then
    check_pass "models/ directory exists"

    # List all GGUF files
    if ls models/*.gguf >/dev/null 2>&1; then
        for file in models/*.gguf; do
            SIZE=$(du -h "$file" | cut -f1)
            if [[ "$file" == *"mmproj"* ]]; then
                check_pass "mmproj file: $(basename "$file") ($SIZE)"
            else
                check_pass "Model file: $(basename "$file") ($SIZE)"
            fi
        done
    else
        check_fail "No .gguf files found in models/"
        echo "  Download with: ./scripts/setup_llama_cpp.sh"
        ALL_GOOD=false
    fi
else
    check_fail "models/ directory not found"
    echo "  Create and download models: ./scripts/setup_llama_cpp.sh"
    ALL_GOOD=false
fi
echo ""

# ── 4. Check .env configuration ─────────────────────────────────────────────
echo "4. Checking .env configuration..."

if [ -f ".env" ]; then
    check_pass ".env file exists"

    # Source .env and check critical variables
    set -a
    source .env 2>/dev/null || true
    set +a

    # Check MEDGEMMA_MODEL
    if [ -n "${MEDGEMMA_MODEL:-}" ]; then
        if [[ "$MEDGEMMA_MODEL" == *"llama_cpp"* ]] || [[ "$MEDGEMMA_MODEL" == *".gguf"* ]]; then
            check_pass "MEDGEMMA_MODEL points to llama-cpp: $MEDGEMMA_MODEL"
        else
            check_warn "MEDGEMMA_MODEL doesn't indicate llama-cpp: $MEDGEMMA_MODEL"
            echo "  Expected: llama_cpp/medgemma-1.5-4b-it-Q4_K_M or similar"
        fi
    else
        check_fail "MEDGEMMA_MODEL is not set"
        ALL_GOOD=false
    fi

    # Check MEDGEMMA_LOCAL_PATH
    if [ -n "${MEDGEMMA_LOCAL_PATH:-}" ]; then
        if [ -f "${MEDGEMMA_LOCAL_PATH}" ]; then
            SIZE=$(du -h "${MEDGEMMA_LOCAL_PATH}" | cut -f1)
            check_pass "MEDGEMMA_LOCAL_PATH exists: $MEDGEMMA_LOCAL_PATH ($SIZE)"
        else
            check_fail "MEDGEMMA_LOCAL_PATH file not found: $MEDGEMMA_LOCAL_PATH"
            ALL_GOOD=false
        fi
    else
        check_fail "MEDGEMMA_LOCAL_PATH is not set in .env"
        echo "  Set to: MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q4_K_M.gguf"
        ALL_GOOD=false
    fi

    # Check MEDGEMMA_MMPROJ_PATH
    if [ -n "${MEDGEMMA_MMPROJ_PATH:-}" ]; then
        if [ -f "${MEDGEMMA_MMPROJ_PATH}" ]; then
            SIZE=$(du -h "${MEDGEMMA_MMPROJ_PATH}" | cut -f1)
            check_pass "MEDGEMMA_MMPROJ_PATH exists: $MEDGEMMA_MMPROJ_PATH ($SIZE)"
        else
            check_fail "MEDGEMMA_MMPROJ_PATH file not found: $MEDGEMMA_MMPROJ_PATH"
            ALL_GOOD=false
        fi
    else
        check_fail "MEDGEMMA_MMPROJ_PATH is not set in .env"
        echo "  Set to: MEDGEMMA_MMPROJ_PATH=models/mmproj-F16.gguf"
        ALL_GOOD=false
    fi

    # Check DATABASE_URL
    if [ -n "${DATABASE_URL:-}" ]; then
        check_pass "DATABASE_URL is set"
    else
        check_warn "DATABASE_URL is not set (optional)"
    fi

    # Check LLM configuration
    if [ -n "${LLM_API_KEY:-}" ] || [ -n "${GEMINI_API_KEY:-}" ] || [ -n "${OPENROUTER_API_KEY:-}" ]; then
        check_pass "LLM API key is configured"
    else
        check_warn "No LLM API key set (will use MedGemma-only mode)"
    fi
else
    check_fail ".env file not found"
    echo "  Copy from local: scp .env $VPS_HOST:/var/www/medcontext/medcontext/"
    ALL_GOOD=false
fi
echo ""

# ── 5. Check system resources ───────────────────────────────────────────────
echo "5. Checking system resources..."

# Check available RAM
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
AVAILABLE_MEM=$(free -g | awk '/^Mem:/{print $7}')

if [ "$TOTAL_MEM" -ge 8 ]; then
    check_pass "Total RAM: ${TOTAL_MEM}GB (sufficient for Q4_K_M)"
else
    check_warn "Total RAM: ${TOTAL_MEM}GB (Q4_K_M needs ~4GB, may be tight)"
fi

if [ "$AVAILABLE_MEM" -ge 4 ]; then
    check_pass "Available RAM: ${AVAILABLE_MEM}GB (sufficient)"
else
    check_warn "Available RAM: ${AVAILABLE_MEM}GB (may need to free up memory)"
fi

# Check disk space
DISK_AVAIL=$(df -h /var/www/medcontext | awk 'NR==2 {print $4}')
check_pass "Available disk space: $DISK_AVAIL"

echo ""

# ── 6. Summary ──────────────────────────────────────────────────────────────
echo "=== Summary ==="
echo ""

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}✓ VPS is READY for llama-cpp deployment${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Deploy: ./scripts/deploy_simple.sh"
    echo "  2. Test: curl https://medcontext.drjforrest.com/health"
else
    echo -e "${RED}✗ VPS is NOT READY - fix the issues above${NC}"
    echo ""
    echo "Common fixes:"
    echo ""
    echo "  Install llama-cpp-python:"
    echo "    ssh $VPS_HOST 'cd /var/www/medcontext/medcontext && uv pip install llama-cpp-python'"
    echo ""
    echo "  Download GGUF models:"
    echo "    ssh $VPS_HOST 'cd /var/www/medcontext/medcontext && ./scripts/setup_llama_cpp.sh'"
    echo ""
    echo "  Upload .env file:"
    echo "    scp .env $VPS_HOST:/var/www/medcontext/medcontext/"
    echo ""
    exit 1
fi

ENDSSH

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== Ready to Deploy ===${NC}"
    echo ""
    echo "Run deployment:"
    echo "  ./scripts/deploy_simple.sh"
else
    echo ""
    echo -e "${RED}=== Not Ready - Fix Issues Above ===${NC}"
    exit 1
fi
