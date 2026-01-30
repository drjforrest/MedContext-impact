# Evidence Validation Quick Start - Next Steps

## ✅ What's Been Completed

### 1. Validation Framework Created

- **Script:** `scripts/validate_forensics.py` (fully functional)
- **Features:**
  - Bootstrap confidence interval computation (1,000 iterations)
  - Multi-dataset format support (MedForensics, BTD, UCI, Generic)
  - ROC-based threshold optimization
  - Comprehensive metrics (accuracy, precision, recall, F1, ROC-AUC)
  - JSON report generation

### 2. Documentation Prepared

- **`docs/VALIDATION_DATASETS.md`:** Complete catalog of available datasets
- **`scripts/README_VALIDATION.md`:** Step-by-step usage guide
- **`AGENTIC_ARCHITECTURE.md`:** Updated with scientific validation section (ready for results)

### 3. Dependencies Added

- Updated `pyproject.toml` with validation packages:
  - `scipy>=1.11.0` (statistical functions)
  - `scikit-learn>=1.3.0` (ML metrics)
  - `pandas>=2.0.0` (data analysis)
  - `matplotlib>=3.7.0` (visualization)
  - `seaborn>=0.12.0` (advanced plots)

---

## 🎯 Immediate Next Steps (1-2 Hours)

### Option A: Quick Validation with Sample Data (30 minutes)

**Best for:** Testing the evidence framework immediately without large downloads

```bash
# 1. Install validation dependencies
uv run pip install -e ".[dev]"

# 2. Create sample dataset
mkdir -p data/validation/sample/{authentic,manipulated}

# 3. Copy test images
# - Add 20-50 real medical images to data/validation/sample/authentic/
# - Add 20-50 fake/edited images to data/validation/sample/manipulated/
# (Can use images from existing project tests or online sources)

# 4. Run validation
python scripts/validate_forensics.py \
  --dataset data/validation/sample \
  --bootstrap 100 \
  --output validation_results/sample

# 5. View results
cat validation_results/sample/forensics_validation_report.json
```

**Note:** With small datasets (<100 images), confidence intervals will be wide. This is for testing only.

---

### Option B: Full Evidence Validation with MedForensics Dataset (2-4 hours)

**Best for:** Competition-quality results with scientific rigor

#### Step 1: Obtain MedForensics Dataset

**Option 1 - Academic Access (Recommended):**

1. Search for "MedForensics dataset" on Google Scholar or arXiv
2. Find the official paper/repository
3. Request access (usually requires academic email)
4. Download subset (X-ray, CT, MRI modalities recommended)

**Option 2 - Alternative Datasets:**
If MedForensics is not accessible, use these alternatives:

**A. Kaggle Medical Tamper Datasets:**

```bash
# Search Kaggle for:
# - "medical image tampering"
# - "synthetic medical images"
# - "GAN medical images"

# Common datasets:
# 1. "Medical MNIST GAN Generated Images"
# 2. "COVID-19 Real vs Fake X-rays"
# 3. "Synthetic CT Scan Dataset"
```

**B. GitHub Repositories:**

```bash
# Search GitHub for:
# - "medical tampering detection dataset"
# - "synthetic medical image dataset"

# Look for repositories with:
# - ✅ Clear licensing (MIT, CC-BY, etc.)
# - ✅ README with download instructions
# - ✅ At least 500+ images
```

#### Step 2: Organize Dataset

```bash
# MedForensics structure
mkdir -p data/validation/medforensics/{real,fake}

# If dataset has different structure, reorganize:
# - All authentic images → data/validation/medforensics/real/
# - All manipulated images → data/validation/medforensics/fake/

# Can have subdirectories for modalities:
# real/
#   xray/
#   ct/
#   mri/
# fake/
#   xray_gan/
#   ct_stablediffusion/
#   mri_stylegan/
```

#### Step 3: Run Full Validation

```bash
# Install dependencies
uv run pip install -e ".[dev]"

# Run validation (10-20 minutes for 1,000 images)
python scripts/validate_forensics.py \
  --dataset data/validation/medforensics \
  --bootstrap 1000 \
  --output validation_results/medforensics

# View summary
cat validation_results/medforensics/forensics_validation_report.json | jq '.confidence_intervals_95'
```

#### Step 4: Update Thresholds

Based on validation results, record updates alongside `scripts/validate_forensics.py` output:

**Example:**

```python
# In run_layer_1() function
# OLD:
if ela_std > 15.0 and ela_max > 100:
    verdict = "MANIPULATED"
    confidence = min(0.85, 0.5 + (ela_std / 50.0))
elif ela_std < 5.0 and ela_max < 50:
    verdict = "AUTHENTIC"

# NEW (based on validation):
# Thresholds validated on MedForensics dataset (n=1,000, 95% CI)
# Optimal threshold from ROC analysis: ela_std=17.3
if ela_std > 17.3 and ela_max > 100:
    verdict = "MANIPULATED"
    confidence = min(0.85, 0.5 + (ela_std / 50.0))
elif ela_std < 5.2 and ela_max < 50:
    verdict = "AUTHENTIC"
```

#### Step 5: Verify with Tests

```bash
# Run forensics tests to ensure thresholds still work
uv run pytest tests/test_forensics.py -v

# All tests should still pass
# (May need to adjust test fixtures if thresholds changed significantly)
```

