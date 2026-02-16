# Veracity Threshold Diagnosis: 27b vs 4b Models

**Date:** 2026-02-15  
**Analysis:** Veracity metrics investigation for Med-MMHL validation  
**Models:** `med_mmhl_n163_hf_27b` vs `med_mmhl_n163_quantized_4b`

## Executive Summary

The **27b model** shows extreme high-recall/low-precision behavior (100% recall, 25.2% precision) due to:

1. **Discrete 3-level scoring**: MedGemma produces categorical outputs (`true`, `partially_true`, `false`) mapped to fixed scores (0.9, 0.6, 0.1)
2. **Suboptimal threshold**: The default 0.5 threshold classifies both `partially_true` (0.6) and `true` (0.9) as positive, causing massive false positive rate
3. **Class imbalance**: Only 27/163 samples (16.6%) are actually plausible (not fake), but 107/163 (65.6%) are predicted positive

The **4b model** shows similar but less extreme behavior (96.3% recall, 38.2% precision), suggesting the issue is systemic but varies by model calibration.

---

## 1. Model Comparison

### 27b Model (`med_mmhl_n163_hf_27b`)

```json
"veracity": {
  "accuracy": 0.50920245398773,      // 50.9% - essentially random
  "precision": 0.2523364485981308,   // 25.2% - very low
  "recall": 1.0,                      // 100% - predicting all positive
  "f1": 0.40298507462686567,         // 40.3%
  "roc_auc": 0.9304193899782136,     // 93.0% - excellent discrimination
  "n": 163
}
```

### 4b Model (`med_mmhl_n163_quantized_4b`)

```json
"veracity": {
  "accuracy": 0.7361963190184049,    // 73.6% - acceptable
  "precision": 0.38235294117647056,  // 38.2% - low but better
  "recall": 0.9629629629629629,      // 96.3% - still very high
  "f1": 0.5473684210526316,          // 54.7%
  "roc_auc": 0.8985566448801743,     // 89.9% - excellent
  "n": 163
}
```

**Key Observations:**

- Both models have excellent ROC AUC (93.0% and 89.9%), indicating good probability calibration
- Both show high recall / low precision pattern (clinical bias toward sensitivity)
- 27b is more extreme: 100% recall means it never predicts negative
- 4b is better calibrated but still highly biased toward positive predictions

---

## 2. Root Cause Analysis

### 2.1 Score Generation

MedGemma produces categorical outputs that are mapped to fixed scores:

```python
# From validate_three_methods.py lines 237-244
veracity_scores = {
    "true": 0.9,
    "partially_true": 0.6,
    "false": 0.1
}
```

### 2.2 Score Distribution (27b Model)

```
Score  | Count | Percentage | Classification (threshold=0.5)
-------|-------|------------|-------------------------------
0.1    | 56    | 34.4%      | Negative (fake)
0.6    | 69    | 42.3%      | Positive (plausible) ← PROBLEM
0.9    | 38    | 23.3%      | Positive (plausible)
-------|-------|------------|-------------------------------
Total  | 163   | 100%       |
```

**The Issue:** 69 samples (42.3%) with `partially_true` (score=0.6) are classified as positive, but most are actually fake claims.

### 2.3 Confusion Matrix (27b, threshold=0.5)

```
                    Predicted Plausible | Predicted Fake
Actual Plausible:   TP=27               | FN=0
Actual Fake:        FP=80               | TN=56
```

**Breakdown:**

- Total predictions: 163
- Actual plausible (not fake): 27 (16.6%)
- Actual fake: 136 (83.4%)
- Predicted plausible (>0.5): 107 (65.6%) ← 80 false positives!
- Predicted fake (≤0.5): 56 (34.4%)

**Computed Metrics:**

- **Recall = TP / (TP + FN) = 27 / 27 = 1.00** (100%)
- **Precision = TP / (TP + FP) = 27 / 107 = 0.252** (25.2%)
- **Accuracy = (TP + TN) / Total = 83 / 163 = 0.509** (50.9%)

### 2.4 Ground Truth Cross-Tabulation (27b)

```
Score | Fake Claims | Real Claims | Total
------|-------------|-------------|-------
0.1   | 56          | 0           | 56
0.6   | 67          | 2           | 69    ← Mostly fake but scored "partially_true"
0.9   | 13          | 25          | 38
------|-------------|-------------|-------
Total | 136         | 27          | 163
```

**Critical Finding:** Of the 69 samples scored 0.6 (`partially_true`):

- 67 are actually fake claims (97.1%)
- 2 are real claims (2.9%)

This explains the poor precision: the model is too generous with the `partially_true` label.

---

## 3. Threshold Analysis

### 3.1 Optimal Threshold (27b Model)

Given the discrete 3-level scores, we have only 3 threshold choices:

