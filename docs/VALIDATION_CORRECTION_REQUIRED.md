# Validation Correction Required

**Status:** 🚨 **CRITICAL - Rerun Required**

**Date Identified:** February 2, 2026

**Priority:** HIGH - Affects thesis validity

---

## Issue Summary

The pilot contextual signals validation (90 samples, reported 61.1% accuracy) used **incorrect weight distribution** due to unintended auto-renormalization when Genealogy and Source Reputation signals were unavailable.

### What Was Tested

**Reported:** 60/15/15/10 weight distribution  
**Actually Tested:** 80/20 weight distribution (Alignment/Plausibility only)

### Root Cause

The `_compute_weighted_score()` function in `src/app/metrics/integrity.py` skipped `None` values and renormalized remaining weights:

```python
# OLD (INCORRECT) BEHAVIOR
if value is None:
    continue  # Skip and renormalize weights
```

When Genealogy (15%) and Source (10%) were `None`, the function redistributed their weight:

- Alignment: 60/75 = **80%** (not 60%)
- Plausibility: 15/75 = **20%** (not 15%)

### Impact on Results

1. **61.1% accuracy** reflects an 80/20 system, not the designed 60/15/15/10 system
2. Cannot claim validation of the proposed weight distribution
3. Full system performance with all 4 signals is **unknown**
4. Thesis claims are undermined without correction

---

## Fix Applied

### Code Changes

1. **`src/app/metrics/integrity.py`** - Modified `_compute_weighted_score()`:

   ```python
   # NEW (CORRECT) BEHAVIOR
   # Treat None as 0.0 (no confidence) rather than skipping
   signal_value = 0.0 if value is None else _clamp(float(value))
   score += weight * signal_value
   ```

2. **`tests/test_integrity.py`** - Updated test expectations to reflect fixed weights

### Verification

Run `scripts/verify_corrected_scoring.py` to see the difference:

```bash
python scripts/verify_corrected_scoring.py
```

**Key Difference:**

- OLD: Alignment=0.8, Plausibility=0.6, others=None → Score = **0.760**
- CORRECTED: Same inputs → Score = **0.570**
- **Difference: 0.190** (25% relative decrease)

---

## Rerun Instructions

### Prerequisites

1. **MedGemma Vertex AI** configured (already working):

   ```bash
   MEDGEMMA_PROVIDER=vertex
   MEDGEMMA_VERTEX_PROJECT=medcontext
   MEDGEMMA_VERTEX_LOCATION=us-central1
   MEDGEMMA_VERTEX_ENDPOINT=<your-endpoint>
   ```

2. **LLM Orchestrator** with valid credentials:

   - **Option A:** Use Google Gemini API directly (Recommended)

     ```bash
     export LLM_PROVIDER="gemini"
     export LLM_API_KEY="<your-google-api-key>"
     export LLM_ORCHESTRATOR="gemini-2.5-pro"    # Complex alignment reasoning
     export LLM_WORKER="gemini-2.5-flash"        # Fast text generation
     ```

   - **Option B:** Use OpenRouter (requires credits)

     ```bash
     export LLM_PROVIDER="openai_compatible"
     export LLM_BASE_URL="https://openrouter.ai/api/v1"
     export LLM_API_KEY="<your-openrouter-key-with-credits>"
     export LLM_ORCHESTRATOR="google/gemini-2.5-pro"
     ```

   - **Option C:** MedGemma fallback (automatic)
     - If LLM calls fail, the agent falls back to MedGemma for synthesis
     - No configuration needed; happens automatically on LLM error

### Run Validation

```bash
# Backup old results (already done)
mv validation_results/contextual_pilot_v1 validation_results/contextual_pilot_v1_OLD_RENORMALIZED

# Run corrected validation (~40-45 minutes)
python scripts/validate_contextual_signals.py \
  --dataset data/contextual_validation_v1.json \
  --output-dir validation_results/contextual_pilot_v1_corrected

# Check results
cat validation_results/contextual_pilot_v1_corrected/contextual_signals_validation_report.json
```

