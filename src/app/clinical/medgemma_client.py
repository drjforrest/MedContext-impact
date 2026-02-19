from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.utils import (
    clean_llm_text,
    detect_image_format,
    parse_llm_json,
    resize_image,
)


class MedGemmaClientError(RuntimeError):
    pass


@dataclass
class MedGemmaResult:
    provider: str
    model: str
    output: Any
    raw_text: Optional[str] = None


class MedGemmaClient:
    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or settings.medgemma_model
        self.provider = self._determine_provider(self.model)
        self._local_model = None
        self._local_processor = None
        self._local_device = None
        self._llm_instance = None

    def _determine_provider(self, model: str) -> str:
        model_lower = model.lower()

        # Explicit provider in model name (e.g. "vertex/my-model")
        if "/" in model_lower:
            prefix = model_lower.split("/")[0]
            if prefix in {"vertex", "huggingface", "vllm", "local", "lmstudio"}:
                if prefix == "lmstudio":
                    return "local"
                return prefix

        # If model name contains vertex, use vertex
        if "vertex" in model_lower:
            return "vertex"

        # Link LM Studio for Quantized models
        if (
            model_lower.endswith(".gguf")
            or "quantized" in model_lower
            or "gguf" in model_lower
        ):
            return "local"

        # Link Hugging Face for PT and IT models
        if model_lower.endswith("-it") or model_lower.endswith("-pt"):
            return "huggingface"

        # Default to huggingface
        return "huggingface"

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        current_model = model or self.model
        current_provider = (
            self._determine_provider(current_model) if model else self.provider
        )
        try:
            if current_provider == "huggingface":
                return self._analyze_huggingface(
                    image_bytes=image_bytes, prompt=prompt, model=current_model
                )
            if current_provider == "local":
                return self._analyze_local(
                    image_bytes=image_bytes, prompt=prompt, model=current_model
                )
            if current_provider == "vllm":
                return self._analyze_vllm(
                    image_bytes=image_bytes, prompt=prompt, model=current_model
                )
            if current_provider == "vertex":
                return self._analyze_vertex(
                    image_bytes=image_bytes, prompt=prompt, model=current_model
                )
            raise MedGemmaClientError(f"Unsupported provider: {current_provider}")
        except MedGemmaClientError as exc:
            if not settings.medgemma_fallback_provider:
                raise exc
            fallback = self._determine_provider(settings.medgemma_fallback_provider)
            if fallback and fallback != current_provider:
                if fallback == "local":
                    return self._analyze_local(
                        image_bytes=image_bytes, prompt=prompt, model=current_model
                    )
                if fallback == "huggingface":
                    return self._analyze_huggingface(
                        image_bytes=image_bytes, prompt=prompt, model=current_model
                    )
                if fallback == "vllm":
                    return self._analyze_vllm(
                        image_bytes=image_bytes, prompt=prompt, model=current_model
                    )
                if fallback == "vertex":
                    return self._analyze_vertex(
                        image_bytes=image_bytes, prompt=prompt, model=current_model
                    )
            raise exc

    def _analyze_huggingface(
        self, image_bytes: bytes, prompt: Optional[str], model: str
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
            url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {settings.medgemma_hf_token}"}

        # Resize image to reduce GPU memory usage for dedicated endpoints
        # Also applies to standard HF API when images are very large
        image_bytes = resize_image(image_bytes, max_size=512)

        payload: dict[str, Any] | bytes
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        inputs_text: Optional[str] = None

        # Use TGI (Text Generation Inference) format for dedicated endpoints
        if settings.medgemma_url and not settings.medgemma_url.startswith(
            "http://localhost"
        ):
            image_format = detect_image_format(image_bytes)
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
            elif isinstance(response_data, dict):
                # Standard HF or other API format
                generated = response_data.get("generated_text", "")
            else:
                generated = str(response_data)

            # Remove the input from the generated text
            if generated:
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
            model=model,
            output=parsed,
            raw_text=raw_text,
        )

    def _load_local_model(self, model: str) -> None:
        if self._local_model is not None and self._local_processor is not None:
            return
        try:
            import torch
            import transformers

            AutoModelForImageTextToText = transformers.AutoModelForImageTextToText
            AutoProcessor = transformers.AutoProcessor
        except Exception as exc:
            raise MedGemmaClientError(
                "Local MedGemma requires torch, transformers, pillow, and accelerate."
            ) from exc

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        processor = AutoProcessor.from_pretrained(model, use_fast=True)
        model_obj = AutoModelForImageTextToText.from_pretrained(
            model,
            dtype=dtype,
            device_map="auto",
        )
        self._local_model = model_obj
        self._local_processor = processor
        self._local_device = model_obj.device

    def _analyze_local(
        self, image_bytes: bytes, prompt: Optional[str], model: str
    ) -> MedGemmaResult:
        # Check for GGUF model being run via llama-cpp-python (Local file mode)
        is_gguf = model.lower().endswith(".gguf") or "gguf" in model.lower()
        if is_gguf and settings.medgemma_local_path:
            import os

            if os.path.exists(settings.medgemma_local_path):
                return self._analyze_llama_cpp(
                    image_bytes=image_bytes, prompt=prompt, model=model
                )

        # Check if we should use the local API endpoint instead of loading the model locally (API mode)
        if (
            settings.local_medgemma_url
            and settings.local_medgemma_url != "http://localhost:8001"
        ):
            return self._analyze_local_api(
                image_bytes=image_bytes, prompt=prompt, model=model
            )

        # Use the original local model loading approach
        self._load_local_model(model)
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
        cleaned = clean_llm_text(decoded)
        parsed = parse_llm_json(cleaned)

        return MedGemmaResult(
            provider="local",
            model=model,
            output=parsed if parsed is not None else {"text": cleaned},
            raw_text=cleaned,
        )

    def _analyze_local_api(
        self, image_bytes: bytes, prompt: Optional[str], model: str
    ) -> MedGemmaResult:
        """Analyze using a local API endpoint that serves the MedGemma model."""
        import base64

        # Resize image to reduce payload size and memory usage for local APIs
        image_bytes = resize_image(image_bytes, max_size=512)

        # Prepare the image for API request
        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"

        # Prepare the payload for the API request
        content = [
            {"type": "text", "text": prompt or "Describe the medical image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": settings.medgemma_max_new_tokens,
            "temperature": 0.1,
        }

        # Candidate endpoints for local inference (LM Studio, vLLM, etc.)
        local_url = settings.local_medgemma_url.rstrip("/")
        candidate_urls = [
            f"{local_url}/v1/chat/completions",
            f"{local_url}/api/v1/chat",  # LM Studio native v1
            f"{local_url}/chat/completions",
        ]
        # Ensure URLs are unique
        candidate_urls = list(dict.fromkeys(candidate_urls))

        headers = {"Content-Type": "application/json"}
        if settings.medgemma_hf_token:
            headers["Authorization"] = f"Bearer {settings.medgemma_hf_token}"

        all_errors = []
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
                            elif "delta" in choice:
                                delta = choice["delta"]
                                if isinstance(delta, dict) and "content" in delta:
                                    content = delta["content"]

                    # If we STILL don't have content, check if it's an error response
                    if not content:
                        if isinstance(data, dict) and "error" in data:
                            err_msg = (
                                f"URL {url} returned an error in body: {data['error']}"
                            )
                            all_errors.append(err_msg)
                            continue

                        # Only use raw data if it doesn't look like an error and we really want it
                        # but for MedGemma analysis, it's better to fail if no content is found
                        err_msg = f"URL {url} returned successful status but no content was found in JSON."
                        all_errors.append(err_msg)
                        continue

                    cleaned = clean_llm_text(content)
                    parsed = parse_llm_json(cleaned)

                    return MedGemmaResult(
                        provider="local_api",
                        model=model,
                        output=parsed,
                        raw_text=cleaned,
                    )
            except httpx.HTTPStatusError as exc:
                error_detail = exc.response.text if exc.response else "No response body"
                err_msg = f"URL {url} failed with {exc.response.status_code}. Response: {error_detail[:500]}"
                all_errors.append(err_msg)
                continue
            except httpx.HTTPError as exc:
                err_msg = f"URL {url} failed with HTTP error: {exc}"
                all_errors.append(err_msg)
                continue
            except Exception as exc:
                err_msg = f"URL {url} failed with error: {exc}"
                all_errors.append(err_msg)
                continue

        error_summary = "\n".join(all_errors)
        raise MedGemmaClientError(
            f"Local API request failed for all URLs. Errors:\n{error_summary}"
        )

    def _analyze_llama_cpp(
        self, image_bytes: bytes, prompt: Optional[str], model: str
    ) -> MedGemmaResult:
        """Analyze using llama-cpp-python for local GGUF models."""
        try:
            import base64

            from llama_cpp import Llama
        except ImportError:
            raise MedGemmaClientError(
                "llama-cpp-python is required for local GGUF inference. "
                "Install with: pip install llama-cpp-python"
            )

        # Resize image to reduce payload size and memory usage for local llama-cpp
        image_bytes = resize_image(image_bytes, max_size=512)

        # We should cache the LLM instance to avoid reloading
        if self._llm_instance is None:
            # clip_model_path is required for vision
            if settings.medgemma_mmproj_path:
                try:
                    from llama_cpp.llama_chat_format import Llava15ChatHandler

                    # Try to detect which handler to use, or default to Llava15
                    # In some versions of llama-cpp-python, there's a PaliGemmaChatHandler
                    try:
                        from llama_cpp.llama_chat_format import PaliGemmaChatHandler

                        chat_handler = PaliGemmaChatHandler(
                            clip_model_path=settings.medgemma_mmproj_path
                        )
                    except ImportError:
                        # Fallback to Llava15 which is a common base for vision models
                        chat_handler = Llava15ChatHandler(
                            clip_model_path=settings.medgemma_mmproj_path
                        )
                except ImportError:
                    raise MedGemmaClientError(
                        "Failed to import vision chat handlers from llama-cpp-python."
                    )
            else:
                # Without mmproj, vision won't work in llama-cpp-python for these models
                raise MedGemmaClientError(
                    "MEDGEMMA_MMPROJ_PATH is required for vision with local GGUF models in llama-cpp-python."
                )

            try:
                self._llm_instance = Llama(
                    model_path=settings.medgemma_local_path,
                    chat_handler=chat_handler,
                    n_ctx=4096,  # Increased context window for vision + longer prompts
                    n_gpu_layers=-1,  # Use all GPU layers if available
                    verbose=False,
                )
            except Exception as e:
                raise MedGemmaClientError(f"Failed to load GGUF model: {e}")

        # Prepare image
        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"

        # Create chat completion
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

        cleaned = clean_llm_text(content)
        parsed = parse_llm_json(cleaned)

        return MedGemmaResult(
            provider="llama-cpp",
            model=model,
            output=parsed,
            raw_text=cleaned,
        )

    def _analyze_vertex(
        self, image_bytes: bytes, prompt: Optional[str], model: str
    ) -> MedGemmaResult:
        if not settings.medgemma_vertex_endpoint:
            raise MedGemmaClientError("Missing MEDGEMMA_VERTEX_ENDPOINT for Vertex AI.")
        if not settings.medgemma_vertex_project:
            raise MedGemmaClientError("Missing MEDGEMMA_VERTEX_PROJECT for Vertex AI.")

        # Resize image to reduce payload size and memory usage for Vertex AI
        image_bytes = resize_image(image_bytes, max_size=512)

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
        self, image_bytes: bytes, prompt: Optional[str], model: str
    ) -> MedGemmaResult:
        if not settings.medgemma_vllm_url:
            raise MedGemmaClientError("Missing MEDGEMMA_VLLM_URL for vLLM.")

        # Resize image to reduce payload size and memory usage for vLLM
        image_bytes = resize_image(image_bytes, max_size=512)

        image_format = detect_image_format(image_bytes)
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:image/{image_format};base64,{encoded_image}"
        content = [
            {"type": "text", "text": prompt or "Describe the medical image."},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
        payload = {
            "model": model,
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

        content = self._extract_vllm_content(data)

        # Check for error in response body even if 200 OK
        if not content and isinstance(data, dict) and "error" in data:
            raise MedGemmaClientError(
                f"vLLM request returned an error: {data['error']}"
            )

        if not content:
            raise MedGemmaClientError(
                f"vLLM request succeeded but no content was found in response: {str(data)[:500]}"
            )

        cleaned = clean_llm_text(content)
        parsed = parse_llm_json(cleaned)

        return MedGemmaResult(
            provider="vllm",
            model=model,
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
