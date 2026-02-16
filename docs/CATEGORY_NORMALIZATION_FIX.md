# Category Normalization Fix

## Problem

Some entries in `veracity_distribution` and `alignment_distribution` used pipe-separated strings in the `"category"` field (e.g., `"true|partially_true|false"` paired with `score: 0.5`), which broke consumers expecting a single discrete category.

## Root Cause

When MedGemma returns uncertain predictions, it sometimes outputs multiple possible categories separated by pipes (e.g., `"true|partially_true|false"`). The `_direct_medgemma_analysis` method in `validate_three_methods.py` was passing these through directly without normalization.

## Solution

### 1. Code Fix (`validate_three_methods.py`)

Added a `normalize_category()` helper function that detects pipe-separated values and resolves them to the middle/uncertain category:

```python
def normalize_category(raw_value: str, valid_options: dict, middle_option: str) -> str:
    """Normalize potentially pipe-separated category to single value."""
    if "|" in raw_value:
        # Multiple options indicate uncertainty - use middle/uncertain category
        return middle_option
    elif raw_value in valid_options:
        return raw_value
    else:
        # Invalid/unknown category - default to middle
        return middle_option
```

**Normalization Rules:**

- Veracity: `"true|partially_true|false"` → `"partially_true"` (score: 0.6)
- Alignment: `"aligns_fully|partially_aligns|does_not_align"` → `"partially_aligns"` (score: 0.6)

### 2. Data Fix Tool (`scripts/fix_chart_data_categories.py`)

Created a standalone script to fix existing `chart_data.json` files:

```bash
# Preview changes
python scripts/fix_chart_data_categories.py validation_results/ --dry-run

# Apply fixes
python scripts/fix_chart_data_categories.py validation_results/
```

**Features:**

- Recursively finds all `chart_data.json` files
- Normalizes pipe-separated categories to middle option
- Reports statistics (files processed, entries fixed)
- Supports dry-run mode

### 3. Validation Test (`scripts/test_category_normalization.py`)

Created a test script to verify category normalization:

```bash
python scripts/test_category_normalization.py
```

**Checks:**

- No pipe-separated values in `category` fields
- All categories are valid discrete values
- Reports issues with file path and entry index

## Impact

**Files Fixed:**

- `validation_results/med_mmhl_n163_quantized_4b/chart_data.json`
  - 3 veracity entries normalized
  - 3 alignment entries normalized

**No Changes Needed:**

- `validation_results/med_mmhl_n163_hf_27b/chart_data.json` (already clean)

## Verification

```bash
# Verify no pipe-separated categories remain
grep -r '"category": "[^"]*|[^"]*"' validation_results/*/chart_data.json
# (Should return no results)

# Run validation test
python scripts/test_category_normalization.py
# (Should show all tests passed)
```

## Future Prevention

All new validation runs will automatically normalize categories due to the code fix in `validate_three_methods.py`. The normalization happens at generation time, so no post-processing is needed.

## Technical Details

### Category Mapping

**Veracity (claim truthfulness):**

- `"true"` → score 0.9 (well-supported)
- `"partially_true"` → score 0.6 (some basis) **[uncertain default]**
- `"false"` → score 0.1 (unsupported)

**Alignment (image-claim match):**

- `"aligns_fully"` → score 0.9 (strong support)
- `"partially_aligns"` → score 0.6 (some relation) **[uncertain default]**
- `"does_not_align"` → score 0.1 (unrelated)

### Data Structure

Each distribution entry has:

```json
{
  "score": 0.5,
  "category": "partially_true", // Single discrete value (FIXED)
  "category_label": "true|partially_true|false", // Display string (preserved)
  "ground_truth": "low",
  "is_misinformation": true
}
```

The `category` field is now guaranteed to be a single discrete value, while `category_label` (used for display purposes) may still contain the original pipe-separated string for transparency.
