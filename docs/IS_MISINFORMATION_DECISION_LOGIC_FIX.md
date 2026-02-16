# is_misinformation Decision Logic Fix

**Date:** 2026-02-15  
**Status:** ✅ Complete  
**Files Modified:**

- `scripts/validate_three_methods.py` (validation script)
- `src/app/orchestrator/langgraph_agent.py` (interactive agent)
- `tests/test_is_misinformation_logic.py` (test suite)

## Problem

The `is_misinformation` flag in validation results was inconsistent with veracity and alignment scores. Example from `med_mmhl_test_265_0`:

```json
{
  "veracity_score": 0.9,
  "veracity_category": "true",
  "alignment_score": 0.1,
  "alignment_category": "does_not_align",
  "is_misinformation": true // ❌ INCORRECT
}
```

**Issue:** A claim with high veracity (factually correct) was being flagged as misinformation solely due to poor alignment.

## Root Cause

The previous logic in `combined_analysis()` treated veracity and alignment equally, using OR logic that would flag content as misinformation if ANY signal was weak. This resulted in factually correct claims (veracity="true") being incorrectly flagged when alignment was poor.

## Solution

Implemented a **veracity-first decision hierarchy** with clear, documented rules in both validation and interactive agent code:

### Decision Rule (Applied in Order)

```
PRIMARY SIGNAL: VERACITY (claim factual correctness)
  • veracity_category = "false" OR veracity_score < 0.5
    → is_misinformation = TRUE (false claim is always misinformation)

  • veracity_category = "true" AND veracity_score >= 0.8
    → is_misinformation = FALSE (high-confidence true claim,
                                  regardless of alignment/pixels)

SECONDARY MODIFIER: ALIGNMENT (only when veracity is ambiguous)
  • If veracity_category = "partially_true" OR 0.5 <= veracity_score < 0.8:
    - alignment_category = "does_not_align" OR alignment_score < 0.5
      → is_misinformation = TRUE (misleading context)

    - alignment_category = "aligns_fully" OR alignment_score >= 0.8
      → is_misinformation = FALSE (well-aligned)

    - Otherwise: is_misinformation = TRUE (conservative default)

PIXEL FORENSICS: NO DIRECT INFLUENCE on is_misinformation
  (preserved in combined_result for transparency, affects overall_score only)
```

### Key Design Principles

1. **Veracity is Primary:** A factually correct claim (veracity="true", score ≥ 0.8) is never misinformation, even if alignment is poor
   - Rationale: Poor alignment might indicate out-of-context use, but doesn't make a true claim false

2. **Alignment as Tiebreaker:** Only used when veracity is ambiguous (partially_true or mid-range scores)
   - Rationale: When veracity is uncertain, alignment helps determine if content is misleading

3. **Conservative Default:** When both veracity and alignment are ambiguous, flag as misinformation for human review
   - Rationale: Better to over-flag for review than miss potential misinformation

4. **Pixel Forensics Excluded:** Does not directly influence `is_misinformation` decision
   - Rationale: High false positive rate (compression artifacts, format conversions)
   - Still preserved in results and affects `overall_score` for transparency

## Implementation Details

### Validation Script (`validate_three_methods.py`)

The validation script now uses a fixed, well-defined `VERACITY_FIRST` logic for research reproducibility:

```python
def combined_analysis(self, pixel_result: Dict, context_result: Dict) -> Dict[str, Any]:
    """Combine pixel + contextual predictions with veracity-first decision logic.

    IS_MISINFORMATION DECISION RULE (applied in order):
    [... full docstring with ASCII diagram ...]
    """
```

### Interactive Agent (`langgraph_agent.py`)

The LangGraph agent now supports **configurable decision logic** via `state["decision_logic"]`:

- **"VERACITY_FIRST"** (recommended, now default): Hierarchical logic matching validation
- **"OR"**: `veracity < threshold OR alignment < threshold → misinformation`
- **"AND"**: `veracity < threshold AND alignment < threshold → misinformation`
- **"MIN"**: `min(veracity, alignment) < min_threshold → misinformation`

**Default changed from "OR" to "VERACITY_FIRST"** to align with best-practice validation methodology.

## Validation

Created comprehensive test suite (`tests/test_is_misinformation_logic.py`) covering:

✅ **Test 1:** High veracity + low alignment → `is_misinformation=False`  
 (Fixes the reported bug: med_mmhl_test_265_0)

✅ **Test 2:** Low veracity + high alignment → `is_misinformation=True`  
 (False claim is always misinformation)

✅ **Test 3:** High veracity + high alignment → `is_misinformation=False`  
 (Strong signals in both dimensions)

✅ **Test 4:** Ambiguous veracity + poor alignment → `is_misinformation=True`  
 (Alignment breaks the tie)

