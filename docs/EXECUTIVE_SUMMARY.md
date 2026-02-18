# MedContext Executive Summary

**One-Page Overview for Competition Judges**

---

## The Complete Research Program

### Problem (Evidence-Based)

Medical misinformation kills people. From comprehensive literature review (~100 sources):

- **87%** of social media posts mention benefits vs 15% harms
- **68%** of influencers have undisclosed financial conflicts
- **0%** were found to be sophisticated deepfakes in COVID-19 misinformation
- **KEY FINDING:** Majority of threat = authentic images with misleading context

### Hypothesis (Testable)

If authentic images dominate misinformation, traditional pixel-level forensics (e.g. ELA) should fail, because
they look for pixel-level tampering — but the images are authentic. Medical images like DICOM require both
specialized tamper detection _and_ a separate contextual analysis layer to assess claim-image alignment.

### Validation on Real-World Misinformation (Med-MMHL Benchmark)

We validated MedContext against the **Med-MMHL (Medical Multimodal Misinformation Benchmark)**, a research-grade dataset of real-world medical misinformation from fact-checking organizations (LeadStories, FactCheck.org, Snopes, health authorities).

**Core Validation: Contextual Authenticity** (Med-MMHL, n=163, authentic images with misleading claims)

Med-MMHL images are predominantly authentic — misinformation resides primarily in the claim or image-claim pairing, not in pixel manipulation. This reflects the dominant real-world threat pattern: the majority of medical misinformation uses authentic images in misleading context. **Model used:** `google/medgemma-27b-it` (27B text-only MedGemma variant on HuggingFace Inference API with A100 GPU).

**Sampling methodology:** Stratified random sampling of 163 samples from the Med-MMHL test set (1,785 total, seed=42). The subset has an 83.4% misinformation rate (136/163), closely matching the full test set's 83.0% base rate. Samples include images with verifiable metadata (source URLs, fact-checker labels) to enable ground-truth validation. Sample size was constrained by the computational cost of running the 27B model via A100 GPU inference and the need for manual verification of image metadata and fact-checker labels; this results in wider confidence intervals and smaller cross-validation folds than a full-dataset evaluation would provide.

| Method              | Approach               | Accuracy  | Precision | Recall    | F1        | n   |
| ------------------- | ---------------------- | --------- | --------- | --------- | --------- | --- |
| **Veracity Only**   | Claim analysis alone   | 71.8%     | —         | —         | —         | 163 |
| **Alignment Only**  | Image-claim pair alone | 71.2%     | —         | —         | —         | 163 |
| **Combined System** | Veracity + alignment   | **94.5%** | **95.0%** | **98.5%** | **0.967** | 163 |

**Confusion Matrix (27B model, 5-fold CV):** Average across folds: TP≈134, FP≈7, TN≈20, FN≈2

**Bootstrap 95% CI (full dataset with CV-selected thresholds):** Accuracy [90.8%, 98.2%], Precision [91.3%, 98.6%], Recall [96.4%, 100.0%], F1 [0.945, 0.989]

**Key findings:**

1. **Veracity alone is insufficient:** 71.8% — claim plausibility without image context performs below effective detection threshold
2. **Alignment alone is insufficient:** 71.2% — image-claim consistency without claim assessment misses false-but-aligned pairs  
3. **Combined system shows substantial improvement:** 94.5% accuracy (+22-23 percentage points over either signal alone) on this 163-sample stratified random subset with `google/medgemma-27b-it`
4. **High precision and recall:** 95.0% precision and 98.5% recall on the 27B model (5-fold cross-validation)
5. **Model-dependent performance:** Results based on `google/medgemma-27b-it` (27B text-only variant, A100 GPU); smaller models show lower performance (90.8% with 4B quantized)

**Updated 4B Quantized Validation (February 17, 2026):**

