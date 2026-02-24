#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# vps_quick_deploy.sh
#
# Quick deployment helper for VPS with DNS troubleshooting
# Run this FROM YOUR LOCAL MACHINE
# ─────────────────────────────────────────────────────────────────────────────

# Find repo root (works whether run from repo root or scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.git/config" ]; then
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    REPO_ROOT="$(cd "$SCRIPT_DIR" && pwd)"
fi

cd "$REPO_ROOT"

VPS_HOST="${VPS_HOST:-Contabo-admin}"
VPS_DIR="/var/www/medcontext/medcontext"

echo "=== MedContext VPS Quick Deploy ==="
echo "VPS: $VPS_HOST"
echo "Repo: $REPO_ROOT"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

step() { echo -e "${GREEN}▶${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# ── 1. Check local repo status ──────────────────────────────────────────────
step "Checking local repository..."

if [[ -n $(git status -s) ]]; then
    warn "You have uncommitted changes:"
    git status -s
    echo ""
    read -p "Commit and push? (y/n) " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
        read -p "Commit message: " commit_msg
        git commit -m "$commit_msg"
        git push origin main
    else
        echo "Continuing without commit..."
    fi
else
    echo "  Working directory clean"
fi

echo ""

# ── 2. Upload DNS fix script to VPS ──────────────────────────────────────────
step "Uploading DNS fix script to VPS..."

# Ensure scripts directory exists on VPS (ignore if exists)
ssh "$VPS_HOST" "mkdir -p $VPS_DIR/scripts" 2>/dev/null || true

# Upload the fix script
scp "$REPO_ROOT/scripts/fix_vps_dns.sh" "$VPS_HOST:$VPS_DIR/scripts/" || {
    error "Failed to upload fix script"
    echo "  Script location: $REPO_ROOT/scripts/fix_vps_dns.sh"
    exit 1
}

echo ""

# ── 3. Fix DNS on VPS ────────────────────────────────────────────────────────
step "Running DNS diagnostics and fix on VPS..."

ssh "$VPS_HOST" << 'ENDSSH'
cd /var/www/medcontext/medcontext

# Make script executable
chmod +x scripts/fix_vps_dns.sh

# Run DNS fix
echo "Running DNS diagnostics..."
sudo bash scripts/fix_vps_dns.sh

echo ""
echo "=== Testing git pull after DNS fix ==="

# Try git pull
if git pull origin main 2>&1; then
    echo "✓ Git pull successful!"
else
    echo "✗ Git pull still failing"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check git remote: git remote -v"
    echo "  2. Check SSH key: ssh -T git@github.com"
    echo "  3. Try HTTPS: git remote set-url origin https://github.com/drjforrest/MedContext-impact.git"
    exit 1
fi

ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    step "DNS fixed and git pull successful!"
    echo ""
else
    error "DNS fix failed - see output above"
    echo ""
    echo "Manual steps:"
    echo "  1. ssh $VPS_HOST"
    echo "  2. sudo bash /var/www/medcontext/medcontext/scripts/fix_vps_dns.sh"
    echo "  3. Check /etc/resolv.conf"
    exit 1
fi

# ── 4. Deploy application ────────────────────────────────────────────────────
step "Deploying application..."

ssh "$VPS_HOST" << 'ENDSSH'
set -euo pipefail
cd /var/www/medcontext/medcontext

echo ""
echo "=== Installing dependencies ==="
uv pip install -r requirements.txt

echo ""
echo "=== Running migrations ==="
uv run alembic upgrade head || echo "  (no new migrations)"

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
echo "=== Restarting services ==="
sudo systemctl restart medcontext
sudo systemctl restart caddy

echo ""
echo "=== Checking service status ==="
sleep 3

if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    echo "  Check logs: journalctl -u medcontext -n 50"
    exit 1
fi

ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo "  Site: https://medcontext.drjforrest.com"
    echo "  API:  https://medcontext.drjforrest.com/api/v1/modules"
    echo ""
    echo "  View logs: ssh $VPS_HOST 'journalctl -u medcontext -f'"
else
    error "Deployment failed - see output above"
    exit 1
fi
