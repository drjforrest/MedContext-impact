# Docker Setup Summary

This document summarizes all Docker-related files created for the MedContext project.

## 📁 Files Created

### Core Docker Configuration

#### 1. `Dockerfile` (Backend)

**Location:** Root directory  
**Purpose:** Defines the Python backend container image

**Features:**

- Based on Python 3.12-slim
- Installs system dependencies (gcc, libpq-dev)
- Copies and installs Python dependencies from `requirements.txt`
- Creates non-root user for security
- Exposes port 8000
- Includes health check
- Runs FastAPI with uvicorn

#### 2. `ui/Dockerfile` (Frontend)

**Location:** `ui/` directory  
**Purpose:** Defines the React frontend container image

**Features:**

- Multi-stage build (Node.js builder + nginx server)
- Stage 1: Builds React app with Vite
- Stage 2: Serves static files with nginx
- Includes nginx reverse proxy configuration for `/api` endpoints
- Exposes port 80

#### 3. `docker-compose.yml` (Main Orchestration)

**Location:** Root directory  
**Purpose:** Orchestrates all services for development

**Services:**

- `db`: PostgreSQL 16 database
- `backend`: FastAPI application
- `frontend`: React + nginx application

**Features:**

- Service dependencies and health checks
- Environment variable configuration
- Volume mounts for development
- Network isolation
- Database migrations on startup

### Environment Configurations

#### 4. `docker-compose.prod.yml`

**Purpose:** Production-specific overrides

**Differences from dev:**

- Removes volume mounts (uses built-in code)
- Runs 4 uvicorn workers instead of 1
- Disables hot reload
- Adds resource limits (CPU/memory)
- Enables restart policies

#### 5. `docker-compose.dev.yml`

**Purpose:** Development-specific overrides

**Features:**

- Volume mounts for hot reload
- Debug logging enabled
- Single worker with reload
- Query logging for database
- Vite dev server instead of nginx build

#### 6. `.env.docker`

**Purpose:** Environment variable template for Docker

**Contents:**

- Database URL (pre-configured for Docker network)
- MedGemma provider settings
- API keys (placeholders)
- Feature flags

### Ignore Files

#### 7. `.dockerignore` (Backend)

**Location:** Root directory  
**Purpose:** Excludes files from backend Docker context

**Excludes:**

- Python cache and build artifacts
- Node modules
- Tests and documentation
- IDE and OS files
- Git files

#### 8. `ui/.dockerignore` (Frontend)

**Location:** `ui/` directory  
**Purpose:** Excludes files from frontend Docker context

**Excludes:**

- node_modules/
- Build outputs
- IDE files
- Documentation

### Documentation

#### 9. `DOCKER.md`

**Purpose:** Comprehensive Docker deployment guide

**Sections:**

- Quick start instructions
- Service details
- Development workflow
- Production deployment
- Troubleshooting
- Performance tips

### Automation Scripts

#### 10. `Makefile`

**Purpose:** Convenient command shortcuts

**Key Commands:**

```bash
make help          # Show all commands
make build         # Build images
make up            # Start services
make dev-up        # Start with hot reload
make prod-up       # Start in production mode
make logs          # View logs
make health        # Run health check
make test          # Run tests
make clean         # Cleanup
```

#### 11. `scripts/docker_health_check.sh`

**Purpose:** Automated health check script

**Features:**

- Checks all service endpoints
- Validates database connectivity
- Scans logs for errors
- Color-coded output
- Exit codes for CI/CD

#### 12. `scripts/test_docker_setup.sh`

**Purpose:** CI/CD test script

**Features:**

- Validates docker-compose configuration
- Builds images
- Starts services
- Tests endpoints
- Automatic cleanup
- Suitable for GitHub Actions

### CI/CD

#### 13. `.github/workflows/docker-ci.yml`

**Purpose:** GitHub Actions workflow for Docker

**Jobs:**

