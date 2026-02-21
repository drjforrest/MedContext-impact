from __future__ import annotations

import base64
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.utils import (
    clean_llm_text,
    detect_image_format,
    parse_llm_json,
    resize_image,
)
from app.clinical.types import BaseMedGemmaClient, MedGemmaClientError, MedGemmaResult


class HuggingFaceMedGemmaClient(BaseMedGemmaClient):
    provider_name = "huggingface"

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        current_model = model or settings.medgemma_model
        if not settings.medgemma_hf_token:
            raise MedGemmaClientError(
                "Missing MEDGEMMA_HF_TOKEN for HuggingFace inference."
            )

        # Use custom endpoint URL if available, otherwise use Inference API
        if settings.medgemma_url and not settings.medgemma_url.startswith(
            "http://localhost"
        ):
            url = settings.medgemma_url.rstrip("/")
        else:
            url = f"https://api-inference.huggingface.co/models/{current_model}"
        headers = {"Authorization": f"Bearer {settings.medgemma_hf_token}"}

        image_bytes = resize_image(image_bytes, max_size=512)

        payload: dict[str, Any] | bytes
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        inputs_text: Optional[str] = None

        # Use TGI format for dedicated endpoints
        if settings.medgemma_url and not settings.medgemma_url.startswith(
            "http://localhost"
        ):
            image_format = detect_image_format(image_bytes)
            image_data_url = f"data:image/{image_format};base64,{encoded_image}"
            inputs_text = (
                f"![]({image_data_url}){prompt or 'Describe this medical image.'}"
            )
            payload = {
                "inputs": inputs_text,
                "parameters": {
                    "max_new_tokens": settings.medgemma_max_new_tokens,
                },
            }
        else:
            if prompt:
                payload = {"inputs": {"image": encoded_image, "text": prompt}}
            else:
                payload = image_bytes

        try:
            timeout = httpx.Timeout(300.0, read=300.0, write=30.0, connect=10.0)
            with httpx.Client(timeout=timeout) as client:
                if isinstance(payload, bytes):
                    response = client.post(url, headers=headers, content=payload)
                else:
                    response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text if exc.response else "No response body"
            raise MedGemmaClientError(
                f"HuggingFace request failed: {exc}. Response: {error_detail[:500]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise MedGemmaClientError(f"HuggingFace request failed: {exc}") from exc

        raw_text = response.text
        try:
            response_data = response.json()
            if isinstance(response_data, list) and response_data:
                generated = response_data[0].get("generated_text", "")
            elif isinstance(response_data, dict):
                generated = response_data.get("generated_text", "")
            else:
                generated = str(response_data)

            if generated:
                if inputs_text and generated.startswith(inputs_text):
                    generated = generated[len(inputs_text) :].strip()
                elif prompt and generated.startswith(prompt):
                    generated = generated[len(prompt) :].strip()
                raw_text = generated
        except Exception:
            pass

        cleaned = clean_llm_text(raw_text)
        parsed = parse_llm_json(cleaned)

        return MedGemmaResult(
            provider="huggingface",
            model=current_model,
            output=parsed,
            raw_text=raw_text,
        )

    async def check_health(self) -> bool:
        return await self.check_model_health()

    @staticmethod
    async def check_model_health(model_id: str | None = None) -> bool:
        """Check HuggingFace availability, optionally for a specific model."""
        if not settings.medgemma_hf_token:
            return False

        headers = {"Authorization": f"Bearer {settings.medgemma_hf_token}"}

        if settings.medgemma_url and not settings.medgemma_url.startswith(
            "http://localhost"
        ):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(
                        f"{settings.medgemma_url.rstrip('/')}/health", headers=headers
                    )
                    if resp.status_code == 200:
                        return True
                    resp = await client.get(
                        settings.medgemma_url.rstrip("/"), headers=headers
                    )
                    return resp.status_code in (200, 401, 403)
            except Exception:
                return False

        if model_id:
            try:
                url = f"https://api-inference.huggingface.co/models/{model_id}"
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(url, headers=headers)
                    return resp.status_code == 200
            except Exception:
                return False

        return bool(settings.medgemma_hf_token)

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "has_token": bool(settings.medgemma_hf_token),
            "custom_endpoint": bool(
                settings.medgemma_url
                and not settings.medgemma_url.startswith("http://localhost")
            ),
        }
