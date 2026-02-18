# Model Version Clarification

**Date:** February 15, 2026
**Issue:** Model capabilities and appropriate use cases for MedGemma variants
**Status:** ✅ RESOLVED (corrected from earlier erroneous framing)

---

## Summary

Google provides three MedGemma variants. The correct model for Med-MMHL validation is
`google/medgemma-27b-it` (27B text-only via HuggingFace) because Med-MMHL uses standard
web images (JPEG/PNG from fact-checking organizations), not clinical DICOM files.

---

## MedGemma Model Variants

| Model | Identifier | Input | Deployment | Use Case |
|-------|-----------|-------|------------|----------|
| **4B multimodal** | `google/medgemma-1.5-4b-it` | JPEG/PNG + text | HuggingFace API | Production: web image + claim analysis |
| **27B text-only** | `google/medgemma-27b-it` | Text only | HuggingFace API | Validation: claim text + medical context |
| **27B multimodal** | `google/medgemma-27b-it` | **DICOM only** + text | Vertex AI Model Garden | Clinical radiology (CT, MRI, X-ray DICOM) |

## Why the 27B Multimodal is NOT Suitable for Med-MMHL

The Vertex AI 27B multimodal endpoint (`google_medgemma-27b-it-dicom-mg-one-click-deploy`)
accepts only **DICOM format** clinical imaging files. Med-MMHL images are sourced from
fact-checking organizations (LeadStories, FactCheck.org, Snopes) and are standard
JPEG/PNG web images — not DICOM. Attempting to use the Vertex endpoint with Med-MMHL
images would fail at format validation.

**Conclusion:** There is no 27B MedGemma variant that handles standard JPEG/PNG web
images. The 27B text-only model (HuggingFace) is the correct and only viable 27B option
for Med-MMHL validation.

---

## Validation Model Choice: Justified

**Med-MMHL validation used:** `google/medgemma-27b-it` (27B text-only, HuggingFace
Inference API, A100 GPU)

**Why this is correct:**

- Med-MMHL misinformation resides primarily in the claim or image-claim pairing, not
  in the image itself (majority are authentic images with misleading context)
- The dominant analytical task is **claim veracity** and **contextual alignment** —
  both are text reasoning tasks
- The 27B model provides superior text reasoning over the 4B model
- The 4B multimodal model can encode JPEG/PNG images, but for this dataset the
  contextual claim analysis is the primary signal
- The 27B DICOM multimodal on Vertex AI is designed for radiology reading — a
  fundamentally different task

**Performance:**
- Combined System (Veracity + Alignment): **88.3% accuracy**, 88.7% precision, 98.5% recall, 0.934 F1
- Veracity Only: 90.8% accuracy
- Alignment Only: 86.5% accuracy

---

## Production Model: 4B Multimodal

**Default production configuration** (`src/app/core/config.py` line 16):

- **Model:** `google/medgemma-1.5-4b-it`
- **Input:** JPEG/PNG images + text (appropriate for web-sourced medical images)
- **Deployment:** HuggingFace Inference API
- **Rationale:** Only MedGemma variant that handles standard web images with multimodal
  encoding AND is cost-efficient for production workloads
- **Performance:** 90.8% accuracy on Med-MMHL (quantized 4B, local LM Studio, threshold-optimized)

---

## Vertex AI DICOM Endpoint

An existing Vertex AI endpoint exists for a different use case:

- **Endpoint:** `google_medgemma-27b-it-dicom-mg-one-click-deploy`
- **Region:** us-central1
- **Hardware:** 1x NVIDIA A100 80GB
- **Input:** DICOM format only
- **Use case:** Clinical radiology assistance (CT, MRI, X-ray reading)
- **NOT used for:** Med-MMHL validation (wrong image format)

This endpoint is intentionally separate from the web image misinformation detection
pipeline and consumes A100 quota in us-central1.

---

## Model Selection Summary

| Task | Correct Model | Reason |
|------|--------------|--------|
| Med-MMHL validation | 27B text-only (HF) | Best text reasoning; DICOM constraint rules out 27B multimodal |
| Production web images | 4B multimodal (HF) | Only variant supporting JPEG/PNG with multimodal encoding |
| Clinical DICOM reading | 27B multimodal (Vertex) | DICOM format, radiology-specific task |

---

## Configuration Reference

**`.env` (validation):**
```bash
MEDGEMMA_MODEL=google/medgemma-1.1-4b-it \
MEDGEMMA_VLLM_URL=https://vt5q953aaaoh81sn.us-east-1.aws.endpoints.huggingface.cloud/v1/chat/completions
```

**`src/app/core/config.py` (production default):**
```python
medgemma_model: str = "google/medgemma-1.1-4b-it"  # 4B multimodal for web images
```

**`validation_results/` directories:**
- `med_mmhl_n163_hf_27b/` — 27B text-only results (HuggingFace, A100)
- `med_mmhl_n163_quantized_4b/` — 4B quantized results (local LM Studio)
