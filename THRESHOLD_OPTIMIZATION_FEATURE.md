# Threshold Optimization Feature - Implementation Summary

## Overview

Added a new **Threshold Optimization** tab to the MedContext UI that allows users to upload labeled validation datasets and automatically find optimal decision thresholds for their specific model, domain, and risk tolerance.

## What Was Built

### 1. Frontend Component (`ui/src/ThresholdOptimization.jsx`)

**Features:**

- File upload for labeled JSON datasets (image-claim pairs with ground truth labels)
- Real-time optimization with progress indicator
- Comprehensive results visualization with multiple charts and tables:
  - **Optimal Configuration Card** — Decision logic, veracity threshold, alignment threshold
  - **Performance Metrics Table** — Accuracy, Precision, Recall, F1 with 95% bootstrap confidence intervals
  - **Performance Metrics Bar Chart** — Visual comparison of all metrics with error bars
  - **Logic Comparison Table** — Side-by-side comparison of OR, AND, MIN logic options
  - **Logic Comparison Bar Chart** — Grouped bar chart showing performance across decision logics
  - **Confusion Matrix** — TP, FP, TN, FN breakdown with visual representation
  - **Configuration Instructions** — Copy-paste code snippet with optimized thresholds

**Integration:**

- Added as third tab in main App.jsx navigation
- Uses Recharts for all visualizations (BarChart for metrics comparison, confusion matrix, logic comparison)
- Consistent styling with existing UI theme

### 2. Backend API Endpoint (`src/app/api/v1/endpoints/orchestrator.py`)

**New Endpoint:**

```
POST /api/v1/orchestrator/optimize-thresholds
```

**Accepts:** Multipart form data with JSON dataset file

**Returns:** Comprehensive optimization results including:

- Optimal configuration (logic, thresholds, metrics)
- Bootstrap 95% confidence intervals (1,000 iterations)
- Per-logic optimal configurations (OR, AND, MIN)
- Sample count

### 3. Threshold Optimizer Module (`src/app/orchestrator/threshold_optimizer.py`)

**Core Functions:**

1. **`run_agent_on_dataset`** — Runs MedContext agent on all samples to extract raw veracity and alignment scores
2. **`grid_search_thresholds`** — Tests 21×21×3 = 1,323 threshold combinations across three decision logics
3. **`apply_threshold_logic`** — Implements OR, AND, MIN decision rules
4. **`compute_metrics`** — Calculates accuracy, precision, recall, F1, TP, FP, TN, FN
5. **`bootstrap_confidence_intervals`** — Computes 95% CIs via 1,000 bootstrap iterations
6. **`optimize_thresholds_from_dataset`** — Full pipeline orchestrator

**Decision Logics:**

- **OR:** Flag if `veracity < veracity_threshold OR alignment < alignment_threshold` (21×21=441 combinations, best for recall-critical applications)
- **AND:** Flag if `veracity < veracity_threshold AND alignment < alignment_threshold` (21×21=441 combinations, best for precision-critical applications)
- **MIN:** Flag if `min(veracity, alignment) < average(veracity_threshold, alignment_threshold)` (21×21=441 combinations, balanced approach that uses both thresholds)

### 4. Documentation Updates

**`THRESHOLD_OPTIMIZATION.md`:**

- Added new subsection: "Model-Specific Threshold Behavior"
- Documented 27B vs 4B model comparison (identical thresholds, different signal weighting)
- Added "Recommendation: Domain-Specific Threshold Optimization" section
- Emphasized that thresholds are not universal constants

**`CLAUDE.md`:**

- Updated "Interface" section to document three-tab UI structure
- Added description of Threshold Optimization tab functionality

### 5. CSS Styles (`ui/src/App.css`)

Added styles for:

- `.reset-button` — Secondary action button
- `.file-upload-zone` and `.file-upload-label` — Drag-and-drop file upload styling
- `.spinner` — Loading animation for optimization progress
- `.threshold-optimization-container` layout styles

## Expected JSON Dataset Format

```json
[
  {
    "image_path": "/path/to/image1.jpg",
    "claim": "This MRI shows...",
    "label": "misinformation"
  },
  {
    "image_path": "/path/to/image2.jpg",
    "claim": "This scan indicates...",
    "label": "legitimate"
  }
]
```

**Valid label values:**

- The `label` field accepts **only two case-sensitive string values**: `"misinformation"` and `"legitimate"`
- Case-sensitivity: Labels are **case-sensitive** — `"Misinformation"`, `"MISINFORMATION"`, or `"Legitimate"` will be rejected
- Alternate encodings are **not supported**: Numeric labels (`0`/`1`) and boolean labels (`true`/`false`) are not accepted
- Any dataset with invalid label values will be rejected with a validation error before optimization begins

## Key Scientific Finding Documented

The validation revealed that **MedGemma 27B and 4B converge to identical optimal thresholds** (veracity < 0.65 OR alignment < 0.30) but use them **very differently**:

| Model   | Precision | Recall | Interpretation                                                     |
| ------- | --------- | ------ | ------------------------------------------------------------------ |
| **27B** | 95.0%     | 98.5%  | **Alignment-driven:** High recall, sensitive to alignment failures |
| **4B**  | 99.2%     | 89.7%  | **Veracity-driven:** Ultra-high precision, conservative flagging   |

This demonstrates that **optimal thresholds depend on**:

1. Model architecture and scale
2. Dataset characteristics (label distribution, domain)
3. Deployment context (risk tolerance for FP vs FN)

## User Workflow

1. User navigates to "Threshold Optimization" tab
2. Uploads a labeled validation dataset (JSON format)
3. Clicks "Find Optimal Thresholds"
4. System runs agent on all samples (2-5 minutes for ~150 samples)
5. Grid search tests 1,323 configurations
6. Bootstrap computes confidence intervals
7. Results displayed with:
   - Optimal configuration card
   - Performance metrics table + chart
   - Logic comparison table + chart
   - Confusion matrix breakdown + chart
   - Copy-paste configuration snippet

## Benefits

✅ **Generalizable** — Users can optimize for their specific domain (not just medical misinformation)  
✅ **Model-agnostic** — Works with any MedGemma model or configuration  
✅ **Scientifically rigorous** — Bootstrap CIs provide statistical robustness  
✅ **User-friendly** — No coding required, visual results with clear next steps  
✅ **Transparent** — Shows all logic options and their trade-offs

## Next Steps (Future Enhancements)

- Add heatmap visualization for threshold sensitivity analysis (2D grid of accuracy)
- Support CSV upload format in addition to JSON
- Export optimization results as downloadable report (PDF/JSON)
- Add ROC curve and precision-recall curve visualizations
- Support cross-validation for more robust threshold estimation
- Add cost-sensitive threshold optimization (custom FP/FN weights)

## Technical Notes

- Backend uses async/await for non-blocking execution
- Temporary file handling with proper cleanup
- Graceful error handling with user-friendly error messages
- Recharts used for all visualizations (consistent with ValidationStory.jsx)
- Bootstrap resampling uses fixed seed (42) for reproducibility
