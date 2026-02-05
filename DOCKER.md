# Docker Deployment Guide

This guide explains how to run MedContext using Docker containers.

## Quick Start

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- `.env` file with required environment variables

### Makefile Shortcuts (Recommended)

For convenience, use the provided Makefile commands:

# - Port 8000 already in usebash

# View all available commands

make help

# Build and start services

make build
make up

# View logs

make logs

# Run health check

make health

# Stop services

make down

````

### Manual Docker Compose Commands

### 1. Configure Environment

Copy the example environment file and fill in your credentials:

Edit `.env` and set at minimum:

- `MEDGEMMA_HF_TOKEN` - Your HuggingFace token (or other provider credentials)
- `MEDGEMMA_PROVIDER` - Choose: `huggingface`, `vertex`, `local`, or `vllm`

### 2. Build and Run

Build and start all services (database, backend, frontend):

```bash
docker-compose up --build
````

Or run in detached mode:

```bash
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

### 4. Check Service Health

View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

Check running containers:

```bash
docker-compose ps
```

### 5. Stop Services

```bash
# Stop but keep containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

## Service Details

### Backend (FastAPI)

- **Container**: `medcontext-backend`
- **Port**: 8000
- **Image**: Built from root `Dockerfile`
- **Health check**: `/health` endpoint
- **Auto-reload**: Enabled in development mode

### Frontend (React + Nginx)

- **Container**: `medcontext-frontend`
- **Port**: 80
- **Image**: Built from `ui/Dockerfile`
- **Multi-stage build**: Node.js builder + Nginx server
- **API Proxy**: `/api/*` requests proxied to backend

### Database (PostgreSQL)

- **Container**: `medcontext-db`
- **Port**: 5432
- **Version**: PostgreSQL 16 Alpine
- **Credentials**: See `docker-compose.yml` (change for production!)
- **Data persistence**: `postgres_data` volume

## Development Workflow

### Running Individual Services

Backend only:

```bash
docker-compose up backend
```

Frontend only:

```bash
docker-compose up frontend
```

### Database Migrations

Migrations run automatically on backend startup. To run manually:

```bash
docker-compose exec backend alembic upgrade head
```

Create a new migration:

```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Rebuild After Code Changes

Backend (with hot reload, no rebuild needed):

```bash
docker-compose restart backend
```

Frontend (requires rebuild):

```bash
docker-compose up --build frontend
```

### Access Container Shell

```bash
# Backend
docker-compose exec backend /bin/sh

# Database
docker-compose exec db psql -U medcontext -d medcontext

# Frontend
docker-compose exec frontend /bin/sh
```

## Production Deployment

### Security Considerations

1. **Change default credentials** in `docker-compose.yml`:

   - Database password
   - Add secrets management

2. **Use environment-specific files**:

   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
   ```

3. **Enable SSL/TLS**:

   - Add reverse proxy (nginx/traefik) with certificates
   - Update frontend nginx config

4. **Set resource limits**:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: "2"
         memory: 4G
   ```

### Production Dockerfile Optimization

For production, consider:

1. **Multi-stage builds** (already implemented for frontend)
2. **Smaller base images** (alpine variants)
3. **Layer caching optimization**
4. **Security scanning** with `docker scan`

### Environment Variables

All environment variables from `.env` are passed to the backend container. Critical ones:

- `DATABASE_URL` - Auto-configured for Docker network
- `MEDGEMMA_PROVIDER` - AI provider selection
- `MEDGEMMA_HF_TOKEN` - HuggingFace authentication
- `VERTEX_API_KEY` - Google Cloud Vertex AI (if applicable)

See `.env.example` for complete list.

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker-compose ps db

# View database logs
docker-compose logs db

# Verify connectivity from backend
docker-compose exec backend ping db
```

# Verify connectivity from backend

docker-compose exec backend python -c "import socket; socket.create_connection(('db', 5432))"

# Check logs

docker-compose logs backend

# Common issues:

# - Missing environment variables

# - Database not ready (increase wait time in docker-compose.yml)

# - Port 8000 already in use

### Frontend Build Fails

```bash
# Check Node.js version in Dockerfile (currently: node:20-alpine)
# Verify package.json and package-lock.json are in sync

# Manual build test
cd ui
docker build -t medcontext-frontend-test .
```

### Port Conflicts

If ports 80, 8000, or 5432 are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8080:80" # Frontend: localhost:8080
  - "8001:8000" # Backend: localhost:8001
  - "5433:5432" # Database: localhost:5433
```

## Clean Up

Remove all MedContext containers, volumes, and images:

```bash
# Stop and remove containers + volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Nuclear option (removes everything)
docker system prune -a --volumes
```

## Performance Tips

1. **Use BuildKit** for faster builds:

   ```bash
   DOCKER_BUILDKIT=1 docker-compose build
   ```

2. **Cache dependencies**:

   - Python packages cached in Docker layers
   - Node modules cached in builder stage

3. **Volume mounts** for development:
   - Source code mounted for hot reload
   - Avoids rebuilds during development

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [React Production Build](https://vitejs.dev/guide/build.html)
