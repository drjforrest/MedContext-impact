# MedContext Configuration Guide

This guide explains how to configure MedContext for different deployment scenarios.

## Quick Start (Zero Configuration)

MedContext runs **out-of-the-box** with local GGUF inference. No API keys or external services required.

```bash
# 1. Download models (one-time setup, ~3.3GB total: ~2.5GB model + ~850MB mmproj)
./scripts/setup_llama_cpp.sh

# 2. Copy configuration
cp .env.example .env

# 3. Start the system
docker-compose up -d
```

**What you get:**

- Medical image analysis powered by MedGemma (local, offline)
- No usage limits or API costs
- Privacy-preserving (images never leave the server)

## Configuration Architecture

MedContext has two main components that need configuration:

1. **MedGemma Provider** — Medical image analysis engine
2. **LLM Orchestrator** — Contextual reasoning and alignment analysis (recommended, not required)

### Default Configuration

```bash
# MedGemma: Local GGUF inference (offline, zero cost)
MEDGEMMA_MODEL=llama_cpp/medgemma-1.5-4b-it-Q4_K_M
MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q4_K_M.gguf
MEDGEMMA_MMPROJ_PATH=models/mmproj-F16.gguf
```

## MedGemma Provider Options

### Option A: Local GGUF Inference (Default)

**Pros:**
- No API costs
- Works offline
- Privacy-preserving (data never leaves your server)

**Cons:**
- Requires ~4GB RAM
- ~2-3 min per image on CPU-only servers

**Setup:**

```bash
# Download models
./scripts/setup_llama_cpp.sh

# Configure .env
MEDGEMMA_MODEL=llama_cpp/medgemma-1.5-4b-it-Q4_K_M
MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q4_K_M.gguf
MEDGEMMA_MMPROJ_PATH=models/mmproj-F16.gguf
```

**Available Quantizations:**

| Quantization | Size  | Quality          | Speed   | RAM |
| ------------ | ----- | ---------------- | ------- | --- |
| Q2_K         | 1.7GB | Lower            | Fastest | 2GB |
| Q4_K_M       | 2.4GB | **Best Balance** | Fast    | 4GB |
| Q5_K_M       | 2.7GB | Higher           | Medium  | 4GB |
| Q6_K         | 3.0GB | Highest          | Slower  | 5GB |
| Q8_0         | 3.9GB | Near-FP16        | Slowest | 6GB |

### Option B: HuggingFace Inference API

**Pros:**
- No local resources needed
- Free tier available with generous usage allowance (Inference Providers include a base credit allocation for free accounts; PRO users receive 20× more credits and higher queue priority)

**Cons:**
- Requires internet connection
- ~5-10s cold-start latency
- Rate limits vary by model and provider; some models (especially multimodal like MedGemma) may require dedicated Inference Endpoints (paid)

**Setup:**

```bash
# Get token: https://huggingface.co/settings/tokens
# Use the exact model ID from huggingface.co
MEDGEMMA_MODEL=google/medgemma-4b-it
MEDGEMMA_HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

*Note: HuggingFace does not publish a fixed monthly request quota for the free tier. Limits depend on inference credits, model type, and provider availability. See [HuggingFace Pricing](https://huggingface.co/pricing) for current details (verified Feb 2026).*

### Option C: Google Vertex AI (Enterprise)

**Pros:**
- Lowest latency (<1s)
- Auto-scaling, enterprise SLAs

**Cons:**
- Requires GCP account and deployed endpoint
- Usage costs

**Setup:**

```bash
MEDGEMMA_MODEL=mg-endpoint-xxxxx
MEDGEMMA_VERTEX_PROJECT=your-gcp-project-id
MEDGEMMA_VERTEX_LOCATION=us-central1
MEDGEMMA_VERTEX_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/us-central1/endpoints/ENDPOINT
VERTEX_API_KEY=your_vertex_api_key
```

### Provider Auto-Detection

The system auto-detects which provider to use based on the `MEDGEMMA_MODEL` value. You can also set `MEDGEMMA_PROVIDER` explicitly to override:

```bash
# Explicit override (optional — auto-detection usually works)
MEDGEMMA_PROVIDER=llama_cpp    # or: huggingface, vertex, local_api, vllm
```

## LLM Orchestrator Options

The LLM handles contextual reasoning and alignment analysis. **Recommended for full accuracy** — without it, the system falls back to MedGemma-only mode (see [Fallback Mode](#fallback-mode-no-llm) below).

### Option A: Google Gemini API (Recommended)

Free tier: 1,500 requests/day.

```bash
# Get API key: https://aistudio.google.com/app/apikey
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash
```

### Option B: OpenRouter (Multi-Provider)

Pay-as-you-go access to GPT-4, Claude, Gemini, and more.

```bash
# Get API key: https://openrouter.ai/keys
LLM_PROVIDER=openai_compatible
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_ORCHESTRATOR=anthropic/claude-3.5-sonnet
LLM_WORKER=openai/gpt-4o-mini
```

The system accepts multiple environment variable names for the API key:

```bash
# Any of these work:
GEMINI_API_KEY=xxx
OPENROUTER_API_KEY=xxx
LLM_API_KEY=xxx
GOOGLE_API_KEY=xxx
```

When multiple keys are set, they are evaluated in the order shown above and the first non-empty value wins (earliest in the list takes precedence).

### Fallback Mode (No LLM)

If no LLM API key is configured, the system still works — the orchestrator automatically falls back to MedGemma for the synthesis step. No configuration flags are needed; the fallback is automatic.

**What changes in fallback mode:**

- Triage (image analysis) works identically
- Synthesis uses MedGemma instead of a dedicated LLM, which means reduced contextual reasoning
- Each request runs llama-cpp inference **twice** (triage + synthesis), so expect ~4-6 min per request on CPU instead of ~2-3 min

**Recommendation:** Configure a Gemini API key (free tier: 1,500 req/day) for significantly better accuracy and faster responses.

## Add-on Modules (Optional)

All add-on modules are **disabled by default**:

```bash
# Reverse Image Search (requires SerpAPI key)
ENABLE_REVERSE_SEARCH=true
SERP_API_KEY=your_serp_api_key

