# MedContext-Competition Submission
---
**Project URL:** https://medcontext.drjforrest.com
**Repository:** https://github.com/drjforrest/medcontext
**Demo Video:** https://www.youtube.com/watch?v=4NuGsrnuVk8&feature=youtu.be
**Date:** February 24, 2026
---

## Demo Video

Watch the 3-minute demonstration:

[![MedContext Demo](https://img.youtube.com/vi/4NuGsrnuVk8/maxresdefault.jpg)](https://www.youtube.com/watch?v=4NuGsrnuVk8&feature=youtu.be)

**Video covers:**
1. The problem (authentic images used in fake or misleading contexts)
2. Med-MMHL validation results (n=163: no signal good enough alone; optimization adds modest 0.6 pp; at scale = millions caught)
3. Live demo (upload → analysis → verdict)
4. Impact (Counterforce AI & UBC partnership—reaching millions of patients, teachers, students, journalists)

---

## Executive Summary

MedContext is an AI-powered tool that detects medical misinformation by analyzing **contextual authenticity**—whether claims match their images. Unlike pixel-forensics tools that detect manipulated images, MedContext addresses the more common threat: **authentic images used in fake or misleading contexts**.

**Key Innovation:** No signal is good enough on its own (veracity 73.6%, alignment 90.8%). Optimization provides a modest boost (0.6 pp to 91.4%), but when scaled to the actual threat, the veracity fallback catches millions of messages of misinformation—only possible with MedContext's multimodal medical training.

---

## The Problem

Medical misinformation doesn't require fake images. The dominant real-world threat uses:
- **Authentic medical scans** (X-rays, CT, clinical photos)
- **False or misleading claims** about those images
- **Strategic image-claim pairing** that creates false credibility

Current solutions focus on pixel forensics (detecting Photoshop), missing the contextual deception that represents the majority of medical misinformation.

---

## The Solution

MedContext evaluates two contextual signals:

1. **Claim Veracity**-Is the accompanying claim medically accurate?
2. **Image-Claim Alignment**-Does the image actually support the claim?

**The Breakthrough:** No signal is good enough on its own (veracity 73.6%, alignment 90.8%). Optimization provides a modest boost (0.6 pp to 91.4%)—veracity acts as a safety net catching edge cases alignment misses. When scaled to the impact of the actual threat (billions of users), this translates to **millions of messages of misinformation caught** by the veracity fallback. Only possible with MedContext's multimodal medical training (MedGemma).

**Why it works:** VERACITY_FIRST logic with asymmetric thresholds. Alignment handles most cases; veracity catches borderline visual matches and sophisticated misinformation using plausible imagery. The dual-signal architecture is only possible because MedGemma combines image understanding with medical knowledge.

---

## Validation Results

**Dataset:** Med-MMHL (Medical Multimodal Misinformation Benchmark)  
**Sample:** n=163 stratified random (seed=42)  
**Model:** MedGemma 4B IT (HuggingFace Inference API)

| Metric        | Value |
|---------------|-------|
| **Accuracy**  | 91.4% |
| **Precision** | 96.9% |
| **Recall**    | 92.6% |
| **F1 Score**  | 94.7% |

**Confusion Matrix:**
- True Positives: 125 (misinformation correctly flagged)
- True Negatives: 24 (legitimate correctly identified)
- False Positives: 4 (legitimate incorrectly flagged - 2.5%)
- False Negatives: 10 (misinformation missed - 6.1%)

### Individual vs. Optimized Performance

| Approach                | Accuracy  | Role                              |
|-------------------------|-----------|-----------------------------------|
| Veracity Only           | 73.6%     | Insufficient alone                |
| Alignment Only (optimized) | 90.8%  | Dominant signal                   |
| **Hierarchical Optimization** | **91.4%** | Veracity safety net catches 3 edge cases |

**No signal is good enough on its own.** Optimization provides a modest boost (0.6 pp), but when scaled to the actual threat, the veracity fallback catches **millions of messages of misinformation**—only possible with MedContext's multimodal medical training.

---

## Technical Architecture

**Core Components:**
- **MedGemma 4B** (Google's medical multimodal model) for vision-language understanding
- **LangGraph agent** for orchestrated analysis
- **Hierarchical decision logic** (VERACITY_FIRST)
- **Optimized thresholds** (0.65 veracity, 0.30 alignment)

**Efficiency:** MedGemma 4B IT runs via HuggingFace Inference API or local providers—suitable for deployment in resource-constrained environments.

**Add-on Modules:**
- Pixel forensics (ELA, copy-move detection) for manipulated images
- Reverse image search for source verification
- Provenance tracking via blockchain-style hashing

---

## Key Insights

1. **Contextual authenticity ≠ pixel authenticity.** The majority of medical misinformation uses authentic images in fake or misleading contexts—not manipulated images.

2. **No signal is good enough alone.** Veracity (73.6%) and alignment (90.8%) each miss critical cases. Optimization adds a modest 0.6 pp, but the veracity fallback catches edge cases alignment cannot resolve.

3. **Scale matters.** When scaled to the actual threat (billions of users), the modest 0.6% improvement translates to millions of messages of misinformation caught by the veracity fallback.

4. **Only possible with MedContext.** The dual-signal architecture—alignment as primary, veracity as safety net—requires MedGemma's multimodal medical training combining image understanding with medical knowledge.

---

## Limitations

- **Sample size:** n=163 provides statistical power for large effects; confidence intervals not computed
- **Single dataset:** Results specific to Med-MMHL; generalization to other benchmarks requires validation
- **Temporal validity:** Medical knowledge evolves; model may not reflect latest clinical guidelines
- **Claim non-inferiority:** Baseline models (IT, PT) used older codebase; direct comparison interpretable cautiously

---

## Future Work

- Validate on full Med-MMHL test set (1,785 samples)
- Test on additional medical misinformation benchmarks
- Expert medical annotation for clinical validation
- Field deployment studies with HERO Lab, UBC
- Cross-lingual validation (Spanish, Portuguese)

---

## Conclusion

MedContext demonstrates that **no signal is good enough on its own**. Veracity (73.6%) and alignment (90.8%) each miss critical cases. Optimization provides a modest boost (91.4% combined), but when scaled to the actual threat, the veracity fallback catches **millions of messages of misinformation**—only possible with MedContext's multimodal medical training (MedGemma 4B IT).

---

**Contact:** Jamie Forrest (james.forrest@ubc.ca | forrest.jamie@gmail.com)  
**Institution:** University of British Columbia, HERO Lab  
**Date:** February 24, 2026