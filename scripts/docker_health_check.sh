#!/bin/bash
# Health check script for MedContext Docker deployment

set -e

echo "🏥 MedContext Docker Health Check"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local service=$1
    local url=$2
    
    echo -n "Checking $service... "
    
    if curl -f -s -o /dev/null "$url"; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Check if Docker Compose is running
echo "📦 Checking Docker containers..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Docker Compose is running${NC}"
else
    echo -e "${RED}✗ Docker Compose is not running${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi
echo ""

# Check individual services
echo "🔍 Testing service endpoints..."
check_service "Backend API" "http://localhost:8000/health" || BACKEND_FAIL=1
check_service "Frontend" "http://localhost" || FRONTEND_FAIL=1
check_service "API Docs" "http://localhost:8000/docs" || DOCS_FAIL=1
echo ""

# Check database connection
echo "💾 Checking database..."
if docker-compose exec -T db pg_isready -U medcontext > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not ready${NC}"
    DB_FAIL=1
fi
echo ""

# Check logs for errors
echo "📋 Checking recent logs for errors..."
if docker-compose logs --tail=50 backend | grep -i "error" > /dev/null; then
    echo -e "${YELLOW}⚠ Found errors in backend logs${NC}"
    echo "View with: docker-compose logs backend"
else
    echo -e "${GREEN}✓ No recent errors in backend logs${NC}"
fi
echo ""

# Summary
echo "=================================="
if [[ -z "$BACKEND_FAIL" && -z "$FRONTEND_FAIL" && -z "$DB_FAIL" ]]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    echo ""
    echo "Access your services at:"
    echo "  • Frontend:  http://localhost"
    echo "  • Backend:   http://localhost:8000"
    echo "  • API Docs:  http://localhost:8000/docs"
    exit 0
else
    echo -e "${RED}✗ Some services are not healthy${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Restart:   docker-compose restart"
    echo "  • Rebuild:   docker-compose up --build"
    exit 1
fi
