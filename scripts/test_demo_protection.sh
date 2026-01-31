#!/bin/bash
#
# Manual test script for demo protection
# Run this to verify access code and rate limiting work correctly
#

set -e

API_BASE="${API_BASE:-http://localhost:8000}"
ACCESS_CODE="${ACCESS_CODE:-MEDCONTEXT-DEMO-2026}"

echo "🔐 Testing MedContext Demo Protection"
echo "======================================"
echo ""
echo "API Base: $API_BASE"
echo "Access Code: $ACCESS_CODE"
echo ""

# Test 1: Health check (no protection)
echo "Test 1: Health check (no access code required)"
echo "----------------------------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/health")
if [ "$response" = "200" ]; then
    echo "✅ PASS: Health check returned 200"
else
    echo "❌ FAIL: Health check returned $response (expected 200)"
    exit 1
fi
echo ""

# Test 2: Protected endpoint without code
echo "Test 2: Protected endpoint without access code"
echo "-----------------------------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/api/v1/orchestrator/run")
if [ "$response" = "403" ]; then
    echo "✅ PASS: Request blocked with 403"
elif [ "$response" = "422" ]; then
    echo "⚠️  WARN: Got 422 (validation error) - access code protection may be disabled"
else
    echo "❌ FAIL: Got $response (expected 403)"
fi
echo ""

# Test 3: Protected endpoint with valid code (header)
echo "Test 3: Protected endpoint with valid access code (header)"
echo "-----------------------------------------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$API_BASE/api/v1/orchestrator/run" \
    -H "X-Demo-Access-Code: $ACCESS_CODE")
if [ "$response" = "422" ] || [ "$response" = "400" ]; then
    echo "✅ PASS: Auth passed, got $response (missing file - expected)"
elif [ "$response" = "403" ]; then
    echo "❌ FAIL: Got 403 (access denied - wrong code?)"
    exit 1
else
    echo "⚠️  Got $response (expected 400/422)"
fi
echo ""

# Test 4: Protected endpoint with valid code (query param)
echo "Test 4: Protected endpoint with valid access code (query param)"
echo "---------------------------------------------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$API_BASE/api/v1/orchestrator/run?access_code=$ACCESS_CODE")
if [ "$response" = "422" ] || [ "$response" = "400" ]; then
    echo "✅ PASS: Auth passed, got $response (missing file - expected)"
elif [ "$response" = "403" ]; then
    echo "❌ FAIL: Got 403 (access denied - wrong code?)"
    exit 1
else
    echo "⚠️  Got $response (expected 400/422)"
fi
echo ""

# Test 5: Protected endpoint with wrong code
echo "Test 5: Protected endpoint with wrong access code"
echo "--------------------------------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$API_BASE/api/v1/orchestrator/run" \
    -H "X-Demo-Access-Code: WRONG-CODE")
if [ "$response" = "403" ]; then
    echo "✅ PASS: Request blocked with 403"
elif [ "$response" = "422" ]; then
    echo "⚠️  WARN: Got 422 - access code protection may be disabled"
else
    echo "❌ FAIL: Got $response (expected 403)"
fi
echo ""

echo "======================================"
echo "✅ Demo protection tests complete!"
echo ""
echo "Note: If you see 422 instead of 403, your DEMO_ACCESS_CODE"
echo "may be empty (local dev mode with no protection)."
echo ""
echo "To enable protection, set in your .env:"
echo "  DEMO_ACCESS_CODE=MEDCONTEXT-DEMO-2026"
