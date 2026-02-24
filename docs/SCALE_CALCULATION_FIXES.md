# Scale Calculation & FN Reduction Fixes

**Date:** February 24, 2026
**Status:** ✅ Fully Corrected

---

## Issues Fixed

### Issue 1: Scale Impact Calculation (MAU/DAU Mismatch)

**Problem:**
- Mixed MAU (Monthly Active Users) and DAU (Daily Active Users) inconsistently
- Assumed 100% of users encounter classifiable medical content daily (unrealistic)
- Claimed "~27 million better classifications daily"

**Root Cause:**
```python
# OLD (WRONG):
Facebook: 2.9B MAU × 0.006 = 17.4M
Twitter/X: 500M DAU × 0.006 = 3.0M
TikTok: 1B MAU × 0.006 = 6.0M
Total: ~27M daily
```

**Corrected Calculation:**
```python
# NEW (CORRECT):
Conservative DAU estimates:
- Facebook: ~2.0B DAU
- Twitter/X: ~500M DAU
- TikTok: ~800M DAU
- Total: ~3.3B DAU

Scenarios with explicit assumptions:
1. Aggressive (100% exposure): 3.3B × 0.006 = ~20M daily
2. Moderate (10% exposure): 3.3B × 0.10 × 0.006 = ~2M daily
3. Conservative (1% exposure): 3.3B × 0.01 × 0.006 = ~200K daily
```

**Changes Made:**
- Added table showing three scenarios (aggressive/moderate/conservative)
- Made medical content exposure rate assumption explicit
- Changed from specific "~27M" to range "hundreds of thousands to millions"
- Added note explaining these are order-of-magnitude estimates

---

### Issue 2: False Negative Reduction Percentage

**Problem:**
- Claimed "7.7% reduction" from baseline of "13 FN"
- But Signal Performance table shows "Alignment Only (a<0.5)" has **11 FN**, not 13 FN
- The "13 FN" doesn't exist in any table row

**Root Cause:**
```
# OLD (WRONG):
Baseline: 13 FN (source unknown)
Combined: 10 FN
Reduction: (13-10)/13 = 7.7%
```

**Corrected Calculation:**
```
# NEW (CORRECT):
Baseline: 11 FN (Alignment Only a<0.5, from table row)
Combined: 10 FN
Reduction: (11-10)/11 = 9.1%
```

**Changes Made:**
- Updated "7.7% reduction" → "9.1% reduction"
- Updated "13 FN" → "11 FN"
- Updated "(13→10)" → "(11→10)"

---

## Files Updated

### Documentation

1. **docs/VALIDATION.md**
   - ✅ Lines 64-67: Fixed FN reduction to 9.1% (11→10)
   - ✅ Lines 107-121: Replaced single "~27M" with scenario table
   - ✅ Line 14: Updated Executive Summary
   - ✅ Line 155: Updated Conclusion

2. **CLAUDE.md**
   - ✅ Line 359: Fixed FN reduction to 9.1% and scale range

### UI Component

3. **ui/src/OptimizationStory.jsx**
   - ✅ Lines 123-127: Updated SCALE_DATA with corrected DAU + 10% exposure
   - ✅ Line 494: Updated subtitle to use range
   - ✅ Line 511-513: Changed "27M" to "200K-20M" range
   - ✅ Lines 408-420: Updated total impact callout to show ~2M (moderate scenario) with range note
   - ✅ Lines 427-444: Updated platform breakdown to show DAU × 10%
   - ✅ Line 618: Fixed FN reduction to 9.1% (11→10)
   - ✅ Line 626: Fixed FN reduction percentage
   - ✅ Line 669: Updated summary to use range

---

## Corrected Numbers Summary

| Metric | Old (Wrong) | New (Correct) |
|--------|-------------|---------------|
| **Scale Impact** | ~27M daily (specific) | 200K-20M daily (range with assumptions) |
| **FN Reduction** | 7.7% (13→10) | 9.1% (11→10) |
| **FN Baseline** | 13 FN (doesn't exist) | 11 FN (Alignment Only a<0.5) |

---

## Key Assumptions Now Explicit

### Scale Calculation
1. **Platform DAU (not MAU):**
   - Facebook: ~2.0B DAU (was 2.9B MAU)
   - Twitter/X: ~500M DAU (correct)
   - TikTok: ~800M DAU (was 1B MAU)

2. **Medical Content Exposure Rate:**
   - Aggressive: 100% of DAU (1 classifiable post/user/day) → 20M
   - Moderate: 10% of DAU → 2M
   - Conservative: 1% of DAU → 200K

3. **Caveats Stated:**
   - Platform-specific content prevalence varies
   - User engagement patterns differ
   - Deployment coverage is partial
   - Content classification policies matter

### FN Reduction Calculation
1. **Baseline:** Alignment Only (a<0.5) with 11 FN
2. **Improved:** Combined Optimized (v<0.65 OR a<0.30) with 10 FN
3. **Reduction:** (11-10)/11 × 100 = 9.1%

---

## Verification Commands

### Check all references are fixed:
```bash
# Should find 0 results for old "27 million" references
grep -r "~27 million\|27M" docs/ ui/src/ CLAUDE.md | grep -v "SCALE_CALCULATION_FIXES"

# Should find 0 results for old "7.7%" FN reduction
grep -r "7\.7%.*false negative\|13.*FN\|13→10" docs/ ui/src/ CLAUDE.md

# Should find 0 results for old "13 FN" baseline
grep -r "13 FN" docs/ ui/src/ CLAUDE.md
```

All searches should return 0 results (except this summary file).

---

## Impact on Thesis Defense

**Stronger Position:**
- Now using **honest, defensible numbers** with explicit assumptions
- Shows scientific rigor by acknowledging uncertainty
- Range (200K-20M) is still impressive at scale
- 9.1% FN reduction (vs 7.7%) is actually slightly better

**Talking Points Updated:**
- "Depending on medical content exposure rates, veracity improves hundreds of thousands to millions of classifications daily"
- "We show three scenarios to bound the impact: conservative (1% exposure), moderate (10%), and aggressive (100%)"
- "Even under conservative assumptions, the safety net improves 200K classifications daily"
- "9.1% reduction in false negatives from alignment baseline"

---

## Status: ✅ Complete

All incorrect calculations have been fixed and made transparent with explicit assumptions.
