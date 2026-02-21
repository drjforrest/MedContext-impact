#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

# ─────────────────────────────────────────────────────────────────────────────
# server_setup.sh
#
# One-time setup on a fresh Ubuntu/Debian VPS.
# Run as root or with sudo.
#
# What this does:
#   1. Installs system deps (Python 3.12, uv, Caddy, PostgreSQL)
#   2. Creates deploy SSH key for private GitHub repo
#   3. Clones the repo
#   4. Installs Python deps
#   5. Configures Caddy reverse proxy + static file serving
#   6. Creates systemd service for the API
#   7. Runs DB migrations
#   8. Starts everything
#
# Prerequisites:
#   - Ubuntu 22.04+ or Debian 12+
#   - DNS for medcontext.drjforrest.com pointing to this server
#   - .env file uploaded to /opt/medcontext/.env (via deploy_local.sh)
#
# Usage:
#   curl -sSL <raw-url> | bash        # or
#   bash scripts/server_setup.sh
# ─────────────────────────────────────────────────────────────────────────────

DOMAIN="medcontext.drjforrest.com"
REPO_URL="git@github.com:drjforrest/MedContext-impact.git"
INSTALL_DIR="/var/www/medcontext/MedContext-impact"
SERVICE_USER="medcontext"

echo "=== MedContext Server Setup ==="
echo "  Domain:  ${DOMAIN}"
echo "  Install: ${INSTALL_DIR}"
echo ""

# ── 0. Must be root ─────────────────────────────────────────────────────────

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run as root or with sudo."
    exit 1
fi

# ── 1. System packages ──────────────────────────────────────────────────────

echo "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3.12 python3.12-venv python3.12-dev \
    build-essential git curl wget \
    postgresql postgresql-contrib \
    libpq-dev

# Install uv (Python package manager)
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Caddy (if not already present)
if ! command -v caddy &>/dev/null; then
    echo "Installing Caddy..."
    apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
        gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
        tee /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -qq
    apt-get install -y -qq caddy
fi

# ── 2. Create service user ──────────────────────────────────────────────────

if ! id "${SERVICE_USER}" &>/dev/null; then
    echo "Creating service user: ${SERVICE_USER}"
    useradd --system --shell /bin/bash --home-dir "${INSTALL_DIR}" "${SERVICE_USER}"
fi

# ── 3. GitHub deploy key ────────────────────────────────────────────────────

KEY_FILE="/root/.ssh/medcontext_deploy_key"
if [ ! -f "${KEY_FILE}" ]; then
    echo ""
    echo "Generating deploy key for GitHub..."
    ssh-keygen -t ed25519 -f "${KEY_FILE}" -N "" -C "medcontext-deploy@${DOMAIN}"
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║  ADD THIS DEPLOY KEY TO YOUR GITHUB REPO                       ║"
    echo "║                                                                ║"
    echo "║  1. Go to: https://github.com/drjforrest/MedContext-impact     ║"
    echo "║  2. Settings → Deploy keys → Add deploy key                    ║"
    echo "║  3. Title: medcontext-vps                                      ║"
    echo "║  4. Paste the key below (read-only is fine):                   ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    cat "${KEY_FILE}.pub"
    echo ""
    read -rp "Press Enter after adding the key to GitHub..."
fi

# Configure SSH to use the deploy key for github.com
if ! grep -q "medcontext_deploy_key" /root/.ssh/config 2>/dev/null; then
    cat >> /root/.ssh/config <<SSHEOF

Host github.com
    HostName github.com
    IdentityFile ${KEY_FILE}
    IdentitiesOnly yes
SSHEOF
    chmod 600 /root/.ssh/config
fi

# ── 4. Clone or update repo ─────────────────────────────────────────────────

cd "${INSTALL_DIR}"
if [ -d ".git" ]; then
    echo "Updating existing repo..."
    git fetch origin
    git reset --hard origin/main
elif [ "$(ls -A "${INSTALL_DIR}" 2>/dev/null)" ]; then
    echo "Directory exists but is not a git repo. Initializing..."
    git init
    git remote add origin "${REPO_URL}"
    git fetch origin
    git reset --hard origin/main
else
    echo "Cloning repo..."
    git clone "${REPO_URL}" "${INSTALL_DIR}"
    cd "${INSTALL_DIR}"
fi

# ── 5. Python environment ───────────────────────────────────────────────────

echo "Setting up Python environment..."
cd "${INSTALL_DIR}"
uv venv --python 3.12
uv pip install -r requirements.txt

# ── 6. PostgreSQL database ───────────────────────────────────────────────────

echo "Setting up PostgreSQL..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='medcontext'" | grep -q 1; then
    sudo -u postgres psql <<SQLEOF
CREATE USER medcontext WITH PASSWORD 'medcontext';
CREATE DATABASE medcontext OWNER medcontext;
GRANT ALL PRIVILEGES ON DATABASE medcontext TO medcontext;
SQLEOF
    echo "  Created database: medcontext"
else
    echo "  Database already exists."
fi

# ── 7. Run migrations ───────────────────────────────────────────────────────

echo "Running database migrations..."
cd "${INSTALL_DIR}"
uv run alembic upgrade head || echo "  (migrations skipped or already current)"

# ── 8. Caddy config ─────────────────────────────────────────────────────────

echo "Configuring Caddy..."
cat > /etc/caddy/Caddyfile <<CADDYEOF
${DOMAIN} {
    # API — reverse proxy to uvicorn
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle /health {
        reverse_proxy localhost:8000
    }

    # Static UI files
    handle {
        root * ${INSTALL_DIR}/ui/dist
        try_files {path} /index.html
        file_server
    }

    # Security headers
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
    }

    # Gzip compression
    encode gzip
}
CADDYEOF

# ── 9. Systemd service for the API ──────────────────────────────────────────

echo "Creating systemd service..."
cat > /etc/systemd/system/medcontext.service <<UNITEOF
[Unit]
Description=MedContext API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=root
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/.venv/bin/uvicorn app.main:app \\
    --host 127.0.0.1 \\
    --port 8000 \\
    --app-dir src \\
    --workers 2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNITEOF

# ── 10. Start services ──────────────────────────────────────────────────────

echo "Starting services..."
systemctl daemon-reload
systemctl enable --now medcontext
systemctl restart medcontext
systemctl restart caddy

# ── 11. Verify ───────────────────────────────────────────────────────────────

echo ""
echo "Waiting for API to start..."
sleep 3

if curl -sf "http://localhost:8000/health" > /dev/null 2>&1; then
    echo "  API:   OK (http://localhost:8000/health)"
else
    echo "  API:   FAILED — check: journalctl -u medcontext -f"
fi

if curl -sf "https://${DOMAIN}/health" > /dev/null 2>&1; then
    echo "  Caddy: OK (https://${DOMAIN}/health)"
else
    echo "  Caddy: FAILED — check: journalctl -u caddy -f"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "  Site:    https://${DOMAIN}"
echo "  API:     https://${DOMAIN}/api/v1/modules"
echo "  Logs:    journalctl -u medcontext -f"
echo "  Caddy:   journalctl -u caddy -f"
echo ""
echo "  Next steps:"
echo "    1. Upload .env:  scp .env root@${DOMAIN}:${INSTALL_DIR}/.env"
echo "    2. Upload UI:    rsync -avz ui/dist/ root@${DOMAIN}:${INSTALL_DIR}/ui/dist/"
echo "    3. Restart:      systemctl restart medcontext"
