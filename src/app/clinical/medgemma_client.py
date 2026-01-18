from __future__ import annotations

from dataclasses import dataclass
import base64
import io
import imghdr
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
        self._local_model = None
        self._local_processor = None
        self._local_device = None

    def analyze_image(
        self, image_bytes: bytes, prompt: Optional[str] = None
    ) -> MedGemmaResult:
        if self.provider == "huggingface":
            return self._analyze_huggingface(image_bytes=image_bytes, prompt=prompt)
        if self.provider == "local":
            return self._analyze_local(image_bytes=image_bytes, prompt=prompt)
        if self.provider == "vllm":
            return self._analyze_vllm(image_bytes=image_bytes, prompt=prompt)
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
            encoded_image = base64.b64encode(image_bytes).decode("ascii")
            payload = {"inputs": {"image": encoded_image, "text": prompt}}
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

    def _load_local_model(self) -> None:
        if self._local_model is not None and self._local_processor is not None:
            return
        try:
            import torch
            from transformers import AutoModelForImageTextToText, AutoProcessor
        except Exception as exc:
            raise MedGemmaClientError(
                "Local MedGemma requires torch, transformers, pillow, and accelerate."
            ) from exc

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        processor = AutoProcessor.from_pretrained(
            settings.medgemma_hf_model, use_fast=True
        )
        model = AutoModelForImageTextToText.from_pretrained(
            settings.medgemma_hf_model,
            dtype=dtype,
            device_map="auto",
        )
        self._local_model = model
        self._local_processor = processor
        self._local_device = model.device

    def _analyze_local(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        self._load_local_model()
        if self._local_model is None or self._local_processor is None:
            raise MedGemmaClientError("Local MedGemma model failed to load.")

        try:
            import torch
            from PIL import Image
        except Exception as exc:
            raise MedGemmaClientError(
                "Pillow is required for local inference."
            ) from exc

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text_prompt = prompt or "Describe the medical image."

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": text_prompt},
                ],
            }
        ]
        inputs = self._local_processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        inputs = inputs.to(self._local_device, dtype=dtype)
        input_len = inputs["input_ids"].shape[-1]
        do_sample = False
        generation_kwargs = {"max_new_tokens": 2000, "do_sample": do_sample}
        if do_sample:
            if self._local_model.generation_config.top_p is not None:
                generation_kwargs["top_p"] = self._local_model.generation_config.top_p
            if self._local_model.generation_config.top_k is not None:
                generation_kwargs["top_k"] = self._local_model.generation_config.top_k
        else:
            self._local_model.generation_config.top_p = None
            self._local_model.generation_config.top_k = None
        with torch.inference_mode():
            generation = self._local_model.generate(**inputs, **generation_kwargs)
            generation = generation[0][input_len:]
        decoded = self._local_processor.decode(generation, skip_special_tokens=True)

        return MedGemmaResult(
            provider="local",
            model=settings.medgemma_hf_model,
            output={"text": decoded},
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

    def _analyze_vllm(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        if not settings.medgemma_vllm_url:
            raise MedGemmaClientError("Missing MEDGEMMA_VLLM_URL for vLLM.")

        image_format = imghdr.what(None, h=image_bytes) or "jpeg"
        if image_format == "jpg":
            image_format = "jpeg"
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"
        content = [
            {"type": "text", "text": prompt or "Describe the medical image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
        payload = {
            "model": settings.medgemma_hf_model,
            "messages": [{"role": "user", "content": content}],
        }

        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(settings.medgemma_vllm_url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MedGemmaClientError(f"vLLM request failed: {exc}") from exc

        return MedGemmaResult(
            provider="vllm",
            model=settings.medgemma_hf_model,
            output=response.json(),
        )
