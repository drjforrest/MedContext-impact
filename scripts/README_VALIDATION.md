# Evidence Validation Guide

## Production Context Scoring (Primary)

Production context scoring uses the MedContext Integrity Score in `src/app/metrics/integrity.py`
(MedGemma plausibility + provenance consistency + reverse-search reputation). This is the
only score used for production context scoring.

**Validation approach:**
- Run unit tests in `tests/test_integrity.py` to verify score weighting and edge cases.
- Evaluate score distributions on labeled datasets (authentic vs. manipulated) and
  document results alongside provenance/reverse-search evidence.
- Use orchestrator runs (`/api/v1/orchestrator/run`) for end-to-end spot checks
  instead of ELA threshold tuning.

## Legacy Signal Validation (Archived) — Quick Start (5 Minutes)

### 1. Install Validation Dependencies

```bash
# Install dev dependencies (includes scipy, scikit-learn, pandas, etc.)
uv run pip install -e ".[dev]"
```

### 2. Prepare Sample Dataset

For quick testing without downloading large datasets:

```bash
# Create sample dataset structure
mkdir -p data/validation/sample/{authentic,manipulated}

# Add a few test images
# (Copy some real medical images to authentic/, some fake/edited to manipulated/)
```

### 3. Run Validation

```bash
python scripts/validate_forensics.py \
  --dataset data/validation/sample \
  --bootstrap 100 \
  --output validation_results
```

**Expected Output (legacy only):**
- Legacy forensics signal metrics with 95% confidence intervals
- ELA threshold analysis (archived supporting evidence)
- JSON report in `validation_results/`

### Legacy Validation Summary (Archived)

Legacy signals (ELA, etc.) are deprecated for production scoring. We still validate them
for transparency, research baselines, and optional secondary indicators in offline analysis.
Full bootstrap/resampling details are archived in Appendix A.

**Summary workflow:**
1. Prepare a labeled dataset (MedForensics, BTD, or UCI).
2. Run `scripts/validate_forensics.py` with bootstrap enabled.
3. Record legacy ELA thresholds for archival comparison only.

---

## Appendix A: Legacy Validation Details (Archived)

This appendix documents the legacy `validate_forensics.py` workflow for archival and
research purposes only. It is not used for production context scoring.

## Dataset Preparation

### Option 1: MedForensics Dataset (Recommended)

**Best for:** Comprehensive multi-modality validation

**Download:**
1. Visit MedForensics dataset page (see `docs/VALIDATION_DATASETS.md`)
2. Download subset (X-ray, CT, MRI recommended)
3. Extract to: `data/validation/medforensics/`

**Expected Structure:**
```
data/validation/medforensics/
  real/
    xray/
      real_001.jpg
      real_002.jpg
      ...
    ct/
      real_101.jpg
      ...
  fake/
    xray_gan/
      fake_001.jpg
      ...
    ct_stablediffusion/
      fake_101.jpg
      ...
```

**Run Validation:**
```bash
python scripts/validate_forensics.py \
  --dataset data/validation/medforensics \
  --bootstrap 1000 \
  --output validation_results/medforensics
```

---

### Option 2: Back-in-Time Diffusion (BTD)

**Best for:** Testing against state-of-the-art diffusion models

**Download:**
```bash
# Clone BTD repository
git clone https://github.com/[btd-repo]/medical-tamper-detection.git

# Follow BTD instructions to download test sets
# (typically involves downloading from Google Drive or Zenodo)

# Create symlink to MedContext structure
ln -s medical-tamper-detection/test_sets/ct_lung data/validation/btd_ct
```

**Expected Structure:**
```
data/validation/btd_ct/
  original/
    ct_001.png
    ct_002.png
    ...
  tampered/
    ct_001_tampered.png
    ct_002_tampered.png
    ...
```

**Prepare MRI subset (PNG-based, recommended):**
```bash
python scripts/prepare_btd_mri_dataset.py \
  --source data/BTD \
  --output data/validation/btd_mri
```

**Run Validation:**
```bash
python scripts/validate_forensics.py \
  --dataset data/validation/btd_mri \
  --balance \
  --bootstrap 1000 \
  --output validation_results/btd_mri
```

---

### Option 3: UCI Medical Image Tamper Detection

**Best for:** Clinical tampering scenarios (tumor insertion/removal)

**Download:**
1. Visit UCI ML Repository and search for "Medical Image Tamper Detection"
   URL: https://archive.ics.uci.edu/datasets
2. Download dataset (requires registration)
3. Keep the provided zip in `data/` (e.g., `data/medical-image-tamper-detection/data.zip`)

