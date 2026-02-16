# Threshold Grid Truncation Bug Fix

**Date**: February 15, 2026  
**Issue**: Incomplete threshold optimization results in JSON output  
**Status**: ✅ Fixed and regenerated

## Problem Description

The `scripts/optimize_thresholds.py` script was truncating the `all_results` array to only the first 50 entries when saving threshold optimization results to JSON files. This caused a critical discrepancy:

- **Reported optimal configuration**: `veracity_threshold=0.65, alignment_threshold=0.30`
- **Actual entries in file**: Only covered `veracity_threshold` from 0.30 to ~0.45
- **Missing entries**: The optimal configuration and all combinations with `veracity_threshold ≥ 0.50` were absent from the JSON

### Root Cause

Line 361 in `scripts/optimize_thresholds.py`:

```python
"all_results": results[:50],  # Save first 50 for analysis
```

With a threshold sweep from 0.3 to 0.95 in steps of 0.05:

- **Grid dimensions**: 13 veracity thresholds × 13 alignment thresholds = 169 combinations
- **Saved entries**: Only 50 (29.6% of the full grid)
- **Missing entries**: 119 combinations (70.4% of the grid)

The truncation was likely added to reduce file size during development but should have saved the complete grid for production validation results.

## Impact

This bug affected both validation result sets:

1. **`validation_results/med_mmhl_n163_quantized_4b/`** (4B quantized model)
2. **`validation_results/med_mmhl_n163_hf_27b/`** (27B HuggingFace model)

For each directory, all three logic types were affected:

- `threshold_optimization_or.json`
- `threshold_optimization_and.json`
- `threshold_optimization_min.json`

**Key consequence**: The UI's threshold optimization viewer and any downstream analysis could not access the complete grid to verify the reported optimal thresholds or explore the full threshold sensitivity landscape.

## Fix Applied

### Code Change

**File**: `scripts/optimize_thresholds.py`  
**Line**: 361

**Before**:

```python
"all_results": results[:50],  # Save first 50 for analysis
```

**After**:

```python
"all_results": results,  # Save all results (complete grid)
```

### Regeneration

Reran the optimization script for both validation result directories:

```bash
uv run python scripts/optimize_thresholds.py validation_results/med_mmhl_n163_quantized_4b
uv run python scripts/optimize_thresholds.py validation_results/med_mmhl_n163_hf_27b
```

## Verification

### File Size Comparison

**Before** (50 entries):

- Each `threshold_optimization_*.json` file: ~8-10 KB

**After** (169 entries):

- Each `threshold_optimization_*.json` file: ~25-30 KB

### Grid Completeness

Verified all files now contain:

- ✅ **169 entries** (complete 13×13 grid)
- ✅ **Optimal configuration present** (veracity_threshold=0.65, alignment_threshold=0.30)
- ✅ **Full threshold range** (0.30 to 0.90 in 0.05 increments for both dimensions)

### Sample Verification

**File**: `validation_results/med_mmhl_n163_quantized_4b/threshold_analysis/threshold_optimization_or.json`

**Optimal entry now present**:

```json
{
  "veracity_threshold": 0.6499999999999999,
  "alignment_threshold": 0.3,
  "accuracy": 0.9079754601226994,
  "precision": 0.991869918699187,
  "recall": 0.8970588235294118,
  "f1": 0.9420849420849421
}
```

This matches the reported optimal configuration at the top of the file:

```json
"optimal_for_accuracy": {
  "veracity_threshold": 0.6499999999999999,
  "alignment_threshold": 0.3,
  "accuracy": 0.9079754601226994,
  "precision": 0.991869918699187,
  "recall": 0.8970588235294118,
  "f1": 0.9420849420849421
}
```

## Results Summary

### Quantized 4B Model (med_mmhl_n163_quantized_4b)

**OR Logic** (optimal):

- Veracity threshold: 0.65
- Alignment threshold: 0.30
- **Accuracy: 90.8%** [95% CI: 85.9%-95.1%]
- Precision: 99.2%
- Recall: 89.7%
- F1: 0.942

**AND Logic**:

- Veracity threshold: 0.65
- Alignment threshold: 0.65
- Accuracy: 79.8%
- F1: 0.863

**MIN Logic**:

- Veracity threshold: 0.35
- Alignment threshold: 0.90
- Accuracy: 90.2%
- F1: 0.939

### 27B HuggingFace Model (med_mmhl_n163_hf_27b)

**OR Logic** (optimal):

- Veracity threshold: 0.65
- Alignment threshold: 0.30
- **Accuracy: 94.5%** [95% CI: 91.4%-97.5%]
- Precision: 95.0%
- Recall: 98.5%
- F1: 0.968

**AND Logic**:

- Veracity threshold: 0.65
- Alignment threshold: 0.65
- Accuracy: 89.0%
- F1: 0.930

**MIN Logic**:

- Veracity threshold: 0.35
- Alignment threshold: 0.90
- Accuracy: 88.3%
- F1: 0.934

## Recommendations

### For Future Validation Runs

1. **Never truncate `all_results`** - The complete grid is essential for:
   - Verification that reported optimal thresholds are actually in the data
   - Threshold sensitivity analysis
   - Heatmap generation (which already uses the full grid)
   - UI visualization of the complete threshold landscape

2. **Add validation checks** - Consider adding assertions to verify:

   ```python
   # Verify optimal config is in all_results
   assert any(
       r["veracity_threshold"] == best_acc["veracity_threshold"]
       and r["alignment_threshold"] == best_acc["alignment_threshold"]
       for r in results
   ), "Optimal configuration missing from all_results!"
   ```

3. **Document file size expectations** - For a 13×13 grid (169 entries), expect ~25-30 KB per JSON file. This is acceptable for modern systems and essential for complete analysis.

### For UI Implementation

The UI threshold optimization viewer should now be able to:

- ✅ Display the complete 13×13 heatmap
- ✅ Highlight the optimal configuration
- ✅ Allow users to explore all threshold combinations
- ✅ Show the full sensitivity landscape around the optimal point

## Files Modified

1. **`scripts/optimize_thresholds.py`** - Removed `[:50]` slice on line 361
2. **Regenerated 6 files** (all now contain 169 entries):
   - `validation_results/med_mmhl_n163_quantized_4b/threshold_analysis/threshold_optimization_or.json`
   - `validation_results/med_mmhl_n163_quantized_4b/threshold_analysis/threshold_optimization_and.json`
   - `validation_results/med_mmhl_n163_quantized_4b/threshold_analysis/threshold_optimization_min.json`
   - `validation_results/med_mmhl_n163_hf_27b/threshold_analysis/threshold_optimization_or.json`
   - `validation_results/med_mmhl_n163_hf_27b/threshold_analysis/threshold_optimization_and.json`
   - `validation_results/med_mmhl_n163_hf_27b/threshold_analysis/threshold_optimization_min.json`
3. **Regenerated 6 heatmap images** (PNG files updated with complete grid visualization)

## Conclusion

The bug has been fixed and all affected files have been regenerated with the complete threshold grid. The reported optimal thresholds (veracity=0.65, alignment=0.30 for OR logic) are now present in the `all_results` array, and the full 169-entry grid enables comprehensive threshold sensitivity analysis.
