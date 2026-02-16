# MedContext: Contextual Authenticity Detection for Medical Images

**Team:** Jamie I. Forrest, PhD, MPH (Counterforce AI)
**Affiliation:** Health Equity & Resilience Observatory, Faculty of Applied Science, University of British Columbia
**Category:** Agentic AI System | Medical AI & Healthcare Innovation

---

## The Problem

Medical misinformation is a global health crisis — but the dominant threat is not what most people assume. A comprehensive scoping review of approximately 100 sources (Forrest 2026) reveals that over 80% of visual medical misinformation consists of authentic images paired with false or misleading claims. Sophisticated deepfakes accounted for 0% of visual misinformation in COVID-19 studies. The real weapon is not image fabrication, it's context manipulation.

This distinction matters because it renders pixel-level forensics fundamentally inadequate. If the image itself is authentic, there is nothing at the pixel level to detect. Yet the vast majority of existing detection tools target exactly this scenario, optimizing for synthetic benchmarks that do not reflect a real threat distribution.

## Proof of Justification (Empirical Motivation)

MedContext was developed **empirically motivated**, not feature-driven. The empirical studies below demonstrate why the contextual approach (veracity + alignment) is necessary and validate the approach on real-world medical misinformation. See [PROOF_OF_JUSTIFICATION.md](./PROOF_OF_JUSTIFICATION.md) for detailed methodology.

**PoJ 1 — ELA on UCI Tamper Detection (n=326 DICOM images):** We evaluated ELA (Error Level Analysis), compression artefact detection, and EXIF metadata with bootstrap resampling across 1,000 iterations. This served as a negative control to demonstrate tool-format incompatibility.

**ELA Result:** 49.9% accuracy [95% CI: 44.5%, 55.5%] — statistically indistinguishable from chance. This result was foreseeable: ELA specifically depends on JPEG compression artifacts (quantization table inconsistencies and recompression errors), while DICOM uses lossless or wavelet-based compression that does not produce these artifacts. _What we proved:_ ELA is format-specific and fails on DICOM due to fundamentally different compression mechanisms, not general ineffectiveness. This demonstrates that medical image forensics requires format-aware tool selection. _Limitation:_ This experiment does not assess ELA's performance on JPEG medical images (where it may perform well). Future work should evaluate compression-aware forensics methods on appropriate formats or re-run ELA on JPEG-encoded medical misinformation.

**Med-MMHL Validation — Real-world medical misinformation benchmark (n=163 samples from Med-MMHL test set):** We validated MedContext against the Med-MMHL (Medical Multimodal Misinformation Benchmark), a research-grade dataset of real-world medical misinformation from fact-checking organizations. All contextual signals (Veracity, Alignment, Combined) evaluated using `google/medgemma-27b-it` (27B MedGemma, HuggingFace Inference API). Note: the 27B MedGemma multimodal variant on Vertex AI accepts DICOM format only — Med-MMHL images are JPEG/PNG from fact-checking organizations, making the 27B text-only HuggingFace model the correct and only viable 27B option for this dataset.

| Method                    | Approach                              | Accuracy  | Precision | Recall    | F1        |
| ------------------------- | ------------------------------------- | --------- | --------- | --------- | --------- |
| **Veracity Only**         | Claim analysis alone                  | 71.8%     | —         | —         | —         |
| **Alignment Only**        | Image-claim pair alone                | 71.2%     | —         | —         | —         |
| **Combined System (27B)** | Veracity + Alignment (5-fold CV)      | **94.5%** | **95.0%** | **98.5%** | **0.967** |

**Bootstrap 95% CI (27B model):** Accuracy [90.8%, 98.2%], Precision [91.3%, 98.6%], Recall [96.4%, 100.0%], F1 [0.945, 0.989]

**Key Finding:** Single contextual signals alone are insufficient—veracity achieves only 71.8% and alignment 71.2%. The combined system achieves 94.5% accuracy (95% CI: 90.8%-98.2%) with 98.5% recall, demonstrating that both dimensions are necessary for effective detection. Decision thresholds (veracity < 0.65, alignment < 0.30) were determined via 5-fold stratified cross-validation to avoid test-set contamination.

