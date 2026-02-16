# MedContext Proof of Justification

**Empirical Motivation for Contextual Authenticity Analysis**

---

## Executive Summary

MedContext was developed **empirically motivated**, not feature-driven. This document describes the _Proof of Justification_ studies that show **why** contextual authenticity requires both veracity and alignment together—and why conventional methods fail at the dominant real-world threat.

**Key Thesis:** Full contextual authenticity cannot be judged by veracity alone or alignment alone. Only by combining **both Veracity and Alignment**—requiring multimodal medical AI (MedGemma)—can we effectively detect contextual misinformation.

---

## Core Framework: Failure Modes and Solution

| Proposition                                        | Conventional Methods          | Failure Mode                                                                 |
| -------------------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------- |
| **1. Veracity alone FAILS on alignment ambiguity** | Claim plausibility assessment | ❌ A claim can be plausible yet misaligned with the specific image           |
| **2. Alignment alone FAILS on claim accuracy**     | Image-claim consistency       | ❌ Image and claim can be consistent but the claim itself is factually false |
| **3. Combined approach is necessary**              | MedGemma veracity + alignment | ✅ Both dimensions required for full contextual authenticity                 |

---

## Proof of Justification Studies (What We Did)

### PoJ 3: Image-Claim Pairs (Veracity + Alignment) — Core Thesis

**Hypothesis:** MedGemma can assess veracity (claim plausibility) and alignment (image-claim consistency) as distinct but complementary dimensions.

**Dataset:** 160 image-claim pairs synthesized from BTD MRI (120 authentic) + UCI tampered DICOMs (40) with programmatically assigned claim templates. Ground truth labels were **synthetically generated**, not expert-annotated.

**Method:** Validation of contextual signals—veracity (claim alone), alignment (image-claim pair).

**Results:**

- **Veracity (claim alone):** 61.3% accuracy
- **Alignment (image-claim pair):** 56.9% accuracy
- **Contextual combined:** 65.6% on a subset of 90 pairs

**What we proved:** MedGemma can produce distinct veracity and alignment scores. The alignment dimension adds signal beyond veracity alone.

**Critical limitation:** The dataset used synthetic claim templates, not real-world misinformation. Labels are programmatic, not expert-annotated. The results are suggestive of capability but **do not constitute proper validation** of MedContext on authentic misinformation.

**Real validation:** See Med-MMHL results (96.3% accuracy with veracity + alignment) in [VALIDATION.md](./VALIDATION.md).

---

### PoJ 1 & PoJ 2: Pixel Forensics Studies (Optional Add-on Module)

**Context:** These studies validated that pixel forensics methods work for detecting manipulated images—a separate task from contextual misinformation detection.

**PoJ 1 Result:** ELA achieved 49.9% accuracy on DICOM images (wrong tool for DICOM format—DICOM is not JPEG-compressed).

**PoJ 2 Result:** DICOM-native forensics achieved 97.5% accuracy on image integrity when using format-appropriate methods (DICOM header validation + copy-move for pixel array).

**Key Limitation:** These studies validated pixel forensics on manipulated-image datasets. However, **~98% of real-world medical misinformation uses authentic PNG/JPEG images** in misleading contexts (Brennen et al., 2021). Pixel forensics is an optional add-on module for MedContext, not part of the core contextual authenticity validation. The pixel forensics add-on addresses a different threat (pixel manipulation) on a different dataset type.

---

## Honest Summary of Proof of Justification

| Study         | What We Proved                                                                                | What We Did Not Prove                                                               |
| ------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **PoJ 3**     | Veracity and alignment are distinct, measurable dimensions; MedGemma can assess both          | Performance on real misinformation; reliability of synthetic labels                 |
| **PoJ 1 & 2** | Pixel forensics work when format-appropriate (DICOM-native for DICOM, copy-move for PNG/JPEG) | Relevance to contextual misinformation (98% uses authentic images, not manipulated) |

**Conclusion:** These studies justify the _design_ of MedContext's contextual authenticity approach—that both veracity and alignment are necessary. They do **not** validate MedContext's performance on real-world medical misinformation. For proper validation on real misinformation, see Med-MMHL results in [VALIDATION.md](./VALIDATION.md).

---

## Why Proper Validation Is Needed

To validate MedContext rigorously, we need:

1. **Real-world image-claim pairs** with ground truth from fact-checkers or expert annotation
2. **Datasets that match the threat model:** authentic images with misleading claims (context manipulation), not just pixel tampering
3. **Format relevance:** PNG/JPEG images, which dominate social media and misinformation contexts

**Completed validation:** Med-MMHL benchmark (n=163) achieves 96.3% accuracy with veracity + alignment. See [VALIDATION.md](./VALIDATION.md) for full results.

---

## References

- **UCI Tamper Detection:** Mirsky et al. (2019). CT-GAN: Malicious Tampering of 3D Medical Imagery. USENIX Security.
- **BTD Dataset:** Graboski, Mirsky (2024). Back-in-Time Diffusion. ACM TIST.
- **Literature:** Brennen et al. (2021). Over half of visual misinformation = authentic images with false context.
- **Med-MMHL:** Sun, Y., He, J., Lei, S., Cui, L., & Lu, C.-T. (2023). Med-MMHL: A Multi-Modal Dataset for Detecting Human- and LLM-Generated Misinformation in the Medical Domain. arXiv preprint arXiv:2306.08871. https://arxiv.org/abs/2306.08871 | Dataset: https://github.com/styxsys0927/Med-MMHL

---

**Document Status:** Proof of Justification (design motivation) — distinct from Validation (performance evaluation)  
**Last Updated:** February 2026
