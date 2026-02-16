# Output Labeling Improvements

**Date:** 2026-02-15  
**Scope:** Validation outputs, chart data, and metrics reports

## Overview

Improved labeling across all validation outputs to provide clarity on:

1. **Model identification** (27B vs 4B)
2. **Classification thresholds** (0.5 default, optimization available)
3. **Class definitions** (positive/negative, misinformation/legitimate)
4. **Score semantics** (categorical mappings and meanings)
5. **Decision logic** (how predictions are made)

## Changes Made

### 1. Model Identification

#### validation_report.json

Added model metadata to all validation reports:

```json
{
  "model_name": "med_mmhl_n163_hf_27b",
  "model_label": "MedGemma 27B (HuggingFace Inference API)"
}
```

**Model Labels:**

- `MedGemma 27B (HuggingFace Inference API)` - for directories with "27b" and "hf"
- `MedGemma 4B (Quantized Local)` - for directories with "4b" and "quantized"
- Auto-detected from output directory name

#### chart_data.json

Added to metadata section:

```json
{
  "metadata": {
    "model_name": "med_mmhl_n163_hf_27b",
    "model_label": "MedGemma 27B (HuggingFace Inference API)",
    "sampling_method": "stratified_random_seed_42",
    "random_seed": 42
  }
}
```

### 2. Threshold Information

#### validation_report.json

Added comprehensive classification info:

```json
{
  "classification_info": {
    "veracity": {
      "threshold": 0.5,
      "positive_class": "Plausible (not fake)",
      "negative_class": "Fake claim",
      "decision_rule": "veracity_score > 0.5 = plausible",
      "score_mapping": {
        "true": 0.9,
        "partially_true": 0.6,
        "false": 0.1
      },
      "note": "High recall/low precision suggests threshold=0.65 may be optimal (excludes partially_true)"
    },
    "alignment": {
      "threshold": 0.5,
      "positive_class": "Aligned",
      "negative_class": "Misaligned",
      "decision_rule": "alignment_score > 0.5 = aligned",
      "score_mapping": {
        "aligns_fully": 0.9,
        "partially_aligns": 0.6,
        "does_not_align": 0.1
      }
    },
    "misinformation": {
      "positive_class": "Misinformation",
      "negative_class": "Legitimate",
      "decision_logic": "Combined veracity-first logic (see validate_three_methods.py lines 284-348)"
    }
  }
}
```

#### chart_data.json

Added threshold metadata:

```json
{
  "metadata": {
    "classification_info": {
      "positive_class": "Misinformation (is_misinformation=True)",
      "negative_class": "Legitimate (is_misinformation=False)",
      "veracity_threshold": 0.5,
      "alignment_threshold": 0.5,
      "threshold_note": "Veracity score > 0.5 = plausible (not fake). Alignment score > 0.5 = aligned.",
      "optimization_available": "See threshold_analysis/ subdirectory for optimized thresholds"
    }
  }
}
```

### 3. Confusion Matrix Labels

#### Before:

```json
{
  "confusion_matrix": [
    { "name": "True Positive", "value": 134 },
    { "name": "False Positive", "value": 17 }
  ]
}
```

#### After:

```json
{
  "confusion_matrix": [
    {
      "name": "True Positive (Correctly Flagged Misinformation)",
      "short_name": "True Positive",
      "value": 134,
      "description": "Misinformation correctly identified as misinformation"
    },
    {
      "name": "False Positive (Legitimate Flagged as Misinformation)",
      "short_name": "False Positive",
      "value": 17,
      "description": "Legitimate content incorrectly flagged as misinformation"
    },
    {
      "name": "True Negative (Correctly Identified Legitimate)",
      "short_name": "True Negative",
      "value": 10,
      "description": "Legitimate content correctly identified as legitimate"
    },
    {
      "name": "False Negative (Missed Misinformation)",
      "short_name": "False Negative",
      "value": 2,
      "description": "Misinformation incorrectly marked as legitimate (missed detection)"
    }
  ],
  "matrix_grid": [
    {
      "actual": "Misinformation (Positive)",
      "predicted": "Misinformation (Positive)",
      "count": 134,
      "label": "TP"
    }
  ],
  "classification_info": {
    "positive_class": "Misinformation (is_misinformation=True)",
    "negative_class": "Legitimate (is_misinformation=False)",
    "threshold_note": "Default threshold: 0.5 (see threshold_analysis/ for optimization)"
  }
}
```

