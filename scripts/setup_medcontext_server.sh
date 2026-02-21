#!/bin/bash
# Complete Web Server + SSL Setup for MedContext
# Using Caddy (auto HTTPS) + MedContext backend

set -e

echo "=== Setting up Caddy Web Server with Auto SSL ==="

# 1. Install Caddy
echo "Installing Caddy..."
sudo apt update
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy

# 2. Create Caddyfile
echo "Creating Caddy configuration..."
sudo tee /etc/caddy/Caddyfile << 'EOF'
medcontext.drjforrest.com {
    # Enable logging
    log {
        output file /var/log/caddy/access.log
        format json
    }

    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Frontend static files (React build)
    root * /var/www/medcontext/dist
    
    # Try files, fallback to index.html (for React Router)
    try_files {path} {path}/ /index.html

    # Enable gzip compression
    encode gzip

    # File server for static assets
    file_server

    # API backend (MedContext FastAPI)
    handle /api/* {
        reverse_proxy localhost:8000
    }

    # Health check endpoint
    handle /health {
        reverse_proxy localhost:8000
    }
}
EOF

# 3. Create web root directory
echo "Creating web root..."
sudo mkdir -p /var/www/medcontext/dist
sudo chown -R caddy:caddy /var/www/medcontext

# 4. Set up log directory
sudo mkdir -p /var/log/caddy
sudo chown -R caddy:caddy /var/log/caddy

# 5. Start and enable Caddy
echo "Starting Caddy..."
sudo systemctl enable caddy
sudo systemctl restart caddy

# 6. Open firewall ports
echo "Configuring firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

echo ""
echo "=== Setup Complete ==="
echo "Web root: /var/www/medcontext/dist"
echo "Logs: /var/log/caddy/access.log"
echo "Config: /etc/caddy/Caddyfile"
echo ""
echo "Next steps:"
echo "1. Ensure DNS medcontext.drjforrest.com points to this server"
echo "2. Deploy your React app to /var/www/medcontext/dist"
echo "3. Start your MedContext backend on localhost:8000"
echo "4. SSL certificate will be automatically obtained on first request"
echo ""
echo "Check status: sudo systemctl status caddy"
echo "Test config: sudo caddy validate --config /etc/caddy/Caddyfile"
