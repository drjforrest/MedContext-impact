.PHONY: help docker-build docker-up docker-down docker-restart docker-logs docker-test docker-clean health

# Default target
help:
	@echo "MedContext Docker Commands"
	@echo "=========================="
	@echo ""
	@echo "Setup:"
	@echo "  make docker-build    Build all Docker images"
	@echo "  make docker-up       Start all services"
	@echo "  make docker-dev      Start services in background"
	@echo "  make dev-up          Start with hot reload (development)"
	@echo "  make dev-build       Build for development mode"
	@echo ""
	@echo "Control:"
	@echo "  make docker-down     Stop all services"
	@echo "  make docker-restart  Restart all services"
	@echo "  make docker-stop     Stop without removing containers"
	@echo ""
	@echo "Monitoring:"
	@echo "  make docker-logs     View all logs (follow mode)"
	@echo "  make logs-backend    View backend logs"
	@echo "  make logs-frontend   View frontend logs"
	@echo "  make logs-db         View database logs"
	@echo "  make health          Run health check"
	@echo "  make docker-ps       Show running containers"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate      Run database migrations"
	@echo "  make db-shell        Open PostgreSQL shell"
	@echo "  make db-reset        Reset database (⚠️  destroys data)"
	@echo ""
	@echo "Testing:"
	@echo "  make docker-test     Run tests in container"
	@echo "  make test-local      Run tests locally"
	@echo ""
	@echo "Cleanup:"
	@echo "  make docker-clean    Remove containers and volumes"
	@echo "  make docker-prune    Deep clean (removes images too)"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up         Start in production mode"
	@echo "  make prod-build      Build for production"

# Build images
docker-build:
	docker-compose build

# Start services (development mode with hot reload)
docker-up:
	docker-compose up

# Start services in background
docker-dev:
	docker-compose up -d

# Start with development config (hot reload)
dev-up:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-build:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# Start with production config
prod-build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop services
docker-down:
	docker-compose down

docker-stop:
	docker-compose stop

# Restart services
docker-restart:
	docker-compose restart

# View logs
docker-logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-db:
	docker-compose logs -f db

# Show running containers
docker-ps:
	docker-compose ps

# Health check
health:
	@bash scripts/docker_health_check.sh

# Database operations
db-migrate:
	docker-compose exec backend alembic upgrade head

db-shell:
	docker-compose exec db psql -U medcontext -d medcontext

db-reset:
	@echo "⚠️  WARNING: This will destroy all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d db; \
		sleep 5; \
		docker-compose up -d backend; \
		echo "✓ Database reset complete"; \
	else \
		echo "Cancelled"; \
	fi

# Testing
docker-test:
	docker-compose exec backend pytest tests/ -v

test-local:
	uv run pytest tests/ -v

# Cleanup
docker-clean:
	docker-compose down -v

docker-prune:
	docker-compose down -v --rmi all
	docker system prune -f

# Quick commands
build: docker-build
up: docker-dev
down: docker-down
restart: docker-restart
logs: docker-logs
ps: docker-ps
test: docker-test
clean: docker-clean
