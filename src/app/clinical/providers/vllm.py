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
from app.clinical.providers._utils import extract_openai_chat_content
from app.clinical.types import BaseMedGemmaClient, MedGemmaClientError, MedGemmaResult


class VllmMedGemmaClient(BaseMedGemmaClient):
    """Client for vLLM-served models via OpenAI-compatible API."""

    provider_name = "vllm"

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        current_model = model or settings.medgemma_model
        if not settings.medgemma_vllm_url:
            raise MedGemmaClientError("Missing MEDGEMMA_VLLM_URL for vLLM.")

        image_bytes = resize_image(image_bytes, max_size=512)

        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"
        content = [
            {"type": "text", "text": prompt or "Describe the medical image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
        payload = {
            "model": current_model,
            "messages": [{"role": "user", "content": content}],
        }

        raw_url = settings.medgemma_vllm_url.rstrip("/")
        candidate_urls = [raw_url]
        if settings.medgemma_url:
            candidate_urls.append(settings.medgemma_url.rstrip("/"))
        if "/chat/completions" not in raw_url:
            if raw_url.endswith("/v1"):
                candidate_urls.append(f"{raw_url}/chat/completions")
            else:
                candidate_urls.append(f"{raw_url}/v1/chat/completions")
                candidate_urls.append(f"{raw_url}/chat/completions")
        for base_url in list(candidate_urls):
            if "/chat/completions" in base_url:
                continue
            if base_url.endswith("/v1"):
                candidate_urls.append(f"{base_url}/chat/completions")
            else:
                candidate_urls.append(f"{base_url}/v1/chat/completions")
                candidate_urls.append(f"{base_url}/chat/completions")
        candidate_urls = list(dict.fromkeys(candidate_urls))

        last_error: Exception | None = None
        last_status: int | None = None
        last_url: str | None = None
        response = None
        headers: dict[str, str] = {}
        if settings.medgemma_hf_token:
            headers["Authorization"] = f"Bearer {settings.medgemma_hf_token}"
        with httpx.Client(timeout=90.0) as client:
            for url in candidate_urls:
                try:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    break
                except httpx.HTTPStatusError as exc:
                    error_detail = (
                        exc.response.text if exc.response else "No response body"
                    )
                    last_error = f"{exc}. Response: {error_detail[:500]}"
                    last_status = exc.response.status_code if exc.response else None
                    last_url = url
                    if exc.response is not None and exc.response.status_code == 404:
                        continue
                    raise MedGemmaClientError(
                        f"vLLM request failed: {last_error}"
                    ) from exc
                except httpx.HTTPError as exc:
                    last_error = exc
                    raise MedGemmaClientError(f"vLLM request failed: {exc}") from exc

        if response is None:
            raise MedGemmaClientError(
                "vLLM request failed for URLs: "
                f"{', '.join(candidate_urls)} (last_status={last_status}, last_url={last_url})"
            ) from last_error

        try:
            data = response.json()
        except ValueError as exc:
            snippet = response.text[:300] if response.text else ""
            raise MedGemmaClientError(
                f"vLLM returned non-JSON response ({response.status_code}). "
                f"Body: {snippet}"
            ) from exc

        text = extract_openai_chat_content(data)

        if not text and isinstance(data, dict) and "error" in data:
            raise MedGemmaClientError(
                f"vLLM request returned an error: {data['error']}"
            )

        if not text:
            raise MedGemmaClientError(
                f"vLLM request succeeded but no content found: {str(data)[:500]}"
            )

        cleaned = clean_llm_text(text)
        parsed = parse_llm_json(cleaned)

        return MedGemmaResult(
            provider="vllm",
            model=current_model,
            output=parsed,
            raw_text=cleaned,
        )

    async def check_health(self) -> bool:
        if not settings.medgemma_vllm_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(settings.medgemma_vllm_url.rstrip("/"))
                return resp.status_code in (200, 401, 403, 404)
        except Exception:
            return False

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "url": settings.medgemma_vllm_url,
        }