### Expected Changes

**Likely Outcomes:**

1. **Overall accuracy will be LOWER** than 61.1% (e.g., 45-55%)

   - Missing signals now contribute 0.0 instead of redistributing weight
   - This is **more honest** about partial system performance

2. **Signal ROC AUC values will remain similar**:

   - Alignment: ~0.778 (unchanged, measures signal quality)
   - Plausibility: ~0.648 (unchanged)

3. **Ablation study will show different contributions**:
   - Removing Alignment will have **larger** impact (60% vs 80% of weight)
   - Removing Plausibility will have **smaller** impact (15% vs 20%)

---

## Documentation Updates

After rerunning, update the following files:

### 1. `docs/VALIDATION.md`

**Already Updated:** Lines 281-340 to reflect partial completion status

**Still Needs Update:** Replace placeholder metrics with actual corrected results:

- Overall accuracy (currently 61.1%)
- ROC AUC (currently 0.721)
- Precision, Recall, F1 scores
- Ablation study results

### 2. `ui/src/ValidationStory.jsx`

Update the validation results section with corrected metrics.

### 3. `README.md` and `START_HERE.md`

Update validation status to reflect corrected 60/15/15/10 system validation.

---

## Scientific Integrity Note

### Why This Matters

**For Your Thesis:**

- You cannot claim to have validated the 60/15/15/10 weight distribution with the old results
- The old 61.1% reflects a different system design (80/20)
- Reviewers will question this discrepancy if not corrected

**The Honest Narrative:**

1. Pilot validation initially had methodology error (auto-renormalization)
2. Error was caught and corrected before thesis submission
3. Corrected validation shows [NEW RESULTS] for designed 60/15/15/10 system
4. Demonstrates scientific rigor and self-correction

### What to Report

**Recommended framing:**

> "Initial pilot validation inadvertently tested an 80/20 weight distribution due to auto-renormalization of missing signals. Upon discovering this methodological issue, we corrected the scoring function to maintain fixed 60/15/15/10 weights (treating missing signals as 0.0). Revalidation with corrected methodology yielded [NEW ACCURACY]% on the same 90-sample dataset, providing accurate performance estimates for the designed system."

This shows:

- Scientific integrity (caught and fixed the error)
- Methodological rigor (understood the impact)
- Honest reporting (didn't sweep it under the rug)

---

## Timeline

**Immediate (Today):**

- [x] Fix scoring function
- [x] Update tests
- [x] Document issue
- [x] Update VALIDATION.md with partial completion status

**Next Steps (Before Thesis Submission):**

- [ ] Configure LLM API credentials
- [ ] Rerun validation (~45 minutes)
- [ ] Update all documentation with corrected results
- [ ] Update UI validation story
- [ ] Commit changes with clear commit message

**Estimated Time:** 2-3 hours (including API setup + validation runtime + documentation)

---

## Questions?

**Q: Can I just use the old results?**  
**A:** No. The old results reflect a different system design. Your thesis claims 60/15/15/10 weights, so you must validate that distribution.

**Q: Will the new accuracy be worse?**  
**A:** Likely yes, but that's **more scientifically honest**. You're testing a partial system (2 of 4 signals), so lower accuracy is expected and defensible.

**Q: Should I change the weights to 80/20 instead?**  
**A:** No. The 60/15/15/10 distribution is your design. Validate it honestly, acknowledge the partial coverage, and show it still beats pixel forensics (49.9%).

**Q: What if I don't have time to rerun?**  
**A:** At minimum, update documentation to clearly state the limitation and report that full validation is pending. But rerunning is strongly recommended for thesis validity.

---

## Contact

For questions about rerunning the validation, check:

- `scripts/validate_contextual_signals.py` - Validation script
- `src/app/metrics/integrity.py` - Scoring logic
- `tests/test_integrity.py` - Test cases showing correct behavior