### 4. Score Distribution Labels

#### Before:

```json
{
  "veracity_distribution": [
    {
      "score": 0.9,
      "category": "true",
      "ground_truth": "low",
      "is_misinformation": true
    }
  ]
}
```

#### After:

```json
{
  "veracity_distribution": [
    {
      "score": 0.9,
      "category": "true",
      "category_label": "True (0.9) - Well-supported claim",
      "ground_truth": "low",
      "is_misinformation": true,
      "predicted_positive": true
    }
  ],
  "score_metadata": {
    "veracity_mapping": {
      "true": "True (0.9) - Well-supported claim",
      "partially_true": "Partially True (0.6) - Mixed accuracy",
      "false": "False (0.1) - Unsupported claim"
    },
    "alignment_mapping": {
      "aligns_fully": "Fully Aligned (0.9) - Image supports claim",
      "partially_aligns": "Partially Aligned (0.6) - Image relates but doesn't support",
      "does_not_align": "Does Not Align (0.1) - Image unrelated/contradicts"
    },
    "threshold": 0.5,
    "threshold_note": "score > 0.5 classified as positive (plausible/aligned)"
  }
}
```

### 5. Terminal Output

#### Before:

```
Med-MMHL Validation Results
====================================
Split: test | n=163

Pixel Authenticity (rate marked authentic):
  38.0%

Veracity (claim plausibility):
  Accuracy: 50.9% | F1: 0.403
```

#### After:

```
============================================================
Med-MMHL Validation Results
============================================================
Model: MedGemma 27B (HuggingFace Inference API)
Split: test | n=163
Sampling: stratified_random_seed_42
Random seed: 42

Classification Info:
  Veracity threshold: 0.5
  Positive class: Plausible (not fake)
  Score mapping: true=0.9, partially_true=0.6, false=0.1

Pixel Authenticity (rate marked authentic):
  38.0%

Veracity (claim plausibility):
  Accuracy: 50.9% | F1: 0.403
  Precision: 25.2% | Recall: 100.0%

Alignment (image-claim consistency):
  Accuracy: 76.1% | F1: 0.530
  Precision: 39.3% | Recall: 81.5%

Report: validation_results/med_mmhl_n163_hf_27b/validation_report.json
```

## Implementation Files

### Modified Scripts

1. **`scripts/generate_validation_charts.py`**
   - `generate_confusion_matrix()`: Added descriptions and labels
   - `generate_score_distributions()`: Added semantic category labels and mappings
   - `main()`: Added model detection and classification info

2. **`scripts/validate_med_mmhl.py`**
   - `run_validation()`: Added model detection from output directory
   - Report generation: Added classification_info block
   - Print summary: Added model label and classification details

### Output Files Updated

All existing validation results regenerated with new labels:

- `validation_results/med_mmhl_n163_hf_27b/chart_data.json`
- `validation_results/med_mmhl_n163_quantized_4b/chart_data.json`

Future validation runs will automatically include improved labels.

## Benefits

### 1. Model Comparisons

Users can now easily distinguish between:

- MedGemma 27B (93.0% ROC AUC, 50.9% accuracy with threshold=0.5)
- MedGemma 4B (89.9% ROC AUC, 73.6% accuracy with threshold=0.5)

### 2. Threshold Understanding

Clear documentation that:

- Default threshold is 0.5
- Scores are discrete (0.1, 0.6, 0.9) from categorical outputs
- Optimal threshold may differ (threshold_analysis/ provides optimization)

### 3. Class Definitions

Explicit labeling prevents confusion about:

- Positive class = Misinformation (not Legitimate)
- High veracity score (>0.5) = plausible/legitimate (NOT misinformation)
- Precision/recall are relative to misinformation detection

### 4. Score Semantics

Users understand categorical meanings:

