# 🐳 Docker Quick Start for Judges

**⏱️ Time to Launch: 5 minutes**

This is the **fastest way** to run MedContext. Everything—database, backend, frontend—launches with a single command.

---

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- MedGemma API access (HuggingFace token or Vertex AI credentials)

---

## 🚀 Launch MedContext (3 Steps)

### Step 1: Clone Repository

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your MedGemma credentials
# Minimum required: MEDGEMMA_HF_TOKEN (get from HuggingFace)
nano .env  # or use your preferred editor
```

**Quick config for HuggingFace (easiest option):**

```env
MEDGEMMA_PROVIDER=huggingface
MEDGEMMA_HF_TOKEN=hf_YOUR_TOKEN_HERE
```

### Step 3: Launch Everything

```bash
docker-compose up -d
```

That's it! 🎉

---

## 📊 Access MedContext

- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **LangGraph Visualization:** http://localhost:8000/api/v1/orchestrator/graph

---

## ✅ Verify It's Working

### Check all services are running:

```bash
docker-compose ps
```

You should see:

```
NAME                    STATUS
medcontext-backend      Up (healthy)
medcontext-db           Up (healthy)
medcontext-frontend     Up
```

### Test the API:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

> **Note:** The JSON response uses compact formatting (no spaces) as returned by FastAPI's default JSON encoder.

### View logs:

```bash
# All services
docker-compose logs -f

# Just backend
docker-compose logs -f backend

# Just frontend
docker-compose logs -f frontend
```

---

## 🧪 Run a Test Analysis

1. Open http://localhost in your browser
2. Upload a medical image (use samples from `tests/fixtures/`)
3. Add a claim (e.g., "This shows COVID-19 infection")
4. Click "Run Analysis"
5. Watch the agentic workflow in action!

---

## 🛠️ What's Running?

The Docker setup includes:

1. **PostgreSQL Database (port 5432)**
   - Persistent storage with named volume
   - Automatic health checks
   - Pre-configured with migrations

2. **FastAPI Backend (port 8000)**
   - Runs database migrations automatically on startup
   - Hot-reload enabled for development
   - Health check endpoint at `/health`
   - Full API documentation at `/docs`

3. **React Frontend (port 80)**
   - Production-optimized build
   - Nginx web server
   - Proxies `/api` requests to backend
   - Single-page app routing

**Network:** All services communicate on isolated `medcontext-network`

---

## 🔧 Troubleshooting

### Problem: "Port already in use"

**Solution:** Change ports in `docker-compose.yml`:

```yaml
# Change frontend port from 80 to 3000
frontend:
  ports:
    - "3000:80" # Access at http://localhost:3000

# Change backend port from 8000 to 8001
backend:
  ports:
    - "8001:8000" # Access at http://localhost:8001
```

### Problem: "Database connection failed"

**Solution:** Wait for database to be ready:

```bash
# Check database health
docker-compose ps db

# If not healthy, restart
docker-compose restart db
docker-compose restart backend
```

### Problem: "Missing MedGemma token"

**Solution:** Ensure `.env` has your credentials:

```bash
# Check what environment variables are set
docker-compose config

# Add token to .env file
echo "MEDGEMMA_HF_TOKEN=hf_YOUR_TOKEN" >> .env

# Restart backend
docker-compose restart backend
```

---

## 🔄 Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove all data (fresh start)
docker-compose down -v

# View logs in real-time
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build

# Run backend tests
docker-compose exec backend pytest

# Access backend shell
docker-compose exec backend bash

# Access database shell
docker-compose exec db psql -U medcontext -d medcontext
```

---

## 🧹 Cleanup

```bash
# Stop services and remove containers
docker-compose down

# Remove containers + volumes (database data)
docker-compose down -v

# Remove everything including images
docker-compose down -v --rmi all
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  Browser (http://localhost)                     │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Nginx Frontend Container (port 80)             │
│  - Serves React build                           │
│  - Proxies /api → backend:8000                  │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  FastAPI Backend Container (port 8000)          │
│  - MedGemma agentic orchestration               │
│  - Tool execution (forensics, search, etc.)     │
│  - API endpoints                                │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  PostgreSQL Database Container (port 5432)      │
│  - Analysis history                             │
│  - User sessions                                │
│  - Persistent volume: postgres_data             │
└─────────────────────────────────────────────────┘
```

---

## 🎯 For Kaggle Judges

**Why Docker is the easiest evaluation method:**

1. **No dependency conflicts** - Everything runs in isolated containers
2. **Consistent environment** - Works the same on any OS (Mac/Windows/Linux)
3. **Automatic setup** - Database migrations, networking all handled
4. **Production-ready** - Same setup used for deployment
5. **One command** - `docker-compose up -d` and you're running

**Alternative methods:**

- **Manual setup:** See [DEPLOYMENT.md](DEPLOYMENT.md) for pip/npm installation
- **Cloud deployment:** One-click deploy to Railway/Render (see README.md)

---

## 📚 Next Steps

Once MedContext is running:

1. **Read the validation:** [docs/VALIDATION.md](docs/VALIDATION.md)
2. **View the architecture:** http://localhost:8000/api/v1/orchestrator/graph
3. **Try different providers:** Edit `MEDGEMMA_PROVIDER` in `.env`
4. **Run comprehensive tests:** `docker-compose exec backend pytest -v`
5. **Explore the code:** Backend in `src/`, Frontend in `ui/src/`

---

## 🆘 Need Help?

- **Documentation:** [START_HERE.md](START_HERE.md)
- **Full deployment guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Validation details:** [docs/VALIDATION.md](docs/VALIDATION.md)
- **Technical submission:** [docs/SUBMISSION.md](docs/SUBMISSION.md)

---

**Built for the Kaggle MedGemma Impact Challenge**
**Ready to run. Ready to deploy. Ready to save lives.**
