# MedContext: Contextual Authenticity Detection for Medical Images

**Team:** Counter Force AI (Jamie I. Forrest, PhD, MPH)
**Affiliation:** HERO Lab, School of Nursing, University of British Columbia
**Category:** Agentic AI System | Medical AI & Healthcare Innovation

---

## The Problem

Medical misinformation is a global health crisis — but the dominant threat is not what most people assume. A comprehensive scoping review of approximately 100 sources (Forrest 2026) reveals that over 80% of visual medical misinformation consists of authentic images paired with false or misleading claims. Sophisticated deepfakes accounted for 0% of visual misinformation in COVID-19 studies. The real weapon is not image fabrication — it is context manipulation.

This distinction matters because it renders pixel-level forensics fundamentally inadequate. If the image itself is authentic, there is nothing at the pixel level to detect. Yet the vast majority of existing detection tools target exactly this scenario — optimising for synthetic benchmarks that do not reflect the actual threat distribution.

## Empirical Validation

We tested this hypothesis directly. Using the UCI Tamper Detection dataset (326 balanced images), we evaluated pixel-level forensics — Error Level Analysis, compression artefact detection, and EXIF metadata examination — with bootstrap resampling across 1,000 iterations.

**Result:** 49.9% accuracy [95% CI: 44.5%, 55.5%] — statistically indistinguishable from chance.

This finding validates the contextual authenticity thesis and provides the empirical foundation for MedContext's design. When we subsequently evaluated contextual dimensions on a purpose-built dataset of 160 medical image–claim pairs across five clinical categories, both claim veracity (AUC 0.648) and image–claim alignment (AUC 0.600) independently outperformed pixel forensics — demonstrating that contextual signals capture information that pixel analysis cannot.

**Important limitation:** These are single-dataset evaluations and do not supersede the broader forensics literature. We treat them as supporting evidence aligned with our threat model, not definitive proof.

## Solution: Agentic Contextual Authenticity

MedContext is an agentic AI system that assesses whether a medical image's accompanying claim is both medically accurate and supported by the visual evidence. The architecture separates clinical reasoning from strategic orchestration — an intentional design principle we describe as *"the doctor does doctor work; the manager does management work."*

### Architecture

The system operates in three phases:

**Phase 1 — Triage.** MedGemma (google/medgemma-1.5-4b-it) performs clinical analysis: image type identification, anatomical findings, and claim plausibility assessment. This medical context is passed to a separate orchestrator LLM (Gemini 2.5 Pro), which decides which investigative tools to deploy based on the clinical assessment and claim characteristics.

**Phase 2 — Dynamic Tool Dispatch.** The orchestrator invokes only the tools warranted by the triage — reverse image search for context verification, pixel forensics if manipulation is suspected, or provenance chain validation. For medically plausible claims with clear image alignment, unnecessary tools are skipped, reducing computational cost by approximately 60% without sacrificing accuracy.

**Phase 3 — Evidence Synthesis.** The orchestrator aggregates MedGemma's clinical analysis with tool results into an explainable verdict — a veracity–alignment matrix that independently scores claim accuracy and image–claim correspondence. Each assessment includes traceable reasoning with clear attribution ("per MedGemma's clinical analysis" versus "per investigative evidence").

This separation of concerns prevents domain overstepping: MedGemma never makes strategic decisions about which tools to run, and the orchestrator never makes medical judgements. LangGraph provides workflow visualisation and state management for the agentic pipeline.

### MedGemma Integration

MedGemma serves as the clinical reasoning backbone across multiple deployment configurations — HuggingFace (minimal setup), Vertex AI (production-grade), local inference (privacy-preserving), and vLLM (high-throughput). Its medical training data makes it uniquely suited for anatomical assessment and claim plausibility evaluation in ways that general-purpose LLMs are not. When the orchestrator LLM is unavailable, MedGemma serves as a complete fallback, ensuring the system degrades gracefully rather than failing.

## Implementation Quality

MedContext is production-ready, not a prototype:

- **4,100+ lines** of Python across a modular FastAPI backend with SQLAlchemy/PostgreSQL, Alembic migrations, and comprehensive error handling
- **33/33 tests passing** covering integrity scoring, provenance chain verification, reverse search caching, and agentic workflow defaults
- **Security hardened** with prompt injection protection (user context wrapped in explicit data-only markers), SSRF prevention via IP validation, tool whitelist enforcement, and rate-limited demo access
- **Full-stack deployment** with React 19 frontend, Docker support with health checks, and a Telegram bot for field verification
- **Reproducible** via documented setup with `.env.example` and Docker Compose

## Real-World Impact

MedContext is designed for deployment through the Health Equity & Resilience Observatory (HERO) Lab at UBC, targeting clinical and public health settings across African health systems — environments where medical misinformation causes measurable harm and where resource constraints demand efficient, explainable tools. The Telegram bot integration provides accessible verification in settings where web applications are impractical. The system's cache-aware design and adaptive tool selection minimise API costs for sustained deployment.

The core insight — that contextual authenticity, not pixel forensics, addresses the dominant misinformation threat — reframes the problem in a way that has implications beyond this specific tool, informing how health systems and platforms approach medical image verification at scale.

---

**Repository:** [github.com/drjforrest/MedContext-impact](https://github.com/drjforrest/MedContext-impact)
**Navigation:** See [START_HERE.md](../START_HERE.md) for judge-optimised reading paths (2-min, 10-min, 30-min)
