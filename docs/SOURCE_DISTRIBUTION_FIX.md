# Source Distribution Fix - Implementation Summary

**Date:** 2026-02-15  
**Issue:** Missing source attribution in Med-MMHL sampling bias analysis  
**Status:** ✅ Fixed and validated

## Problem

The `sampling_bias_analysis.json` file showed all 1785 records with `source: "unknown"`, preventing meaningful source distribution analysis. This indicated that source information was not being extracted from the Med-MMHL dataset.

**Original output:**
```json
{
  "full_dataset": {
    "source_distribution": {
      "unknown": 1785
    }
  }
}
```

## Root Cause

The Med-MMHL dataset doesn't have an explicit `source` field in the CSV files. However, source information **is embedded in the image paths**:

- `../images/2023-05-09_fakenews//LeadStories/3545_1.jpg` → LeadStories
- `../images/2023-05-09/Healthline/753_0.jpg` → Healthline  
- `../images/2023-05-09/Nih/426_0.jpg` → Nih

The data loader (`src/app/validation/loaders.py`) was not extracting this source information from paths.

## Solution

### 1. Source Extraction Function

Added `_extract_source_from_path()` to parse source names from Med-MMHL image paths:

```python
def _extract_source_from_path(path_str: str) -> str:
    """Extract source name from Med-MMHL image path.
    
    Examples:
        ../images/2023-05-09_fakenews//LeadStories/3545_1.jpg -> LeadStories
        ../images/2023-05-09/Healthline/753_0.jpg -> Healthline
        ../images/2023-05-09/Nih/426_0.jpg -> Nih
    """
    # Implementation extracts second-to-last path component (directory before filename)
```

**Location:** `src/app/validation/loaders.py:167-195`

### 2. Data Loader Update

Modified `load_med_mmhl_dataset()` to populate the `source` field for each record:

```python
# Extract source from image path
source = _extract_source_from_path(img_path)

records.append({
    "image_id": claim_id,
    "image_path": str(resolved),
    "claim": content,
    "source": source,  # NEW: Source extracted from path
    "ground_truth": {...},
})
```

**Location:** `src/app/validation/loaders.py:117-132`

### 3. Validation & Warning System

Enhanced `compute_distribution_stats()` to detect and warn about missing source data:

```python
# Warn if all sources are "unknown"
if len(source_counts) == 1 and "unknown" in source_counts:
    print(
        f"WARNING: All {n} records have source='unknown'. "
        "Source distribution analysis will be invalid.",
        file=sys.stderr,
    )
```

Added `source_metadata` to track source data quality:

```python
"source_metadata": {
    "total_sources": len(source_counts),
    "all_unknown": len(source_counts) == 1 and "unknown" in source_counts,
    "unknown_count": source_counts.get("unknown", 0),
    "unknown_rate": source_counts.get("unknown", 0) / n,
}
```

**Location:** `scripts/check_sampling_bias.py:42-82`

### 4. Graceful Degradation

Updated `compare_distributions()` to handle missing source data:

```python
# Check if source data is invalid (all unknown)
if full_stats["source_metadata"]["all_unknown"]:
    source_overlap = None  # N/A
    source_assessment = "UNAVAILABLE"
else:
    source_overlap = len(full_top_sources & subset_top_sources) / 5
    source_assessment = "ACCEPTABLE" if source_overlap >= 0.6 else "POTENTIAL_BIAS"
```

The overall assessment now excludes `UNAVAILABLE` assessments:

```python
biases = [v["assessment"] for v in comparison.values() if v["assessment"] != "UNAVAILABLE"]
```

**Location:** `scripts/check_sampling_bias.py:85-138`

## Results

### Before Fix
```json
{
  "source_distribution": {
    "unknown": 1785
  },
  "source_bias": {
    "top_source_overlap": 0.2,
    "assessment": "POTENTIAL_BIAS"
  }
}
```

