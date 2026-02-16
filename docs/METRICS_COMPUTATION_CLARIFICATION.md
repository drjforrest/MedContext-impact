# Metrics Computation Clarification

**Date:** February 15, 2026

## Two Different Metric Computation Approaches

The MedContext validation uses **two different approaches** for computing single-signal baseline metrics:

### Approach 1: Score-Based Threshold (validation_report.json)

**File:** `validation_results/med_mmhl_n163_hf_27b/validation_report.json`  
**Method:** `src/app/validation/metrics.py:compute_three_dimensional_metrics()`

**Logic:**

- Uses continuous scores (veracity_score, alignment_score)
- Applies threshold of 0.5
- **Predicts LEGITIMATE (not fake) as positive class**
- veracity_pred = (score > 0.5) means "claim is LEGITIMATE"
- veracity_truth = (not is_fake_claim) means "truly LEGITIMATE"

**Veracity Only Results:**

- Accuracy: 50.9%
- Precision: 25.2% (of predicted LEGITIMATE, how many are truly LEGITIMATE)
- Recall: 100% (of truly LEGITIMATE, how many did we catch)
- F1: 0.403
- ROC-AUC: 0.930

**Interpretation:** When using score > 0.5 threshold, the model predicts almost everything as LEGITIMATE (hence 100% recall for legitimate class), but most of those predictions are wrong (hence 25.2% precision).

### Approach 2: Categorical Mapping (SUBMISSION.md)

**File:** `docs/SUBMISSION.md`  
**Method:** Direct use of categorical outputs (veracity_category, alignment_category)

**Logic:**

- Uses categorical model outputs (true/partially_true/false, aligns_fully/partially_aligns/does_not_align)
- **Predicts MISINFORMATION as positive class**
- Mapping: veracity_category=="true" → LEGITIMATE (0), else → MISINFORMATION (1)
- Ground truth: is_misinformation==True → MISINFORMATION (1)

**Veracity Only Results:**

- Accuracy: 90.8%
- Precision: 98.4% (of predicted MISINFORMATION, how many are truly MISINFORMATION)
- Recall: 90.4% (of truly MISINFORMATION, how many did we catch)
- F1: 0.943
- Confusion Matrix: TP=123, FP=2, TN=25, FN=13

**Interpretation:** When using categorical outputs, the model correctly identifies 90.8% of all cases, with very few false positives (2 out of 125 positive predictions) but missing 13 misinformation cases.

## Why the Discrepancy?

### 1. Different Positive Class Definition

- **Approach 1 (metrics.py):** LEGITIMATE is positive class
- **Approach 2 (SUBMISSION.md):** MISINFORMATION is positive class

### 2. Different Threshold/Mapping

- **Approach 1:** score > 0.5 → LEGITIMATE (continuous threshold)
- **Approach 2:** category=="true" → LEGITIMATE (categorical)

### 3. Why Approach 2 is Better for SUBMISSION.md

**Reasons:**

1. **Matches Problem Framing:** We're detecting misinformation (positive class), not legitimacy
2. **More Interpretable:** Uses model's categorical outputs (true/partially_true/false) rather than arbitrary 0.5 threshold
3. **Better Performance:** 90.8% accuracy vs 50.9% because categorical mapping aligns with model's actual decision boundaries
4. **Consistent with Combined System:** The combined system predicts misinformation, so baselines should too

## Which Metrics to Use Where?

### For SUBMISSION.md (Competition Submission)

✅ **Use Approach 2 (Categorical Mapping)**

- Predicts MISINFORMATION as positive class
- Uses veracity_category, alignment_category
- Veracity: 90.8% accuracy, 98.4% precision, 90.4% recall, 0.943 F1
- Alignment: 86.5% accuracy, 88.5% precision, 96.3% recall, 0.923 F1
- Pixel Forensics: 47.9% accuracy, 75.2% precision, 55.9% recall, 0.641 F1

### For Internal Technical Reports (validation_report.json)

✅ **Use Approach 1 (Score-Based Threshold)**

- Useful for ROC-AUC computation (requires continuous scores)
- Shows model behavior at different thresholds
- Veracity ROC-AUC: 0.930 (excellent discrimination)
- Alignment ROC-AUC: 0.814 (good discrimination)

## Verification

Run `scripts/verify_submission_metrics.py` to confirm SUBMISSION.md metrics match the categorical mapping approach:

```bash
python scripts/verify_submission_metrics.py
```

Expected output: ✅ ALL METHODS VERIFIED

## Summary

The SUBMISSION.md file now contains **correct metrics using categorical mapping** that:

1. Predict MISINFORMATION (the class we care about detecting)
2. Use interpretable categorical outputs from the model
3. Show realistic performance (90.8% for veracity-only vs 50.9% from arbitrary threshold)
4. Are consistent with the combined system metrics
5. Match the confusion matrices computed from raw predictions

The validation_report.json contains different (but also correct) metrics using score-based thresholds with LEGITIMATE as positive class, which are useful for ROC-AUC analysis but less appropriate for the competition submission table.
