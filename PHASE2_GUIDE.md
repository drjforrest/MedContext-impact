# Phase 2: HuggingFace 27B Model

**Status:** ⏳ READY TO START  
**Prerequisites:** ✅ Phase 1 completed successfully

---

## Quick Start

### 1. Get HuggingFace Token

Visit: https://huggingface.co/settings/tokens
- Click "New token"
- Select "Read" permissions
- Copy the token (starts with `hf_...`)

### 2. Accept MedGemma License

Visit: https://huggingface.co/google/medgemma-27b-it
- Click "Agree and access repository"
- This grants access to the model

### 3. Update `.env`

```bash
# Edit your .env file
nano .env

# Change these lines:
MEDGEMMA_PROVIDER=huggingface
MEDGEMMA_HF_TOKEN=hf_your_token_here
MEDGEMMA_HF_MODEL=google/medgemma-27b-it

# Optional: Uncomment/add this if not already set
# MEDGEMMA_HF_MODEL=google/medgemma-27b-it
```

### 4. Test Connection

```bash
# Test your HF token
export MEDGEMMA_HF_TOKEN="hf_your_token_here"
curl -H "Authorization: Bearer $MEDGEMMA_HF_TOKEN" \
  https://huggingface.co/api/whoami

# Should return your username and email
```

### 5. Start Phase 2

```bash
# Start validation (same seed as Phase 1 for comparison)
nohup .venv/bin/python scripts/validate_med_mmhl.py \
  --data-dir data/med-mmhl \
  --split test \
  --limit 163 \
  --random-seed 42 \
  --output validation_results/med_mmhl_n163_hf_27b \
  > validation_results/med_mmhl_n163_hf_27b_run.log 2>&1 &

# Note the PID
echo $!
```

### 6. Monitor Progress

```bash
# Check if running
ps aux | grep validate_med_mmhl

# Watch real-time output
tail -f validation_results/med_mmhl_n163_hf_27b_run.log

# Check for output files
ls -lh validation_results/med_mmhl_n163_hf_27b/
```

---

## Expected Results

### Runtime:
- **Phase 1 (Quantized 4B):** 29 minutes
- **Phase 2 (HF 27B):** ~18-25 minutes (HF Inference API is fast)

### Metrics (Expected):
- **Veracity accuracy:** 75-80% (potentially better with 27B)
- **Alignment accuracy:** 75-80% (potentially better with 27B)
- **Precision:** 40-50% (may improve with better reasoning)
- **Recall:** ~95% (should remain high)

### Key Comparison Points:

| Metric | Phase 1 (4B) | Phase 2 (27B) | Expected Change |
|--------|--------------|---------------|-----------------|
| Veracity accuracy | 73.6% | 75-80% | +1-6pp |
| Alignment accuracy | 74.8% | 75-80% | +0-5pp |
| Veracity precision | 38.2% | 40-50% | +2-12pp |
| Alignment precision | 39.4% | 40-50% | +1-11pp |

---

## Troubleshooting

### If HF API fails:

**Check token:**
```bash
curl -H "Authorization: Bearer $MEDGEMMA_HF_TOKEN" \
  https://huggingface.co/api/whoami
```

**Check model access:**
```bash
curl -H "Authorization: Bearer $MEDGEMMA_HF_TOKEN" \
  https://huggingface.co/api/models/google/medgemma-27b-it
```

**Common issues:**
- Token expired → Generate new token
- License not accepted → Visit model page and accept
- Rate limited → Wait a few minutes, HF free tier has limits

---

## After Phase 2 Completes

### 1. View Results:

```bash
cat validation_results/med_mmhl_n163_hf_27b/validation_report.json | jq '.metrics'
```

### 2. Compare Both Phases:

```bash
# Quick comparison
echo "=== Phase 1 (Quantized 4B) ==="
cat validation_results/med_mmhl_n163_quantized_4b/validation_report.json | jq '.metrics'

echo ""
echo "=== Phase 2 (HuggingFace 27B) ==="
cat validation_results/med_mmhl_n163_hf_27b/validation_report.json | jq '.metrics'
```

### 3. Choose Primary Result:

- If **27B > 4B by >2pp** → Use 27B as primary, mention 4B for reproducibility
- If **27B ≈ 4B (within 2pp)** → Use 27B for credibility, mention quantization works well
- If **4B > 27B** (unlikely) → Investigate, may indicate overfitting or API issues

### 4. Update Documentation:

Files to update with final results:
- `docs/VALIDATION.md` - Part 11 results table
- `docs/EXECUTIVE_SUMMARY.md` - Results summary
- `README.md` - Validation section
- `ui/src/ValidationStory.jsx` - VALIDATION_DATA object
- `docs/SUBMISSION.md` - Main results

---

## Ready?

Once you have your HuggingFace token, update `.env` and run the Phase 2 command!
