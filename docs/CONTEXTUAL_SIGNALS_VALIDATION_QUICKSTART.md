# Contextual Signals Validation - Quick Start Guide

**TL;DR:** Validate MedContext's contextual signals (alignment, plausibility, genealogy, source reputation) against ground truth medical image-claim pairs.

---

## Prerequisites

- Python 3.12+
- MedContext environment set up (see main README)
- MedGemma provider configured (HuggingFace or Vertex AI)
- Ground truth dataset with medical images and labeled claims

---

## Step 1: Prepare Your Dataset

### Option A: Use CSV Template

1. Fill in the template:

   ```bash
   # Create your dataset CSV in data/
   # Columns: image_filename, claim, alignment, plausibility, is_misinformation, notes
   # See scripts/prepare_contextual_validation_dataset.py for format details
   ```

2. Place your images in a directory:

   ```
   data/medical_images/
   ├── chest_xray_001.jpg
   ├── brain_mri_002.jpg
   └── ...
   ```

3. Convert to validation format:
   ```bash
   python scripts/prepare_contextual_validation_dataset.py \
     --input-csv data/my_dataset.csv \
     --image-dir data/medical_images \
     --output data/my_dataset_v1.json
   ```

### Option B: Use JSONL Format

Create a JSONL file with one item per line:

```jsonl
{"image_path": "data/img1.jpg", "claim": "Shows pneumonia", "ground_truth": {"alignment": "aligned", "plausibility": "high", "is_misinformation": false}}
{"image_path": "data/img2.jpg", "claim": "Vaccines cause autism", "ground_truth": {"alignment": "misaligned", "plausibility": "low", "is_misinformation": true}}
```

Convert:

```bash
python scripts/prepare_contextual_validation_dataset.py \
  --input-jsonl data/my_dataset.jsonl \
  --output data/my_dataset_v1.json
```

### Option C: Create Sample Template

Generate a sample template to get started:

```bash
python scripts/prepare_contextual_validation_dataset.py \
  --create-sample \
  --output data/sample_v1.json
```

---

## Step 2: Configure Environment

Ensure your `.env` file has MedGemma configured:

```bash
# For HuggingFace (easiest)
MEDGEMMA_PROVIDER=huggingface
MEDGEMMA_HF_TOKEN=hf_your_token_here
MEDGEMMA_HF_MODEL=google/medgemma-1.5-4b-it

# OR for Vertex AI (production)
MEDGEMMA_PROVIDER=vertex
MEDGEMMA_VERTEX_PROJECT=your-gcp-project
MEDGEMMA_VERTEX_LOCATION=us-central1
MEDGEMMA_VERTEX_ENDPOINT=your-endpoint-id
```

---

## Step 3: Run Validation

```bash
python scripts/validate_contextual_signals.py \
  --dataset data/my_dataset_v1.json \
  --output-dir validation_results/my_dataset_v1
```

**What this does:**

