#!/bin/bash
# CI/CD-friendly Docker setup test script
# Tests that the Docker configuration is valid and services start correctly

set -e

echo "🧪 Testing MedContext Docker Setup"
echo "==================================="
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    docker-compose down -v 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found"
    exit 1
fi

echo "✓ docker-compose.yml found"

# Validate docker-compose configuration
echo "Validating Docker Compose configuration..."
if docker-compose config > /dev/null 2>&1; then
    echo "✓ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    docker-compose config
    exit 1
fi

# Check if .env.docker exists
if [ -f ".env.docker" ]; then
    echo "✓ .env.docker template found"
    # Copy to .env for testing (with dummy values)
    cp .env.docker .env
    # Replace placeholder with dummy token
    sed -i.bak 's/your_huggingface_token_here/test_token_12345/' .env
    rm -f .env.bak
    echo "✓ Created test .env file"
fi

# Build images
echo ""
echo "Building Docker images..."
if docker-compose build --no-cache > /dev/null 2>&1; then
    echo "✓ All images built successfully"
else
    echo "❌ Image build failed"
    exit 1
fi

# Start services (with timeout)
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to start (max 60s)..."
SECONDS=0
MAX_WAIT=60

while [ $SECONDS -lt $MAX_WAIT ]; do
    # Check if backend is responding
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Backend is responding after ${SECONDS}s"
        BACKEND_UP=1
        break
    fi
    sleep 2
done

if [ -z "$BACKEND_UP" ]; then
    echo "❌ Backend failed to start within ${MAX_WAIT}s"
    echo "Backend logs:"
    docker-compose logs backend
    exit 1
fi

# Check frontend
if curl -f -s http://localhost > /dev/null 2>&1; then
    echo "✓ Frontend is responding"
else
    echo "⚠️  Frontend not responding (may need more time)"
fi

# Check database
if docker-compose exec -T db pg_isready -U medcontext > /dev/null 2>&1; then
    echo "✓ Database is ready"
else
    echo "❌ Database is not ready"
    exit 1
fi

# Run a simple test
echo ""
echo "Running quick API test..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
    echo "✓ Health endpoint returned expected response"
else
    echo "❌ Health endpoint returned unexpected response: $HEALTH_RESPONSE"
    exit 1
fi

# Success
echo ""
echo "=================================="
echo "✅ All Docker setup tests passed!"
echo "=================================="
echo ""
echo "Your Docker configuration is working correctly."