**Prepare Dataset (convert DICOM → PNG):**
```bash
uv run pip install pydicom
python scripts/prepare_uci_tamper_dataset.py \
  --zip data/medical-image-tamper-detection/data.zip \
  --output data/validation/uci_tamper
```

**Run Validation:**
```bash
python scripts/validate_forensics.py \
  --dataset data/validation/uci_tamper \
  --balance \
  --prediction-mode layer_1 \
  --bootstrap 1000 \
  --output validation_results/uci
```

**Optional: Use MedGemma for Layer 2**

Requires env configuration (e.g., `MEDGEMMA_PROVIDER` and tokens for your provider).

```bash
python scripts/validate_forensics.py \
  --dataset data/validation/uci_tamper \
  --balance \
  --prediction-mode ensemble \
  --use-medgemma \
  --bootstrap 1000 \
  --output validation_results/uci_medgemma
```

---

## Command Options

```bash
python scripts/validate_forensics.py --help
```

**Arguments:**
- `--dataset PATH` (required): Path to validation dataset
- `--bootstrap INT` (default: 1000): Bootstrap iterations for confidence intervals
- `--output PATH` (default: validation_results): Output directory

---

## Understanding Results

### Performance Metrics

**Accuracy:** Overall correct classification rate
- **Interpretation:** Percentage of correctly identified authentic vs. manipulated images
- **Target:** ≥80% for competition credibility

**Precision:** Of all images flagged as manipulated, how many were truly manipulated
- **Interpretation:** False positive rate (incorrectly flagging real images)
- **Target:** ≥75% (minimize false alarms)

**Recall:** Of all truly manipulated images, how many were detected
- **Interpretation:** True positive rate (catch tampering signals)
- **Target:** ≥85% (catch most fakes)

**F1 Score:** Harmonic mean of precision and recall
- **Interpretation:** Balanced metric
- **Target:** ≥80%

**ROC-AUC:** Area under receiver operating characteristic curve
- **Interpretation:** Overall discrimination ability
- **Target:** ≥0.85

### Confidence Intervals

**95% Confidence Interval [lower, upper]:**
- **Interpretation:** If we repeated this experiment 100 times, the true metric would fall within this range 95 times
- **Width:** Narrower intervals = more stable estimates
- **Example:** Accuracy: 0.847 [0.821, 0.871] → 82.1% to 87.1% accuracy with 95% confidence

### Threshold Analysis

**ELA Statistics:**
- **Authentic mean:** Average ELA standard deviation for real images
- **Manipulated mean:** Average ELA standard deviation for fake images
- **Recommended thresholds:** Optimal cutoffs based on ROC analysis

**Example (legacy ELA thresholds only):**
```json
{
  "note": "Legacy example only",
  "authentic_ela_std": {"mean": 4.8},
  "manipulated_ela_std": {"mean": 18.3},
  "recommended_thresholds": {
    "ela_std_manipulated": 17.3,
    "ela_std_authentic": 5.2
  }
}
```

**Action:** Record these values for legacy signal analysis only (archived for transparency,
research baselines, and optional secondary indicators). Production context scoring uses the
MedContext Integrity Score described above.

---

## Updating Legacy Signal Thresholds (Archived)

Legacy ELA thresholds are deprecated for production scoring. We still validate them for
transparency, research comparisons, and offline secondary indicators. Do not ship these
thresholds as production context scoring logic.

After validation, record thresholds alongside your validation notes (legacy-only):

**Before (hardcoded):**
```python
# Legacy signal thresholds (legacy example only)
if ela_std > 15.0 and ela_max > 100:
    verdict = "MANIPULATED"
```

**After (validated):**
```python
# Legacy signal thresholds (legacy example only; validated on MedForensics dataset, n=58,000)
# Optimal threshold from ROC analysis: ela_std=17.3 (archived)
if ela_std > 17.3 and ela_max > 100:
    verdict = "MANIPULATED"
elif ela_std < 5.2 and ela_max < 50:
    verdict = "AUTHENTIC"
```

---

## Example Report Output (Legacy Only)