The 4B quantized model was re-evaluated using the LangGraph agentic workflow with VERACITY_FIRST decision logic (veracity < 0.65 OR alignment < 0.30, 5-fold CV). Results improved from the initial 90.8% to **92.0% accuracy [87.7%, 95.7%]**, F1=0.951 [0.923, 0.975], with better recall (94.1% vs 89.7%) and balanced precision (96.2%). This demonstrates that the VERACITY_FIRST hierarchical decision logic outperforms simple α-weighted scoring for the 4B model. A three-variant comparison (IT full-precision, quantized GGUF, pre-trained base) is in progress. See [VALIDATION.md Part 12](./VALIDATION.md#part-12-three-variant-medgemma-comparison-february-2026) for details.

> **Critical Insight:** The majority of medical misinformation threats use authentic images in misleading context. Contextual authenticity (veracity + alignment) is what Med-MMHL validates. With the `google/medgemma-27b-it` model (27B text-only variant), the combined system achieves 94.5% accuracy where veracity alone reaches 71.8% and alignment alone reaches 71.2%, demonstrating both dimensions contribute to detection performance.
>
> **Methodology:** Decision thresholds (veracity < 0.65, alignment < 0.30) were determined via 5-fold stratified cross-validation (seed=42) to avoid test-set contamination. Thresholds were optimized on training folds only, with performance evaluated on held-out validation folds. Final reported metrics (94.5% accuracy, 95.0% precision, 98.5% recall) represent the mean performance across all validation folds. Bootstrap 95% confidence intervals computed on the full dataset using CV-selected thresholds: accuracy [90.8%, 98.2%], precision [91.3%, 98.6%], recall [96.4%, 100.0%], F1 [0.945, 0.989]. 
>
> **Limitations:** Stratified random sampling (seed=42) produces a 163-sample subset with 83.4% misinformation rate, closely matching the full test set's 83.0% base rate. With n=163, 5-fold CV yields only ~32–33 samples per validation fold, producing high variance in per-fold performance estimates. Bootstrap 95% CIs reflect this uncertainty (e.g., accuracy spans 7.4 pp from 90.8% to 98.2%). Results should be interpreted as performance on this 163-sample subset; the small fold sizes and wide confidence intervals limit generalizability and increase uncertainty for deployment-scale performance projections.
>
> **Scope:** Validation used the 2 core contextual signals (veracity and alignment) with `google/medgemma-27b-it` (27B text-only MedGemma variant). **Production deployment** uses `google/medgemma-1.5-4b-it` (4B multimodal variant) for cost-efficient inference. Optional add-on modules (reverse image search, provenance chain, pixel forensics) were not activated in this validation.

### Solution (MedContext)

First agentic AI system optimized for real-world threat distribution:

- **Core (80%):** MedGemma contextual authenticity (veracity + alignment)
- **Add-ons (20%):** Reverse search, provenance tracking, pixel forensics (DICOM-native + copy-move)

**Architecture:** 3-step agentic workflow (triage → dynamic tool dispatch → synthesis)

- **Triage:** MedGemma performs clinical analysis (image type, anatomical findings, claim plausibility)
- **MedGemma multimodal analysis:** Covers veracity and alignment for all image-claim pairs
- **LLM orchestrator:** Synthesizes across all signals into a single verdict
- **Production deployment:** Uses `google/medgemma-1.5-4b-it` (4B multimodal) for cost-efficient inference
- **Validation experiments:** Used `google/medgemma-27b-it` (27B text-only) to demonstrate best-case performance

### Quality (Production-Ready)

- **45/45 unit tests passing** (comprehensive test suite for core modules)
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

**Scientific:** Empirical evaluation providing evidence that single contextual signals (veracity alone 71.8%, alignment alone 71.2%) are each insufficient for contextual misinformation detection, while their combination reaches 94.5% accuracy (95% CI: [90.8%, 98.2%]) on a 163-sample Med-MMHL stratified random subset (seed=42) with MedGemma 27B. Decision thresholds determined via 5-fold cross-validation to avoid test-set contamination.
**Technical:** A multi-modal system using MedGemma for combined veracity + alignment assessment, demonstrated on the Med-MMHL benchmark with results suggesting that neither signal alone is sufficient
**Practical:** To our knowledge, first system with field deployment partnership targeting under-resourced clinical settings in Africa via HERO Lab, UBC

### Why MedContext Wins

✅ **Problem understanding:** Evidence-based from ~100-source literature review documenting that the majority of threat is authentic images in misleading context
✅ **Scientific rigor:** Empirical evaluation on 163-sample Med-MMHL stratified random subset showing single contextual signals (veracity 71.8%, alignment 71.2%) are each insufficient; combined system (94.5% accuracy, 95% CI: [90.8%, 98.2%] with MedGemma 27B) shows substantial improvement with proper cross-validated threshold selection
✅ **Technical quality:** Production-ready code with 45/45 tests, 4 MedGemma providers, full-stack architecture
✅ **Real-world path:** Field deployment partnership with HERO Lab, UBC targeting African Ministries of Health
✅ **Honest science:** Stratified random sampling with proper cross-validation to avoid test-set contamination, and results interpreted with appropriate uncertainty

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
