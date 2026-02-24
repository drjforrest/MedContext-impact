# VPS Deployment Troubleshooting Guide

## Quick Fix: DNS Resolution Issues

If you're experiencing DNS resolution issues on your VPS (can't git pull, can't reach external APIs, etc.), follow these steps:

### Option 1: Automated Fix (Recommended)

**From your local machine:**

```bash
./scripts/vps_quick_deploy.sh
```

This script will:
1. Upload the DNS fix script to your VPS
2. Run DNS diagnostics and apply fixes
3. Test git connectivity
4. Deploy your application

### Option 2: Manual Fix

**Step 1: SSH into your VPS**

```bash
ssh Contabo-admin
# or
ssh root@your-vps-ip
```

**Step 2: Run DNS diagnostics**

```bash
cd /var/www/medcontext/medcontext
sudo bash scripts/fix_vps_dns.sh
```

This will:
- Check current DNS configuration
- Test DNS resolution for common domains
- Apply fixes if needed (updates `/etc/resolv.conf`)
- Configure systemd-resolved if applicable

**Step 3: Test git pull**

```bash
cd /var/www/medcontext/medcontext
git pull origin main
```

If git pull still fails, check:

```bash
# Test GitHub SSH
ssh -T git@github.com

# Check git remote
git remote -v

# Try switching to HTTPS if SSH fails
git remote set-url origin https://github.com/drjforrest/MedContext-impact.git
```

## Common DNS Issues and Solutions

### Issue 1: `/etc/resolv.conf` is Empty or Has Invalid Nameservers

**Fix:**

```bash
sudo tee /etc/resolv.conf > /dev/null <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
nameserver 1.0.0.1
EOF
```

### Issue 2: systemd-resolved Overwriting `/etc/resolv.conf`

**Fix:**

```bash
# Configure systemd-resolved
sudo mkdir -p /etc/systemd/resolved.conf.d/
sudo tee /etc/systemd/resolved.conf.d/dns.conf > /dev/null <<EOF
[Resolve]
DNS=8.8.8.8 8.8.4.4 1.1.1.1 1.0.0.1
FallbackDNS=1.1.1.1 1.0.0.1
DNSStubListener=yes
EOF

sudo systemctl restart systemd-resolved
```

### Issue 3: Firewall Blocking DNS (Port 53)

**Check:**

```bash
sudo iptables -L -n -v | grep 53
```

**Fix:**

```bash
sudo iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
sudo iptables -A INPUT -p udp --sport 53 -j ACCEPT
```

### Issue 4: VPS Provider DNS Restrictions

Some VPS providers (Contabo, OVH, etc.) may restrict DNS. Contact support or:

```bash
# Use provider's DNS servers
# For Contabo:
nameserver 213.239.242.238
nameserver 213.239.242.206
```

## Testing DNS Resolution

```bash
# Test DNS lookup
nslookup github.com
nslookup google.com

# Test with dig
dig github.com

# Test with ping
ping -c 3 8.8.8.8
ping -c 3 github.com
```

## After DNS is Fixed

### Deploy Application

```bash
cd /var/www/medcontext/medcontext

# Pull latest code
git pull origin main

# Install dependencies
uv pip install -r requirements.txt

# Run migrations
uv run alembic upgrade head

# Build frontend
cd ui
npm install
npm run build

# Deploy frontend
sudo cp -r dist/* /var/www/medcontext/dist/
sudo chown -R caddy:caddy /var/www/medcontext/dist/

# Restart services
sudo systemctl restart medcontext
sudo systemctl restart caddy

# Check health
curl http://localhost:8000/health
```

### Check Logs

```bash
# Backend logs
journalctl -u medcontext -f

# Caddy logs
journalctl -u caddy -f

# System logs
tail -f /var/log/syslog
```

## Deployment Checklist

- [ ] DNS resolution working (`nslookup github.com`)
- [ ] Git pull successful
- [ ] Dependencies installed
- [ ] Database migrations run
- [ ] Frontend built and deployed
- [ ] Backend service running (`systemctl status medcontext`)
- [ ] Caddy reverse proxy running (`systemctl status caddy`)
- [ ] Health endpoint responding (`curl http://localhost:8000/health`)
- [ ] Frontend accessible (https://medcontext.drjforrest.com)

## Emergency Rollback

If deployment fails:

```bash
# Rollback git
cd /var/www/medcontext/medcontext
git reset --hard HEAD~1

# Restart services
sudo systemctl restart medcontext
sudo systemctl restart caddy
```

## Contact Information

If issues persist:
1. Check VPS provider status page
2. Contact VPS support about DNS/network issues
3. Review deployment logs for specific errors
4. Open an issue in the GitHub repo

## Automated Deployment Script

For future deployments without issues:

```bash
# From local machine
./scripts/deploy_to_vps.sh
```

This handles:
- Code sync via rsync
- Dependency installation
- Frontend build
- Service restart
- Health checks