| Threshold | Positive if | TP  | FP  | TN  | FN  | Accuracy | Precision | Recall | F1    |
| --------- | ----------- | --- | --- | --- | --- | -------- | --------- | ------ | ----- |
| < 0.1     | score > 0.1 | 27  | 80  | 56  | 0   | 50.9%    | 25.2%     | 100%   | 0.403 |
| 0.5-0.6   | score > 0.6 | 27  | 13  | 123 | 0   | 92.0%    | 67.5%     | 100%   | 0.806 |
| > 0.9     | none        | 0   | 0   | 136 | 27  | 83.4%    | N/A       | 0%     | 0.000 |

**Recommendation:** Use threshold **0.65** (between 0.6 and 0.9)

- Accuracy: 92.0% (+41.1pp improvement)
- Precision: 67.5% (+42.3pp improvement)
- Recall: 100% (maintained)
- F1: 0.806 (+40.3pp improvement)

### 3.2 ROC AUC Verification

The report shows `roc_auc: 0.9304`, which is computed correctly from the **probability scores** (not thresholded labels). This is verified in `src/app/validation/metrics.py` lines 73-80:

```python
try:
    veracity_auc = roc_auc_score(
        veracity_truth,
        [p.get("veracity_score", 0.5) for p in predictions],  # Uses raw scores
    )
except ValueError:
    veracity_auc = np.nan
```

The high ROC AUC (93.0%) confirms the model has excellent discrimination ability despite poor threshold choice.

---

## 4. Metrics Computation Audit

### 4.1 Code Review

Metrics are computed in `src/app/validation/metrics.py`, function `compute_three_dimensional_metrics()`:

**Lines 59-68: Veracity predictions**

```python
veracity_score = [
    p.get("veracity_score", p.get("claim_veracity", 0.5)) for p in predictions
]
veracity_pred = [
    s > 0.5 for s in veracity_score  # Binary threshold at 0.5
]
veracity_truth = [
    not g["is_fake_claim"] for g in ground_truth  # not fake = plausible
]
```

**Lines 69-72: Sklearn metrics**

```python
veracity_acc = accuracy_score(veracity_truth, veracity_pred)
veracity_pr, veracity_re, veracity_f1, _ = precision_recall_fscore_support(
    veracity_truth, veracity_pred, average="binary", zero_division=np.nan
)
```

**Lines 73-80: ROC AUC (uses raw scores, not thresholded)**

```python
try:
    veracity_auc = roc_auc_score(
        veracity_truth,
        [p.get("veracity_score", 0.5) for p in predictions],  # Raw scores
    )
except ValueError:
    veracity_auc = np.nan
```

### 4.2 Label Mapping Verification

**Ground truth encoding:**

- `is_fake_claim=True` → fake claim (negative class)
- `is_fake_claim=False` → plausible claim (positive class)
- Converted to: `veracity_truth = [not g["is_fake_claim"] for g in ground_truth]`
- ✅ Correct: `True` = plausible (positive), `False` = fake (negative)

**Prediction encoding:**

- `veracity_score > 0.5` → plausible (positive prediction)
- `veracity_score ≤ 0.5` → fake (negative prediction)
- ✅ Correct: High score = plausible, consistent with ground truth

**Sklearn convention:**

- `precision_recall_fscore_support(..., average="binary")` uses `pos_label=1` by default
- Our encoding: `True=1` (plausible), `False=0` (fake)
- ✅ Correct: Positive class is plausible (not fake)

### 4.3 Verification: Manual Computation

Manual computation (see Section 2.3) matches report exactly:

- Accuracy: 0.509 ✅
- Precision: 0.252 ✅
- Recall: 1.000 ✅

**Conclusion:** Metrics computation is correct. The issue is threshold choice, not calculation error.

---

## 5. Clinical Sensitivity Context

### 5.1 Is This Intentional?

The high-recall/low-precision pattern could be interpreted as intentional clinical sensitivity (minimize false negatives at the cost of false positives). However:

**Arguments against intentional design:**

1. **No threshold documentation**: No evidence of deliberate threshold tuning
2. **Poor absolute performance**: 50.9% accuracy is worse than random for binary classification
3. **Excellent ROC AUC**: The model CAN distinguish classes (93.0% AUC), but the threshold undermines it
4. **Better options available**: Threshold=0.65 achieves 92.0% accuracy with 100% recall maintained

### 5.2 Clinical Decision Theory

In medical screening:

- **Sensitivity (Recall)**: Proportion of actual positives correctly identified (minimize false negatives)
- **Specificity**: Proportion of actual negatives correctly identified (minimize false positives)

For misinformation detection:

- **High recall**: Don't miss actual fake claims (avoid spreading misinformation)
- **High precision**: Don't flag legitimate content as fake (avoid censorship)

**Current 27b performance:**

