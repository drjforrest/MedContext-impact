from __future__ import annotations

from pathlib import Path

import base64
import threading
from typing import Any, Optional

from app.core.config import settings
from app.core import provider_state
from app.core.utils import (
    clean_llm_text,
    detect_image_format,
    parse_llm_json,
    resize_image,
)
from app.clinical.types import BaseMedGemmaClient, MedGemmaClientError, MedGemmaResult

# Module-level singleton so the GGUF model loads exactly once per process
# lifetime, regardless of how many LlamaCppMedGemmaClient instances are created.
_llm_singleton = None
_singleton_lock = threading.Lock()


def _get_or_load_model():
    """Return the shared Llama instance, loading it on first call (thread-safe)."""
    global _llm_singleton

    # Fast path — already loaded
    if _llm_singleton is not None:
        return _llm_singleton

    with _singleton_lock:
        # Re-check inside the lock to handle concurrent first calls
        if _llm_singleton is not None:
            return _llm_singleton

        try:
            from llama_cpp import Llama
        except ImportError:
            raise MedGemmaClientError(
                "llama-cpp-python is required for local GGUF inference. "
                "Install with: pip install llama-cpp-python"
            )

        if not settings.medgemma_mmproj_path:
            raise MedGemmaClientError(
                "MEDGEMMA_MMPROJ_PATH is required for vision with local GGUF models."
            )

        if not settings.medgemma_local_path:
            raise MedGemmaClientError(
                "MEDGEMMA_LOCAL_PATH is required for local GGUF inference."
            )

        model_path = Path(settings.medgemma_local_path)
        if not model_path.exists():
            raise MedGemmaClientError(
                f"Model file not found at {settings.medgemma_local_path}. "
                "Please check MEDGEMMA_LOCAL_PATH setting."
            )
        if not model_path.is_file():
            raise MedGemmaClientError(
                f"MEDGEMMA_LOCAL_PATH ({settings.medgemma_local_path}) is not a file."
            )

        try:
            from llama_cpp.llama_chat_format import Llava15ChatHandler

            try:
                from llama_cpp.llama_chat_format import PaliGemmaChatHandler

                chat_handler = PaliGemmaChatHandler(
                    clip_model_path=settings.medgemma_mmproj_path
                )
            except ImportError:
                chat_handler = Llava15ChatHandler(
                    clip_model_path=settings.medgemma_mmproj_path
                )
        except ImportError:
            raise MedGemmaClientError(
                "Failed to import vision chat handlers from llama-cpp-python."
            )

        try:
            _llm_singleton = Llama(
                model_path=settings.medgemma_local_path,
                chat_handler=chat_handler,
                n_ctx=settings.medgemma_n_ctx,
                n_gpu_layers=0,
                verbose=False,
            )
        except Exception as e:
            raise MedGemmaClientError(f"Failed to load GGUF model: {e}")

        return _llm_singleton


class LlamaCppMedGemmaClient(BaseMedGemmaClient):
    """Client for local GGUF models via llama-cpp-python.

    Uses a module-level singleton so the GGUF model loads once per process
    lifetime, regardless of how many client instances are created.
    """

    provider_name = "llama_cpp"

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        current_model = model or settings.medgemma_model
        image_bytes = resize_image(image_bytes, max_size=512, quality=70)
        llm = _get_or_load_model()

        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"

        provider_state.set_llama_cpp_busy(True)
        try:
            response = llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt or "Analyze this image."},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                max_tokens=settings.medgemma_max_new_tokens,
            )
            content = response["choices"][0]["message"]["content"]
        except Exception as e:
            raise MedGemmaClientError(f"llama-cpp-python inference failed: {e}")
        finally:
            provider_state.set_llama_cpp_busy(False)

        cleaned = clean_llm_text(content)
        parsed = parse_llm_json(cleaned)

        return MedGemmaResult(
            provider=self.provider_name,
            model=current_model,
            output=parsed,
            raw_text=cleaned,
        )

    async def check_health(self) -> bool:
        if _llm_singleton is not None:
            return True
        if settings.medgemma_local_path:
            return Path(settings.medgemma_local_path).exists()
        return False

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model_path": settings.medgemma_local_path,
            "mmproj_path": settings.medgemma_mmproj_path,
            "loaded": _llm_singleton is not None,
        }
