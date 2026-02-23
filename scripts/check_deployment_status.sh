#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# check_deployment_status.sh
#
# Diagnose current deployment state for GGUF MedGemma on VPS
# Run this on your VPS to check if everything is ready for testing
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "=== MedContext Deployment Status Check ==="
echo "Time: $(date)"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() { echo -e "${GREEN}✓${NC} $1"; }
check_fail() { echo -e "${RED}✗${NC} $1"; }
check_warn() { echo -e "${YELLOW}!${NC} $1"; }

# ── 1. Check working directory ──────────────────────────────────────────────
echo "1. Checking working directory..."
if [ -d "/var/www/medcontext" ]; then
    check_pass "Project directory exists: /var/www/medcontext"
    cd /var/www/medcontext
else
    check_fail "Project directory not found: /var/www/medcontext"
    exit 1
fi
echo ""

# ── 2. Check Python environment ─────────────────────────────────────────────
echo "2. Checking Python environment..."
if command -v uv &>/dev/null; then
    check_pass "uv is installed: $(uv --version)"
else
    check_fail "uv is not installed"
fi

if [ -d ".venv" ]; then
    check_pass "Virtual environment exists: .venv"
else
    check_warn "Virtual environment not found - run: uv venv"
fi
echo ""

# ── 3. Check GGUF model files ───────────────────────────────────────────────
echo "3. Checking GGUF model files..."
if [ -d "models" ]; then
    check_pass "models/ directory exists"

    # Check for GGUF model
    GGUF_FILES=(models/*.gguf)
    if [ -f "${GGUF_FILES[0]}" ]; then
        for file in models/*.gguf; do
            if [[ "$file" == *"mmproj"* ]]; then
                check_pass "mmproj file: $(basename "$file") ($(du -h "$file" | cut -f1))"
            else
                check_pass "Model file: $(basename "$file") ($(du -h "$file" | cut -f1))"
            fi
        done
    else
        check_fail "No .gguf files found in models/"
        echo "  Run: ./scripts/setup_llama_cpp.sh"
    fi
else
    check_fail "models/ directory not found"
    echo "  Run: ./scripts/setup_llama_cpp.sh"
fi
echo ""

# ── 4. Check .env configuration ─────────────────────────────────────────────
echo "4. Checking .env configuration..."
if [ -f ".env" ]; then
    check_pass ".env file exists"

    # Check critical variables
    source .env 2>/dev/null || true

    if [ -n "${MEDGEMMA_MODEL:-}" ]; then
        check_pass "MEDGEMMA_MODEL is set: $MEDGEMMA_MODEL"
    else
        check_fail "MEDGEMMA_MODEL is not set"
    fi

    if [ -n "${MEDGEMMA_LOCAL_PATH:-}" ]; then
        if [ -f "${MEDGEMMA_LOCAL_PATH}" ]; then
            check_pass "MEDGEMMA_LOCAL_PATH exists: $MEDGEMMA_LOCAL_PATH"
        else
            check_fail "MEDGEMMA_LOCAL_PATH file not found: $MEDGEMMA_LOCAL_PATH"
        fi
    else
        check_fail "MEDGEMMA_LOCAL_PATH is not set"
    fi

    if [ -n "${MEDGEMMA_MMPROJ_PATH:-}" ]; then
        if [ -f "${MEDGEMMA_MMPROJ_PATH}" ]; then
            check_pass "MEDGEMMA_MMPROJ_PATH exists: $MEDGEMMA_MMPROJ_PATH"
        else
            check_fail "MEDGEMMA_MMPROJ_PATH file not found: $MEDGEMMA_MMPROJ_PATH"
        fi
    else
        check_fail "MEDGEMMA_MMPROJ_PATH is not set"
    fi

    if [ -n "${DATABASE_URL:-}" ]; then
        check_pass "DATABASE_URL is set"
    else
        check_warn "DATABASE_URL is not set"
    fi

    if [ -n "${LLM_API_KEY:-}" ]; then
        check_pass "LLM_API_KEY is set"
    else
        check_warn "LLM_API_KEY is not set (will fall back to MedGemma)"
    fi
else
    check_fail ".env file not found"
    echo "  Copy .env.example to .env and configure"
fi
echo ""

# ── 5. Check Python dependencies ────────────────────────────────────────────
echo "5. Checking Python dependencies..."
if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"

    # Test imports
    if uv run python -c "import llama_cpp" 2>/dev/null; then
        check_pass "llama-cpp-python is installed"
        VERSION=$(uv run python -c "import llama_cpp; print(llama_cpp.__version__)" 2>/dev/null || echo "unknown")
        echo "  Version: $VERSION"
    else
        check_fail "llama-cpp-python is not installed"
        echo "  Run: uv pip install -r requirements.txt"
    fi

    if uv run python -c "import fastapi" 2>/dev/null; then
        check_pass "FastAPI is installed"
    else
        check_fail "FastAPI is not installed"
    fi
else
    check_fail "requirements.txt not found"
fi
echo ""

# ── 6. Check database ───────────────────────────────────────────────────────
echo "6. Checking database..."
if command -v psql &>/dev/null; then
    check_pass "PostgreSQL client is installed"

    # Test connection if DATABASE_URL is set
    if [ -n "${DATABASE_URL:-}" ]; then
        if uv run python -c "import psycopg2; psycopg2.connect('${DATABASE_URL}')" 2>/dev/null; then
            check_pass "Database connection successful"
        else
            check_fail "Cannot connect to database"
        fi
    fi
else
    check_warn "psql not installed (optional)"
fi
echo ""

# ── 7. Check web server ─────────────────────────────────────────────────────
echo "7. Checking web server..."
if systemctl is-active --quiet caddy 2>/dev/null; then
    check_pass "Caddy is running"
elif systemctl is-active --quiet nginx 2>/dev/null; then
    check_pass "Nginx is running"
else
    check_warn "No web server running (Caddy/Nginx)"
fi

if systemctl is-active --quiet medcontext 2>/dev/null; then
    check_pass "MedContext service is running"
else
    check_warn "MedContext systemd service not running"
fi
echo ""

# ── 8. Check ports ──────────────────────────────────────────────────────────
echo "8. Checking ports..."
if command -v netstat &>/dev/null || command -v ss &>/dev/null; then
    if netstat -tuln 2>/dev/null | grep -q ":8000" || ss -tuln 2>/dev/null | grep -q ":8000"; then
        check_pass "Port 8000 is listening (FastAPI)"
    else
        check_warn "Port 8000 is not listening"
    fi

    if netstat -tuln 2>/dev/null | grep -q ":80" || ss -tuln 2>/dev/null | grep -q ":80"; then
        check_pass "Port 80 is listening (HTTP)"
    else
        check_warn "Port 80 is not listening"
    fi

    if netstat -tuln 2>/dev/null | grep -q ":443" || ss -tuln 2>/dev/null | grep -q ":443"; then
        check_pass "Port 443 is listening (HTTPS)"
    else
        check_warn "Port 443 is not listening"
    fi
else
    check_warn "netstat/ss not available"
fi
echo ""

# ── 9. Summary ──────────────────────────────────────────────────────────────
echo "=== Summary ==="
echo ""

READY=true
if [ ! -f ".env" ]; then
    check_fail "Missing .env file"
    READY=false
elif [ -z "${MEDGEMMA_LOCAL_PATH:-}" ]; then
    check_fail "MEDGEMMA_LOCAL_PATH not set in .env"
    READY=false
elif [ ! -f "${MEDGEMMA_LOCAL_PATH}" ]; then
    check_fail "Model file not found: ${MEDGEMMA_LOCAL_PATH}"
    READY=false
fi

if [ -n "${MEDGEMMA_MMPROJ_PATH:-}" ] && [ ! -f "${MEDGEMMA_MMPROJ_PATH}" ]; then
    check_fail "mmproj file not found: ${MEDGEMMA_MMPROJ_PATH}"
    READY=false
fi

if [ "$READY" = true ]; then
    echo -e "${GREEN}✓ READY FOR TESTING${NC}"
    echo ""
    echo "To test the deployment:"
    echo "  1. Restart the service:"
    echo "     sudo systemctl restart medcontext"
    echo ""
    echo "  2. Test the health endpoint:"
    echo "     curl http://localhost:8000/health"
    echo ""
    echo "  3. Test MedGemma provider:"
    echo "     curl http://localhost:8000/api/v1/orchestrator/providers"
else
    echo -e "${RED}✗ NOT READY${NC}"
    echo ""
    echo "Missing components. Run setup:"
    echo "  ./scripts/setup_llama_cpp.sh"
fi
