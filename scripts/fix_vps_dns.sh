#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# fix_vps_dns.sh
#
# Diagnose and fix DNS resolution issues on VPS
# Run this script ON THE VPS SERVER
# ─────────────────────────────────────────────────────────────────────────────

echo "=== MedContext VPS DNS Diagnostics & Fix ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() { echo -e "${GREEN}✓${NC} $1"; }
check_fail() { echo -e "${RED}✗${NC} $1"; }
check_warn() { echo -e "${YELLOW}!${NC} $1"; }

# ── 1. Check current DNS configuration ──────────────────────────────────────
echo "1. Checking DNS configuration..."
echo ""

if [ -f /etc/resolv.conf ]; then
    echo "Current /etc/resolv.conf:"
    cat /etc/resolv.conf | grep -v '^#' | grep -v '^$'
    echo ""
else
    check_fail "/etc/resolv.conf not found"
fi

# ── 2. Test DNS resolution ──────────────────────────────────────────────────
echo "2. Testing DNS resolution..."
echo ""

# Test common domains
DOMAINS=("github.com" "google.com" "api.openai.com" "pypi.org")
DNS_WORKING=true

for domain in "${DOMAINS[@]}"; do
    if nslookup "$domain" >/dev/null 2>&1; then
        check_pass "Can resolve $domain"
    else
        check_fail "Cannot resolve $domain"
        DNS_WORKING=false
    fi
done

echo ""

# ── 3. Check network connectivity ───────────────────────────────────────────
echo "3. Testing network connectivity..."
echo ""

if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    check_pass "Can reach 8.8.8.8 (Google DNS)"
else
    check_fail "Cannot reach 8.8.8.8"
fi

if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1; then
    check_pass "Can reach 1.1.1.1 (Cloudflare DNS)"
else
    check_fail "Cannot reach 1.1.1.1"
fi

echo ""

# ── 4. Check if systemd-resolved is running ─────────────────────────────────
echo "4. Checking systemd-resolved..."
echo ""

if systemctl is-active --quiet systemd-resolved; then
    check_pass "systemd-resolved is active"
    echo "  Status:"
    systemctl status systemd-resolved --no-pager | head -5
    echo ""
else
    check_warn "systemd-resolved is not active"
fi

# ── 5. Fix DNS if needed ────────────────────────────────────────────────────
if [ "$DNS_WORKING" = false ]; then
    echo ""
    echo "=== DNS Resolution Failed - Applying Fix ==="
    echo ""

    # Backup current config
    if [ -f /etc/resolv.conf ]; then
        cp /etc/resolv.conf /etc/resolv.conf.backup.$(date +%Y%m%d_%H%M%S)
        check_pass "Backed up /etc/resolv.conf"
    fi

    # Method 1: Update /etc/resolv.conf directly
    echo "Applying DNS fix (Google DNS + Cloudflare DNS)..."

    cat > /etc/resolv.conf.new <<EOF
# MedContext VPS - Fixed DNS configuration
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
nameserver 1.0.0.1
options timeout:2 attempts:3 rotate
EOF

    # Check if resolv.conf is a symlink (systemd-resolved)
    if [ -L /etc/resolv.conf ]; then
        check_warn "/etc/resolv.conf is a symlink (systemd-resolved)"
        echo "  Removing symlink and creating regular file..."
        rm /etc/resolv.conf
        cp /etc/resolv.conf.new /etc/resolv.conf
    else
        mv /etc/resolv.conf.new /etc/resolv.conf
    fi

    chmod 644 /etc/resolv.conf
    check_pass "Updated /etc/resolv.conf"

    # Method 2: Configure systemd-resolved if it's running
    if systemctl is-active --quiet systemd-resolved; then
        echo ""
        echo "Configuring systemd-resolved..."

        mkdir -p /etc/systemd/resolved.conf.d/
        cat > /etc/systemd/resolved.conf.d/dns.conf <<EOF
[Resolve]
DNS=8.8.8.8 8.8.4.4 1.1.1.1 1.0.0.1
FallbackDNS=1.1.1.1 1.0.0.1
DNSStubListener=yes
EOF

        systemctl restart systemd-resolved
        check_pass "Restarted systemd-resolved"
    fi

    # Test again
    echo ""
    echo "Testing DNS resolution after fix..."
    sleep 2

    ALL_OK=true
    for domain in "${DOMAINS[@]}"; do
        if nslookup "$domain" >/dev/null 2>&1; then
            check_pass "Can now resolve $domain"
        else
            check_fail "Still cannot resolve $domain"
            ALL_OK=false
        fi
    done

    if [ "$ALL_OK" = true ]; then
        echo ""
        echo -e "${GREEN}=== DNS Fixed Successfully ===${NC}"
        echo ""
    else
        echo ""
        echo -e "${RED}=== DNS Still Not Working ===${NC}"
        echo ""
        echo "Additional troubleshooting steps:"
        echo "  1. Check firewall rules: iptables -L"
        echo "  2. Check if DNS ports are blocked: telnet 8.8.8.8 53"
        echo "  3. Contact your VPS provider about DNS issues"
        echo "  4. Check /var/log/syslog for errors"
        exit 1
    fi
fi

# ── 6. Test git connectivity ────────────────────────────────────────────────
echo ""
echo "6. Testing git connectivity..."
echo ""

# Add GitHub to known_hosts if not already present
if ! grep -q "github.com" ~/.ssh/known_hosts 2>/dev/null; then
    echo "Adding GitHub to known_hosts..."
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
fi

# Test SSH with timeout to avoid hanging
if timeout 5 ssh -T -o "StrictHostKeyChecking=no" git@github.com 2>&1 | grep -q "successfully authenticated\|Hi "; then
    check_pass "GitHub SSH authentication working"
else
    check_warn "GitHub SSH authentication may have issues (this is OK if using HTTPS)"
    echo "  Try manually: ssh -T git@github.com"
fi

# Test HTTPS git access
if timeout 5 git ls-remote https://github.com/git/git.git HEAD >/dev/null 2>&1; then
    check_pass "GitHub HTTPS access working"
else
    check_warn "GitHub HTTPS access may have issues"
fi

echo ""

# ── 7. Summary and recommendations ──────────────────────────────────────────
echo "=== Summary ==="
echo ""

if [ "$DNS_WORKING" = true ]; then
    echo -e "${GREEN}✓ DNS is working correctly${NC}"
    echo ""
    echo "You can now run git pull:"
    echo "  cd /var/www/medcontext/medcontext"
    echo "  git pull origin main"
else
    echo "Run this script with sudo if DNS issues persist:"
    echo "  sudo bash scripts/fix_vps_dns.sh"
fi

echo ""
echo "To complete deployment:"
echo "  1. cd /var/www/medcontext/medcontext"
echo "  2. git pull origin main"
echo "  3. ./scripts/deploy_to_vps.sh"
echo ""
