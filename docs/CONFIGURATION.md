# MedContext Configuration Guide

This guide explains how to configure MedContext for different deployment scenarios.

## Quick Start (Zero Configuration)

The system works **out-of-the-box** with local GGUF inference:

```bash
# 1. Download models (one-time setup, ~3GB)
./scripts/setup_llama_cpp.sh

# 2. Copy configuration
cp .env.example .env

# 3. Start the system
docker-compose up -d
```

**No API keys needed!** The system runs entirely offline with local GGUF models.

## Configuration Architecture

MedContext has two main components that need configuration:

1. **MedGemma Provider** - Medical image analysis engine
2. **LLM Orchestrator** - Contextual reasoning and alignment analysis

### Default Configuration

```bash
# MedGemma: Local GGUF inference (offline, zero cost)
MEDGEMMA_MODEL=llama_cpp/medgemma-1.5-4b-it-Q4_K_M
MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q4_K_M.gguf
MEDGEMMA_MMPROJ_PATH=models/mmproj-F16.gguf

# LLM: Google Gemini API (1500 free requests/day)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash
```

## MedGemma Provider Options

### Option A: Local GGUF Inference (Recommended for Development)

**Pros:**
- ✅ No API costs
- ✅ Works offline
- ✅ Low latency (~2-3s per image)
- ✅ Privacy-preserving (data never leaves your server)

**Cons:**
- ⚠️ Requires ~4GB RAM
- ⚠️ One-time download (~2.4GB)

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

| Quantization | Size | Quality | Speed | RAM |
|--------------|------|---------|-------|-----|
| Q2_K | 1.7GB | Lower | Fastest | 2GB |
| Q4_K_M | 2.4GB | **Best Balance** | Fast | 4GB |
| Q5_K_M | 2.7GB | Higher | Medium | 4GB |
| Q6_K | 3.0GB | Highest | Slower | 5GB |
| Q8_0 | 3.9GB | Near-FP16 | Slowest | 6GB |

### Option B: HuggingFace Inference API (Production Ready)

**Pros:**
- ✅ No local resources needed
- ✅ Always latest model
- ✅ Free tier available (1,000 requests/month)
- ✅ Easy setup

**Cons:**
- ⚠️ Requires internet connection
- ⚠️ ~5-10s latency (cold start)
- ⚠️ API rate limits

**Setup:**

```bash
# Get token: https://huggingface.co/settings/tokens
# Use the exact model ID from huggingface.co (e.g., google/medgemma-4b-it)
MEDGEMMA_MODEL=google/medgemma-4b-it
MEDGEMMA_HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Option C: Google Vertex AI (Enterprise Production)

**Pros:**
- ✅ Lowest latency (<1s)
- ✅ High throughput
- ✅ Enterprise SLAs
- ✅ Auto-scaling

**Cons:**
- ⚠️ Requires GCP account
- ⚠️ Complex setup (deploy endpoint)
- ⚠️ Usage costs ($$$)

**Setup:**

```bash
# 1. Deploy MedGemma to Vertex AI (see docs/vertex-deployment.md)
# 2. Configure .env
MEDGEMMA_MODEL=mg-endpoint-xxxxx
MEDGEMMA_VERTEX_PROJECT=your-gcp-project-id
MEDGEMMA_VERTEX_LOCATION=us-central1
MEDGEMMA_VERTEX_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/us-central1/endpoints/ENDPOINT
VERTEX_API_KEY=your_vertex_api_key  # Optional: for key-based auth
```

## LLM Orchestrator Options

### Option A: Google Gemini API (Recommended)

**Pros:**
- ✅ 1,500 free requests/day (Gemini 2.5 Flash)
- ✅ Best performance for medical reasoning
- ✅ Native multimodal support
- ✅ Fast response times (~1-2s)

**Setup:**

```bash
# Get API key: https://aistudio.google.com/app/apikey
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash
```

### Option B: OpenRouter (Multi-Provider)

**Pros:**
- ✅ Access GPT-4, Claude, Gemini, etc.
- ✅ Pay-as-you-go pricing
- ✅ No rate limits (paid tier)
- ✅ Model switching without code changes

**Setup:**

```bash
# Get API key: https://openrouter.ai/keys
LLM_PROVIDER=openai_compatible
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_ORCHESTRATOR=anthropic/claude-3.5-sonnet
LLM_WORKER=openai/gpt-4o-mini
```

### Fallback Mode (No LLM)

If no LLM API key is provided, the system operates in **MedGemma-only mode**:
- ✅ Medical image analysis still works
- ⚠️ Limited contextual reasoning
- ⚠️ No alignment scoring

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
ENABLE_FORENSICS_MEDGEMMA=true  # MedGemma semantic layer
```

## Configuration Validation

Test your configuration:

```bash
# Check MedGemma provider status
curl http://localhost:8000/api/v1/orchestrator/providers | jq

# Expected output:
# {
#   "id": "medgemma-4b-quantized",
#   "available": true,  # <-- Should be true
#   "provider": "llama_cpp"
# }

# Check enabled modules
curl http://localhost:8000/api/v1/modules | jq

# Test end-to-end
curl -X POST http://localhost:8000/api/v1/orchestrator/run \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/medical-image.jpg",
    "context": "Patient has fever and cough"
  }'
```

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

### LLM API key not recognized

The system accepts multiple environment variable names:

```bash
# Any of these work:
GEMINI_API_KEY=xxx
OPENROUTER_API_KEY=xxx
LLM_API_KEY=xxx
GOOGLE_API_KEY=xxx
```

### Out of memory with GGUF models

Try a smaller quantization:

```bash
# Switch from Q4_K_M (2.4GB) to Q2_K (1.7GB)
MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q2_K.gguf
```

## Recommended Configurations

### Development (Local Laptop)

```bash
MEDGEMMA_MODEL=llama_cpp/medgemma-1.5-4b-it-Q4_K_M
MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q4_K_M.gguf
MEDGEMMA_MMPROJ_PATH=models/mmproj-F16.gguf
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

**Cost:** $0/month (local + Gemini free tier)
**Performance:** Good for testing

### Production (VPS/Cloud)

```bash
MEDGEMMA_MODEL=google/medgemma-4b-it  # Use exact model ID from huggingface.co
MEDGEMMA_HF_TOKEN=your_hf_token
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

**Cost:** ~$10-50/month (HF paid tier + Gemini)
**Performance:** Excellent for production traffic

### Enterprise (High Volume)

```bash
MEDGEMMA_MODEL=mg-endpoint-xxxxx
MEDGEMMA_VERTEX_PROJECT=your-project
MEDGEMMA_VERTEX_LOCATION=us-central1
MEDGEMMA_VERTEX_ENDPOINT=your_endpoint_url
LLM_PROVIDER=openai_compatible
OPENROUTER_API_KEY=your_key
LLM_ORCHESTRATOR=anthropic/claude-3.5-sonnet
```

**Cost:** $$$$ (Vertex AI + OpenRouter)
**Performance:** Sub-second latency, unlimited scale

## Security Best Practices

1. **Never commit .env files** - Already in `.gitignore`
2. **Use environment-specific configs** - `.env.dev`, `.env.prod`
3. **Rotate API keys regularly** - Set calendar reminders
4. **Use secret management** - AWS Secrets Manager, GCP Secret Manager
5. **Enable rate limiting** - See `app/middleware/rate_limit.py`

## Next Steps

- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide
- See [VALIDATION.md](VALIDATION.md) for testing and validation
- See [API.md](API.md) for API reference
