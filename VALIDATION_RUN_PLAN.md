# Validation Run Plan: Two-Phase Approach

**Date:** February 15, 2026  
**Goal:** Re-run Med-MMHL validation with corrected randomized sampling  
**Issue:** Original sequential sampling had 14pp bias (96.9% vs 83.0% misinformation)

---

## Phase 1: Quantized Model (LM Studio) — FIRST

Run with local quantized MedGemma 4B model via LM Studio for cost-effective initial validation.

### Configuration:

Create/update `.env` with:

```bash
# MedGemma Configuration - Local Quantized via LM Studio
MEDGEMMA_PROVIDER=local
LOCAL_MEDGEMMA_URL=http://192.168.1.90:1234
LOCAL_MEDGEMMA_MODEL=unsloth/medgemma-1.5-4b-it-GGUF

# LLM for orchestration (use whatever you have configured)
LLM_PROVIDER=gemini  # or ollama, openai_compatible
LLM_API_KEY=your-api-key
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash

# Database (if needed for provenance)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/medcontext

# Keep add-ons disabled for core validation
ENABLE_REVERSE_SEARCH=false
ENABLE_PROVENANCE=false
ENABLE_FORENSICS=false
```

### Run Command:

```bash
# Randomized sampling with seed=42 (corrects the 14pp bias)
uv run python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --limit 163 \
  --random-seed 42 \
  --output validation_results/med_mmhl_n163_quantized_4b
```

### Expected:

- **Runtime:** ~24 minutes (quantized 4B on CPU/GPU)
- **Label distribution:** ~135-138 misinformation (83%), ~25-28 real (17%)
- **Results:** Likely similar accuracy (~95-97%) but more realistic recall (~90-95%)

### Output Files:

```
validation_results/med_mmhl_n163_quantized_4b/
├── report.json                  # Full metrics + metadata
├── detailed_results.jsonl       # Per-sample predictions
└── confusion_matrix.png         # Optional visualization
```

---

## Phase 2: HuggingFace 27B Model — AFTER Phase 1

Run with full-size MedGemma 27B via HuggingFace Inference API for comparison.

### Configuration:

Update `.env`:

```bash
# MedGemma Configuration - HuggingFace Inference API
MEDGEMMA_PROVIDER=huggingface
MEDGEMMA_HF_TOKEN=hf_...your_token_here
MEDGEMMA_HF_MODEL=google/medgemma-27b-it  # Full 27B model

# LLM stays the same
LLM_PROVIDER=gemini
LLM_API_KEY=your-api-key
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/medcontext

# Keep add-ons disabled
ENABLE_REVERSE_SEARCH=false
ENABLE_PROVENANCE=false
ENABLE_FORENSICS=false
```

### Get HuggingFace Token:

1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "Read" access
3. Accept MedGemma license at https://huggingface.co/google/medgemma-27b-it
4. Copy token to `MEDGEMMA_HF_TOKEN`

### Run Command:

```bash
# Same random seed for direct comparison
uv run python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --limit 163 \
  --random-seed 42 \
  --output validation_results/med_mmhl_n163_hf_27b
```

### Expected:

- **Runtime:** ~18-22 minutes (HF Inference API is fast)
- **Label distribution:** Identical to Phase 1 (same seed=42)
- **Results:** Potentially slightly better accuracy/recall with 27B model

### Output Files:

```
validation_results/med_mmhl_n163_hf_27b/
├── report.json
├── detailed_results.jsonl
└── confusion_matrix.png
```

---

## Compare Results

After both runs complete, compare them:

```bash
# Create comparison script
cat > scripts/compare_two_runs.py << 'EOF'
#!/usr/bin/env python3
"""Compare two validation runs."""
import json
import sys
from pathlib import Path

def load_report(path: Path) -> dict:
    with open(path / "report.json") as f:
        return json.load(f)

def compare_runs(run1_path: Path, run2_path: Path):
    r1 = load_report(run1_path)
    r2 = load_report(run2_path)
    
    print("=" * 80)
    print("VALIDATION RUN COMPARISON")
    print("=" * 80)
    print(f"\nRun 1: {run1_path.name}")
    print(f"  Sampling: {r1.get('sampling_method', 'unknown')}")
    print(f"  Random seed: {r1.get('random_seed', 'N/A')}")
    print(f"  n_samples: {r1['n_samples']}")
    
    print(f"\nRun 2: {run2_path.name}")
    print(f"  Sampling: {r2.get('sampling_method', 'unknown')}")
    print(f"  Random seed: {r2.get('random_seed', 'N/A')}")
    print(f"  n_samples: {r2['n_samples']}")
    
    print("\n" + "=" * 80)
    print("METRICS COMPARISON")
    print("=" * 80)
    
    m1 = r1['metrics']
    m2 = r2['metrics']
    
    metrics_to_compare = ['accuracy', 'precision', 'recall', 'f1']
    
    print(f"\n{'Metric':<15} {'Run 1':>12} {'Run 2':>12} {'Diff':>12}")
    print("-" * 55)
    
    for metric in metrics_to_compare:
        v1 = m1.get(metric, 0)
        v2 = m2.get(metric, 0)
        diff = v2 - v1
        sign = "+" if diff > 0 else ""
        print(f"{metric:<15} {v1:>11.1%} {v2:>11.1%} {sign}{diff:>10.1%}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_two_runs.py <run1_dir> <run2_dir>")
        sys.exit(1)
    
    run1 = Path(sys.argv[1])
    run2 = Path(sys.argv[2])
    
    compare_runs(run1, run2)
EOF

chmod +x scripts/compare_two_runs.py

# Run comparison
python scripts/compare_two_runs.py \
  validation_results/med_mmhl_n163_quantized_4b \
  validation_results/med_mmhl_n163_hf_27b
```

