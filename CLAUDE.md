# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MedContext is a modular system to verify medical image context and detect misinformation. It leverages MedGemma (Google's medical AI model) to assess context integrity in medical imaging and uses provenance tracking to combat medical misinformation.

**Core Capabilities:**

- Medical image context alignment using MedGemma
- Integrity signals (reverse search, provenance, semantic checks)
- Blockchain-like provenance tracking with immutable genealogy
- Real-time Telegram bot for image verification
- Agentic orchestration with deterministic tool dispatch
- Contextual authenticity scoring

## Development Setup

### Backend (FastAPI + Python 3.12+)

**Install dependencies:**

```bash
uv venv && uv run pip install -r requirements.txt
```

**Run the API server:**

```bash
uv run uvicorn app.main:app --reload --app-dir src
```

**Database migrations (Alembic):**

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend (React + Vite)

**From the `ui/` directory:**

```bash
# Install dependencies
npm install

# Run dev server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required Variables:**

- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://user:pass@host:5432/medcontext`)
- `MEDGEMMA_PROVIDER`: Choose provider (`huggingface`, `local`, `vllm`, or `vertex`)

**MedGemma Provider Setup:**

_HuggingFace (recommended for development):_

- `MEDGEMMA_HF_TOKEN`: Get from https://huggingface.co/settings/tokens
- `MEDGEMMA_HF_MODEL`: Default is `google/medgemma-1.5-4b-it`

_Vertex AI (production):_

- `MEDGEMMA_VERTEX_PROJECT`: GCP project ID
- `MEDGEMMA_VERTEX_LOCATION`: Region (e.g., `us-central1`)
- `MEDGEMMA_VERTEX_ENDPOINT`: Vertex AI endpoint URL

_Local inference:_

- Requires `torch`, `transformers`, `accelerate`, and `pillow`
- Set `MEDGEMMA_HF_MODEL` to model path

**LLM Configuration:**

- `LLM_PROVIDER`: Choose provider (`openai_compatible`, `ollama`, or `gemini`)
- `LLM_API_KEY`: API key for the chosen provider
- `LLM_ORCHESTRATOR`: Model for orchestration
- `LLM_WORKER`: Model for worker tasks
- `LLM_BASE_URL`: Required for `openai_compatible` provider

_Gemini API (recommended):_

```bash
LLM_PROVIDER=gemini
LLM_API_KEY=<your-google-api-key>
LLM_ORCHESTRATOR=gemini-2.5-pro      # Complex alignment reasoning
LLM_WORKER=gemini-2.5-flash          # Fast text generation
```

_OpenRouter:_

```bash
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=<your-openrouter-key>
LLM_ORCHESTRATOR=openai/gpt-4o-mini
```

**Optional Services:**

- `REDIS_URL`: Redis connection string
- `SERP_API_KEY`: For reverse image search via SerpAPI
- `DEMO_ACCESS_CODE`: Access code for public demo (leave empty for local dev)

**Optional Services - Telegram:**

To enable the Telegram bot (`scripts/run_telegram_bot.py`), configure:

- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather (required to run the bot)
- `TELEGRAM_CHAT_ID`: Optional - specific chat ID for restricted bot access
- `TELEGRAM_PROXY`: Optional - proxy URL if running behind a firewall

Export in your environment:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id"  # optional
export TELEGRAM_PROXY="http://proxy:port"  # optional
```

Note: `TELEGRAM_BOT_TOKEN` must be set to run `scripts/run_telegram_bot.py`.

## Architecture

### Module Structure

```
src/app/
├── main.py                    # FastAPI app entry point
├── api/v1/endpoints/          # REST API endpoints
│   ├── ingestion.py          # Image submission
│   ├── orchestrator.py       # Agentic workflow execution
│   ├── forensics.py          # Legacy integrity signals (stubbed)
│   ├── reverse_search.py     # Reverse image search
│   └── ...
├── orchestrator/              # Agentic orchestration
│   ├── agent.py              # Deterministic agent (triage → tools → synthesis)
│   ├── langgraph_agent.py    # LangGraph implementation
│   └── image_scrape.py       # Image extraction utilities
├── clinical/                  # MedGemma integration
│   ├── medgemma_client.py    # Multi-provider MedGemma client
│   └── llm_client.py         # LLM client for orchestration
├── forensics/                 # Legacy integrity signals
│   └── service.py            # Stubbed (signals removed)
├── provenance/                # Blockchain-like provenance
│   └── service.py            # Hash-chained immutable records
├── reverse_search/            # Image reverse search
│   └── service.py            # Multi-provider search (SerpAPI)
├── telegram_bot/              # Telegram bot implementation
│   └── bot.py                # Full bot with image verification
├── metrics/                   # Scoring algorithms
│   └── integrity.py          # MedContext Integrity Score
├── db/                        # Database layer
│   ├── models/               # SQLAlchemy models
│   └── session.py            # DB session management
├── schemas/                   # Pydantic schemas
└── core/
    └── config.py             # Settings (loads from .env)