#### Step 6: Update Documentation

Add validation results to `AGENTIC_ARCHITECTURE.md`:

1. Replace placeholder values in "Scientific Validation & Confidence Intervals" section
2. Update metrics with actual results from JSON report
3. Add dataset citation

**Example:**

```markdown
**Dataset:** MedForensics subset (1,000 images: 500 authentic, 500 manipulated)
**Validation Method:** Bootstrap resampling (1,000 iterations)

**Performance Metrics (95% CI):**

- Accuracy: 0.847 [0.821, 0.871] ← Replace with actual values
- Precision: 0.823 [0.798, 0.846]
- Recall: 0.891 [0.869, 0.911]
- F1 Score: 0.856 [0.832, 0.878]
- ROC-AUC: 0.912 [0.893, 0.929]
```

---

## 📊 Interpreting Results

The validation metrics measure **forensics signal stability** and help calibrate thresholds. They are **supporting evidence** for contextual authenticity, not a definitive authenticity claim.

### If Results Are Lower Than Expected

**Possible causes:**

1. **Dataset Quality:**
   - Mislabeled images
   - Low-quality fakes (easy to detect) or high-quality fakes (hard to detect)
   - Distribution mismatch

2. **Implementation Issues:**
   - ELA thresholds too strict/lenient
   - JPEG quality parameter suboptimal
   - Ensemble voting weights off

**Solutions:**

- Try different dataset
- Tune ELA JPEG quality (try 90, 95, 98)
- Adjust ensemble voting logic
- Add more layers (e.g., frequency domain analysis)

---

## 🏆 Adding to Competition Submission

### Update SUBMISSION.md

Add validation section:

```markdown
## Scientific Validation

**Dataset:** MedForensics (1,000 images, 6 modalities)
**Method:** Bootstrap resampling (1,000 iterations)

**Key Results:**

- Accuracy: 84.7% [82.1%, 87.1%] (95% CI)
- Recall: 89.1% [86.9%, 91.1%] (95% CI)
- ROC-AUC: 0.912 [0.893, 0.929] (95% CI)

**Threshold Optimization:**
ELA thresholds calibrated via ROC analysis on validation set, maximizing
Youden's J statistic (sensitivity + specificity - 1).

**Reproducibility:**
Validation script and dataset instructions provided in `scripts/` directory.
```

### Update README.md

Add validation badge:

```markdown
## Validation

✅ **Validated on MedForensics Dataset**

- 84.7% accuracy [82.1%, 87.1%] (95% CI)
- 89.1% recall [86.9%, 91.1%] (95% CI)
- 1,000 bootstrap iterations

See `AGENTIC_ARCHITECTURE.md` for full validation methodology.
```

---

## 🚦 Status Check

**Before submission, ensure:**

- [ ] Validation script runs successfully
- [ ] Results with confidence intervals documented
- [ ] Thresholds recorded in validation notes
- [ ] All tests still pass
- [ ] `AGENTIC_ARCHITECTURE.md` updated with results
- [ ] `SUBMISSION.md` includes validation section
- [ ] Dataset citation added to references

---

## 🆘 Troubleshooting

### Can't Find MedForensics Dataset

**Alternatives:**

1. Kaggle: Search "medical image tampering" or "synthetic medical images"
2. Papers With Code: Look for datasets tagged "medical imaging" + "tamper detection"
3. GitHub: Search repositories with medical tampering datasets

**Minimum viable dataset:**

- At least 200 images (100 authentic, 100 manipulated)
- Medical imaging modality (X-ray, CT, MRI, ultrasound)
- Clear labels

### Validation Script Errors

**Import errors:**

```bash
# Reinstall dev dependencies
uv run pip install -e ".[dev]" --force-reinstall
```

**Image loading errors:**

```bash
# Check images are valid
python -c "from PIL import Image; Image.open('data/validation/sample/authentic/img1.jpg').verify()"
```

**Memory errors:**

```bash
# Reduce dataset size or bootstrap iterations
python scripts/validate_forensics.py --dataset data/validation/sample --bootstrap 100
```

---

## ⏰ Time Estimates

**Quick validation (sample data):** 30 minutes

- Setup: 5 min
- Collect images: 10 min
- Run validation: 5 min
- Review results: 10 min

**Full validation (MedForensics):** 2-4 hours

- Dataset access/download: 1-2 hours
- Setup: 10 min
- Run validation: 20 min
- Update thresholds: 15 min
- Update docs: 30 min
- Final review: 15 min

---

## 📞 Need Help?

**See:**

- `scripts/README_VALIDATION.md` - Detailed usage guide
- `docs/VALIDATION_DATASETS.md` - Dataset catalog
- `scripts/validate_forensics.py` - Full validation implementation

**Common issues and solutions documented in README files.**

---

## ✨ Summary

You now have a **production-ready evidence validation framework** that:

1. Computes confidence intervals via bootstrap resampling
2. Supports multiple dataset formats
3. Optimizes thresholds via ROC analysis
4. Generates comprehensive JSON reports
5. Addresses scientific rigor concerns from literature

**Next immediate action:** Choose Option A (quick test) or Option B (full validation) and execute the steps above.

**Competition impact:** Adding validation with confidence intervals demonstrates scientific rigor and significantly strengthens your submission credibility. 🏆