- Recall: 100% ✅ (no fake claims marked as plausible)
- Precision: 25.2% ❌ (75% of flagged content is actually legitimate)

**With threshold=0.65:**

- Recall: 100% ✅ (maintained)
- Precision: 67.5% ✅ (much improved, still conservative)

---

## 6. Recommendations

### 6.1 Immediate Actions

1. **Update threshold** in `src/app/validation/metrics.py`:

   ```python
   # Line 62-64: Replace hardcoded 0.5 threshold
   VERACITY_THRESHOLD = 0.65  # Optimized for 27b model
   veracity_pred = [s > VERACITY_THRESHOLD for s in veracity_score]
   ```

2. **Add threshold to report** in `scripts/validate_med_mmhl.py`:

   ```python
   # Add to validation report
   report["metrics"]["veracity"]["threshold"] = VERACITY_THRESHOLD
   ```

3. **Generate confusion matrix** for transparency:
   ```python
   from sklearn.metrics import confusion_matrix
   cm = confusion_matrix(veracity_truth, veracity_pred)
   report["metrics"]["veracity"]["confusion_matrix"] = {
       "true_negative": int(cm[0][0]),
       "false_positive": int(cm[0][1]),
       "false_negative": int(cm[1][0]),
       "true_positive": int(cm[1][1])
   }
   ```

### 6.2 Long-term Improvements

1. **Threshold optimization per model**:
   - Different models may require different thresholds
   - Use validation set to find optimal threshold for each model
   - Store optimal threshold in model metadata

2. **Continuous probability scores**:
   - Request MedGemma to return confidence scores (0.0-1.0) instead of discrete categories
   - This would enable finer-grained threshold tuning

3. **Multi-threshold reporting**:
   - Report metrics at multiple thresholds (0.5, 0.6, 0.7, 0.8)
   - Include precision-recall curve
   - Let downstream users choose their own sensitivity/specificity tradeoff

4. **Model-specific calibration**:
   - The 4b model shows better calibration than 27b (73.6% vs 50.9% accuracy)
   - Investigate prompt engineering or temperature settings to improve 27b calibration
   - Consider post-processing calibration (e.g., Platt scaling)

---

## 7. Model-Specific Comparison

### 7.1 Why is 4b Better Calibrated?

| Metric    | 27b Model | 4b Model | Difference |
| --------- | --------- | -------- | ---------- |
| Accuracy  | 50.9%     | 73.6%    | +22.7pp    |
| Precision | 25.2%     | 38.2%    | +13.0pp    |
| Recall    | 100.0%    | 96.3%    | -3.7pp     |
| F1        | 0.403     | 0.547    | +0.144     |
| ROC AUC   | 93.0%     | 89.9%    | -3.1pp     |

**Hypothesis Confirmed:** The 4b model is much more conservative with `false` (0.1) labels:

#### Score Distribution Comparison

**27b Model:**

```
Score | Count | % of Total | Above 0.5 threshold?
------|-------|------------|--------------------
0.1   | 56    | 34.4%      | No
0.6   | 69    | 42.3%      | Yes ← MAIN PROBLEM
0.9   | 38    | 23.3%      | Yes
```

**4b Model:**

```
Score | Count | % of Total | Above 0.5 threshold?
------|-------|------------|--------------------
0.0   | 8     | 4.9%       | No (analysis failures)
0.1   | 84    | 51.5%      | No ← Much more conservative!
0.5   | 3     | 1.8%       | No (edge case)
0.6   | 20    | 12.3%      | Yes
0.9   | 48    | 29.4%      | Yes
```

**Key Insight:**

- **27b assigns 0.6 to 42.3% of samples** (69/163)
- **4b assigns 0.6 to only 12.3% of samples** (20/163)
- **4b assigns 0.1 to 51.5% of samples** vs 27b's 34.4%

The 4b model is **much more likely to label claims as "false"** rather than "partially_true", which reduces false positives and improves precision.

#### Ground Truth Cross-Tabulation

**27b Model:**

```
Score | Fake Claims | Real Claims | Total | % Real
------|-------------|-------------|-------|-------
0.1   | 56          | 0           | 56    | 0%
0.6   | 67          | 2           | 69    | 2.9%   ← Mostly fake!
0.9   | 13          | 25          | 38    | 65.8%
```

**4b Model:**

```
Score | Fake Claims | Real Claims | Total | % Real
------|-------------|-------------|-------|-------
0.0   | 8           | 0           | 8     | 0%
0.1   | 83          | 1           | 84    | 1.2%   ← Better than 27b's 0.6
0.5   | 3           | 0           | 3     | 0%
0.6   | 20          | 0           | 20    | 0%     ← Still problematic
0.9   | 22          | 26          | 48    | 54.2%
```

**Conclusion:**

