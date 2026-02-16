# Phase 2 Validation - Running Now

**Status:** ✅ IN PROGRESS  
**Started:** February 15, 2026 at 11:13 AM PST  
**PID:** 53676  
**Log File:** `validation_results/med_mmhl_n163_hf_27b_run.log`

---

## Configuration

**Model:** MedGemma 27B (HuggingFace Dedicated Endpoint)

- Provider: `vllm` (OpenAI-compatible)
- Endpoint: `$HF_ENDPOINT_URL/v1/chat/completions` (configured via environment)
- Model: `google/medgemma-27b-it`
- Hardware: 2x A100 80GB GPUs (inferred from endpoint)

**Dataset:**

- Source: Med-MMHL test set
- Sampling: **Randomized with seed=42** (same as Phase 1)
- n_samples: 163
- Expected label distribution: ~135 misinformation (83%), ~28 real (17%)

**LLM:** OpenRouter (for orchestration)

---

## Expected Timeline

- **Per-sample processing time:** ~6-8 seconds (faster than quantized due to GPU acceleration)
- **Total expected runtime:** ~16-22 minutes
- **Completion ETA:** ~11:31 AM PST

---

## Monitoring Commands

```bash
# Check if still running
ps -p 53676 || echo "Completed"

# View real-time progress
tail -f validation_results/med_mmhl_n163_hf_27b_run.log

# Check for output files
ls -lh validation_results/med_mmhl_n163_hf_27b/

# View final results (after completion)
cat validation_results/med_mmhl_n163_hf_27b/validation_report.json | jq '.'
```

---

## Phase 1 vs Phase 2 Comparison

### Phase 1 Results (Quantized 4B):

| Metric                | Value     |
| --------------------- | --------- |
| **Combined Accuracy** | **89.0%** |
| **Precision**         | **96.8%** |
| **Recall**            | **89.7%** |
| **F1 Score**          | **0.931** |
| Veracity Accuracy     | 73.6%     |
| Alignment Accuracy    | 74.8%     |

### Phase 2 Expected (HuggingFace 27B):

| Metric             | Expected Range |
| ------------------ | -------------- |
| Combined Accuracy  | 90-95%         |
| Precision          | 95-98%         |
| Recall             | 90-95%         |
| F1 Score           | 0.93-0.95      |
| Veracity Accuracy  | 75-80%         |
| Alignment Accuracy | 75-80%         |

**Key Question:** Will the larger 27B model improve upon the quantized 4B's 89% accuracy?

---

## What's Different in Phase 2

1. ✅ **Larger Model:** 27B parameters vs 4B parameters
2. ✅ **Better Hardware:** 2x A100 GPUs vs local quantized CPU/GPU
3. ✅ **No Quantization:** Full precision vs 4-bit quantization
4. ✅ **Same Seed:** Random seed=42 ensures same subset of data
5. ✅ **Direct Comparison:** All differences are due to model size/quality

---

## Current Status

- ✅ Process running (PID: 53676)
- ✅ Dataset file created (897 KB)
- ⏳ Processing samples (~33 seconds elapsed)
- ⏳ Expected completion in ~16-21 minutes

---

## After Completion

1. Compare Phase 1 vs Phase 2 results
2. Choose primary result (likely Phase 2 if it's better)
3. Regenerate validation figures with best result
4. Update all documentation with final metrics
5. Document methodology transparency (bias correction + model comparison)

**Waiting for Phase 2 to complete...**
