#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# deploy_simple.sh
#
# Simple deployment using rsync (no git pull needed)
# Run from project root: ./scripts/deploy_simple.sh
# ─────────────────────────────────────────────────────────────────────────────

# Find repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

VPS_HOST="${VPS_HOST:-Contabo-admin}"
VPS_DIR="/var/www/medcontext/medcontext"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step() { echo -e "${GREEN}▶${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

echo "=== MedContext Simple Deploy ==="
echo "Local:  $REPO_ROOT"
echo "Remote: $VPS_HOST:$VPS_DIR"
echo ""

# ── 1. Sync code to VPS ──────────────────────────────────────────────────────
step "Syncing code to VPS (via rsync)..."

rsync -avz --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '.env' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'node_modules' \
  --exclude 'ui/dist' \
  --exclude 'ui/node_modules' \
  --exclude '.pytest_cache' \
  --exclude '.DS_Store' \
  "$REPO_ROOT/" "$VPS_HOST:$VPS_DIR/" || {
    error "rsync failed"
    echo ""
    echo "If you get 'No such file or directory', the VPS path might be wrong."
    echo "Run: ssh $VPS_HOST 'ls -la /var/www/medcontext/'"
    exit 1
}

step "Code synced successfully"
echo ""

# ── 2. Deploy on VPS ─────────────────────────────────────────────────────────
step "Deploying on VPS..."

ssh "$VPS_HOST" << 'ENDSSH'
set -euo pipefail

cd /var/www/medcontext/medcontext

echo ""
echo "=== Installing Python dependencies ==="
uv pip install -r requirements.txt || {
    echo "⚠ uv install failed, trying pip..."
    source .venv/bin/activate
    pip install -r requirements.txt
}

echo ""
echo "=== Running database migrations ==="
uv run alembic upgrade head || echo "  (no new migrations)"

echo ""
echo "=== Building frontend ==="
cd ui
npm install --silent
# Explicitly clear VITE_API_BASE so the production build uses relative URLs
# (Caddy proxies /api/* to uvicorn). Never bake in localhost:8000.
VITE_API_BASE= npm run build

echo ""
echo "=== Deploying frontend to web root ==="
sudo cp -r dist/* /var/www/medcontext/dist/
sudo chown -R caddy:caddy /var/www/medcontext/dist/

echo ""
echo "=== Restarting backend service ==="
sudo systemctl restart medcontext

# Wait for backend
echo "Waiting for backend to start..."
for i in {1..10}; do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    if [[ $i -eq 10 ]]; then
        echo "❌ Backend failed to start"
        echo ""
        echo "Check logs: journalctl -u medcontext -n 50"
        exit 1
    fi
    sleep 2
done

echo ""
echo "=== Restarting Caddy ==="
sudo systemctl restart caddy

ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo "  Frontend: https://medcontext.drjforrest.com"
    echo "  Backend:  https://medcontext.drjforrest.com/api/v1/modules"
    echo ""
    echo "  View logs: ssh $VPS_HOST 'journalctl -u medcontext -f'"
    echo ""
else
    error "Deployment failed"
    echo ""
    echo "SSH into VPS to debug:"
    echo "  ssh $VPS_HOST"
    echo "  cd /var/www/medcontext/medcontext"
    echo "  journalctl -u medcontext -n 50"
    exit 1
fi