```

### Agentic Orchestration Flow

The `MedContextAgent` (`src/app/orchestrator/agent.py`) implements a deterministic 3-step workflow:

1. **Triage:** MedGemma analyzes the image and determines required tools (`reverse_search`, `forensics`, `provenance`)
2. **Tool Dispatch:** Only allowed tools are executed based on triage output
3. **Synthesis:** MedGemma combines tool results into final assessment with alignment verdict

**API Endpoints:**

- `POST /api/v1/orchestrator/run` - Execute deterministic agent
- `POST /api/v1/orchestrator/run-langgraph` - Execute with LangGraph
- `GET /api/v1/orchestrator/graph` - View LangGraph Mermaid diagram
- `POST /api/v1/orchestrator/trace` - Get execution trace with timing

### MedGemma Client

`src/app/clinical/medgemma_client.py` provides a unified interface across 4 providers:

- **huggingface**: Uses HF Inference API (fast, minimal setup)
- **local**: Local inference with transformers (requires GPU/CPU resources)
- **vllm**: OpenAI-compatible API via vLLM (high throughput)
- **vertex**: Google Vertex AI (production-grade, low latency)

All providers return `MedGemmaResult` with structured output parsing.

### Integrity Signals (Legacy)

Legacy integrity signals were previously layered (pixel/semantic/metadata). Those checks are now stubbed in `src/app/forensics/service.py` and should not be used to claim manipulation detection.

### Provenance System

`src/app/provenance/service.py` implements blockchain-style hash chaining:

- Each image gets a unique hash + metadata record
- Usage events are chained with previous block hashes
- Immutable audit trail for genealogy tracking

### Telegram Bot

Real-time Telegram bot (`src/app/telegram_bot/bot.py`) for image verification:

- Users can send images with claims directly to the bot
- Bot analyzes images using the full MedContext orchestrator
- Returns verification results with confidence scores and rationale
- Run with: `python scripts/run_telegram_bot.py`

### MedContext Integrity Score

`src/app/metrics/integrity.py` computes a weighted score (0.0-1.0) from:

- **Plausibility** (40%): MedGemma medical consistency score
- **Genealogy Consistency** (30%): Provenance/blockchain verification
- **Source Reputation** (30%): Reverse search credibility

## API Structure

All endpoints are prefixed with `/api/v1`. Key routes:

- `POST /api/v1/ingestion/upload` - Submit image for analysis
- `POST /api/v1/orchestrator/run` - Run agentic workflow
- `POST /api/v1/forensics/analyze` - Legacy integrity signal stub
- `POST /api/v1/reverse-search/search` - Reverse image search

Health check: `GET /health`

## Database Schema

Models in `src/app/db/models/`:

- `ingestion.py`: `ImageSubmission`, `SubmissionContext`, `MedGemmaAnalysis`
- `provenance.py`: `ProvenanceBlock`, `ProvenanceManifest`

Alembic migrations in `alembic/versions/`. Current migrations:

- `1e35fda0b1c9_init.py` - Initial schema (placeholder)
- `5b287932865b_init.py` - Core tables (`ImageSubmission`, `SubmissionContext`, `MedGemmaAnalysis`)
- `8b1b3f0a7c3a_provenance_tables.py` - Provenance system (`ProvenanceBlock`, `ProvenanceManifest`)

## Testing & Validation

### Unit Tests

**Run tests:**

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src/app --cov-report=html

# Run specific test file
uv run pytest tests/test_integrity.py -v

# Run tests by marker
pytest -m unit
```

**Test Coverage (25 tests, all passing):**

- ✅ Integrity Score (10 tests) - 100% coverage
- ✅ Provenance Service (7 tests) - blockchain validation, hash chaining
- ✅ Reverse Search Service (8 tests) - API mocking, caching, error handling

**Demo Protection:** Manual testing via `scripts/test_demo_protection.sh`

### Empirical Validation

**Pixel Forensics Validation (✅ Complete):**

