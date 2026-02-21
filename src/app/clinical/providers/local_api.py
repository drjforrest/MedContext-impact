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


class LocalApiMedGemmaClient(BaseMedGemmaClient):
    """Client for local OpenAI-compatible servers (LM Studio, etc.)."""

    provider_name = "local_api"

    @staticmethod
    def _resolve_model_name(model: str) -> str:
        """Query the local server's /v1/models to get the actual loaded model ID."""
        api_model = model
        if "/" in api_model:
            prefix, _, actual_model = api_model.partition("/")
            if prefix in ("local", "lmstudio"):
                api_model = actual_model

        local_url = settings.local_medgemma_url.rstrip("/")
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{local_url}/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and "data" in data:
                        model_list = data["data"]
                        if isinstance(model_list, list) and model_list:
                            loaded_id = model_list[0].get("id", "")
                            if loaded_id:
                                return loaded_id
        except Exception:
            pass

        if settings.local_medgemma_model:
            return settings.local_medgemma_model

        return api_model

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        current_model = model or settings.medgemma_model
        image_bytes = resize_image(image_bytes, max_size=512)

        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"

        content = [
            {"type": "text", "text": prompt or "Describe the medical image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

        api_model = self._resolve_model_name(current_model)

        payload = {
            "model": api_model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": settings.medgemma_max_new_tokens,
            "temperature": 0.1,
        }

        local_url = settings.local_medgemma_url.rstrip("/")
        candidate_urls = list(
            dict.fromkeys(
                [
                    f"{local_url}/v1/chat/completions",
                    f"{local_url}/api/v1/chat",
                    f"{local_url}/chat/completions",
                ]
            )
        )

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.medgemma_hf_token:
            headers["Authorization"] = f"Bearer {settings.medgemma_hf_token}"

        all_errors: list[str] = []
        for url in candidate_urls:
            try:
                timeout = httpx.Timeout(300.0, read=300.0, write=30.0, connect=10.0)
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                    text = extract_openai_chat_content(data)

                    if not text:
                        if isinstance(data, dict) and "error" in data:
                            all_errors.append(
                                f"URL {url} returned error: {data['error']}"
                            )
                            continue
                        all_errors.append(
                            f"URL {url} returned OK but no content found in JSON."
                        )
                        continue

                    cleaned = clean_llm_text(text)
                    parsed = parse_llm_json(cleaned)

                    return MedGemmaResult(
                        provider="local_api",
                        model=current_model,
                        output=parsed,
                        raw_text=cleaned,
                    )
            except httpx.HTTPStatusError as exc:
                error_detail = exc.response.text if exc.response else "No response body"
                all_errors.append(
                    f"URL {url} failed with {exc.response.status_code}. "
                    f"Response: {error_detail[:500]}"
                )
            except httpx.HTTPError as exc:
                all_errors.append(f"URL {url} failed with HTTP error: {exc}")
            except Exception as exc:
                all_errors.append(f"URL {url} failed with error: {exc}")

        error_summary = "\n".join(all_errors)
        raise MedGemmaClientError(
            f"Local API request failed for all URLs. Errors:\n{error_summary}"
        )

    async def check_health(self) -> bool:
        ok, _ = await self.check_health_with_model()
        return ok

    @staticmethod
    async def check_health_with_model() -> tuple[bool, str | None]:
        """Check LM Studio availability. Returns (available, loaded_model_id)."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                url = f"{settings.local_medgemma_url.rstrip('/')}/v1/models"
                response = await client.get(url)
                if response.status_code != 200:
                    return False, None
                data = response.json()
                model_id = None
                if isinstance(data, dict) and "data" in data:
                    model_list = data["data"]
                    if isinstance(model_list, list) and model_list:
                        model_id = model_list[0].get("id")
                return True, model_id
        except Exception:
            return False, None

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "url": settings.local_medgemma_url,
        }
