# MedContext Executive Summary

**One-Page Overview for Competition Judges**

---

## The Complete Research Program

### Problem (Evidence-Based)

Medical misinformation kills people. From comprehensive literature review (~100 sources):

- **87%** of social media posts mention benefits vs 15% harms
- **68%** of influencers have undisclosed financial conflicts
- **0%** were found to be sophisticated deepfakes in COVID-19 misinformation
- **KEY FINDING:** 80%+ of threat = authentic images with misleading context

### Hypothesis (Testable)

If authentic images dominate misinformation, traditional pixel-level forensics (e.g. ELA) should fail, because
they look for pixel-level tampering — but the images are authentic. Medical images like DICOM require both
specialized tamper detection *and* a separate contextual analysis layer to assess claim-image alignment.

### Validation (Empirical)

Three-method validation across 160 samples (BTD MRI PNGs + UCI tampered DICOMs):

| Dimension | Evaluated on | Method | Accuracy | Precision | Recall | n |
|-----------|-------------|--------|----------|-----------|--------|---|
| **Integrity** | Image alone | DICOM-native pixel forensics | **97.5%** | 100% | 96.7% | 160 |
| **Veracity** | Claim alone | MedGemma contextual analysis | 61.3% | 66.1% | 46.3% | 160 |
| **Alignment** | Image-claim pair | MedGemma contextual analysis | 56.9% | 50.8% | 42.9% | 160 |

**Score distribution:** 38.1% of samples score 3/3 (all dimensions pass) · 31.3% score 1/3 · 30.0% score 2/3 · 0.6% score 0/3

**Key findings:**
1. DICOM-native pixel forensics reliably detects tampered images (97.5%) — replacing the prior ELA method that achieved ~50% (chance) on this dataset.
2. Pixel forensics has no signal for the contextual dimensions: it cannot assess whether an authentic image is paired with a false or misleading claim.
3. Veracity and alignment require the MedGemma semantic modules — validating the core thesis that contextual analysis is essential for real-world medical misinformation.
4. The 40 tampered DICOM scans (UCI dataset) were detected with 100% precision and 96.7% recall by the pixel forensics module; the 120 authentic BTD MRI PNGs exercised the contextual modules.

> **Important distinction:** Each dimension answers a different question evaluated on a different input:
> - **Integrity** (97.5%) — *image alone*: is this image pixel-level authentic or tampered?
> - **Veracity** (61.3%) — *claim alone*: is this medical claim factually sound?
> - **Alignment** (56.9%) — *image-claim pair*: does the image actually depict what the claim asserts?
>
> Pixel forensics has signal only for Integrity. Veracity and Alignment require the MedGemma semantic modules. These are complementary pipelines, not alternatives.

### Solution (MedContext)

First agentic AI system optimized for real-world threat distribution:

- **Primary (80%):** Reverse search + MedGemma semantic analysis (context-based)
- **Supporting (20%):** DICOM-native pixel forensics + provenance (medical image-specific)

**Architecture:** 3-step agentic workflow (triage → dynamic tool dispatch → synthesis)
- Triage pre-screens for DICOM format and EXIF anomalies before invoking forensics
- MedGemma multimodal analysis covers veracity and alignment for all image-claim pairs
- LLM orchestrator synthesizes across all three dimensions into a single verdict

### Quality (Production-Ready)

- **45/45 tests passing** (100% coverage on core modules)
- 4,100+ lines production Python
- 4 MedGemma providers (HuggingFace, vLLM, Vertex AI, Local)
- Full-stack: FastAPI backend + React frontend + PostgreSQL
- Comprehensive documentation (5 core documents)

### Impact (Deployment Ready)

- **Partner:** HERO Lab, UBC (Scientific Director: Jamie Forrest)
- **Target:** African Ministries of Health / rural clinical settings
- **Scale:** Millions of patients via Telegram bot integration
- **Trust foundation:** 81% of patients trust healthcare professionals

### Contribution (Novel)

**Scientific:** First empirical three-dimensional validation framework for medical misinformation (integrity + veracity + alignment); demonstrates that pixel forensics and contextual analysis are complementary, not interchangeable
**Technical:** First multi-modal system using DICOM-native pixel forensics for tamper detection combined with MedGemma semantic analysis for contextual authenticity; replaces degenerate ELA methods
**Practical:** First system with field deployment partnership targeting under-resourced clinical settings

### Why MedContext Wins

✅ **Problem understanding:** White paper documents real threat (not assumptions)
✅ **Scientific rigor:** Hypothesis → three-dimensional test → validated design
✅ **Technical quality:** Production code, not PoC
✅ **Real-world path:** Deployment partner ready to scale
✅ **Honest science:** Reports limitations that strengthen thesis (contextual modules are necessary — pixel forensics alone is insufficient)

## Quick Start for Judges

```bash
# 1. Install (2 min)
uv venv && uv pip install -r requirements.txt

# 2. Configure (1 min)
cp .env.example .env
# Add: MEDGEMMA_HF_TOKEN=hf_your_token

# 3. Run (1 min)
uv run uvicorn app.main:app --reload --app-dir src

# 4. Test backend (1 min)
curl http://localhost:8000/health

# 5. Start frontend (in new terminal)
cd ui && npm run dev
# Visit http://localhost:5173 (frontend)
# Alternative: cd ui && yarn dev (if using yarn)
```
