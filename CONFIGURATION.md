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
MEDGEMMA_MODEL=google/medgemma-4b-it  # Use exact model ID from huggingface.co
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

The LLM handles contextual reasoning and alignment analysis. **Recommended for full accuracy** — without it, the system falls back to MedGemma-only mode (see [Fallback Mode](#fallback-mode-no-llm) below).

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
# Restart via systemd (production VPS)
sudo systemctl restart medcontext

# Check provider status
curl http://localhost:8000/api/v1/orchestrator/providers | python3 -m json.tool
```

For local development without systemd:

```bash
# Stop and restart manually
cd /var/www/medcontext/medcontext
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir src --reload
```

**Expected output** (provider will reflect your configuration — `llama_cpp`, `huggingface`, or `vertex`):

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

## Fallback Mode (No LLM)

If no LLM API key is configured (`GEMINI_API_KEY` / `OPENROUTER_API_KEY` unset), the system still works — the orchestrator automatically falls back to MedGemma for the synthesis step. No configuration flags are needed; the fallback is automatic.

**What changes in fallback mode:**

- Triage (image analysis) works identically
- Synthesis uses MedGemma instead of a dedicated LLM, which means reduced contextual reasoning — alignment and claim veracity analysis will be less nuanced
- Each request runs llama-cpp inference **twice** (triage + synthesis), so expect ~4-6 min per request on CPU instead of ~2-3 min

**Recommendation:** Configure a Gemini API key (free tier: 1,500 req/day) for significantly better accuracy and faster responses.

## Configuration Summary

| Scenario            | MedGemma Provider   | LLM Key Required | Cost               |
| ------------------- | ------------------- | ---------------- | ------------------ |
| **Default (VPS)**   | `llama_cpp` (local) | No (fallback)    | $0                 |
| **VPS + Gemini**    | `llama_cpp` (local) | Yes              | $0 (free tier LLM) |
| **BYO HuggingFace** | `huggingface`       | Recommended      | HF API + LLM costs |
| **BYO Vertex AI**   | `vertex`            | Recommended      | GCP + LLM costs    |

## Need Help?

- Check the [API documentation](docs/API.md)
- View [validation results](docs/VALIDATION.md)
- Report issues: https://github.com/yourusername/medcontext/issues
