# MedContext Deployment Guide

Quick setup guide for running MedContext locally or in production.

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** (for UI)
- **PostgreSQL 14+**
- **uv** (Python package manager) - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## Quick Start (5 Minutes)

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
uv venv && uv run pip install -r requirements.txt

# Install UI dependencies
cd ui && npm install && cd ..
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Minimum Required Configuration:**
```env
# Database (required)
DATABASE_URL=postgresql://username:password@db-host:5432/medcontext

# MedGemma Provider (choose one)
MEDGEMMA_PROVIDER=vllm
MEDGEMMA_VLLM_URL=https://your-vllm-endpoint.com/v1/chat/completions
MEDGEMMA_HF_MODEL=google/medgemma-1.5-4b-it

# LLM for Orchestration (required for best results)
LLM_ORCHESTRATOR=google/gemini-2.5-pro
LLM_WORKER=google/gemini-2.5-flash
LLM_API_KEY=your-openrouter-or-google-api-key
LLM_BASE_URL=https://openrouter.ai/api/v1

# Reverse Image Search (optional but recommended)
SERP_API_KEY=your-serpapi-key
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start Services

**Backend:**
```bash
uv run uvicorn app.main:app --reload --app-dir src
```

**Frontend (separate terminal):**
```bash
cd ui
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Environment Configuration Details

### MedGemma Provider Options

#### Option 1: vLLM (Recommended - Fast & Cheap)
```env
MEDGEMMA_PROVIDER=vllm
MEDGEMMA_VLLM_URL=https://your-runpod-endpoint.com/v1/chat/completions
MEDGEMMA_HF_MODEL=google/medgemma-1.5-4b-it
```

**Pros:** Fast inference, cost-effective, OpenAI-compatible API
**Cons:** Requires separate vLLM server

#### Option 2: HuggingFace (Easiest for Demo)
```env
MEDGEMMA_PROVIDER=huggingface
MEDGEMMA_HF_TOKEN=hf_your_token_here
MEDGEMMA_HF_MODEL=google/medgemma-1.5-4b-it
```

**Pros:** No server setup, just need HF token
**Cons:** Rate limited, slower than vLLM
**Get Token:** https://huggingface.co/settings/tokens

#### Option 3: Vertex AI (Production)
```env
MEDGEMMA_PROVIDER=vertex
MEDGEMMA_VERTEX_PROJECT=your-gcp-project-id
MEDGEMMA_VERTEX_LOCATION=us-central1
MEDGEMMA_VERTEX_ENDPOINT=your-vertex-endpoint-id
```

**Pros:** Low latency, high scale, Google Cloud native
**Cons:** Requires GCP account and setup

#### Option 4: Local Inference
```env
MEDGEMMA_PROVIDER=local
MEDGEMMA_HF_MODEL=google/medgemma-1.5-4b-it
```

**Pros:** No API costs, runs offline
**Cons:** Requires GPU (8GB+ VRAM), slow on CPU

### LLM Orchestration

For best agentic reasoning, configure an LLM:

```env
# OpenRouter (Recommended - Access to all models)
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-your-key-here
LLM_ORCHESTRATOR=google/gemini-2.5-pro
LLM_WORKER=google/gemini-2.5-flash

# Or Google AI Studio (Direct)
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta
LLM_API_KEY=your-google-api-key
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash
```

### Reverse Image Search

```env
# SerpAPI (Recommended - Google Reverse Image Search)
SERP_API_KEY=your-serpapi-key
SERP_API_TIMEOUT_SECONDS=20.0
```

**Get API Key:** https://serpapi.com/

Without this key, the system uses synthetic fallback data (still works but less accurate).

### Reddit Monitoring (Optional)

```env
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
REDDIT_USER_AGENT=MedContext/1.0
REDDIT_SUBREDDITS=medicine,radiology,medicalimaging
REDDIT_KEYWORDS=mri,xray,ct scan
REDDIT_POLL_INTERVAL_MINUTES=60
ENABLE_MONITORING_POLLING=true
```

**Get Credentials:** https://www.reddit.com/prefs/apps

---

## Testing the Deployment

### 1. Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

### 2. Test Agentic Workflow

```bash
# Upload a medical image for analysis
curl -X POST http://localhost:8000/api/v1/orchestrator/run \
  -F "file=@/path/to/medical_image.jpg" \
  -F "context=This MRI shows a brain tumor"

# Or with image URL
curl -X POST http://localhost:8000/api/v1/orchestrator/run \
  -F "image_url=https://example.com/medical-image.jpg" \
  -F "context=Chest X-ray showing pneumonia"
```

