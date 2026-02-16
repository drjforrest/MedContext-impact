# Category Normalization Fix - Summary

## Changes Made

### 1. Core Code Fix

**File:** `scripts/validate_three_methods.py`

Added normalization logic in `_direct_medgemma_analysis()` method (lines 234-258) to handle pipe-separated category values from MedGemma:

- Created `normalize_category()` helper function
- Detects pipe-separated values (e.g., `"true|partially_true|false"`)
- Resolves ambiguous categories to middle/uncertain option
- Applies to both veracity and alignment categories

**Normalization Rules:**

- Veracity: `"true|partially_true|false"` → `"partially_true"` (score: 0.6)
- Alignment: `"aligns_fully|partially_aligns|does_not_align"` → `"partially_aligns"` (score: 0.6)

### 2. Data Fix Script

**File:** `scripts/fix_chart_data_categories.py` (NEW)

Standalone utility to fix existing `chart_data.json` files:

- Finds all `chart_data.json` files recursively
- Normalizes pipe-separated categories in `veracity_distribution` and `alignment_distribution`
- Reports statistics (files processed, entries fixed)
- Supports dry-run mode for safe previewing

**Usage:**

```bash
# Preview changes
python scripts/fix_chart_data_categories.py validation_results/ --dry-run

# Apply fixes
python scripts/fix_chart_data_categories.py validation_results/
```

### 3. Validation Test

**File:** `scripts/test_category_normalization.py` (NEW)

Test script to verify category normalization:

- Checks all `chart_data.json` files for pipe-separated categories
- Validates discrete category values
- Reports issues with file path and entry index

**Usage:**

```bash
python scripts/test_category_normalization.py
```

### 4. Documentation

**File:** `docs/CATEGORY_NORMALIZATION_FIX.md` (NEW)

Comprehensive documentation covering:

- Problem description and root cause
- Solution approach (code fix + data fix + tests)
- Impact on existing files
- Verification steps
- Technical details (category mappings, data structure)

## Results

### Fixed Files

- `validation_results/med_mmhl_n163_quantized_4b/chart_data.json`
  - 3 veracity entries normalized (`"true|partially_true|false"` → `"partially_true"`)
  - 3 alignment entries normalized (`"aligns_fully|partially_aligns|does_not_align"` → `"partially_aligns"`)

### Already Clean

- `validation_results/med_mmhl_n163_hf_27b/chart_data.json`
  - No fixes needed (0 pipe-separated categories)

### Verification

✅ No pipe-separated categories remain in any `chart_data.json` file
✅ All tests pass (`test_category_normalization.py`)
✅ All categories are valid discrete values

## Future Prevention

The code fix in `validate_three_methods.py` ensures that all future validation runs will automatically normalize categories at generation time. No post-processing will be needed.

## Technical Notes

### Data Structure

Each distribution entry now has:

```json
{
  "score": 0.5,
  "category": "partially_true", // Single discrete value ✅
  "category_label": "true|partially_true|false", // Display string (preserved)
  "ground_truth": "low",
  "is_misinformation": true
}
```

The `category` field is guaranteed to be a single discrete value, while `category_label` (used for display) may still contain the original pipe-separated string for transparency.

### Category Mappings

**Veracity:**

- `"true"` → 0.9 (well-supported claim)
- `"partially_true"` → 0.6 (some basis) **[uncertain default]**
- `"false"` → 0.1 (unsupported claim)

**Alignment:**

- `"aligns_fully"` → 0.9 (strong image-claim support)
- `"partially_aligns"` → 0.6 (some relation) **[uncertain default]**
- `"does_not_align"` → 0.1 (unrelated image-claim pair)

## Files Modified/Created

### Modified

1. `scripts/validate_three_methods.py` - Added category normalization logic

### Created

1. `scripts/fix_chart_data_categories.py` - Data fix utility
2. `scripts/test_category_normalization.py` - Validation test
3. `docs/CATEGORY_NORMALIZATION_FIX.md` - Documentation
4. `docs/CATEGORY_NORMALIZATION_SUMMARY.md` - This file

### Fixed Data

1. `validation_results/med_mmhl_n163_quantized_4b/chart_data.json` - 6 entries normalized