✅ **Test 5:** Ambiguous veracity + strong alignment → `is_misinformation=False`  
 (Alignment breaks the tie)

✅ **Test 6:** Both ambiguous → `is_misinformation=True`  
 (Conservative default)

**All tests pass:** 6/6 ✅

## Impact on Existing Results

This fix changes the `is_misinformation` decision logic, so **existing validation results will need to be regenerated** to reflect the corrected logic:

```bash
# Re-run validation with fixed logic
uv run python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --limit 163 \
  --random-seed 42 \
  --output validation_results/med_mmhl_n163_hf_27b_fixed

# Regenerate chart data
uv run python scripts/generate_validation_charts.py \
  validation_results/med_mmhl_n163_hf_27b_fixed
```

## Documentation

The decision logic is now fully documented in:

1. **Validation script inline docstring** (`validate_three_methods.py:284-307`)
   - Includes ASCII diagram showing the full decision tree
   - Clear mapping: `[veracity_category, alignment_category] → is_misinformation`

2. **Agent method docstring** (`langgraph_agent.py:1005-1017`)
   - Documents all decision logic options (VERACITY_FIRST, OR, AND, MIN)
   - Cross-references validation script for consistency

3. **Inline comments** (both files)
   - Step-by-step explanation of each decision branch
   - Rationale for each rule

4. **Test suite** (`tests/test_is_misinformation_logic.py`)
   - 6 test cases covering all decision paths
   - Human-readable test names and reasons

## Future Reviewers

To understand how `is_misinformation` is determined, read:

### Validation Script

```python
# In scripts/validate_three_methods.py
def combined_analysis(self, pixel_result: Dict, context_result: Dict) -> Dict[str, Any]:
    """Combine pixel + contextual predictions with veracity-first decision logic.

    IS_MISINFORMATION DECISION RULE (applied in order):
    ────────────────────────────────────────────────────────────────────────
    Primary Signal: VERACITY (claim factual correctness)
      • veracity_category = "false" OR veracity_score < 0.5
        → is_misinformation = TRUE (false claim is always misinformation)
      • veracity_category = "true" AND veracity_score >= 0.8
        → is_misinformation = FALSE (high-confidence true claim, regardless of alignment/pixels)

    Secondary Modifier: ALIGNMENT (only when veracity is ambiguous)
      • If veracity_category = "partially_true" OR 0.5 <= veracity_score < 0.8:
        - alignment_category = "does_not_align" OR alignment_score < 0.5
          → is_misinformation = TRUE (misleading context)
        - alignment_category = "aligns_fully" OR alignment_score >= 0.8
          → is_misinformation = FALSE (well-aligned)
        - Otherwise: is_misinformation = TRUE (ambiguous defaults to misinformation)

    Pixel Forensics: NO DIRECT INFLUENCE on is_misinformation
      (preserved in combined_result for transparency, affects overall_score only)
    ────────────────────────────────────────────────────────────────────────
    """
```

### Interactive Agent

```python
# In src/app/orchestrator/langgraph_agent.py
def _build_contextual_integrity(...) -> dict[str, Any]:
    """Build contextual integrity assessment with configurable decision logic.

    Decision Logic Options (set via state["decision_logic"]):
    ─────────────────────────────────────────────────────────────────────
    • "VERACITY_FIRST" (recommended, default):
      Hierarchical logic matching validation methodology
      - Primary: veracity (false claim → always misinformation)
      - Secondary: alignment (tiebreaker when veracity ambiguous)
      See: scripts/validate_three_methods.py:combined_analysis()

    • "OR": veracity < threshold OR alignment < threshold → misinformation
    • "AND": veracity < threshold AND alignment < threshold → misinformation
    • "MIN": min(veracity, alignment) < min_threshold → misinformation
    ─────────────────────────────────────────────────────────────────────
    """
```

## Examples

| veracity_category | veracity_score | alignment_category | alignment_score | is_misinformation | Reason                            |
| ----------------- | -------------- | ------------------ | --------------- | ----------------- | --------------------------------- |
| "true"            | 0.9            | "does_not_align"   | 0.1             | **False**         | High-confidence true claim        |
| "false"           | 0.1            | "aligns_fully"     | 0.9             | **True**          | False claim always misinformation |
| "true"            | 0.9            | "aligns_fully"     | 0.9             | **False**         | Strong signals in both            |
| "partially_true"  | 0.6            | "does_not_align"   | 0.1             | **True**          | Ambiguous + poor alignment        |
| "partially_true"  | 0.6            | "aligns_fully"     | 0.9             | **False**         | Ambiguous + strong alignment      |
| "partially_true"  | 0.6            | "partially_aligns" | 0.6             | **True**          | Both ambiguous (conservative)     |