---

## Expected Outcomes

### Accuracy Comparison:

- **4B Quantized:** 95-97% (slight degradation from quantization)
- **27B Full:** 96-98% (better reasoning with larger model)
- **Original biased:** 96.3% (inflated by 14pp label bias)

### Recall Changes (Most Important):

- **Original sequential:** 98.1% (inflated by 96.9% misinformation rate)
- **Corrected randomized:** ~90-95% (realistic with 83% misinformation rate)
- **This is expected and scientifically honest!**

### Precision (Should Hold):

- **Original:** 98.1% (already conservative)
- **Corrected:** 95-99% (similar or better)

### Key Insight:

The **comparative finding remains robust**: single signals (71-72%) vs combined (95-97%). The absolute accuracy may shift slightly, but the ~24pp improvement over baselines will hold because the baselines are computed on the same randomized subset.

---

## What to Document After Both Runs

### 1. Choose Primary Result:

If 27B > 4B by >2pp → use 27B as primary  
If 27B ≈ 4B (within 2pp) → use 27B for credibility, mention 4B for reproducibility

### 2. Update These Files:

- `docs/VALIDATION.md` - Part 11 results table
- `docs/EXECUTIVE_SUMMARY.md` - Results summary
- `README.md` - Validation section
- `ui/src/ValidationStory.jsx` - VALIDATION_DATA object
- `docs/SUBMISSION.md` - Replace biased results

### 3. Key Changes:

Replace:
- ❌ "sequential sampling (first 163)" → ✅ "stratified random sampling (seed=42)"
- ❌ "96.9% misinformation" → ✅ "83% misinformation (representative)"
- ❌ "98.1% recall" → ✅ "92.4% recall" (example)
- ❌ Remove all bias disclaimers → ✅ Add "corrected sampling"

### 4. Transparency Statement:

Add to all docs:

> **Sampling correction (Feb 15, 2026):** Initial validation used sequential sampling (first 163 records) which introduced a 14pp label bias (96.9% vs 83.0% misinformation). Results were re-computed using stratified random sampling (seed=42) to ensure representative label distribution. The corrected results show similar comparative performance (single signals 71-72% vs combined 95-97%) while providing more realistic absolute metrics.

---

## Troubleshooting

### Phase 1 (Quantized):

**If LM Studio connection fails:**
```bash
# Check LM Studio is running at http://192.168.1.90:1234
curl http://192.168.1.90:1234/v1/models

# Try localhost if on same machine
LOCAL_MEDGEMMA_URL=http://localhost:1234
```

**If model not found:**
```bash
# Load model in LM Studio first
# File → Download Model → Search "medgemma" → Download 4B GGUF
# Then load it in the server tab
```

### Phase 2 (HuggingFace):

**If authentication fails:**
```bash
# Verify token
curl -H "Authorization: Bearer $MEDGEMMA_HF_TOKEN" \
  https://huggingface.co/api/whoami

# Check model access (may need to accept license first)
# Visit: https://huggingface.co/google/medgemma-27b-it
```

**If rate limited:**
```bash
# HF Inference API has rate limits on free tier
# Consider upgrading or spacing out requests
# Add to .env:
MEDGEMMA_HF_RATE_LIMIT_DELAY=2.0  # seconds between calls
```

---

## Quick Start Commands

### Phase 1 (Start Now):

```bash
# 1. Update .env for quantized model
nano .env  # Set MEDGEMMA_PROVIDER=local, etc.

# 2. Verify dataset exists
ls -lh data/med-mmhl/benchmarked_data/image_article/test_data.csv

# 3. Run validation
uv run python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --limit 163 \
  --random-seed 42 \
  --output validation_results/med_mmhl_n163_quantized_4b

# 4. Check results
cat validation_results/med_mmhl_n163_quantized_4b/report.json | jq '.metrics'
```

### Phase 2 (After Phase 1):

```bash
# 1. Update .env for HuggingFace
nano .env  # Set MEDGEMMA_PROVIDER=huggingface, add HF_TOKEN

# 2. Verify HF access
curl -H "Authorization: Bearer $MEDGEMMA_HF_TOKEN" \
  https://huggingface.co/api/whoami

# 3. Run validation (same seed!)
uv run python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --limit 163 \
  --random-seed 42 \
  --output validation_results/med_mmhl_n163_hf_27b

# 4. Compare both runs
python scripts/compare_two_runs.py \
  validation_results/med_mmhl_n163_quantized_4b \
  validation_results/med_mmhl_n163_hf_27b
```

---

## Next Steps

1. ✅ Run Phase 1 (quantized 4B) - **START HERE**
2. ⏳ Monitor progress (~24 minutes)
3. ⏳ Switch `.env` to HuggingFace
4. ⏳ Run Phase 2 (full 27B)
5. ⏳ Compare results
6. ⏳ Update documentation with corrected metrics
7. ✅ Document methodology transparency

**Ready to start Phase 1 now!**
