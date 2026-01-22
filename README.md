# MedContext: Contextual Integrity Detector 2.0

MedContext focuses on **contextual integrity** for medical images: whether an image (authentic or manipulated) is being used in a way that genuinely reflects what it depicts. Instead of claiming definitive deepfake detection, the system evaluates alignment between the image, its provenance, and the surrounding claim or caption, surfacing risks of misleading reuse or miscaptioning.

## Quick Start

1. Create a virtual environment with uv (optional but recommended).
2. Install dependencies:
   - `uv venv && uv run pip install -r requirements.txt`
3. Run the API:
   - `uv run uvicorn app.main:app --reload --app-dir src`

The API exposes placeholder endpoints for each module under `/api/v1/*`. These are safe stubs intended for incremental implementation.

## Database Migrations (Alembic)

- Create a new migration: `alembic revision --autogenerate -m "init"`
- Apply migrations: `alembic upgrade head`

The migration system uses `DATABASE_URL` from your environment.

## MedGemma Providers

Toggle providers with `MEDGEMMA_PROVIDER`:

- `huggingface` (default): set `MEDGEMMA_HF_TOKEN` and optionally `MEDGEMMA_HF_MODEL`
- `local`: uses local `transformers` inference; requires `accelerate` and `MEDGEMMA_HF_MODEL`
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

`src/app/metrics/integrity.py` defines the MedContext Integrity Score, a weighted blend of plausibility, genealogy consistency, and source reputation. This score is used to communicate alignment risk rather than binary authenticity.

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

- Strengthen claim extraction and alignment prompts for contextual integrity.
- Add citation and source-credibility weighting for reverse search results.
- Expand provenance logging to capture claim/context at time of upload.
- Add UI emphasis on alignment verdicts and evidence traceability.

## Notes

- The docs mention PostgreSQL + IPFS + Redis; the skeleton is ready for these integrations.
- Edge AI hardening includes 4-bit quantized MedGemma (GGUF/CoreML) for privacy-preserving triage on WhatsApp/mobile ingestion.
- See `docs/MedContext-Backend-Architecture.md` for provenance, monitoring, and evidence aggregation architecture.
- If you want a different stack (e.g., Neo4j first, or Rust services), say the word and I will realign the scaffold.

## Interface

See `interface/` for a lightweight debug console focused on observability.
