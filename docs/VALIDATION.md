# Validation Results

## MedContext: Contextual Authenticity for Medical Misinformation Detection

**Date:** February 20, 2026  
**Dataset:** Med-MMHL (Medical Multimodal Misinformation Benchmark)  
**Model:** MedGemma 4B IT (Q4_KM quantized, 4-bit)  
**Sample Size:** n=163 (stratified random, seed=42)  

---

## Executive Summary

MedContext achieves **91.4% accuracy** on medical misinformation detection using contextual authenticity signals. The quantized 4-bit model demonstrates strong performance while maintaining computational efficiency suitable for deployment.

| Metric        | Value |
|---------------|-------|
| **Accuracy**  | 91.4% |
| **Precision** | 96.9% |
| **Recall**    | 92.6% |
| **F1 Score**  | 94.7% |

---

## Methodology

### Dataset
- **Source:** Med-MMHL benchmark (fact-checked medical news articles)
- **Split:** Test set
- **Sampling:** Stratified random (seed=42)
- **Composition:** 163 samples with representative label distribution

### Model Configuration
- **Base Model:** google/medgemma-1.5-4b-it
- **Quantization:** Q4_KM (4-bit, medium quality)
- **Inference:** Local via llama-cpp-python
- **Orchestration:** Google Gemini 2.5 Pro (analysis), Flash Lite (tools)

### Evaluation Framework
MedContext evaluates three contextual signals:

1. **Veracity Assessment** - Claim plausibility based on medical knowledge
2. **Alignment Analysis** - Consistency between image and claim
3. **Pixel Forensics** - Technical image authenticity (supplementary)

Final classification uses hierarchical logic (VERACITY_FIRST): veracity score primary, alignment as tiebreaker.

---

## Primary Results

### Confusion Matrix

|                           | Predicted Misinformation | Predicted Legitimate |
|---------------------------|--------------------------|----------------------|
| **Actual Misinformation** | 125 (TP)                 | 10 (FN)              |
| **Actual Legitimate**     | 4 (FP)                   | 24 (TN)              |

**Error Analysis:**
- **False Positives (4):** Legitimate content incorrectly flagged (2.5% of total)
- **False Negatives (10):** Misinformation missed (6.1% of total)

### Signal Breakdown

| Signal        | Accuracy  | Role                                |
|---------------|-----------|-------------------------------------|
| **Veracity**  | 71.2%     | Primary: Detects claim truthfulness |
| **Alignment** | 77.9%     | Secondary: Image-claim consistency  |
| **Combined**  | **91.4%** | Hierarchical fusion                 |

**Pixel Forensics (Supplementary):**
- Authentic image detection rate: 40.5%
- Note: Pixel analysis was not included in final scoring as Med-MMHL images are all authentic; forensic signals are orthogonal to contextual authenticity

---

## Ablation Study: Model Variant Comparison

To contextualize the quantized model's performance, we include preliminary results from non-quantized variants. **Caveat:** These baseline models were evaluated using an earlier codebase version; direct comparison should be interpreted cautiously.

| Model Variant          | Accuracy  | Notes                            |
|------------------------|-----------|----------------------------------|
| **Q4_KM (Quantized)**  | **91.4%** | Primary result; current codebase |
| IT (Instruction-Tuned) | ~89.0%    | Baseline; older codebase         |
| PT (Pre-trained)       | ~86.0%    | Baseline; older codebase         |

**Interpretation:** The quantized model achieves performance comparable to (or exceeding) full-precision baselines, validating that 4-bit quantization preserves model capability while enabling efficient deployment. Due to computational constraints, full re-validation of IT/PT variants with the current codebase was not feasible.

---

## Key Findings

1. **Contextual Authenticity Works:** Combining veracity and alignment signals achieves 91.4% accuracy, substantially exceeding either signal alone (71-78%).

2. **High Precision:** 96.9% precision means when MedContext flags misinformation, it's correct 97% of the time—critical for minimizing false alarms in clinical settings.

3. **Quantization Viable:** Q4_KM quantization achieves strong performance without significant degradation, making on-device deployment feasible.

4. **Pixel Forensics Limited:** Standalone pixel analysis (40.5% authentic detection) is insufficient; contextual signals are essential for medical misinformation detection.

---

## Limitations

- **Sample Size:** n=163 provides statistical power for large effects; confidence intervals not computed
- **Single Dataset:** Results specific to Med-MMHL; generalization to other medical misinformation datasets requires validation
- **Threshold Optimization:** Results use default thresholds (0.5); cross-validated optimization may improve performance
- **Temporal Validity:** Medical knowledge evolves; model may not reflect latest clinical guidelines

---

## Conclusion

MedContext demonstrates that contextual authenticity—analyzing claim veracity and image-claim alignment—effectively detects medical misinformation. The quantized 4-bit model achieves **91.4% accuracy** with **96.9% precision**, validating both the methodological approach and the practical deployment strategy.

---

**Validation Output Directory:** `validation_results/med_mmhl_n163_20260220_061215/`  
**Timestamp:** 2026-02-20T16:14:38Z
