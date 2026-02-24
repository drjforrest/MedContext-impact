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
VPS_HOST="${VPS_HOST:-Contabo-admin}"
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
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" != "main" ]]; then
    warn "You are on branch '$BRANCH', not 'main'. Deploy pushes to main."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || { echo "Aborting."; exit 1; }
fi

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
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
step "Ensuring target directory exists on VPS..."
# Remove if not a directory (handles file, symlink, broken symlink)
ssh $VPS_HOST "if [ ! -d $VPS_DIR ]; then rm -rf $VPS_DIR 2>/dev/null; fi; mkdir -p $VPS_DIR"

step "Syncing code to VPS..."

rsync -avz --delete \
  --exclude '.git' \
  --exclude-from="$REPO_ROOT/.gitignore" \
  "$REPO_ROOT/" "$VPS_HOST:$VPS_DIR/"

step "Connecting to VPS and deploying..."

ssh $VPS_HOST << 'ENDSSH'
set -euo pipefail

cd /var/www/medcontext/medcontext

# Fix systemd service if it references old MedContext-impact path
if grep -q MedContext-impact /etc/systemd/system/medcontext.service 2>/dev/null; then
    echo "Updating medcontext.service to use /var/www/medcontext/medcontext..."
    sudo sed -i 's|MedContext-impact|medcontext|g' /etc/systemd/system/medcontext.service
    sudo systemctl daemon-reload
fi

echo ""
echo "=== Restarting backend ==="
sudo systemctl restart medcontext

# Wait for backend to come up
for i in {1..10}; do
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        echo "✅ Backend is healthy"
        break
    fi
    if [[ $i -eq 10 ]]; then
        echo "❌ Backend health check failed after 10 attempts"
        echo ""
        echo "=== Service status ==="
        sudo systemctl status medcontext --no-pager || true
        echo ""
        echo "=== Recent logs ==="
        sudo journalctl -u medcontext -n 30 --no-pager || true
        exit 1
    fi
    echo "Waiting for backend to start (attempt $i/10)..."
    sleep 2
done

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