1. **docker-test**: Builds and tests Docker setup
2. **lint-dockerfiles**: Lints Dockerfiles with hadolint
3. **security-scan**: Scans for vulnerabilities with Trivy

**Triggers:**

- Push to main/develop
- Pull requests to main/develop

## 🚀 Quick Start

### For Development

```bash
# Option 1: Using Makefile (recommended)
make dev-build
make dev-up

# Option 2: Using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### For Production

```bash
# Using Makefile
make prod-build
make prod-up

# Using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### For Testing

```bash
# Quick test
make health

# Full CI test
bash scripts/test_docker_setup.sh
```

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Docker Host                          │
│                                                              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │  Frontend   │      │   Backend   │      │  Database   │ │
│  │  (nginx)    │────▶ │  (FastAPI)  │────▶ │ (Postgres)  │ │
│  │  Port: 80   │      │  Port: 8000 │      │  Port: 5432 │ │
│  └─────────────┘      └─────────────┘      └─────────────┘ │
│        │                     │                     │         │
│        └─────────────────────┴─────────────────────┘         │
│                   medcontext-network                         │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration Matrix

| Feature         | Development | Production  |
| --------------- | ----------- | ----------- |
| Hot Reload      | ✅ Enabled  | ❌ Disabled |
| Workers         | 1           | 4           |
| Volume Mounts   | ✅ Yes      | ❌ No       |
| Resource Limits | ❌ No       | ✅ Yes      |
| Debug Logging   | ✅ Enabled  | ❌ Disabled |
| Auto-Restart    | ❌ No       | ✅ Yes      |

## 🔒 Security Features

1. **Non-root user** in backend container
2. **Health checks** for all services
3. **Network isolation** with bridge network
4. **Secret management** via environment variables
5. **Security scanning** in CI/CD (Trivy)
6. **Dockerfile linting** (hadolint)

## 📈 Performance Optimizations

1. **Multi-stage builds** (frontend)
2. **Layer caching** for dependencies
3. **Alpine base images** where applicable
4. **Resource limits** in production
5. **Connection pooling** for database
6. **Static file serving** with nginx

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**: Change ports in `docker-compose.yml`
2. **Database connection failed**: Increase wait time in backend command
3. **Frontend build failed**: Check Node version in `ui/Dockerfile`
4. **Permission denied**: Ensure non-root user has access

### Debug Commands

```bash
# View logs
make logs

# Check service status
docker-compose ps

# Access container shell
docker-compose exec backend /bin/sh

# Database shell
make db-shell

# Rebuild from scratch
make clean
make build
```

## 📝 Maintenance

### Updating Dependencies

**Backend:**

```bash
# Update requirements.txt
# Rebuild image
make docker-build
```

**Frontend:**

```bash
# Update package.json
# Rebuild image
cd ui && docker build -t medcontext-frontend .
```

### Database Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
make db-migrate
```

### Backup and Restore

```bash
# Backup database
docker-compose exec db pg_dump -U medcontext medcontext > backup.sql

# Restore database
docker-compose exec -T db psql -U medcontext medcontext < backup.sql
```

## 🎯 Best Practices

1. ✅ Use `.env` files for configuration (never commit secrets)
2. ✅ Run tests before deploying (`make test`)
3. ✅ Use health checks (`make health`)
4. ✅ Monitor logs regularly (`make logs`)
5. ✅ Keep images updated (`docker-compose pull`)
6. ✅ Clean up unused resources (`docker system prune`)

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)

## 🤝 Contributing

When adding new services:

1. Add service to `docker-compose.yml`
2. Create Dockerfile if needed
3. Update `.dockerignore`
4. Add to health check script
5. Update this documentation
6. Test with `scripts/test_docker_setup.sh`

## 📞 Support

For issues with Docker setup:

1. Check [DOCKER.md](DOCKER.md) for detailed troubleshooting
2. Run `make health` to diagnose issues
3. Check service logs: `make logs`
4. Review CI/CD workflow logs in GitHub Actions
