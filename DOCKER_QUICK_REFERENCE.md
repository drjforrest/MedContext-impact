# Docker Quick Reference Card

## 🚀 Getting Started

```bash
# 1. Setup environment
cp .env.docker .env
# Edit .env with your API keys

# 2. Build images
make build

# 3. Start services
make up

# 4. Check health
make health
```

## 📋 Essential Commands

| Task             | Command        | Description                 |
| ---------------- | -------------- | --------------------------- |
| **Start**        | `make up`      | Start all services          |
| **Start (dev)**  | `make dev-up`  | Start with hot reload       |
| **Start (prod)** | `make prod-up` | Start in production mode    |
| **Stop**         | `make down`    | Stop and remove containers  |
| **Restart**      | `make restart` | Restart all services        |
| **Logs**         | `make logs`    | View all logs (follow mode) |
| **Health**       | `make health`  | Run health check            |
| **Test**         | `make test`    | Run tests in container      |
| **Clean**        | `make clean`   | Remove containers & volumes |

## 🔍 Monitoring

```bash
# View logs
make logs                # All services
make logs-backend        # Backend only
make logs-frontend       # Frontend only
make logs-db            # Database only

# Check status
make ps                  # List containers
make health             # Health check

# Access containers
docker-compose exec backend /bin/sh   # Backend shell
docker-compose exec frontend /bin/sh  # Frontend shell
make db-shell                         # Database shell
```

## 🗄️ Database

```bash
# Run migrations
make db-migrate

# Open PostgreSQL shell
make db-shell

# Reset database (⚠️ destroys data)
make db-reset

# Backup database
# Note: Replace "medcontext" with your actual database name/username if different
# (Format: pg_dump -U <username> <database_name>)
docker-compose exec db pg_dump -U medcontext medcontext > backup.sql

# Restore database
# Note: Replace "medcontext" with your actual database name/username if different
# (Format: psql -U <username> <database_name>)
docker-compose exec -T db psql -U medcontext medcontext < backup.sql
```

## 🌐 Service URLs

| Service  | URL                          | Description      |
| -------- | ---------------------------- | ---------------- |
| Frontend | http://localhost             | React UI         |
| Backend  | http://localhost:8000        | FastAPI API      |
| API Docs | http://localhost:8000/docs   | Swagger UI       |
| ReDoc    | http://localhost:8000/redoc  | Alternative docs |
| Health   | http://localhost:8000/health | Health check     |
| Database | localhost:5432               | PostgreSQL       |

## 🔧 Development vs Production

### Development Mode (Hot Reload)

```bash
make dev-build
make dev-up
```

**Features:**

- ✅ Hot reload enabled
- ✅ Debug logging
- ✅ Volume mounts
- ✅ Single worker
- ✅ Vite dev server

### Production Mode

```bash
make prod-build
make prod-up
```

**Features:**

- ✅ 4 workers
- ✅ No volume mounts
- ✅ Resource limits
- ✅ Auto-restart
- ✅ Static file serving

## 🐛 Troubleshooting

### Services won't start

```bash
# Check logs
make logs

# Rebuild from scratch
make clean
make build
make up
```

### Database connection failed

```bash
# Check database status
docker-compose ps db

# View database logs
make logs-db

# Restart database
docker-compose restart db
```

### Port conflicts

Edit `docker-compose.yml`:

```yaml
ports:
  - "8080:80" # Frontend
  - "8001:8000" # Backend
  - "5433:5432" # Database
```

### Permission errors

```bash
# Reset permissions
sudo chown -R $USER:$USER .

# Clean and rebuild
make clean
make build
```

## 🧹 Cleanup

````bash

# Stop and remove containers

make down

# Remove containers + volumes

make clean

# Nuclear option (removes images too)

make docker-prune

# Docker system cleanup commands

docker container prune -f # Remove stopped containers
docker image prune -f # Remove dangling images
docker volume prune -f # Remove unused volumes

## 📊 Resource Management

```bash
# View resource usage
docker stats

# Limit resources (edit docker-compose.prod.yml)
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
````

## 🔒 Security

```bash
# Scan for vulnerabilities
docker scout cves

# Update base images
docker-compose pull
make build

# View security issues in CI/CD
# Check GitHub Actions → Security tab
```

## 📦 Image Management

```bash
# List images
docker images

# Remove unused images
docker image prune

# Build specific service
docker-compose build backend
docker-compose build frontend

# Pull latest base images
docker-compose pull
```

## 🔄 CI/CD

```bash
# Run CI/CD test locally
bash scripts/test_docker_setup.sh

# GitHub Actions runs automatically on:
# - Push to main/develop
# - Pull requests
```

## 🎯 Common Workflows

### Daily Development

```bash
make dev-up          # Start with hot reload
make logs            # Monitor logs
# Make code changes (auto-reloads)
make down            # Stop when done
```

### Testing Changes

```bash
make build           # Rebuild after dependency changes
make up              # Start services
make test            # Run tests
make health          # Verify health
```

### Production Deployment

```bash
make prod-build      # Build production images
make prod-up         # Start in production mode
make health          # Verify health
make logs            # Monitor startup
```

### Database Maintenance

```bash
make db-migrate      # Run migrations
make db-shell        # Interactive SQL
make logs-db         # View query logs
```

## 📚 Documentation

- **Full Guide**: `DOCKER.md`
- **Architecture**: `DOCKER_SETUP_SUMMARY.md`
- **Files Created**: `DOCKER_FILES_CREATED.md`
- **All Commands**: `make help`

## 💡 Pro Tips

1. **Use Makefile**: All commands have shortcuts (`make help`)
2. **Health Checks**: Run `make health` after any changes
3. **Watch Logs**: Use `make logs` to catch issues early
4. **Dev Mode**: Use `make dev-up` for faster iteration
5. **Clean State**: Use `make clean` if things get weird

## 🆘 Getting Help

1. Run `make health` to diagnose issues
2. Check logs: `make logs`
3. See troubleshooting: `DOCKER.md`
4. Rebuild: `make clean && make build && make up`

---

**Quick Help**: `make help` | **Full Docs**: `DOCKER.md` | **Health Check**: `make health`
