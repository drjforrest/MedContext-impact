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


class LlamaCppMedGemmaClient(BaseMedGemmaClient):
    """Client for local GGUF models via llama-cpp-python."""

    provider_name = "llama_cpp"

    def __init__(self) -> None:
        self._llm_instance = None
        self._model_lock = threading.Lock()

    def _load_model(self) -> None:
        # Double-checked locking for thread safety
        if self._llm_instance is not None:
            return

        with self._model_lock:
            if self._llm_instance is not None:
                return

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

        # Validate medgemma_local_path before attempting to load model
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
            self._llm_instance = Llama(
                model_path=settings.medgemma_local_path,
                chat_handler=chat_handler,
                n_ctx=4096,
                n_gpu_layers=0,
                verbose=False,
            )
        except Exception as e:
            raise MedGemmaClientError(f"Failed to load GGUF model: {e}")

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        current_model = model or settings.medgemma_model
        image_bytes = resize_image(image_bytes, max_size=512, quality=70)
        self._load_model()

        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"

        provider_state.set_llama_cpp_busy(True)
        try:
            response = self._llm_instance.create_chat_completion(
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
        if self._llm_instance is not None:
            return True
        if settings.medgemma_local_path:

            return Path(settings.medgemma_local_path).exists()
        return False

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model_path": settings.medgemma_local_path,
            "mmproj_path": settings.medgemma_mmproj_path,
            "loaded": self._llm_instance is not None,
        }
