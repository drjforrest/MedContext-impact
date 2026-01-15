from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import settings


class MedGemmaClientError(RuntimeError):
    pass


@dataclass
class MedGemmaResult:
    provider: str
    model: str
    output: Any


class MedGemmaClient:
    def __init__(self) -> None:
        self.provider = settings.medgemma_provider.lower()

    def analyze_image(
        self, image_bytes: bytes, prompt: Optional[str] = None
    ) -> MedGemmaResult:
        if self.provider == "huggingface":
            return self._analyze_huggingface(image_bytes=image_bytes, prompt=prompt)
        if self.provider == "vertex":
            return self._analyze_vertex(image_bytes=image_bytes, prompt=prompt)
        raise MedGemmaClientError(f"Unsupported provider: {self.provider}")

    def _analyze_huggingface(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        if not settings.medgemma_hf_token:
            raise MedGemmaClientError(
                "Missing MEDGEMMA_HF_TOKEN for HuggingFace inference."
            )

        url = (
            f"https://api-inference.huggingface.co/models/{settings.medgemma_hf_model}"
        )
        headers = {"Authorization": f"Bearer {settings.medgemma_hf_token}"}

        payload: dict[str, Any] | bytes
        if prompt:
            payload = {"inputs": {"image": image_bytes, "text": prompt}}
        else:
            payload = image_bytes

        try:
            with httpx.Client(timeout=60.0) as client:
                if isinstance(payload, bytes):
                    response = client.post(url, headers=headers, content=payload)
                else:
                    response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MedGemmaClientError(f"HuggingFace request failed: {exc}") from exc

        return MedGemmaResult(
            provider="huggingface",
            model=settings.medgemma_hf_model,
            output=response.json(),
        )

    def _analyze_vertex(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        if (
            not settings.medgemma_vertex_project
            or not settings.medgemma_vertex_endpoint
        ):
            raise MedGemmaClientError(
                "Missing MEDGEMMA_VERTEX_PROJECT or MEDGEMMA_VERTEX_ENDPOINT for Vertex AI."
            )

        try:
            from google.cloud import aiplatform
        except Exception as exc:
            raise MedGemmaClientError(
                "Vertex AI client not installed. Install google-cloud-aiplatform."
            ) from exc

        aiplatform.init(
            project=settings.medgemma_vertex_project,
            location=settings.medgemma_vertex_location,
        )

        endpoint = aiplatform.Endpoint(settings.medgemma_vertex_endpoint)
        instance = {"image": image_bytes}
        if prompt:
            instance["prompt"] = prompt

        try:
            prediction = endpoint.predict(instances=[instance])
        except Exception as exc:
            raise MedGemmaClientError(f"Vertex AI request failed: {exc}") from exc

        return MedGemmaResult(
            provider="vertex",
            model=settings.medgemma_vertex_endpoint,
            output=prediction.predictions,
        )
