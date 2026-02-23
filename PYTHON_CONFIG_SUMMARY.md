# Python Configuration Summary

## ✅ Completed Python Configuration

### 1. Environment Variables Added

```python
# src/app/core/config.py

# Explicit MedGemma provider override (NEW)
medgemma_provider: str = Field(
    default="",  # Empty = auto-detect
    validation_alias=AliasChoices("MEDGEMMA_PROVIDER"),
)

# LLM API key now accepts GEMINI_API_KEY (NEW)
llm_api_key: str = Field(
    default="",
    validation_alias=AliasChoices(
        "LLM_API_KEY",
        "GEMINI_API_KEY",           # ← NEW
        "OPENROUTER_API_KEY",
        "GOOGLE_API_KEY",
        "VERTEX_API_KEY",
    ),
)
```

### 2. Provider Selection Logic Updated

```python
# src/app/clinical/factory.py

def create_client(provider: Optional[str] = None) -> BaseMedGemmaClient:
    if provider is None:
        # Check for explicit provider override first (NEW)
        if settings.medgemma_provider:
            provider = settings.medgemma_provider
        else:
            # Auto-detect from model name (existing)
            provider = determine_provider(settings.medgemma_model)
    # ... rest of factory logic
```

## Configuration Options for Users

### Default (Free - Local GGUF)

```bash
MEDGEMMA_PROVIDER=llama_cpp
MEDGEMMA_LOCAL_PATH=/var/www/medcontext/models/medgemma-1.5-4b-it-Q4_K_M.gguf
MEDGEMMA_MMPROJ_PATH=/var/www/medcontext/models/mmproj-F16.gguf
GEMINI_API_KEY=user_provides
```

### Option: HuggingFace

```bash
MEDGEMMA_PROVIDER=huggingface
MEDGEMMA_MODEL=google/medgemma-1.1-4b-it
MEDGEMMA_HF_TOKEN=user_provides
GEMINI_API_KEY=user_provides  # or OPENROUTER_API_KEY
```

### Option: Vertex AI

```bash
MEDGEMMA_PROVIDER=vertex
MEDGEMMA_VERTEX_PROJECT=user_provides
MEDGEMMA_VERTEX_ENDPOINT=user_provides
VERTEX_API_KEY=user_provides
GEMINI_API_KEY=user_provides  # or OPENROUTER_API_KEY
```

## API Endpoint for UI

The existing `/api/v1/orchestrator/providers` endpoint already returns provider information:

```json
GET /api/v1/orchestrator/providers

[
  {
    "id": "medgemma-4b-quantized",
    "name": "MedGemma 4B Quantized",
    "provider": "llama_cpp",  // or "huggingface" or "vertex"
    "available": true,
    "model": "google/medgemma-1.1-4b-it.gguf"
  }
]
```

## What UI Needs to Expose

### Settings/Configuration Page

**Section 1: MedGemma Provider**

- [ ] Radio buttons: "Local GGUF (Free)" | "HuggingFace" | "Vertex AI"
- [ ] Conditional inputs based on selection:
  - HuggingFace: `MEDGEMMA_HF_TOKEN` (text input)
  - Vertex AI: `MEDGEMMA_VERTEX_PROJECT`, `MEDGEMMA_VERTEX_ENDPOINT`, `VERTEX_API_KEY`

**Section 2: LLM Orchestrator**

- [ ] Radio buttons: "Google Gemini" | "OpenRouter"
- [ ] Conditional inputs:
  - Gemini: `GEMINI_API_KEY` (text input)
  - OpenRouter: `OPENROUTER_API_KEY` (text input)

**Section 3: Save & Test**

- [ ] "Save Configuration" button
- [ ] "Test Connection" button (calls `/api/v1/orchestrator/providers`)
- [ ] Status indicator showing current provider health

## Next Steps for UI

1. **Create settings page/modal** in React app
2. **Add form fields** for each configuration option
3. **Send to backend API** for secure storage (credentials should never be stored client-side)
4. **Show current provider status** using `/api/v1/orchestrator/providers`

Ready for you to show me where to add the UI controls! 🎨