1. Runs MedContext agent on each image-claim pair
2. Extracts all four contextual signals
3. Computes overall contextual integrity score
4. Compares predictions to ground truth
5. Generates metrics with bootstrap confidence intervals
6. Performs ablation study (measures each signal's contribution)

**Runtime:** ~3-5 seconds per image (depends on MedGemma provider)

---

## Step 4: Review Results

### Console Output

```
======================================================================
CONTEXTUAL SIGNALS VALIDATION REPORT
======================================================================

Dataset: 100 samples

Overall Performance (with 95% CI):
  accuracy       : 0.780 [0.705, 0.845]
  precision      : 0.812 [0.736, 0.881]
  recall         : 0.765 [0.681, 0.842]
  f1_score       : 0.788 [0.715, 0.856]
  roc_auc        : 0.835 [0.771, 0.893]

Signal Analysis (Individual ROC AUC):
  alignment_score          : 0.842 (coverage: 100.0%)
  plausibility_score       : 0.712 (coverage: 100.0%)
  genealogy_score          : 0.618 (coverage: 85.0%)
  source_score             : 0.592 (coverage: 72.0%)

Ablation Study (Signal Contribution):
  baseline                 : 0.780
  without_alignment        : 0.615 (contribution: +0.165)
  without_plausibility     : 0.745 (contribution: +0.035)
  without_genealogy        : 0.765 (contribution: +0.015)
  without_source           : 0.770 (contribution: +0.010)
======================================================================
```

### Output Files

```
validation_results/my_dataset_v1/
├── contextual_signals_validation_report.json  # Full results (JSON)
└── metadata.txt                               # Run configuration
```

### Interpreting Results

**Overall Performance:**

- **Accuracy > 0.75:** Good performance (exceeds target)
- **ROC AUC > 0.80:** Strong discrimination ability
- **95% CI:** Confidence intervals should not include 0.5 (random chance)

**Signal Analysis:**

- **Alignment:** Should have highest ROC AUC (primary signal)
- **Plausibility:** Moderate AUC (supporting signal)
- **Genealogy/Source:** Lower AUC (limited coverage, deterministic)

**Ablation Study:**

- **Alignment contribution:** Should be largest (15%+ drop)
- **Other signals:** Smaller contributions (2-10% drop)

---

## Step 5: Iterate and Improve

### If Performance is Below Target (<75% accuracy):

1. **Inspect Failures:**

   ```python
   import json

   with open("validation_results/my_dataset_v1/contextual_signals_validation_report.json") as f:
       report = json.load(f)

   # Find misclassified cases
   for result in report["raw_results"]:
       gt = result["ground_truth"]["alignment"]
       pred = result["predicted"]["alignment"]
       if gt != pred:
           print(f"Failed: {result['image_id']}")
           print(f"  Claim: {result['claim']}")
           print(f"  Expected: {gt}, Got: {pred}")
           print()
   ```

2. **Check Signal Coverage:**

   - Low genealogy coverage? Images may lack provenance data.
   - Low source coverage? Reverse search may not find matches.
   - Consider adjusting weights based on available signals.

3. **Refine Prompts:**
   - Triage prompt in `src/app/orchestrator/agent.py` (line 76)
   - Synthesis prompt (line 135)
   - Alignment system message (line 110)

### If Performance Exceeds Target (>85% accuracy):

Congratulations! Your contextual signals are working well. Consider:

1. **Expanding Dataset:** Test on harder cases (ambiguous claims, edge cases)
2. **Cross-Validation:** Split data into train/val/test and optimize weights
3. **Field Deployment:** Test with real-world misinformation cases

---

## Expected Performance Targets

| Metric    | Minimum | Target   | Stretch |
| --------- | ------- | -------- | ------- |
| Accuracy  | 65%     | **75%**  | 85%     |
| ROC AUC   | 0.70    | **0.80** | 0.90    |
| Precision | 70%     | **80%**  | 90%     |
| Recall    | 60%     | **70%**  | 80%     |

**Rationale:** Medical context alignment is challenging even for experts. 75% accuracy represents meaningful improvement over baselines (random: 50%, text-only: ~60%).

---

## Comparison to Pixel Forensics

| Approach                        | Accuracy | ROC AUC   | Threat Coverage                           |
| ------------------------------- | -------- | --------- | ----------------------------------------- |
| Pixel Forensics (UCI Tamper)    | 49.9%    | 0.533     | 20% (manipulated images)                  |
| **Contextual Signals** (target) | **75%+** | **0.80+** | 87% (authentic images with false context) |

Contextual signals address the dominant threat in medical misinformation.

---

## Troubleshooting

### "MedGemma request failed"

- Check `.env` configuration (provider, token, endpoint)
- Verify API quota/rate limits
- Try fallback provider (set `MEDGEMMA_FALLBACK_PROVIDER`)

### "Image not found"

- Ensure image paths in dataset are correct (absolute or relative to dataset file)
- Check file permissions

### "All signals are None"

- MedGemma may be failing silently
- Check logs for errors
- Verify model is loaded correctly

### Low coverage for genealogy/source signals

- Expected! These signals have limited availability
- Focus on alignment and plausibility for primary signal
- Genealogy/source provide additional evidence when available

---

## Advanced Usage

### Optimize Signal Weights

Use grid search to find optimal weights:

```python
from scipy.optimize import differential_evolution
from app.metrics.integrity import ContextualIntegrityWeights, compute_contextual_integrity_score

# Define objective (maximize F1 on validation set)
def objective(weights):
    # ... evaluate on validation set ...
    return -f1_score  # Negative for minimization

# Optimize
bounds = [(0.0, 1.0)] * 4
result = differential_evolution(objective, bounds)
optimal_weights = result.x
```

### Export Predictions for Analysis

```python
import json
import pandas as pd

with open("validation_results/my_dataset_v1/contextual_signals_validation_report.json") as f:
    report = json.load(f)

# Convert to DataFrame
data = []
for result in report["raw_results"]:
    data.append({
        "image_id": result["image_id"],
        "claim": result["claim"],
        "ground_truth_alignment": result["ground_truth"]["alignment"],
        "predicted_alignment": result["predicted"]["alignment"],
        "overall_score": result["predicted"]["overall_score"],
        "alignment_score": result["predicted"]["alignment_score"],
        "plausibility_score": result["predicted"]["plausibility_score"],
    })

df = pd.DataFrame(data)
df.to_csv("validation_results/my_dataset_v1/predictions.csv", index=False)
```

---

## References

- **Full Validation Framework:** `docs/CONTEXTUAL_SIGNALS_VALIDATION.md`
- **Pixel Forensics Validation:** `docs/VALIDATION.md`
- **Dataset Format Spec:** `scripts/prepare_contextual_validation_dataset.py`
- **Validator Implementation:** `scripts/validate_contextual_signals.py`

---

## Support

For questions or issues:

1. Check `docs/CONTEXTUAL_SIGNALS_VALIDATION.md` for detailed methodology
2. Review validator code: `scripts/validate_contextual_signals.py` for dataset format details
3. See `scripts/prepare_contextual_validation_dataset.py` for sample dataset format

---

**Status:** Framework complete, ready for dataset curation and validation execution.

**Last Updated:** January 31, 2026