### After Fix
```json
{
  "source_distribution": {
    "LeadStories": 1454,
    "Nih": 141,
    "Healthline": 84,
    "Mayo": 41,
    "ClevelandClinic": 38,
    "CheckYourFact": 27
  },
  "source_metadata": {
    "total_sources": 6,
    "all_unknown": false,
    "unknown_count": 0,
    "unknown_rate": 0.0
  },
  "source_bias": {
    "top_source_overlap": 0.8,
    "assessment": "ACCEPTABLE"
  }
}
```

**Key Findings:**
- 81.5% of the full Med-MMHL test set comes from LeadStories (fact-checking site covering misinformation)
- 96.9% of the first 163 samples come from LeadStories
- Top source overlap is 80% (4 out of 5 top sources match between full and subset)
- Source distribution is now **ACCEPTABLE** instead of **POTENTIAL_BIAS**

## Validation

### Unit Tests

Created comprehensive tests for source extraction (`scripts/test_source_validation.py`):

1. ✅ **Missing source data** - Warns when all sources are "unknown"
2. ✅ **Partial source data** - Handles mixed known/unknown sources
3. ✅ **Complete source data** - Validates full source attribution

**Test Results:**
```
Testing source data validation and warning system
======================================================================
Testing warning system for missing source data
✅ All assertions passed!

Testing with partial source data (50% known, 50% unknown)
✅ All assertions passed!

Testing with complete source data (no unknown)
✅ All assertions passed!

======================================================================
✅ ALL TESTS PASSED
```

### Integration Test

Re-ran the full sampling bias analysis:

```bash
uv run python scripts/check_sampling_bias.py \
  --data-dir data/med-mmhl \
  --split test \
  --subset-size 163 \
  --output validation_results/sampling_bias_analysis.json
```

**Result:** Successfully extracted sources for all 1785 records with no warnings.

## Files Changed

1. **`src/app/validation/loaders.py`**
   - Added `_extract_source_from_path()` function
   - Updated `load_med_mmhl_dataset()` to populate `source` field

2. **`scripts/check_sampling_bias.py`**
   - Enhanced `compute_distribution_stats()` with warning system
   - Added `source_metadata` tracking
   - Updated `compare_distributions()` to handle unavailable source data
   - Improved console output for missing source scenarios

3. **`validation_results/sampling_bias_analysis.json`**
   - Regenerated with correct source distribution
   - Changed source_bias assessment from POTENTIAL_BIAS → ACCEPTABLE

4. **New Files:**
   - `scripts/test_source_validation.py` - Validation test suite
   - `tests/test_source_extraction.py` - Unit tests for path parsing

## Impact on Findings

The corrected analysis reveals:

1. **Source bias is ACCEPTABLE** (was incorrectly flagged as POTENTIAL_BIAS)
   - 80% overlap in top sources between full and subset
   - Both dominated by LeadStories fact-checking content

2. **Label bias remains POTENTIAL_BIAS**
   - 13.96 percentage point difference in misinformation rate
   - This is a real bias that should be documented

3. **More accurate dataset characterization**
   - Can now identify that Med-MMHL is heavily weighted toward LeadStories content
   - Helps understand the nature of the misinformation examples

## Future Improvements

1. **Source diversity analysis**: Track source entropy or Gini coefficient
2. **Source-stratified sampling**: Balance sources explicitly in subset selection
3. **Source credibility scoring**: Weight authoritative sources (Nih, Mayo) differently from fact-checking sites
4. **Automatic source taxonomy**: Group sources by type (medical authority, fact-checker, health media)

## Lessons Learned

1. **Implicit metadata matters**: Always check if information is embedded in file paths, names, or structure
2. **Early validation is critical**: Add checks that fail fast when data quality is poor
3. **Graceful degradation**: Handle missing data scenarios explicitly rather than defaulting silently
4. **Comprehensive testing**: Test both happy path and edge cases (all unknown, partial, complete)
