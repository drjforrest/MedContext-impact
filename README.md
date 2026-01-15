# MedContext

MedContext is a modular system to verify medical image context and detect misinformation. The docs in `docs/` define the MVP architecture; this repo now includes a minimal FastAPI skeleton that mirrors those modules so you can start wiring real logic in small, testable pieces.

## Quick Start

1. Create a virtual environment (optional but recommended).
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run the API:
   - `uvicorn app.main:app --reload --app-dir src`

The API exposes placeholder endpoints for each module under `/api/v1/*`. These are safe stubs intended for incremental implementation.

## Database Migrations (Alembic)

- Create a new migration: `alembic revision --autogenerate -m "init"`
- Apply migrations: `alembic upgrade head`

The migration system uses `DATABASE_URL` from your environment.

## MedGemma Providers

Toggle providers with `MEDGEMMA_PROVIDER`:

- `huggingface` (default): set `MEDGEMMA_HF_TOKEN` and optionally `MEDGEMMA_HF_MODEL`
- `vertex`: set `MEDGEMMA_VERTEX_PROJECT`, `MEDGEMMA_VERTEX_LOCATION`, and `MEDGEMMA_VERTEX_ENDPOINT`

### Recommended for Competition Submissions

Use Hugging Face for fast, reproducible evaluation:

- **Why:** minimal setup, no GCP account required, easy for judges to run
- **Config:** `MEDGEMMA_PROVIDER=huggingface`, `MEDGEMMA_HF_TOKEN=...`, optional `MEDGEMMA_HF_MODEL`

Document Vertex AI as the production path:

- **Why:** lower latency and higher scale for real deployments
- **Config:** `MEDGEMMA_PROVIDER=vertex`, plus the Vertex env vars above

## Agentic Orchestrator (Deterministic)

`POST /api/v1/orchestrator/run` executes a deterministic agentic flow:

1. MedGemma triage selects required tools.
2. Only allowed tools are dispatched.
3. MedGemma synthesizes the final assessment.

`POST /api/v1/orchestrator/run-langgraph` runs the same flow using LangGraph.
`GET /api/v1/orchestrator/graph` returns a Mermaid diagram of the LangGraph.
`POST /api/v1/orchestrator/trace` returns a trace with timestamps and durations per node.

## Contextual Integrity Metric

`src/app/metrics/integrity.py` defines the MedContext Integrity Score, a weighted blend of plausibility, genealogy consistency, and source reputation.

## Project Layout

```
src/
  app/
    main.py
    api/v1/endpoints/
    core/
    db/
    schemas/
```

## Immediate Next Steps

- Implement database models from `docs/MedContext-Complete-TechSpec.md`.
- Wire ingestion endpoints to persist `ImageSubmission` and `SubmissionContext`.
- Add background task queue for MedGemma + reverse search (Celery/ARQ/RQ).
- Build MedGemma adapter and structured output parsing.
- Add reverse image search integrations (TinEye, Google Vision).

## Notes

- The docs mention PostgreSQL + IPFS + Redis; the skeleton is ready for these integrations.
- Edge AI hardening includes 4-bit quantized MedGemma (GGUF/CoreML) for privacy-preserving triage on WhatsApp/mobile ingestion.
- See `docs/MedContext-Backend-Architecture.md` for deepfake, provenance, and monitoring architecture.
- If you want a different stack (e.g., Neo4j first, or Rust services), say the word and I will realign the scaffold.

## Interface

See `interface/` for a lightweight debug console focused on observability.
