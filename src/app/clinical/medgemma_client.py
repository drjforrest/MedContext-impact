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
        self.provider = self._normalize_provider(settings.medgemma_provider)
        self._local_model = None
        self._local_processor = None
        self._local_device = None

    def _normalize_provider(self, value: str) -> str:
        provider = (value or "").strip().lower()
        if provider in {"vertexai", "vertex_ai"}:
            return "vertex"
        if provider in {"lmstudio", "lm_studio"}:
            return "local"
        return provider

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
            fallback = self._normalize_provider(
                settings.medgemma_fallback_provider or ""
            )
            if fallback and fallback != self.provider:
                if fallback == "local":
                    return self._analyze_local(image_bytes=image_bytes, prompt=prompt)
                if fallback == "huggingface":
                    return self._analyze_huggingface(
                        image_bytes=image_bytes, prompt=prompt
                    )
                if fallback == "vllm":
                    return self._analyze_vllm(image_bytes=image_bytes, prompt=prompt)
                if fallback == "vertex":
                    return self._analyze_vertex(image_bytes=image_bytes, prompt=prompt)
            raise exc

    def _resize_image_for_api(self, image_bytes: bytes, max_size: int = 512) -> bytes:
        """Resize image to keep base64 token count under model context limits.

        A 512px max JPEG at quality 80 is typically 20-50KB, which base64-encodes
        to ~27-67K chars (~10-25K tokens) — well within the 131K context window.
        """
        # Safety check: if raw bytes are small enough, skip resize
        # ~100KB raw means ~133KB base64 which is ~50K tokens — safe
        if len(image_bytes) < 100_000:
            return image_bytes

        try:
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            if img.mode == "RGBA":
                img = img.convert("RGB")

            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            resized = buffer.getvalue()

            # Verify the resize actually reduced size
            if len(resized) < len(image_bytes):
                return resized
            return image_bytes
        except Exception as exc:
            # Log warning instead of silently swallowing
            import logging
            logging.getLogger(__name__).warning(
                "Image resize failed (%s), using original (%d bytes). "
                "Large images may cause OOM on GPU endpoints.",
                exc,
                len(image_bytes),
            )
            return image_bytes

    def _analyze_huggingface(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        if not settings.medgemma_hf_token:
            raise MedGemmaClientError(
                "Missing MEDGEMMA_HF_TOKEN for HuggingFace inference."
            )

        # Use custom endpoint URL if available (for dedicated endpoints), otherwise use Inference API
        if settings.medgemma_url and not settings.medgemma_url.startswith(
            "http://localhost"
        ):
            url = settings.medgemma_url.rstrip("/")
        else:
            url = f"https://api-inference.huggingface.co/models/{settings.medgemma_hf_model}"
        headers = {"Authorization": f"Bearer {settings.medgemma_hf_token}"}

        # Resize image to reduce GPU memory usage for dedicated endpoints
        # Also applies to standard HF API when images are very large
        image_bytes = self._resize_image_for_api(image_bytes)

        payload: dict[str, Any] | bytes
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        inputs_text: Optional[str] = None

        # Use TGI (Text Generation Inference) format for dedicated endpoints
        if settings.medgemma_url and not settings.medgemma_url.startswith(
            "http://localhost"
        ):
            # Dedicated endpoints expect image embedded in inputs string with markdown syntax
            image_format = _detect_image_format(image_bytes)
            image_data_url = f"data:image/{image_format};base64,{encoded_image}"
            # Format: ![](image_url)prompt_text
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
            # Use standard HF Inference API format
            if prompt:
                payload = {"inputs": {"image": encoded_image, "text": prompt}}
            else:
                payload = image_bytes

        try:
            # CPU-based vision endpoints can take 90+ seconds per request
            timeout = httpx.Timeout(300.0, read=300.0, write=30.0, connect=10.0)
            with httpx.Client(timeout=timeout) as client:
                if isinstance(payload, bytes):
                    response = client.post(url, headers=headers, content=payload)
                else:
                    response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # Include response body in error message for debugging
            error_detail = exc.response.text if exc.response else "No response body"
            raise MedGemmaClientError(
                f"HuggingFace request failed: {exc}. Response: {error_detail[:500]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise MedGemmaClientError(f"HuggingFace request failed: {exc}") from exc

        # Clean and parse the response - TGI returns [{"generated_text": "..."}]
        raw_text = response.text
        try:
            response_data = response.json()
            if isinstance(response_data, list) and response_data:
                # TGI format: extract generated_text from first item
                generated = response_data[0].get("generated_text", "")
                # Remove the input from the generated text
                # First try stripping inputs_text (full input with image markdown), then prompt
                if inputs_text and generated.startswith(inputs_text):
                    generated = generated[len(inputs_text) :].strip()
                elif prompt and generated.startswith(prompt):
                    generated = generated[len(prompt) :].strip()
                raw_text = generated
        except Exception:
            pass  # Fall back to using raw response.text

        cleaned = self._clean_text(raw_text)
        parsed = self._parse_json(cleaned)

        return MedGemmaResult(
            provider="huggingface",
            model=settings.medgemma_hf_model,
            output=parsed,
            raw_text=raw_text,
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
        # Check if we should use the local API endpoint instead of loading the model locally
        if (
            settings.local_medgemma_url
            and settings.local_medgemma_url != "http://localhost:8001"
        ):
            return self._analyze_local_api(image_bytes=image_bytes, prompt=prompt)

        # Use the original local model loading approach
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
        try:
            inputs = self._local_processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            )
        except ValueError as e:
            # Handle image normalization issues by ensuring consistent format
            if "mean must have" in str(e) and "elements if it is an iterable" in str(e):
                # Re-process image to ensure consistent format
                import numpy as np

                # Convert to numpy array and back to PIL to ensure consistent format
                image_np = np.array(image)
                image = Image.fromarray(image_np.astype("uint8"), "RGB")

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
            else:
                raise
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

    def _analyze_local_api(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        """Analyze using a local API endpoint that serves the MedGemma model."""
        import base64

        # Prepare the image for API request
        image_format = _detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"

        # Prepare the payload for the API request
        # Check if we're using LM Studio API (has vision capabilities)
        lm_studio_url = settings.local_medgemma_url.rstrip("/")
        if (
            "127.0.0.1:1234" in lm_studio_url
            or "localhost:1234" in lm_studio_url
            or "192.168." in lm_studio_url
        ):
            # LM Studio API format - use OpenAI compatible endpoint which we confirmed works
            content = [
                {"type": "text", "text": prompt or "Describe the medical image."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]

            payload = {
                "model": settings.local_medgemma_model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": settings.medgemma_max_new_tokens,
                "temperature": 0.1,  # Lower temperature for more consistent medical responses
            }

            # Try LM Studio API endpoints in order of preference
            candidate_urls = [
                f"{lm_studio_url}/v1/chat/completions",  # OpenAI compatible - confirmed working
                f"{lm_studio_url}/api/v1/chat",  # Native LM Studio endpoint
            ]
        else:
            # Standard OpenAI compatible format
            content = [
                {"type": "text", "text": prompt or "Describe the medical image."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]

            payload = {
                "model": settings.local_medgemma_model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": settings.medgemma_max_new_tokens,
            }

            # Try standard OpenAI compatible endpoints
            candidate_urls = [
                f"{lm_studio_url}/v1/chat/completions",
                f"{lm_studio_url}/chat/completions",
                lm_studio_url,
            ]

        headers = {"Content-Type": "application/json"}
        if settings.medgemma_hf_token:
            headers["Authorization"] = f"Bearer {settings.medgemma_hf_token}"

        last_error = None
        for url in candidate_urls:
            try:
                timeout = httpx.Timeout(300.0, read=300.0, write=30.0, connect=10.0)
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()

                    data = response.json()

                    # Try different ways to extract content based on API response format
                    content = self._extract_vllm_content(data)  # Standard OpenAI format
                    if not content:
                        # Try LM Studio native format
                        choices = data.get("choices", [])
                        if choices and isinstance(choices, list):
                            first_choice = choices[0]
                            if isinstance(first_choice, dict):
                                # Check for LM Studio native format
                                if "message" in first_choice:
                                    msg = first_choice["message"]
                                    if isinstance(msg, dict) and "content" in msg:
                                        content = msg["content"]
                                elif "delta" in first_choice:
                                    delta = first_choice["delta"]
                                    if isinstance(delta, dict) and "content" in delta:
                                        content = delta["content"]

                    if not content:
                        # Fallback: try to get content from various possible fields
                        if "choices" in data and len(data["choices"]) > 0:
                            choice = data["choices"][0]
                            if "text" in choice:
                                content = choice["text"]
                            elif "message" in choice and "content" in choice["message"]:
                                content = choice["message"]["content"]
                            elif "content" in choice:
                                content = choice["content"]

                    cleaned = self._clean_text(content if content else str(data))
                    parsed = self._parse_json(cleaned)

                    return MedGemmaResult(
                        provider="local_api",
                        model=settings.local_medgemma_model,
                        output=parsed,
                        raw_text=cleaned,
                    )
            except httpx.HTTPError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                continue

        raise MedGemmaClientError(
            f"Local API request failed for all URLs: {last_error}"
        )

    def _analyze_vertex(
        self, image_bytes: bytes, prompt: Optional[str]
    ) -> MedGemmaResult:
        if not settings.medgemma_vertex_endpoint:
            raise MedGemmaClientError("Missing MEDGEMMA_VERTEX_ENDPOINT for Vertex AI.")
        if not settings.medgemma_vertex_project:
            raise MedGemmaClientError("Missing MEDGEMMA_VERTEX_PROJECT for Vertex AI.")

        # Build chat completions format
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/png;base64,{encoded_image}"

        user_content = [
            {"type": "text", "text": prompt or "Analyze this medical image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

        instance = {
            "@requestFormat": "chatCompletions",
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": 1024,
        }

        # Use Vertex AI SDK (handles dedicated endpoint routing without DNS dependency)
        try:
            from google.cloud import aiplatform
        except ImportError as exc:
            raise MedGemmaClientError(
                "Vertex AI requires google-cloud-aiplatform. Install with: pip install google-cloud-aiplatform"
            ) from exc

        endpoint_id = settings.medgemma_vertex_endpoint
        project = settings.medgemma_vertex_project or "medcontext"
        location = settings.medgemma_vertex_location or "us-central1"

        try:
            aiplatform.init(project=project, location=location)
            endpoint = aiplatform.Endpoint(endpoint_id)

            # Set dedicated endpoint DNS if configured
            if settings.medgemma_vertex_dedicated_domain:
                domain = settings.medgemma_vertex_dedicated_domain.strip()
                if domain.startswith("https://"):
                    domain = domain[len("https://") :]
                elif domain.startswith("http://"):
                    domain = domain[len("http://") :]
                domain = domain.rstrip("/")

                # Populate dedicated_endpoint_dns if empty
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

        # Extract text from chat completions response
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

        url = f"projects/{project}/locations/{location}/endpoints/{endpoint_id}"

        # Clean and parse the response
        cleaned = self._clean_text(raw_text)
        parsed = self._parse_json(cleaned)

        return MedGemmaResult(
            provider="vertex",
            model=url,
            output=parsed,
            raw_text=raw_text,
        )

    def _build_vertex_predict_url(self, endpoint: str) -> str:
        cleaned = (endpoint or "").strip()
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            url = cleaned.rstrip("/")
        else:
            if cleaned.startswith("projects/"):
                resource = cleaned
            else:
                if not settings.medgemma_vertex_project:
                    raise MedGemmaClientError(
                        "Missing MEDGEMMA_VERTEX_PROJECT for Vertex AI."
                    )
                resource = (
                    f"projects/{settings.medgemma_vertex_project}/locations/"
                    f"{settings.medgemma_vertex_location}/endpoints/{cleaned}"
                )

            # Use dedicated domain if set, otherwise shared domain
            if settings.medgemma_vertex_dedicated_domain:
                domain = settings.medgemma_vertex_dedicated_domain.rstrip("/")
                if domain.startswith("https://"):
                    domain = domain[len("https://") :]
                elif domain.startswith("http://"):
                    domain = domain[len("http://") :]
                url = f"https://{domain}/v1/{resource}"
            else:
                url = (
                    f"https://{settings.medgemma_vertex_location}-aiplatform.googleapis.com/v1/"
                    f"{resource}"
                )
        if not url.endswith(":predict"):
            url = f"{url}:predict"
        return url

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
        headers = {}
        if settings.medgemma_hf_token:
            headers["Authorization"] = f"Bearer {settings.medgemma_hf_token}"
        with httpx.Client(timeout=90.0) as client:
            for url in candidate_urls:
                try:
                    response = client.post(url, json=payload, headers=headers)
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

        # Remove leading "JSON" markers that models sometimes add
        cleaned = re.sub(r"^JSON\s*\n+", "", cleaned, flags=re.IGNORECASE)

        # Remove <unused*> tags and thought markers
        cleaned = re.sub(r"<unused\d+>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(
            r"^thought\s*:?\s*", "", cleaned, flags=re.IGNORECASE | re.MULTILINE
        )
        cleaned = re.sub(
            r"^tool_name\s*:.*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE
        )
        cleaned = re.sub(
            r"^tool_code\s*:.*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE
        )

        # Try to extract JSON from markdown code fences - this is critical
        json_fence = re.search(
            r"```json\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        if json_fence:
            return json_fence.group(1).strip()

        # Try any code fence
        any_fence = re.search(r"```\s*(.*?)```", cleaned, flags=re.DOTALL)
        if any_fence:
            potential = any_fence.group(1).strip()
            # If it looks like JSON, use it
            if potential.startswith("{"):
                return potential

        # If content has reasoning before JSON, extract just the JSON part
        json_obj = self._extract_json_by_brackets(cleaned)
        if json_obj:
            return json_obj

        cleaned = re.sub(r"\s{3,}", "  ", cleaned)
        return cleaned.strip()

    def _extract_json_by_brackets(self, content: str) -> Optional[str]:
        """Extract JSON object using bracket counting for deeply nested structures."""
        start_idx = content.find("{")
        if start_idx == -1:
            return None

        depth = 0
        in_string = False
        escape_next = False
        end_idx = start_idx

        for i, char in enumerate(content[start_idx:], start=start_idx):
            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break

        if depth == 0 and end_idx > start_idx:
            return content[start_idx : end_idx + 1]

        return None

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

        # Try direct parsing first
        direct = _try_load(content)
        if direct is not None:
            return direct

        # Try to extract from markdown code fences (```json...```)
        fenced = re.search(
            r"```json\s*(.*?)```", content, flags=re.DOTALL | re.IGNORECASE
        )
        if fenced:
            candidate = fenced.group(1).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded
            unescaped = _unescape_candidate(candidate)
            loaded = _try_load(unescaped)
            if loaded is not None:
                return loaded

        # Try to extract from any code fence (```...```)
        fenced_any = re.search(r"```\s*(.*?)```", content, flags=re.DOTALL)
        if fenced_any:
            candidate = fenced_any.group(1).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded

        # Use bracket matching to extract JSON from reasoning-heavy responses
        bracket_extracted = self._extract_json_by_brackets(content)
        if bracket_extracted:
            loaded = _try_load(bracket_extracted)
            if loaded is not None:
                return loaded
            unescaped = _unescape_candidate(bracket_extracted)
            loaded = _try_load(unescaped)
            if loaded is not None:
                return loaded

        # Fallback: try greedy regex
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
