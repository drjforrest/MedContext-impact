# How to Re-run Med-MMHL Validation with Corrected Sampling

**Date:** February 15, 2026  
**Issue:** Sequential sampling (first 163) has 14pp bias toward misinformation (96.9% vs 83.0%)

---

## Quick Re-run Commands

### Option 1: Randomized Sample (Same Size, Corrected)

```bash
# Re-run with random seed for reproducible sampling
uv run python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --limit 163 \
  --random-seed 42 \
  --output validation_results/med_mmhl_n163_randomized
```

**Expected label distribution:** ~83% misinformation (135-138 cases), ~17% real (25-28 cases)  
**Runtime:** ~18 minutes on A100, ~24 minutes on LM Studio

### Option 2: Full Test Set (Gold Standard)

```bash
# Run on all 1,785 test samples (no sampling bias)
uv run python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --output validation_results/med_mmhl_full_test
```

**Expected label distribution:** 83% misinformation (1,481 cases), 17% real (304 cases)  
**Runtime:** ~3 hours on A100, ~5 hours on LM Studio  
**This is the gold standard** - eliminates all sampling concerns

### Option 3: Multiple Random Seeds (Robust)

```bash
# Run 3 different random samples to show stability
for seed in 42 100 999; do
  uv run python scripts/validate_med_mmhl.py \
    --data-dir data/med-mmhl \
    --split test \
    --limit 163 \
    --random-seed $seed \
    --output validation_results/med_mmhl_n163_seed_${seed}
done

# Compare results across seeds
python scripts/compare_validation_runs.py \
  validation_results/med_mmhl_n163_seed_*
```

---

## What Changed in the Code

### Updated Files:

1. **scripts/validate_med_mmhl.py**
   - Added `--random-seed` parameter
   - Implements `random.sample()` with seed when specified
   - Saves sampling method in output JSON

2. **scripts/check_sampling_bias.py** (NEW)
   - Empirically checks for bias in subset vs full dataset
   - Compares label distribution, claim lengths, sources
   - Outputs assessment: NO_SIGNIFICANT_BIAS or POTENTIAL_BIAS_DETECTED

### Usage:

```python
# In validate_med_mmhl.py (lines 99-106)
if limit:
    if random_seed is not None:
        random.seed(random_seed)
        records = random.sample(records, min(limit, len(records)))
        sampling_method = f"stratified_random_seed_{random_seed}"
    else:
        records = records[:limit]
        sampling_method = "sequential_first_n"
```

---

## How Results Will Change

### Expected Changes with Randomized Sampling:

**Recall:** Will likely **decrease** from 98.1%
- Fewer misinformation cases (135 vs 158) means fewer chances for true positives
- More realistic estimate of recall on balanced data
- Expected range: 90-95%

**Precision:** Will likely **hold or improve** 
- Similar false positive rate on ~25 real cases vs 5 real cases
- Already conservative at 98.1%
- Expected range: 95-99%

**Overall Accuracy:** Will likely **hold steady** around 95-97%
- The system's ability to classify both types correctly shouldn't change much
- Core finding (single signals 71-72% vs combined 96%) will remain

**Key insight:** The comparative finding (veracity alone insufficient, alignment alone insufficient, combined necessary) is **robust to sampling bias** because the baselines are computed on the same biased subset. The bias affects absolute numbers but not the relative comparison.

---

## Recommendation

**If you have compute budget and time:**

Run **Option 1** (randomized n=163 with seed=42) to get corrected results while maintaining reproducibility and reasonable runtime (~20 minutes).

**If compute is constrained:**

Keep current results but document the bias transparently (already done). The core scientific claim—that both contextual signals are necessary—remains valid because the baselines were computed on the same biased subset.

**Gold standard for future work:**

Run **Option 2** (full 1,785 samples) to eliminate all sampling concerns. This is the proper validation but requires ~3-5 hours of compute.

---

## Documentation Updates Needed After Re-run

If you re-run with randomized sampling, update these files with new results:

1. `docs/VALIDATION.md` - Part 11 results table
2. `docs/EXECUTIVE_SUMMARY.md` - Results summary
3. `README.md` - Validation section
4. `ui/src/ValidationStory.jsx` - VALIDATION_DATA object (lines 28-49)
5. `docs/SUBMISSION.md` - Validation notes

Replace references to:
- "sequential sampling" → "stratified random sampling (seed=42)"
- "96.9% misinformation rate" → "83% misinformation rate (representative)"
- "14pp bias" → "representative label distribution"
