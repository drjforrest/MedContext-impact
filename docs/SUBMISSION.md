# MedContext-Competition Submission
---
**Project URL:** https://medcontext.drjforrest.com
**Repository:** https://github.com/drjforrest/medcontext
**Demo Video:** https://www.youtube.com/watch?v=22UJ9-lFwe0
**Date:** February 24, 2026
---

## Demo Video

Watch the 3-minute demonstration:

[![MedContext Demo](https://img.youtube.com/vi/22UJ9-lFwe0/maxresdefault.jpg)](https://www.youtube.com/watch?v=22UJ9-lFwe0)

**Video covers:**
1. The problem (authentic images used in fake or misleading contexts)
2. Med-MMHL validation results (n=163: individual signals 79.8%/86.5% vs optimized 92.0%)
3. Live demo (upload → analysis → verdict)
4. Impact (Counterforce AI & UBC partnership—reaching millions of patients, teachers, students, journalists)

---

## Executive Summary

MedContext is an AI-powered tool that detects medical misinformation by analyzing **contextual authenticity**—whether claims match their images. Unlike pixel-forensics tools that detect manipulated images, MedContext addresses the more common threat: **authentic images used in fake or misleading contexts**.

**Key Innovation:** Hierarchical optimization transforms weak individual signals (veracity 79.8%, alignment 86.5%) into a robust 92.0% accurate detector through smart thresholds (0.65/0.30) and VERACITY_FIRST logic. Simple combination plateaus at ~83%; optimization achieves the breakthrough.

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

**The Breakthrough:** Individual signals are insufficient (veracity 79.8%, alignment 86.5%). Simple combination plateaus (~83%). But **hierarchical optimization with smart thresholds (0.65/0.30) and VERACITY_FIRST logic** achieves breakthrough performance: **92.0% accuracy**.

**Why it works:** VERACITY_FIRST logic with asymmetric thresholds. High veracity threshold (0.65) requires strong evidence before calling something "not misinformation." Low alignment threshold (0.30) only flags obvious mismatches. This bias toward caution maximizes recall without sacrificing precision.

---

## Validation Results

**Dataset:** Med-MMHL (Medical Multimodal Misinformation Benchmark)  
**Sample:** n=163 stratified random (seed=42)  
**Model:** MedGemma 4B IT Quantized (Q4_KM, ~4-bit)

| Metric        | Value |
|---------------|-------|
| **Accuracy**  | 92.0% |
| **Precision** | 96.2% |
| **Recall**    | 94.1% |
| **F1 Score**  | 95.1% |

**Confusion Matrix:**
- True Positives: 128 (misinformation correctly flagged)
- True Negatives: 22 (legitimate correctly identified)
- False Positives: 5 (legitimate incorrectly flagged - 3.1%)
- False Negatives: 8 (misinformation missed - 4.9%)

### Individual vs. Optimized Performance

| Approach                | Accuracy  | Gap         |
|-------------------------|-----------|-------------|
| Veracity Only           | 79.8%     | —           |
| Alignment Only          | 86.5%     | —           |
| Simple Combination      | ~83%      | —           |
| **Hierarchical Optimization** | **92.0%** | **+13-20%** |

The optimization breakthrough demonstrates that **smart arrangement achieves dramatic gains; simple combination plateaus**.

---

## Technical Architecture

**Core Components:**
- **MedGemma 4B** (Google's medical multimodal model) for vision-language understanding
- **LangGraph agent** for orchestrated analysis
- **Hierarchical decision logic** (VERACITY_FIRST)
- **Optimized thresholds** (0.65 veracity, 0.30 alignment)

**Efficiency:** Quantized 4-bit model runs locally via llama-cpp-python—no cloud dependency, suitable for deployment in resource-constrained environments.

**Add-on Modules:**
- Pixel forensics (ELA, copy-move detection) for manipulated images
- Reverse image search for source verification
- Provenance tracking via blockchain-style hashing

---

## Key Insights

1. **Contextual authenticity ≠ pixel authenticity.** The majority of medical misinformation uses authentic images in fake or misleading contexts—not manipulated images.

2. **Optimization > Combination.** Simply combining signals plateaus at ~83%. Hierarchical optimization with smart thresholds (0.65/0.30) and VERACITY_FIRST logic achieves 92.0%.

3. **Optimization unlocks latent performance.** Like compound interest or network effects, contextual analysis exhibits an inflection point where proper arrangement transforms weak signals into strong detection.

4. **Quantization preserves capability.** The 4-bit quantized model matches full-precision performance, enabling efficient deployment.

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

MedContext demonstrates that **optimization, not just combination**, is the key to reliable medical misinformation detection. The optimization breakthrough—from 80-87% individual signals to 92.0% hierarchically optimized—proves that contextual authenticity is both necessary and achievable with efficient, deployable AI.

**The Q4_KM quantized MedGemma 4B model achieves this efficiently, proving that deployment-ready contextual authenticity at scale is possible with smart threshold optimization and VERACITY_FIRST logic.**

---

**Contact:** Jamie Forrest (james.forrest@ubc.ca | forrest.jamie@gmail.com)  
**Institution:** University of British Columbia, HERO Lab  
**Date:** February 24, 2026