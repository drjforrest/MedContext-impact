# MedContext Proof of Justification

**Empirical Motivation for a Three-Dimensional Assessment Framework**

---

## Executive Summary

MedContext was developed **empirically motivated**, not feature-driven. This document describes the *Proof of Justification* studies that show **why** the three-dimensional framework (Pixel Authenticity, Veracity, Alignment) is necessary—and why conventional methods fail at the dominant real-world threat.

**Key Thesis:** Full contextual authenticity cannot be judged by pixel forensics alone or veracity alone. Only by adding the third dimension of **Alignment**—a task that requires multimodal medical AI (MedGemma)—can we detect whether misinformation is present.

---

## The Three Propositions We Sought to Prove

| Proposition | Conventional Methods | Failure Mode |
|------------|---------------------|--------------|
| **1. Pixel forensics CAN detect image integrity** | ELA, copy-move, DICOM header validation | ✅ Work when appropriate—but only for pixel tampering |
| **2. Pixel forensics FAIL on image-claim pairs** | When image is authentic but the pair is misinformation | ❌ Cannot assess whether the claim aligns with the image |
| **3. Veracity alone FAILS on alignment ambiguity** | Claim plausibility assessment | ❌ A claim can be plausible yet misaligned with the specific image |
| **4. Only Alignment completes the picture** | MedGemma on image-claim pair | ✅ Third dimension required for full contextual authenticity |

---

## Proof of Justification Studies (What We Did)

### PoJ 1: Conventional Pixel Forensics on Medical Images

**Hypothesis:** Conventional JPEG-based forensics (ELA) would fail on medical DICOM images because DICOM is not JPEG-compressed.

**Dataset:** 326 balanced images from UCI Tamper Detection (163 authentic, 163 manipulated). DICOM CT scans.

**Method:** Applied ELA (Error Level Analysis), which relies on JPEG compression artifacts.

**Result:** ELA achieved **49.9% accuracy** [95% CI: 44.5%, 55.5%]—indistinguishable from chance. ELA features showed no separability between authentic and manipulated DICOM images.

**What we proved:** ELA does not work on DICOM images. (DICOM files are not JPEG-compressed.)

**Limitation:** We selected a DICOM dataset without initially considering that DICOM requires specialized tampering detection methods. ELA was the wrong tool for DICOM from the start.

---

### PoJ 2: DICOM-Specific Methods vs. Format Reality

**Hypothesis:** Upon realizing our mistake, we switched to DICOM-native forensics (header integrity + copy-move on pixel array).

**Dataset:** 160 samples (120 BTD MRI PNGs + 40 UCI tampered DICOMs).

**Method:** Format-routed pixel forensics—DICOM → header integrity + copy-move; PNG/JPEG → copy-move.

**Result:** **97.5% accuracy** on image integrity (100% precision, 96.7% recall) for the pixel authenticity dimension.

**What we proved:** DICOM-specific methods work well on DICOM images. Copy-move detection works on PNG/JPEG.

**Critical limitation:** DICOM-specific methods apply only to DICOMs. In the real world, **~98% of medical images shared on social media and in misinformation contexts are PNG or JPEG**, not DICOM. So we proved that DICOM-native forensics work on DICOMs—but that is a minority use case for MedContext’s target threat (authentic images with misleading claims in PNG/JPEG format).

**Summary of PoJ 1 + PoJ 2:**
- ELA does not work on DICOM.
- DICOM-specific methods work on DICOM, but only on DICOM.
- Neither finding directly validates performance on the 98% of PNG/JPEG images where MedContext will operate.

---

### PoJ 3: Synthetic Image-Claim Pairs (Veracity + Alignment)

**Hypothesis:** MedGemma can assess veracity (claim plausibility) and alignment (image-claim consistency) as distinct dimensions.

**Dataset:** 160 image-claim pairs synthesized from BTD MRI (120 authentic) + UCI tampered DICOMs (40) with programmatically assigned claim templates. Ground truth labels were **synthetically generated**, not expert-annotated.

**Method:** Three-method validation—pixel forensics, veracity (claim alone), alignment (image-claim pair).

**Results:**
- **Veracity (claim alone):** 61.3% accuracy
- **Alignment (image-claim pair):** 56.9% accuracy
- **Contextual combined:** 65.6% on a subset of 90 pairs

**What we proved:** MedGemma can produce distinct veracity and alignment scores. The alignment dimension adds signal beyond veracity alone.

**Critical limitation:** The dataset was “thrown together” from existing tampering datasets with synthetic claim templates. It is not a real-world misinformation corpus. Labels are programmatic, not expert-annotated. The results are suggestive of capability but **do not constitute proper validation** of MedContext on authentic misinformation.

---

## Honest Summary of Proof of Justification

| Study | What We Proved | What We Did Not Prove |
|-------|----------------|------------------------|
| **PoJ 1** | ELA fails on DICOM (wrong tool for format) | Anything about PNG/JPEG or real-world misinformation |
| **PoJ 2** | DICOM-native forensics work on DICOM; copy-move works on PNG/JPEG | Generalizability to the 98% PNG/JPEG misinformation cases |
| **PoJ 3** | Veracity and alignment are distinct, measurable dimensions; MedGemma can assess both | Performance on real misinformation; reliability of synthetic labels |

**Conclusion:** These studies justify the *design* of MedContext—that three dimensions are needed and that alignment is a necessary third dimension. They do **not** validate MedContext’s performance on real-world medical misinformation.

---

## Why Proper Validation Is Needed

To validate MedContext rigorously, we need:

1. **Real-world image-claim pairs** with ground truth from fact-checkers or expert annotation
2. **Datasets that match the threat model:** authentic images with misleading claims (context manipulation), not just pixel tampering
3. **Format relevance:** PNG/JPEG images, which dominate social media and misinformation contexts

**Planned validation:** See [NEXT_STEPS_FOR_VALIDATION.md](../NEXT_STEPS_FOR_VALIDATION.md) for the strategy using Med-MMHL and AMMeBa.

---

## References

- **UCI Tamper Detection:** Mirsky et al. (2019). CT-GAN: Malicious Tampering of 3D Medical Imagery. USENIX Security.
- **BTD Dataset:** Graboski, Mirsky (2024). Back-in-Time Diffusion. ACM TIST.
- **Literature:** Brennen et al. (2021). Over half of visual misinformation = authentic images with false context.

---

**Document Status:** Proof of Justification (design motivation) — distinct from Validation (performance evaluation)  
**Last Updated:** February 2026