# Provenance Tracking (blockchain-style hash chains)
ENABLE_PROVENANCE=true

# Forensics Analysis (pixel-level ELA, EXIF)
ENABLE_FORENSICS=true
ENABLE_FORENSICS_MEDGEMMA=true
```

## Production Server Settings

```bash
# Admin IP — bypasses all rate limits (use your static IP)
# ⚠️ SECURITY WARNING: ADMIN_IP bypasses all rate limits and is unsafe for shared or dynamic addresses.
# Must be a dedicated, static, non-shared IP (not a corporate NAT, ISP-assigned dynamic address, or other
# shared gateway). Do NOT use for broad networks (e.g., entire office subnets).
# Safer alternatives: assign a higher dedicated quota via LLAMA_CPP_RATE_LIMIT, or use authenticated admin
# tokens instead of global rate-limit bypass.
ADMIN_IP=your.static.ip

# Rate limit for llama-cpp requests (per hour, per IP)
LLAMA_CPP_RATE_LIMIT=5

# BYO GPU auto-revert timeout (seconds of inactivity)
BYO_GPU_INACTIVITY_SECS=120

# Demo access code (leave empty for local dev)
DEMO_ACCESS_CODE=your-access-code
```

## Testing Your Configuration

After updating `.env`, restart the service:

```bash
# Production VPS (systemd)
sudo systemctl restart medcontext

# Check provider status
curl http://localhost:8000/api/v1/orchestrator/providers | python3 -m json.tool
```

For local development:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir src --reload
```

**Expected output** (provider will reflect your configuration):

```json
[
  {
    "id": "medgemma-4b-quantized",
    "provider": "llama_cpp",
    "available": true,
    "model": "your-configured-model"
  }
]
```

Verify that `"available": true` — if `false`, check your provider configuration above.

## Configuration Summary

| Scenario            | MedGemma Provider   | LLM Key Required | Cost               |
| ------------------- | ------------------- | ---------------- | ------------------ |
| **Default (VPS)**   | `llama_cpp` (local) | No (fallback)    | $0                 |
| **VPS + Gemini**    | `llama_cpp` (local) | Yes              | $0 (free tier LLM) |
| **BYO HuggingFace** | `huggingface`       | Recommended      | HF API + LLM costs |
| **BYO Vertex AI**   | `vertex`            | Recommended      | GCP + LLM costs    |

## Troubleshooting

### "available": false for GGUF provider

```bash
# Check model files exist
ls -lh models/*.gguf

# Check .env paths are correct
grep MEDGEMMA_LOCAL_PATH .env
grep MEDGEMMA_MMPROJ_PATH .env

# Verify llama-cpp-python is installed
python -c "import llama_cpp; print('OK')"
```

### Out of memory with GGUF models

Try a smaller quantization:

```bash
# Switch from Q4_K_M (2.4GB) to Q2_K (1.7GB)
MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q2_K.gguf
```

### Backend not responding

```bash
sudo systemctl status medcontext
sudo journalctl -u medcontext --no-pager -n 50
curl http://localhost:8000/health
```

## Security Best Practices

1. **Never commit .env files** — already in `.gitignore`
2. **Rotate API keys regularly**
3. **Use secret management** in production (AWS Secrets Manager, GCP Secret Manager)
4. **Rate limiting is enabled by default** for llama-cpp endpoints

## Next Steps

- See [VALIDATION.md](VALIDATION.md) for testing and validation results
