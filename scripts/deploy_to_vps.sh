#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# deploy_to_vps.sh
#
# Deploy backend + frontend changes to VPS
# ─────────────────────────────────────────────────────────────────────────────

echo "=== MedContext VPS Deployment ==="
echo ""

# Configuration
VPS_HOST="${VPS_HOST:-admin@vmi3089488}"
VPS_DIR="/var/www/medcontext/medcontext"
WEB_ROOT="/var/www/medcontext/dist"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

step() {
    echo -e "${GREEN}▶${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ── 1. Commit and push changes ───────────────────────────────────────────────
step "Checking for uncommitted changes..."
if [[ -n $(git status -s) ]]; then
    warn "You have uncommitted changes. Commit them first:"
    git status -s
    echo ""
    read -p "Commit now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        read -p "Commit message: " commit_msg
        git commit -m "$commit_msg"
        git push origin main
        step "Changes committed and pushed!"
    else
        echo "Aborting deployment."
        exit 1
    fi
else
    step "Working directory clean. Pushing to remote..."
    git push origin main
fi

# ── 2. Deploy to VPS ─────────────────────────────────────────────────────────
step "Connecting to VPS and deploying..."

ssh $VPS_HOST << 'ENDSSH'
set -euo pipefail

echo ""
echo "=== On VPS: Pulling latest code ==="
cd /var/www/medcontext/medcontext
git pull origin main

echo ""
echo "=== Restarting backend ==="
pkill -f uvicorn || true
sleep 2
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir src > logs/uvicorn.log 2>&1 &
echo "Backend restarted (PID: $!)"

sleep 3

# Test backend health
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

echo ""
echo "=== Building frontend ==="
cd ui
npm install --silent
npm run build

echo ""
echo "=== Deploying frontend ==="
sudo cp -r dist/* /var/www/medcontext/dist/
sudo chown -R caddy:caddy /var/www/medcontext/dist/

echo ""
echo "✅ Deployment complete!"
ENDSSH

# ── 3. Test deployment ───────────────────────────────────────────────────────
step "Testing deployment..."

echo ""
echo "Backend API:"
ssh $VPS_HOST "curl -s http://localhost:8000/api/v1/orchestrator/providers | python3 -m json.tool | head -20"

echo ""
echo "=== Deployment Summary ==="
echo "  Backend: http://localhost:8000"
echo "  Frontend: https://medcontext.drjforrest.com"
echo ""
echo "Test in browser: https://medcontext.drjforrest.com"
echo ""
