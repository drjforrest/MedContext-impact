#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# deploy_frontend.sh
#
# Build frontend locally and rsync to VPS.
# Use this when you only need to update the UI (faster than full deploy).
# ─────────────────────────────────────────────────────────────────────────────

VPS_HOST="${VPS_HOST:-Contabo-admin}"
VPS_DIST="/var/www/medcontext/dist"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UI_DIR="$REPO_ROOT/ui"

echo "=== MedContext Frontend Deploy ==="
echo ""
echo "  Host: $VPS_HOST"
echo "  Target: $VPS_DIST"
echo ""

# Build
echo "▶ Building frontend..."
cd "$UI_DIR"
npm run build

# Make dist writable on VPS (admin may not own it)
echo "▶ Preparing remote dist..."
ssh $VPS_HOST "sudo chown -R admin:admin $VPS_DIST 2>/dev/null || sudo mkdir -p $VPS_DIST && sudo chown -R admin:admin $VPS_DIST"

# Rsync
echo "▶ Syncing to VPS..."
rsync -avz --delete "$UI_DIR/dist/" "$VPS_HOST:$VPS_DIST/"

# Restore ownership for Caddy
echo "▶ Setting ownership for Caddy..."
ssh $VPS_HOST "sudo chown -R caddy:caddy $VPS_DIST"

echo ""
echo "✅ Frontend deployed to https://medcontext.drjforrest.com"
echo "   (Hard refresh: Cmd+Shift+R / Ctrl+Shift+R if you don't see changes)"
echo ""
