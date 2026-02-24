#!/usr/bin/env bash
# Quick script to check VPS directory structure

VPS_HOST="${VPS_HOST:-Contabo-admin}"

echo "=== Checking VPS Directory Structure ==="
echo ""

ssh "$VPS_HOST" << 'ENDSSH'
echo "Contents of /var/www/medcontext:"
ls -la /var/www/medcontext/ 2>/dev/null || echo "Directory doesn't exist"

echo ""
echo "Looking for git repositories:"
find /var/www/medcontext -maxdepth 2 -type d -name ".git" 2>/dev/null | sed 's|/.git||' || echo "No git repos found"

echo ""
echo "Looking for medcontext directories:"
find /var/www -maxdepth 3 -type d -name "*medcontext*" -o -name "*MedContext*" 2>/dev/null || echo "None found"
ENDSSH

echo ""
echo "Based on the output above, we'll determine the correct path."
