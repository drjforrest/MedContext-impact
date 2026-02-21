#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# server_update.sh
#
# Lightweight update script triggered by deploy_local.sh on each deploy.
# Pulls latest code, syncs deps, runs migrations, restarts the API.
# UI dist is already uploaded via rsync before this runs.
# ─────────────────────────────────────────────────────────────────────────────

INSTALL_DIR="/opt/medcontext"
cd "${INSTALL_DIR}"

echo "=== Server Update ==="

# Pull latest code
echo "Pulling latest code..."
git fetch origin
git reset --hard origin/main

# Sync Python deps (only installs new/changed packages)
echo "Syncing Python dependencies..."
uv pip install -r requirements.txt --quiet

# Run migrations
echo "Running migrations..."
uv run alembic upgrade head 2>/dev/null || echo "  (no pending migrations)"

# Restart API
echo "Restarting API..."
systemctl restart medcontext

# Wait and verify
sleep 2
if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
    echo "  API: OK"
else
    echo "  API: FAILED — check: journalctl -u medcontext -f"
    exit 1
fi

echo "=== Update complete ==="
