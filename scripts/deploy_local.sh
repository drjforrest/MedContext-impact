#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# deploy_local.sh
#
# Run from your local machine to build, push, and deploy to the VPS.
#
# Usage:
#   ./scripts/deploy_local.sh                 # first time (includes .env)
#   ./scripts/deploy_local.sh --skip-env      # subsequent deploys
#   ./scripts/deploy_local.sh --env-only      # just push .env changes
# ─────────────────────────────────────────────────────────────────────────────

SSH_HOST="${DEPLOY_SSH_HOST:-Contabo-root}"
REMOTE_DIR="/var/www/medcontext/MedContext-impact"
REPO_URL="git@github.com:drjforrest/MedContext-impact.git"
DOMAIN="medcontext.drjforrest.com"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SKIP_ENV=false
ENV_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --skip-env) SKIP_ENV=true ;;
        --env-only) ENV_ONLY=true ;;
    esac
done

echo "=== MedContext Deploy ==="
echo "  Server: ${SSH_HOST}"
echo "  Remote: ${REMOTE_DIR}"
echo ""

# ── 1. Build UI locally ─────────────────────────────────────────────────────

if [ "$ENV_ONLY" = false ]; then
    echo "Building UI for production..."
    (cd "${PROJECT_ROOT}/ui" && VITE_API_BASE="" npm run build)
    echo ""
fi

# ── 2. Push latest code to GitHub ────────────────────────────────────────────

if [ "$ENV_ONLY" = false ]; then
    echo "Pushing to GitHub..."
    (cd "${PROJECT_ROOT}" && git push origin main)
    echo ""
fi

# ── 3. Upload .env (contains secrets — never committed) ─────────────────────

if [ "$SKIP_ENV" = false ]; then
    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        echo "ERROR: No .env file found at ${PROJECT_ROOT}/.env"
        echo "Copy .env.example to .env and fill in your secrets first."
        exit 1
    fi
    echo "Uploading .env to server..."
    scp "${PROJECT_ROOT}/.env" "${SSH_HOST}:${REMOTE_DIR}/.env"
    echo ""
fi

# ── 4. Upload pre-built UI dist (avoids installing Node on server) ──────────

if [ "$ENV_ONLY" = false ]; then
    echo "Uploading built UI..."
    rsync -avz --delete \
        "${PROJECT_ROOT}/ui/dist/" \
        "${SSH_HOST}:${REMOTE_DIR}/ui/dist/"
    echo ""
fi

# ── 5. Trigger server-side update ────────────────────────────────────────────

if [ "$ENV_ONLY" = false ]; then
    echo "Running server-side update..."
    ssh "${SSH_HOST}" "cd ${REMOTE_DIR} && bash scripts/server_update.sh"
fi

echo ""
echo "=== Deploy complete ==="
echo "  https://${DOMAIN}"
