from __future__ import annotations

import os
from typing import Optional

from app.core.config import settings
from app.core import provider_state
from app.clinical.types import BaseMedGemmaClient


def determine_provider(model: str) -> str:
    """Determine which provider to use based on the model name."""
    model_lower = model.lower()

    # Explicit provider prefix (e.g. "vertex/my-model", "lmstudio/model")
    if "/" in model_lower:
        prefix = model_lower.split("/")[0]
        if prefix in {"vertex", "huggingface", "vllm", "local", "lmstudio"}:
            if prefix == "lmstudio":
                return "local_api"
            if prefix == "local":
                return _resolve_local_provider()
            return prefix

    if "vertex" in model_lower:
        return "vertex"

    # GGUF / quantized models -> local provider
    if (
        model_lower.endswith(".gguf")
        or "quantized" in model_lower
        or "gguf" in model_lower
    ):
        return _resolve_local_provider()

    # IT / PT models -> HuggingFace
    if model_lower.endswith("-it") or model_lower.endswith("-pt"):
        return "huggingface"

    return "huggingface"


def _resolve_local_provider() -> str:
    """Pick between local_api (LM Studio) and llama_cpp based on config."""
    # If a local GGUF file path is set and exists, prefer llama-cpp
    if settings.medgemma_local_path and os.path.exists(settings.medgemma_local_path):
        return "llama_cpp"
    # Otherwise, assume an API server (LM Studio, etc.)
    return "local_api"


def create_client(provider: Optional[str] = None) -> BaseMedGemmaClient:
    """Create a provider-specific MedGemma client.

    Priority order:
    1. Runtime BYO GPU override (set by admin via /api/v1/config/activate-byo-gpu)
    2. Explicit provider argument (passed by caller)
    3. MEDGEMMA_PROVIDER env var
    4. Auto-detect from model name
    """
    # Check for BYO GPU runtime override first (auto-reverts after inactivity).
    # Uses a single atomic call so that auto-revert check + credential read
    # happen under one lock — no TOCTOU race.
    active, byo_endpoint, byo_key = provider_state.get_effective_provider_config()
    if active == "byo_gpu":
        from app.clinical.providers.local_api import LocalApiMedGemmaClient
        return LocalApiMedGemmaClient(url_override=byo_endpoint, api_key_override=byo_key)

    if provider is None:
        # Check for explicit provider override first
        if settings.medgemma_provider:
            provider = settings.medgemma_provider
        else:
            # Auto-detect from model name
            provider = determine_provider(settings.medgemma_model)

    if provider == "huggingface":
        from app.clinical.providers.huggingface import HuggingFaceMedGemmaClient

        return HuggingFaceMedGemmaClient()

    if provider in ("local", "local_api"):
        from app.clinical.providers.local_api import LocalApiMedGemmaClient

        return LocalApiMedGemmaClient()

    if provider == "llama_cpp":
        from app.clinical.providers.llama_cpp import LlamaCppMedGemmaClient

        return LlamaCppMedGemmaClient()

    if provider == "vllm":
        from app.clinical.providers.vllm import VllmMedGemmaClient

        return VllmMedGemmaClient()

    if provider == "vertex":
        from app.clinical.providers.vertex import VertexMedGemmaClient

        return VertexMedGemmaClient()

    from app.clinical.types import MedGemmaClientError

    raise MedGemmaClientError(f"Unsupported provider: {provider}")


def get_all_providers() -> dict[str, BaseMedGemmaClient]:
    """Return a dict of provider_name -> client for all known providers."""
    from app.clinical.providers.huggingface import HuggingFaceMedGemmaClient
    from app.clinical.providers.local_api import LocalApiMedGemmaClient
    from app.clinical.providers.llama_cpp import LlamaCppMedGemmaClient
    from app.clinical.providers.vllm import VllmMedGemmaClient
    from app.clinical.providers.vertex import VertexMedGemmaClient

    return {
        "huggingface": HuggingFaceMedGemmaClient(),
        "local_api": LocalApiMedGemmaClient(),
        "llama_cpp": LlamaCppMedGemmaClient(),
        "vllm": VllmMedGemmaClient(),
        "vertex": VertexMedGemmaClient(),
    }