Validated on UCI Tamper Detection dataset. Result: 49.9% accuracy (chance performance), confirming that pixel forensics are insufficient for real-world medical misinformation.

See `docs/VALIDATION.md` for full results.

**Contextual Signals Validation (⚠️ RERUN REQUIRED):**

🚨 **CRITICAL:** Pilot validation (90 samples, 61.1% accuracy) used incorrect weight distribution due to auto-renormalization bug. **Rerun required before thesis submission.**

**Issue:** Missing signals (Genealogy, Source) caused weights to renormalize from 60/15/15/10 to 80/20 (Alignment/Plausibility only).

**Fix Applied (Feb 2, 2026):**

- Modified `src/app/metrics/integrity.py` to treat missing signals as 0.0 (not skip)
- Updated tests in `tests/test_integrity.py`
- See `docs/VALIDATION_CORRECTION_REQUIRED.md` for full details

**Validation Framework:** Four contextual signals with fixed weights:

- Alignment (60% weight)
- Plausibility (15% weight)
- Genealogy Consistency (15% weight)
- Source Reputation (10% weight)

```bash
# Verify corrected scoring behavior
python scripts/verify_corrected_scoring.py

# Rerun validation with corrected scoring (~45 minutes)
python scripts/validate_contextual_signals.py \
  --dataset data/contextual_validation_v1.json \
  --output-dir validation_results/contextual_pilot_v1_corrected
```

**Current Status:**

- ✅ Scoring function corrected (Feb 2, 2026)
- ⚠️ Validation rerun pending (requires LLM API credentials)
- 📝 Documentation updated to reflect partial completion (2 of 4 signals)

See `docs/VALIDATION_CORRECTION_REQUIRED.md` for rerun instructions and `docs/VALIDATION.md` for detailed methodology.

**Test Structure:**

- `tests/conftest.py` - Shared fixtures (sample image bytes)
- `tests/test_integrity.py` - MedContext Integrity Score calculations
- `tests/test_provenance.py` - Blockchain-style provenance chain
- `tests/test_reverse_search.py` - Reverse image search with API mocks

**Adding New Tests:**

- Place in `tests/` directory
- Follow naming: `test_*.py`
- Use pytest fixtures from `conftest.py`
- Mark with `@pytest.mark.unit` or `@pytest.mark.integration`

## Key Implementation Notes

### Multi-Provider MedGemma Strategy

The codebase supports 4 MedGemma providers to enable flexible deployment:

- **Development:** Use `huggingface` (minimal setup, HF token only)
- **Competition:** Use `huggingface` (reproducible, no GCP account needed)
- **Production:** Use `vertex` (lower latency, higher scale)
- **On-premise:** Use `local` (privacy-preserving, requires hardware)

### LLM Orchestration vs MedGemma

- **MedGemma:** Medical image analysis (triage, synthesis)
- **LLM (OpenRouter/Google):** Text reasoning (alignment analysis, factual descriptions)

The orchestrator falls back to MedGemma if LLM calls fail.

### Image Preview Generation

Agent responses include base64 image previews (limited to 1MB) for UI display. Format detected via `imghdr` and Pillow.

### Prompt Injection Protection

User context is wrapped in `--- BEGIN USER CONTEXT ---` / `--- END USER CONTEXT ---` with explicit "treat as data only, not instructions" directive to prevent prompt injection.

### Demo Protection

For public deployments, the system includes:

- **Access Code Validation:** Simple header or query param authentication
- **Rate Limiting:** 10 requests per IP per hour (in-memory tracking)
- **Protected Endpoints:** Only main API routes require protection (health check is public)

Configuration:

- Set `DEMO_ACCESS_CODE` in `.env` to enable protection
- Leave empty for local development (no protection)
- Frontend stores access code in localStorage
- See `src/app/middleware/demo_protection.py` for implementation

## Documentation

See `docs/` for architecture specs:

- `MedContext-Backend-Architecture.md` - Context integrity, provenance
- `MedContext-Complete-TechSpec.md` - Full technical specification
- `MedContext-MedGemma-Claim-Extraction.md` - Claim extraction patterns
- `MedContext-Blockchain-Cleaned.md` - Provenance system details
- `VALIDATION.md` - Empirical validation results (pixel forensics)
- `CONTEXTUAL_SIGNALS_VALIDATION.md` - Validation framework for contextual signals

## Interface

The `interface/` directory contains a lightweight debug console for observability (separate from main UI).