### 3. Run Test Suite

```bash
# Run all tests (33 tests)
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=src/app --cov-report=html
```

### 4. Test UI

1. Open http://localhost:5173
2. Configure API base URL (should auto-detect http://localhost:8000)
3. Upload a medical image
4. Add context/claim
5. Click "Run Analysis"
6. View results (alignment verdict, confidence, forensics details)

---

## Production Deployment

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: medcontext
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: medcontext
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://medcontext:${DB_PASSWORD}@postgres:5432/medcontext
      REDIS_URL: redis://redis:6379
      # Add other env vars from .env
    depends_on:
      - postgres
      - redis

  ui:
    build: ./ui
    ports:
      - "80:80"
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### Environment Variables for Production

```env
# Use strong passwords
DATABASE_URL=postgresql://user:strong-password@db-host:5432/medcontext

# Enable production mode
LOG_LEVEL=INFO

# Use production LLM endpoints
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-prod-your-key

# Enable monitoring
ENABLE_MONITORING_POLLING=true

# Secure secrets
JWT_SECRET=your-32-character-secret
ENCRYPTION_KEY=your-32-byte-encryption-key
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql postgresql://username:password@localhost:5432/medcontext

# Run migrations manually
alembic upgrade head

# Check migration status
alembic current
```

### MedGemma Provider Errors

**Error:** `MedGemmaClientError: Missing MEDGEMMA_HF_TOKEN`
**Fix:** Set `MEDGEMMA_HF_TOKEN` in `.env` or switch to vLLM provider

**Error:** `404 Not Found` from vLLM endpoint
**Fix:** Verify `MEDGEMMA_VLLM_URL` is correct and server is running

### LLM API Failures

**Error:** `LlmClientError: Unauthorized`
**Fix:** Check `LLM_API_KEY` is valid

**Error:** Agent falls back to MedGemma for synthesis
**Note:** This is expected behavior when LLM is unavailable. Not an error.

### Reverse Search Not Working

**Error:** `SerpAPI reverse search failed: 404`
**Fix:** This is expected without `SERP_API_KEY`. System uses synthetic fallback data.

### UI Can't Connect to API

1. Check API is running: `curl http://localhost:8000/health`
2. Check CORS settings in `src/app/main.py`
3. Configure API base URL in UI settings

---

## Performance Optimization

### Cache Configuration

```env
# Increase cache TTL for reverse search (default: 3600s)
# Modify in src/app/reverse_search/service.py
```

### Database Indexes

Migrations include optimized indexes. For manual tuning:

```sql
-- Check index usage
SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'public';

-- Add custom index if needed
CREATE INDEX idx_custom ON image_submissions (created_at DESC);
```

### API Rate Limiting

Configure rate limits for production:

```python
# src/app/main.py
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/orchestrator/run")
@limiter.limit("10/minute")
async def run_orchestrator(...):
    ...
```

---

## Security Checklist

- [ ] Change default database password
- [ ] Use HTTPS in production
- [ ] Set strong JWT_SECRET and ENCRYPTION_KEY
- [ ] Enable rate limiting on API endpoints
- [ ] Review CORS allowed origins
- [ ] Rotate API keys regularly
- [ ] Enable database backups
- [ ] Set up monitoring and alerting

---

## Support & Resources

- **CLAUDE.md** - Full technical documentation
- **AGENTIC_ARCHITECTURE.md** - Agent system deep dive
- **README.md** - Project overview
- **API Docs** - http://localhost:8000/docs (when running)
- **Tests** - Run `pytest tests/ -v` for examples

---

## Quick Reference

**Start Development:**
```bash
uv run uvicorn app.main:app --reload --app-dir src
cd ui && npm run dev
```

**Run Tests:**
```bash
uv run pytest tests/ -v
```

**Database Migrations:**
```bash
alembic upgrade head
```

**API Endpoints:**
- `POST /api/v1/orchestrator/run` - Main agentic workflow
- `POST /api/v1/orchestrator/run-langgraph` - LangGraph version
- `GET /api/v1/orchestrator/graph` - Workflow visualization
- `POST /api/v1/orchestrator/trace` - Execution trace
- `GET /health` - Health check
