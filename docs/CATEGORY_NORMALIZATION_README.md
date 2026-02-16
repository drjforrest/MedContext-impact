# Category Normalization Fix - Quick Reference

## What Was Fixed

Pipe-separated category values (e.g., `"true|partially_true|false"`) in `chart_data.json` files have been normalized to single discrete values.

## Status

✅ **COMPLETE** - All existing data fixed, future runs will auto-normalize

## Verification

```bash
# Run validation test
python scripts/test_category_normalization.py
```

Expected output: `✅ ALL TESTS PASSED`

## Files Changed

### Code (prevents future occurrences)

- `scripts/validate_three_methods.py` - Added normalization logic

### Tools (fix existing data)

- `scripts/fix_chart_data_categories.py` - Fix utility
- `scripts/test_category_normalization.py` - Validation test

### Data (fixed)

- `validation_results/med_mmhl_n163_quantized_4b/chart_data.json` - 6 entries normalized

### Documentation

- `docs/CATEGORY_NORMALIZATION_FIX.md` - Detailed technical doc
- `docs/CATEGORY_NORMALIZATION_SUMMARY.md` - Complete summary
- `docs/CATEGORY_NORMALIZATION_README.md` - This file

## How It Works

When MedGemma is uncertain, it returns multiple categories separated by pipes:

- Input: `"true|partially_true|false"` with score `0.5`
- Output: `"partially_true"` with score `0.6`

The normalization resolves uncertainty to the middle category:

- **Veracity**: `"partially_true"` (some basis)
- **Alignment**: `"partially_aligns"` (some relation)

## Impact

- **Breaking**: Consumers expecting pipe-separated strings will now get discrete values
- **Fix Required**: Update any code that parses category strings with `|` characters
- **Migration**: Run `scripts/fix_chart_data_categories.py` on any custom validation results

## Need Help?

See `docs/CATEGORY_NORMALIZATION_FIX.md` for full technical details.