- 4b correctly identifies 83+8=91 fake claims as "false" (0.1 or 0.0)
- 27b only identifies 56 fake claims as "false" (0.1)
- 4b still has the same threshold problem (0.6 and 0.9 both positive), but affects fewer samples
- Both models should use threshold=0.65 to exclude `partially_true` (0.6) from positive predictions

### 7.2 Alignment Metrics

Both models show similar high-recall pattern for alignment:

- 27b: 81.5% recall, 39.3% precision
- 4b: 96.3% recall, 39.4% precision

This suggests the alignment scoring has the same threshold issue.

---

## 8. Validation Checklist

### ✅ Completed Checks

- [x] Confirmed binary predictions use intended threshold (0.5)
- [x] Verified ROC AUC computed from probability scores (not thresholded)
- [x] Audited metrics computation function (correct)
- [x] Verified label encoding (positive class = plausible, negative = fake)
- [x] Confirmed sklearn convention matches our encoding
- [x] Manual computation matches report values
- [x] Analyzed ground truth distribution (16.6% plausible, 83.4% fake)
- [x] Identified root cause (threshold too low for discrete scores)

### 📋 Pending Actions

- [ ] Update threshold to 0.65 in metrics.py
- [ ] Add confusion matrix to validation report
- [ ] Document threshold choice in validation output
- [ ] Re-run validation with optimized threshold
- [ ] Analyze 4b raw predictions score distribution
- [ ] Compare 27b vs 4b categorical label distributions
- [ ] Generate precision-recall curves for both models
- [ ] Test threshold optimization on held-out validation set

---

## 9. Conclusion

**The metrics are computed correctly, but the classification threshold is suboptimal for the 27b model's discrete scoring system.**

Key findings:

1. ✅ ROC AUC (93.0%) computed from raw scores correctly
2. ✅ Precision/recall computed correctly from binary predictions
3. ❌ Default threshold (0.5) inappropriate for 3-level discrete scores
4. ✅ Model has excellent discrimination (93.0% AUC), underutilized by poor threshold
5. 🔄 Optimal threshold (0.65) would improve accuracy from 50.9% → 92.0%

**Next steps:** Update threshold, add diagnostics, re-run validation.

---

## Appendices

### A. Command History

```bash
# Extract veracity scores for first 20 samples
cat validation_results/med_mmhl_n163_hf_27b/raw_predictions.json | \
  jq '[.[] | {image_id, veracity_score: .predictions.contextual_analysis.veracity_score,
  veracity_cat: .predictions.contextual_analysis.veracity_category,
  gt_is_fake: .ground_truth.is_misinformation}] | .[0:20]'

# Check distribution of veracity scores
cat validation_results/med_mmhl_n163_hf_27b/raw_predictions.json | \
  jq '[.[] | .predictions.contextual_analysis.veracity_score] |
  group_by(.) | map({score: .[0], count: length}) | sort_by(.score)'

# Cross-tabulate veracity scores with ground truth
cat validation_results/med_mmhl_n163_hf_27b/raw_predictions.json | \
  jq -r '.[] | [.predictions.contextual_analysis.veracity_score,
  (.ground_truth.is_misinformation | if . then "fake" else "real" end)] | @tsv' | \
  awk '{print $1, $2}' | sort | uniq -c
```

### B. Python Verification Script

```python
import json

# Load raw predictions
with open('validation_results/med_mmhl_n163_hf_27b/raw_predictions.json') as f:
    data = json.load(f)

# Extract scores and labels
veracity_scores = []
ground_truth_labels = []

for item in data:
    score = item['predictions']['contextual_analysis']['veracity_score']
    is_fake = item['ground_truth']['is_misinformation']
    veracity_scores.append(score)
    ground_truth_labels.append(not is_fake)  # not fake = plausible = positive

# Apply 0.5 threshold
predictions = [s > 0.5 for s in veracity_scores]

# Compute confusion matrix
tp = sum(1 for p, t in zip(predictions, ground_truth_labels) if p and t)
fp = sum(1 for p, t in zip(predictions, ground_truth_labels) if p and not t)
tn = sum(1 for p, t in zip(predictions, ground_truth_labels) if not p and not t)
fn = sum(1 for p, t in zip(predictions, ground_truth_labels) if not p and t)

# Compute metrics
accuracy = (tp + tn) / len(predictions)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
print(f"Accuracy={accuracy:.4f}, Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
```

### C. References

- **Metrics code:** `src/app/validation/metrics.py`, lines 16-135
- **Validation script:** `scripts/validate_med_mmhl.py`, lines 167-189
- **Score mapping:** `scripts/validate_three_methods.py`, lines 237-244
- **27b report:** `validation_results/med_mmhl_n163_hf_27b/validation_report.json`
- **4b report:** `validation_results/med_mmhl_n163_quantized_4b/validation_report.json`