- `true` (0.9) ≠ True Positive (they're unrelated concepts)
- `partially_true` (0.6) is a score, not a prediction outcome
- Threshold determines classification, not category name

### 5. Decision Logic Transparency

Documentation points to:

- Veracity-first combined logic (validate_three_methods.py)
- Threshold optimization results (threshold_analysis/)
- Classification rules for each dimension

## Usage Examples

### Reading Model Comparison

```bash
# Compare models directly from chart_data
jq '.metadata.model_label, .raw_metrics.accuracy' \
  validation_results/*/chart_data.json

# Output:
# "MedGemma 27B (HuggingFace Inference API)"
# 0.883
# "MedGemma 4B (Quantized Local)"
# 0.890
```

### Understanding Confusion Matrix

```bash
# Get full confusion matrix with descriptions
jq '.confusion_matrix[] | {name, value, description}' \
  validation_results/med_mmhl_n163_hf_27b/chart_data.json

# Output includes:
# {
#   "name": "True Positive (Correctly Flagged Misinformation)",
#   "value": 134,
#   "description": "Misinformation correctly identified as misinformation"
# }
```

### Checking Classification Logic

```bash
# Get threshold and classification rules
jq '.classification_info' \
  validation_results/med_mmhl_n163_hf_27b/validation_report.json

# Shows:
# - Thresholds for each dimension
# - Positive/negative class definitions
# - Score mappings (categorical → numeric)
# - Decision logic references
```

### Analyzing Score Distributions

```bash
# Count samples by category with labels
jq '.veracity_distribution |
  group_by(.category_label) |
  map({category: .[0].category_label, count: length})' \
  validation_results/med_mmhl_n163_hf_27b/chart_data.json

# Output:
# [
#   {
#     "category": "True (0.9) - Well-supported claim",
#     "count": 38
#   },
#   {
#     "category": "Partially True (0.6) - Mixed accuracy",
#     "count": 69
#   },
#   {
#     "category": "False (0.1) - Unsupported claim",
#     "count": 56
#   }
# ]
```

## Future Improvements

### Potential Enhancements

1. **Dynamic Threshold Labeling**
   - Load optimal threshold from threshold_analysis/ if available
   - Show both default (0.5) and optimized threshold in outputs
   - Include performance comparison at both thresholds

2. **ROC Curve Metadata**
   - Add point-by-point threshold → metrics mapping
   - Include optimal operating point (F1, Youden's index)
   - Visualize threshold selection trade-offs

3. **Sample-Level Annotations**
   - Add explanations for edge cases (FP, FN)
   - Include confidence scores for predictions
   - Link to reasoning/rationale from MedGemma

4. **Interactive Documentation**
   - Generate HTML reports with tooltips
   - Include interactive threshold sliders
   - Embed Mermaid diagrams for decision logic

5. **Standardized Naming Convention**
   - Formalize model naming pattern in filenames
   - Auto-detect model from config/environment
   - Version tracking for model updates

## Related Documentation

- **Threshold Analysis:** `docs/VERACITY_THRESHOLD_DIAGNOSIS.md`
- **Validation Methodology:** `docs/VALIDATION.md`
- **Metrics Computation:** `src/app/validation/metrics.py`
- **Decision Logic:** `scripts/validate_three_methods.py` lines 284-348

## Backward Compatibility

All changes are **additive** - new fields added, existing fields preserved:

- Old UI code will ignore new fields
- New fields provide additional context
- `short_name` preserves original labels for compatibility

Existing code reading `confusion_matrix[0].name` will still work, but can now also read:

- `confusion_matrix[0].short_name` (backward compatible)
- `confusion_matrix[0].description` (new, more detailed)

## Testing

To verify labeling improvements:

```bash
# Regenerate chart data for both models
python scripts/generate_validation_charts.py validation_results/med_mmhl_n163_hf_27b
python scripts/generate_validation_charts.py validation_results/med_mmhl_n163_quantized_4b

# Check metadata
jq '.metadata | {model_label, classification_info}' \
  validation_results/*/chart_data.json

# Verify confusion matrix labels
jq '.confusion_matrix[] | {name, description}' \
  validation_results/med_mmhl_n163_hf_27b/chart_data.json

# Check score metadata
jq '.score_metadata' \
  validation_results/med_mmhl_n163_hf_27b/chart_data.json
```

## Summary

These labeling improvements make validation outputs **self-documenting** and **unambiguous**:

- ✅ Model identity clear (27B vs 4B)
- ✅ Classification thresholds explicit (0.5, optimizable)
- ✅ Class definitions unambiguous (misinformation = positive)
- ✅ Score semantics explained (categorical → numeric mapping)
- ✅ Decision logic referenced (veracity-first combined approach)

Users can now understand validation results without consulting external documentation or source code.