```json
{
  "validation_summary": {
    "dataset": "data/validation/medforensics",
    "bootstrap_iterations": 1000,
    "timestamp": "2026-01-22T10:30:00"
  },
  "note": "Legacy report output only",
  "metrics": {
    "accuracy": 0.847,
    "precision": 0.823,
    "recall": 0.891,
    "f1_score": 0.856,
    "roc_auc": 0.912
  },
  "confidence_intervals_95": {
    "accuracy": {
      "mean": 0.847,
      "lower_ci": 0.821,
      "upper_ci": 0.871,
      "ci_width": 0.050
    },
    "precision": {
      "mean": 0.823,
      "lower_ci": 0.798,
      "upper_ci": 0.846,
      "ci_width": 0.048
    },
    "recall": {
      "mean": 0.891,
      "lower_ci": 0.869,
      "upper_ci": 0.911,
      "ci_width": 0.042
    },
    "f1_score": {
      "mean": 0.856,
      "lower_ci": 0.832,
      "upper_ci": 0.878,
      "ci_width": 0.046
    },
    "roc_auc": {
      "mean": 0.912,
      "lower_ci": 0.893,
      "upper_ci": 0.929,
      "ci_width": 0.036
    }
  },
  "threshold_analysis": {
    "authentic_ela_std": {
      "mean": 4.8,
      "median": 4.5,
      "std": 1.2
    },
    "manipulated_ela_std": {
      "mean": 18.3,
      "median": 17.8,
      "std": 3.5
    },
    "recommended_thresholds": {
      "ela_std_manipulated": 17.3,
      "ela_std_authentic": 5.2
    }
  }
}
```

---

## Troubleshooting

### No Images Found

**Error:** `ValueError: No images found in {dataset_path}`

**Causes:**
1. Incorrect directory structure
2. Wrong file extensions (only .jpg and .png supported)
3. Empty subdirectories

**Fix:**
```bash
# Check structure
ls -R data/validation/your_dataset/

# Verify images exist
find data/validation/your_dataset/ -name "*.jpg" -o -name "*.png" | wc -l
```

### Low Bootstrap Performance

**Symptom:** Very wide confidence intervals (>0.10 width)

**Causes:**
1. Small dataset (<100 images)
2. Class imbalance (90% authentic, 10% manipulated)
3. Not enough bootstrap iterations

**Fix:**
- Increase dataset size
- Balance classes (equal authentic/manipulated)
- Increase `--bootstrap` to 2000 or 5000

### Out of Memory

**Error:** `MemoryError` during validation

**Causes:**
1. Too many images loaded at once
2. High-resolution images (>4K)

**Fix:**
- Process in batches (modify script to load/process incrementally)
- Resize images before validation
- Reduce dataset size for initial testing

---

## Integration with Competition Submission

### Adding to AGENTIC_ARCHITECTURE.md (Legacy Only)

```markdown
## Scientific Validation (Legacy Forensics Signals)

**Dataset:** MedForensics (116,000 images, 6 modalities)
**Subset Tested:** 1,000 images (500 authentic, 500 manipulated)
**Validation Method:** Bootstrap resampling (1,000 iterations, legacy forensics)

**Performance Metrics (95% CI):**
- Accuracy: 0.847 [0.821, 0.871]
- Precision: 0.823 [0.798, 0.846]
- Recall: 0.891 [0.869, 0.911]
- F1 Score: 0.856 [0.832, 0.878]
- ROC-AUC: 0.912 [0.893, 0.929]

**Threshold Calibration (legacy only):**
Based on legacy validation, ELA thresholds updated for archival tracking:
- Manipulated threshold: 17.3 (ROC-optimal)
- Authentic threshold: 5.2 (conservative)

**Dataset Citation:**
[Author et al., "MedForensics: A Large-Scale Multi-Modal Medical Synthetic Manipulation Benchmark", 2024]
```

### Adding to README.md (Legacy Only)

```markdown
## Validation (Legacy Forensics Signals)

Legacy forensic signals have been validated on the MedForensics dataset (116K images, 6 modalities) with the following performance:

- **Accuracy:** 84.7% [82.1%, 87.1%] (95% CI)
- **Recall:** 89.1% [86.9%, 91.1%] (95% CI)

Confidence intervals computed via bootstrap resampling (1,000 iterations, legacy forensics).
```

---

## Next Steps

1. **Run validation on sample dataset** (5 min)
2. **Download MedForensics subset** (30 min)
3. **Run full validation** (10-20 min)
4. **Record legacy thresholds in validation notes** (2 min)
5. **Add results to AGENTIC_ARCHITECTURE.md** (5 min)
6. **Rerun tests to verify updated thresholds** (1 min)

```bash
# Complete workflow
uv run pip install -e ".[dev]"
python scripts/validate_forensics.py --dataset data/validation/medforensics --bootstrap 1000
# Record thresholds in validation notes or report
uv run pytest tests/test_forensics.py -v
```

---

## References

- See `docs/VALIDATION_DATASETS.md` for dataset details
- See `AGENTIC_ARCHITECTURE.md` for scientific rigor section
- See validation report JSON for full results
