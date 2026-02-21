#!/bin/bash
# Deploy MedContext Frontend to Web Server
# Run this from the medcontext/ui directory

set -e

echo "=== Deploying MedContext Frontend ==="

# 1. Build the React app
echo "Building React app..."
cd /Users/drjforrest/dev/projects/hero-counterforce/medcontext/ui
npm run build

# 2. Deploy to VPS (adjust user@host as needed)
echo "Deploying to server..."
rsync -avz --delete dist/ admin@vmi3089488.tail449a19.ts.net:/var/www/medcontext/dist/

# 3. Restart web server (if needed)
echo "Restarting web server..."
ssh admin@vmi3089488.tail449a19.ts.net "sudo systemctl restart caddy || sudo systemctl restart nginx"

echo ""
echo "=== Deployment Complete ==="
echo "Site: https://medcontext.drjforrest.com"