**Validation notes:** (1) Med-MMHL contains real-world medical misinformation from fact-checkers (LeadStories, FactCheck.org, Snopes). (2) 163-sample stratified random subset (seed=42) from 1,785 total test samples (83.4% misinformation rate, matching 83.0% base rate). (3) Validation used 2 of 4 contextual signals (veracity and alignment via MedGemma 27B; reverse image search and provenance chain not activated). (4) **Validation model:** `google/medgemma-27b-it` (27B, HuggingFace Inference API on A100 GPU) — chosen because Med-MMHL images are JPEG/PNG web images; the 27B Vertex AI variant accepts DICOM only and is format-incompatible with this dataset. **Production model:** `google/medgemma-1.5-4b-it` (4B multimodal, JPEG/PNG) for cost-efficient web image inference. See VALIDATION.md Part 11 and MODEL_CLARIFICATION.md for full model comparison.

## Solution: Agentic Contextual Authenticity

MedContext is an agentic AI system that assesses whether a medical image's accompanying claim is both medically accurate and supported by the visual evidence. The architecture separates clinical reasoning from strategic orchestration — an intentional design principle we describe as _"the doctor does doctor work; the manager does management work."_

### Architecture

The system operates in three phases:

**Phase 1 — Triage.** MedGemma performs clinical analysis: image type identification, anatomical findings, and claim plausibility assessment. This medical context is passed to a separate orchestrator LLM (Gemini 2.5 Pro), which decides which investigative tools to deploy based on the clinical assessment and claim characteristics. **Production deployment** uses `google/medgemma-1.5-4b-it` (4B multimodal, JPEG/PNG) for cost-efficient inference with standard web images; **validation experiments** used `google/medgemma-27b-it` (27B, HuggingFace) for superior text reasoning on claim veracity and alignment — the appropriate choice since Med-MMHL misinformation is claim-based rather than image-manipulation-based, and the 27B DICOM-only Vertex variant is not format-compatible with web images.

**Phase 2 — Dynamic Tool Dispatch.** The orchestrator invokes only the tools warranted by the triage — reverse image search via Google Cloud Vision API Web Detection for context verification, pixel forensics if manipulation is suspected, or provenance verification (C2PA manifest reading, SHA-256 hash-chained observation blocks, optional Polygon blockchain anchoring). For medically plausible claims with clear image alignment, unnecessary tools are skipped, reducing computational cost without sacrificing accuracy.

**Phase 3 — Evidence Synthesis.** The orchestrator aggregates MedGemma's clinical analysis with tool results into an explainable verdict — a veracity–alignment matrix that independently scores claim accuracy and image–claim alignment. Each assessment includes traceable reasoning with clear attribution ("per MedGemma's clinical analysis" versus "per investigative evidence").

This separation of concerns prevents domain overstepping: MedGemma never makes strategic decisions about which tools to run, and the orchestrator never makes medical judgements. LangGraph provides workflow visualisation and state management for the agentic pipeline.

### MedGemma Integration

MedGemma serves as the clinical reasoning backbone across multiple deployment configurations — HuggingFace (minimal setup), Vertex AI (production-grade), local inference (privacy-preserving), and vLLM (high-throughput). Its medical training data makes it uniquely suited for anatomical assessment and claim plausibility evaluation in ways that general-purpose LLMs are not. When the orchestrator LLM is unavailable, MedGemma serves as a complete fallback, ensuring the system degrades gracefully rather than failing.

## Implementation Quality

MedContext is production-ready, not a prototype:

- **4,100+ lines** of Python across a modular FastAPI backend with SQLAlchemy/PostgreSQL, Alembic migrations, and comprehensive error handling
- **51/51 tests passing** covering image integrity scoring, provenance chain verification, blockchain anchoring, reverse search caching, MedGemma Vertex AI integration, and agentic workflow defaults
- **Security hardened** with prompt injection protection (user context wrapped in explicit data-only markers), SSRF prevention via IP validation, tool whitelist enforcement, and rate-limited demo access
- **Full-stack deployment** with React 19 frontend, Docker support with health checks, and a Telegram bot for field verification
- **Reproducible** via documented setup with `.env.example` and Docker Compose

## Real-World Impact

MedContext is designed for deployment through the Health Equity & Resilience Observatory (HERO) at UBC, targeting clinical and public health settings across African health systems and other settings — environments where medical misinformation causes measurable harm and where resource constraints demand efficient, explainable tools. The Telegram bot integration provides accessible verification in settings where web applications are impractical. The system's cache-aware design and adaptive tool selection minimize API costs for sustained deployment.

The core insight: contextual authenticity, not pixel forensics, addresses the dominant misinformation threat and reframes the problem in a way that has implications beyond this specific tool, informing how health systems and platforms approach medical image verification at scale.

---

**Repository:** [github.com/drjforrest/MedContext-impact](https://github.com/drjforrest/MedContext-impact)
**Navigation:** See [START_HERE.md](../START_HERE.md) for judge-optimised reading paths (2-min, 10-min, 30-min)
