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


class VertexMedGemmaClient(BaseMedGemmaClient):
    """Client for Google Vertex AI-hosted MedGemma endpoints."""

    provider_name = "vertex"

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        if not settings.medgemma_vertex_endpoint:
            raise MedGemmaClientError("Missing MEDGEMMA_VERTEX_ENDPOINT for Vertex AI.")
        if not settings.medgemma_vertex_project:
            raise MedGemmaClientError("Missing MEDGEMMA_VERTEX_PROJECT for Vertex AI.")

        image_bytes = resize_image(image_bytes, max_size=512)

        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"

        user_content = [
            {"type": "text", "text": prompt or "Analyze this medical image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

        instance = {
            "@requestFormat": "chatCompletions",
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": settings.medgemma_max_new_tokens,
        }

        try:
            from google.cloud import aiplatform
        except ImportError as exc:
            raise MedGemmaClientError(
                "Vertex AI requires google-cloud-aiplatform. "
                "Install with: pip install google-cloud-aiplatform"
            ) from exc

        endpoint_id = settings.medgemma_vertex_endpoint
        project = settings.medgemma_vertex_project or "medcontext"
        location = settings.medgemma_vertex_location or "us-central1"

        try:
            aiplatform.init(project=project, location=location)
            endpoint = aiplatform.Endpoint(endpoint_id)

            if settings.medgemma_vertex_dedicated_domain:
                domain = settings.medgemma_vertex_dedicated_domain.strip()
                if domain.startswith("https://"):
                    domain = domain[len("https://") :]
                elif domain.startswith("http://"):
                    domain = domain[len("http://") :]
                domain = domain.rstrip("/")

                if not (
                    getattr(endpoint, "dedicated_endpoint_dns", None) or ""
                ).strip():
                    endpoint.gca_resource.dedicated_endpoint_dns = domain

            response_obj = endpoint.predict(
                instances=[instance],
                use_dedicated_endpoint=(
                    True if settings.medgemma_vertex_dedicated_domain else False
                ),
            )
        except Exception as exc:
            raise MedGemmaClientError(f"Vertex AI SDK predict failed: {exc}") from exc

        predictions = response_obj.predictions
        if isinstance(predictions, dict):
            choices = predictions.get("choices", [])
        elif isinstance(predictions, list) and predictions:
            first = predictions[0]
            choices = first.get("choices", []) if isinstance(first, dict) else []
        else:
            choices = []

        if choices and isinstance(choices, list):
            if isinstance(choices[0], dict):
                raw_text = choices[0].get("message", {}).get("content", "")
            else:
                raw_text = str(choices[0])
        else:
            raw_text = str(predictions)

        model_url = f"projects/{project}/locations/{location}/endpoints/{endpoint_id}"

        cleaned = clean_llm_text(raw_text)
        parsed = parse_llm_json(cleaned)

        return MedGemmaResult(
            provider="vertex",
            model=model_url,
            output=parsed,
            raw_text=raw_text,
        )

    async def check_health(self) -> bool:
        if not (settings.medgemma_vertex_project and settings.medgemma_vertex_endpoint):
            return False

        if settings.medgemma_vertex_dedicated_domain:
            try:
                domain = settings.medgemma_vertex_dedicated_domain.rstrip("/")
                if not domain.startswith("http"):
                    domain = f"https://{domain}"
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(domain)
                    return resp.status_code in (200, 401, 403, 404)
            except Exception:
                return False

        return True

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "project": settings.medgemma_vertex_project,
            "location": settings.medgemma_vertex_location,
            "endpoint": settings.medgemma_vertex_endpoint,
        }
