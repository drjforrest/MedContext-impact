# Source Distribution Fix - Quick Reference

## Problem
`validation_results/sampling_bias_analysis.json` showed all 1785 records with `source: "unknown"`, preventing meaningful source distribution analysis.

## Solution
Extracted source information from Med-MMHL image paths and added validation warnings for incomplete data.

## Changes Made

### 1. Data Loader (src/app/validation/loaders.py)
- **Added:** `_extract_source_from_path()` function (lines 167-195)
  - Parses source name from path: `../images/2023-05-09/Healthline/753_0.jpg` → `Healthline`
  - Returns `"unknown"` for invalid/missing paths
- **Modified:** `load_med_mmhl_dataset()` to populate `source` field for each record (line 117)

### 2. Sampling Bias Script (scripts/check_sampling_bias.py)
- **Enhanced:** `compute_distribution_stats()` with warning system
  - Detects when all sources are `"unknown"` and prints diagnostic warning to stderr
  - Added `source_metadata` object tracking source data quality
- **Updated:** `compare_distributions()` to handle unavailable source data gracefully
  - Returns `source_assessment: "UNAVAILABLE"` when source data is missing
  - Excludes `UNAVAILABLE` from overall bias assessment
- **Improved:** Console output to display source availability status

### 3. Results File (validation_results/sampling_bias_analysis.json)
- **Before:** `{"source_distribution": {"unknown": 1785}}`
- **After:** Proper distribution with 6 sources (LeadStories 81.5%, Nih 7.9%, etc.)
- **Added:** `source_metadata` object with quality metrics
- **Changed:** Source bias assessment from `POTENTIAL_BIAS` → `ACCEPTABLE` (80% overlap)

### 4. Test Files (New)
- **scripts/test_source_validation.py** - Unit tests for warning system (3 test cases)
- **scripts/test_e2e_source_distribution.py** - End-to-end integration test
- **docs/SOURCE_DISTRIBUTION_FIX.md** - Detailed implementation documentation

## Verification

### Quick Test
```bash
# Test source extraction on real data
uv run python scripts/test_e2e_source_distribution.py
```

### Full Re-run
```bash
# Regenerate sampling bias analysis with correct sources
uv run python scripts/check_sampling_bias.py \
  --data-dir data/med-mmhl \
  --split test \
  --subset-size 163 \
  --output validation_results/sampling_bias_analysis.json
```

## Results
- ✅ All 1785 records now have valid source attribution (0% unknown)
- ✅ 6 unique sources identified: LeadStories, Nih, Healthline, Mayo, ClevelandClinic, CheckYourFact
- ✅ Source bias changed from POTENTIAL_BIAS → ACCEPTABLE (80% top source overlap)
- ✅ Warning system detects and reports incomplete source data

## Key Findings
Med-MMHL test set is heavily weighted toward LeadStories (81.5%), a fact-checking site that documents misinformation. This explains the high misinformation rate (83%) in the dataset.

**Subset Bias:** The first 163 samples are 96.9% LeadStories (vs 81.5% in full set), but still maintain 80% overlap in top sources, meeting the acceptability threshold.
