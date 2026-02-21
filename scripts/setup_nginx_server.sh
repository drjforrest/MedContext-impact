#!/bin/bash
# Alternative: Nginx + Let's Encrypt SSL for MedContext

set -e

echo "=== Setting up Nginx + Let's Encrypt SSL ==="

# 1. Install Nginx and Certbot
echo "Installing Nginx and Certbot..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# 2. Create Nginx configuration
echo "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/medcontext << 'EOF'
server {
    listen 80;
    server_name medcontext.drjforrest.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name medcontext.drjforrest.com;

    # SSL certificates (Certbot will fill these in)
    ssl_certificate /etc/letsencrypt/live/medcontext.drjforrest.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/medcontext.drjforrest.com/privkey.pem;

    # Security
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Logging
    access_log /var/log/nginx/medcontext_access.log;
    error_log /var/log/nginx/medcontext_error.log;

    # Frontend static files
    root /var/www/medcontext/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # API backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
    }

    # React Router - fallback to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# 3. Enable site
sudo ln -sf /etc/nginx/sites-available/medcontext /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 4. Create web root
sudo mkdir -p /var/www/medcontext/dist
sudo chown -R $USER:$USER /var/www/medcontext

# 5. Test Nginx config
sudo nginx -t

# 6. Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# 7. Open firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

echo ""
echo "=== Nginx Setup Complete ==="
echo "Next: Obtain SSL certificate..."
echo ""
echo "Run this AFTER DNS is pointing to your server:"
echo "  sudo certbot --nginx -d medcontext.drjforrest.com"
echo ""
echo "Or use the staging server first (to avoid rate limits):"
echo "  sudo certbot --nginx -d medcontext.drjforrest.com --staging"
