# MedContext Configuration

## Default Setup (Free, Zero Configuration)

MedContext runs **out-of-the-box** with local GGUF inference on the VPS. No API keys or external services required.

```bash
# Already configured on the VPS
MEDGEMMA_PROVIDER=llama_cpp
MEDGEMMA_LOCAL_PATH=/var/www/medcontext/models/medgemma-1.5-4b-it-Q4_K_M.gguf
MEDGEMMA_MMPROJ_PATH=/var/www/medcontext/models/mmproj-F16.gguf
```

**What you get:**

- ✅ Multimodal Medical image analysis powered by MedGemma
- ✅ Runs entirely on VPS (no external API calls)
- ✅ No usage limits
- ✅ Privacy-preserving (images never leave the server)

## Bring Your Own GPU (Optional)

If you have access to your own GPU infrastructure, you can configure MedContext to use it instead.

### Option 1: HuggingFace Inference API

Use HuggingFace's managed inference endpoints:

```bash
# .env configuration
MEDGEMMA_PROVIDER=huggingface
MEDGEMMA_MODEL=google/medgemma-1.1-4b-it
MEDGEMMA_HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# LLM Orchestrator (required)
GEMINI_API_KEY=your_gemini_api_key
# OR
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxx
```

**Get HuggingFace Token:** https://huggingface.co/settings/tokens

### Option 2: Google Vertex AI

Use your own Google Cloud Vertex AI deployment:

```bash
# .env configuration
MEDGEMMA_PROVIDER=vertex
MEDGEMMA_VERTEX_PROJECT=your-gcp-project-id
MEDGEMMA_VERTEX_LOCATION=us-central1
MEDGEMMA_VERTEX_ENDPOINT=https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/LOCATION/endpoints/ENDPOINT
VERTEX_API_KEY=your_vertex_api_key

# LLM Orchestrator (required)
GEMINI_API_KEY=your_gemini_api_key
# OR
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxx
```

**Note:** You must deploy MedGemma to Vertex AI first. See [Vertex AI documentation](https://cloud.google.com/vertex-ai/docs).

## LLM Orchestrator Configuration

The LLM handles contextual reasoning and alignment analysis. **Required for all deployments.**

### Option A: Google Gemini (Recommended)

**Free tier:** 1,500 requests/day

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash
```

**Get API Key:** https://aistudio.google.com/app/apikey

### Option B: OpenRouter

**Pay-as-you-go** pricing for GPT-4, Claude, Gemini, and more.

```bash
LLM_PROVIDER=openai_compatible
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_ORCHESTRATOR=anthropic/claude-3.5-sonnet
LLM_WORKER=openai/gpt-4o-mini
```

**Get API Key:** https://openrouter.ai/keys

## Testing Your Configuration

After updating `.env`, restart the service:

```bash
# Stop current server
pkill -f uvicorn

# Restart with new configuration
cd /var/www/medcontext/medcontext
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir src &

# Wait for startup
sleep 5

# Check provider status
curl http://localhost:8000/api/v1/orchestrator/providers | python3 -m json.tool
```

**Expected output:**

```json
[
  {
    "id": "medgemma-4b-quantized",
    "provider": "llama_cpp", // or "huggingface" or "vertex"
    "available": true, // <-- Should be true
    "model": "your-configured-model"
  }
]
```

## Configuration Summary

| Scenario            | MedGemma Provider   | LLM Key Required | Cost               |
| ------------------- | ------------------- | ---------------- | ------------------ |
| **Default (VPS)**   | `llama_cpp` (local) | Yes              | $0 (free tier LLM) |
| **BYO HuggingFace** | `huggingface`       | Yes              | HF API + LLM costs |
| **BYO Vertex AI**   | `vertex`            | Yes              | GCP + LLM costs    |

## Need Help?

- Check the [API documentation](docs/API.md)
- View [validation results](docs/VALIDATION.md)
- Report issues: https://github.com/yourusername/medcontext/issues
