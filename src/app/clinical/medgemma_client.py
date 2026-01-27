from __future__ import annotations

import base64
import io
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
    raw_text: Optional[str] = None


def _detect_image_format(image_bytes: bytes) -> str:
    try:
        from PIL import Image
    except Exception:
        return "jpeg"
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image_format = (image.format or "JPEG").lower()
    except Exception:
        image_format = "jpeg"
    if image_format == "jpg":
        image_format = "jpeg"
    return image_format


class MedGemmaClient:
    def __init__(self) -> None:
        self.provider = settings.medgemma_provider.lower()
        self._local_model = None
        self._local_processor = None
        self._local_device = None

    def analyze_image(
        self, image_bytes: bytes, prompt: Optional[str] = None
    ) -> MedGemmaResult:
        try:
            if self.provider == "huggingface":
                return self._analyze_huggingface(image_bytes=image_bytes, prompt=prompt)
            if self.provider == "local":
                return self._analyze_local(image_bytes=image_bytes, prompt=prompt)
            if self.provider == "vllm":
                return self._analyze_vllm(image_bytes=image_bytes, prompt=prompt)
            if self.provider == "vertex":
                return self._analyze_vertex(image_bytes=image_bytes, prompt=prompt)
            raise MedGemmaClientError(f"Unsupported provider: {self.provider}")
        except MedGemmaClientError as exc:
            fallback = settings.medgemma_fallback_provider.strip().lower()
            if fallback and fallback != self.provider:
                if fallback == "local":
                    return self._analyze_local(image_bytes=image_bytes, prompt=prompt)
                if fallback == "huggingface":
                    return self._analyze_huggingface(image_bytes=image_bytes, prompt=prompt)
                if fallback == "vertex":
                    return self._analyze_vertex(image_bytes=image_bytes, prompt=prompt)
            raise

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
            raw_text=response.text,
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
        generation_kwargs = {
            "max_new_tokens": settings.medgemma_max_new_tokens,
            "do_sample": do_sample,
        }
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
        cleaned = self._clean_text(decoded)
        parsed = self._parse_json(cleaned)

        return MedGemmaResult(
            provider="local",
            model=settings.medgemma_hf_model,
            output=parsed if parsed is not None else {"text": cleaned},
            raw_text=cleaned,
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
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        instance = {"image": encoded_image}
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
            raw_text=None,
        )

    def _analyze_vllm(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        if not settings.medgemma_vllm_url:
            raise MedGemmaClientError("Missing MEDGEMMA_VLLM_URL for vLLM.")

        image_format = _detect_image_format(image_bytes)
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
        with httpx.Client(timeout=90.0) as client:
            for url in candidate_urls:
                try:
                    response = client.post(url, json=payload)
                    response.raise_for_status()
                    break
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    last_status = exc.response.status_code if exc.response else None
                    last_url = url
                    if exc.response is not None and exc.response.status_code == 404:
                        continue
                    raise MedGemmaClientError(f"vLLM request failed: {exc}") from exc
                except httpx.HTTPError as exc:
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
        content = self._extract_vllm_content(data)
        cleaned = self._clean_text(content)
        parsed = self._parse_json(cleaned)

        return MedGemmaResult(
            provider="vllm",
            model=settings.medgemma_hf_model,
            output=parsed,
            raw_text=cleaned,
        )

    def _extract_vllm_content(self, data: Any) -> str:
        if not isinstance(data, dict):
            return ""
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0] if isinstance(choices[0], dict) else None
            if first:
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                content = first.get("text")
                if isinstance(content, str):
                    return content
        return ""

    def _clean_text(self, content: str) -> str:
        import re

        cleaned = content.strip()
        cleaned = cleaned.lstrip("|").strip()
        cleaned = re.sub(r"<unused\d+>\s*thought", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<unused\d+>", "", cleaned)
        cleaned = re.sub(r"^thought\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s{3,}", "  ", cleaned)
        return cleaned.strip()

    def _parse_json(self, content: str) -> Any:
        import codecs
        import json
        import re

        def _try_load(raw: str) -> Any:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None

        def _unescape_candidate(raw: str) -> str:
            try:
                return codecs.decode(raw, "unicode_escape")
            except (UnicodeDecodeError, ValueError):
                return raw

        direct = _try_load(content)
        if direct is not None:
            return direct

        fenced = re.search(r"```json(.*?)```", content, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded
            unescaped = _unescape_candidate(candidate)
            loaded = _try_load(unescaped)
            if loaded is not None:
                return loaded

        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match:
            candidate = match.group(0).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded
            unescaped = _unescape_candidate(candidate)
            loaded = _try_load(unescaped)
            if loaded is not None:
                return loaded

        return {"text": content}
