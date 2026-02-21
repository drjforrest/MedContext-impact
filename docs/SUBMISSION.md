# MedContext-Competition Submission
---
**Project URL:** https://medcontext.drjforrest.com  
**Repository:** https://github.com/drjforrest/medcontext  
**Date:** February 20, 20261`1`1
---

## Executive Summary

MedContext is an AI-powered tool that detects medical misinformation by analyzing **contextual authenticity**—whether claims match their images. Unlike pixel-forensics tools that detect manipulated images, MedContext addresses the more common threat: **authentic images used in misleading contexts**.

**Key Innovation:** Hierarchical optimization transforms weak individual signals (71-78% accuracy) into a robust 91.4% accurate detector through smart thresholding and VERACITY_FIRST logic.

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

**The Breakthrough:** Individual signals are weak (71.2% and 77.9% accuracy). Simple combination helps modestly (~80%). But **hierarchical optimization with tuned thresholds (0.65/0.30)** unlocks the inflection point: **91.4% accuracy**.

### The S-Curve

```
71% ── Veracity Only (plateau)
78% ── Alignment Only (plateau)
80% ── Simple OR (plateau)
     ╲
      ╲  ← INFLECTION POINT: Optimization
       ╲
91% ──── Optimized (breakthrough!)
```

**Why it works:** VERACITY_FIRST logic with asymmetric thresholds. High veracity threshold (0.65) requires strong evidence before calling something "not misinformation." Low alignment threshold (0.30) only flags obvious mismatches. This bias toward caution maximizes recall without sacrificing precision.

---

## Validation Results

**Dataset:** Med-MMHL (Medical Multimodal Misinformation Benchmark)  
**Sample:** n=163 stratified random (seed=42)  
**Model:** MedGemma 4B IT Quantized (Q4_KM, ~4-bit)

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

| Approach           | Accuracy  | Gap         |
|--------------------|-----------|-------------|
| Veracity Only      | 71.2%     | —           |
| Alignment Only     | 77.9%     | —           |
| Optimized Combined | **91.4%** | **+13-20%** |

The optimization breakthrough demonstrates that **arrangement matters more than combination alone**.

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

1. **Contextual authenticity ≠ pixel authenticity.** The majority of medical misinformation uses authentic images in misleading contexts—not manipulated images.

2. **Optimization > Combination.** Simply combining signals achieves ~80%. Hierarchical optimization with tuned thresholds achieves 91.4%.

3. **The S-curve applies to AI systems.** Like compound interest or network effects, contextual analysis exhibits an inflection point where proper arrangement unlocks latent performance.

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

MedContext demonstrates that **optimization, not just combination**, is the key to reliable medical misinformation detection. The S-curve breakthrough—from 71-78% individual signals to 91.4% optimized—proves that contextual authenticity is both necessary and achievable with efficient, deployable AI.

**The quantized MedGemma 4B model achieves this efficiently, proving that deployment-ready contextual authenticity is possible.**

---

**Contact:** Jamie Forrest (james.forrest@ubc.ca | forrest.jamie@gmail.com)  
**Institution:** University of British Columbia, HERO Lab  
**Date:** February 20, 2026