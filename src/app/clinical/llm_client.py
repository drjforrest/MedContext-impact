from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.utils import clean_llm_text, parse_llm_json


class LlmClientError(RuntimeError):
    pass


@dataclass
class LlmResult:
    provider: str
    model: str
    output: Any
    raw_text: str


class LlmClient:
    def __init__(self) -> None:
        self.provider = settings.llm_provider.lower()

    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> LlmResult:
        if self.provider == "openrouter":
            return self._generate_openrouter(
                prompt,
                system=system,
                model=model or settings.llm_orchestrator,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        if self.provider == "openai_compatible":
            return self._generate_openai_compatible(
                prompt,
                system=system,
                model=model or settings.llm_orchestrator,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        if self.provider == "ollama":
            return self._generate_ollama(
                prompt,
                system=system,
                model=model or settings.llm_orchestrator,
                temperature=temperature,
            )
        if self.provider == "gemini":
            return self._generate_gemini(
                prompt,
                system=system,
                model=model or settings.llm_orchestrator,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        raise LlmClientError(f"Unsupported provider: {self.provider}")

    def _generate_openrouter(
        self,
        prompt: str,
        *,
        system: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> LlmResult:
        """Generate using OpenRouter API (OpenAI-compatible format)."""
        base_url = "https://openrouter.ai/api/v1"

        api_key = settings.llm_api_key
        if not api_key:
            raise LlmClientError("Missing LLM_API_KEY for OpenRouter.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LlmClientError(f"OpenRouter request failed: {exc}") from exc

        try:
            data = response.json()
        except (json.JSONDecodeError, TypeError) as exc:
            raise LlmClientError(
                f"Invalid JSON in OpenRouter response: {exc}. Raw: {response.text[:500]}"
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmClientError(
                f"Unexpected OpenRouter response format: {str(data)[:500]}"
            ) from exc

        cleaned = clean_llm_text(content)
        return LlmResult(
            provider="openrouter",
            model=model or settings.llm_orchestrator,
            output=parse_llm_json(cleaned),
            raw_text=cleaned,
        )

    def _generate_openai_compatible(
        self,
        prompt: str,
        *,
        system: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> LlmResult:
        if not settings.llm_base_url:
            raise LlmClientError("Missing LLM_BASE_URL for OpenAI-compatible API.")
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Candidate endpoints for OpenAI-compatible APIs (like LM Studio or vLLM)
        base_url = settings.llm_base_url.rstrip("/")
        candidate_urls = []
        
        if base_url.endswith("/chat/completions") or base_url.endswith("/api/v1/chat"):
            candidate_urls.append(base_url)
        else:
            # Standard order for LM Studio/vLLM/Local APIs
            candidate_urls.extend([
                f"{base_url}/v1/chat/completions",
                f"{base_url}/api/v1/chat",  # LM Studio native v1
                f"{base_url}/chat/completions",
            ])
        
        candidate_urls = list(dict.fromkeys(candidate_urls))

        response_data = None
        last_error = None
        
        for url in candidate_urls:
            try:
                with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                    response = client.post(
                        url,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    
                    # Even if 200 OK, check for error in body
                    try:
                        data = response.json()
                    except (json.JSONDecodeError, TypeError):
                        last_error = f"URL {url} returned non-JSON response"
                        continue

                    if "choices" not in data and "error" in data:
                        last_error = f"URL {url} returned an error in body: {data['error']}"
                        continue
                        
                    # Successfully got content
                    response_data = data
                    break
            except httpx.HTTPStatusError as exc:
                error_detail = exc.response.text if exc.response else "No response body"
                last_error = f"URL {url} failed with {exc.response.status_code}: {error_detail[:500]}"
                if exc.response is not None and exc.response.status_code in (404, 405):
                    continue
                continue
            except httpx.HTTPError as exc:
                last_error = f"URL {url} failed with HTTP error: {exc}"
                continue
            except Exception as exc:
                last_error = f"URL {url} failed with error: {exc}"
                continue

        if response_data is None:
            raise LlmClientError(
                f"OpenAI-compatible request failed for all URLs: {', '.join(candidate_urls)}. Last error: {last_error}"
            )

        data = response_data
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmClientError(
                "Unexpected OpenAI-compatible response format."
            ) from exc

        cleaned = clean_llm_text(content)
        return LlmResult(
            provider="openai_compatible",
            model=model or settings.llm_orchestrator,
            output=parse_llm_json(cleaned),
            raw_text=cleaned,
        )

    def _generate_ollama(
        self,
        prompt: str,
        *,
        system: Optional[str],
        model: Optional[str],
        temperature: float,
    ) -> LlmResult:
        if not settings.llm_base_url:
            raise LlmClientError("Missing LLM_BASE_URL for Ollama.")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    f"{settings.llm_base_url.rstrip('/')}/api/chat", json=payload
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LlmClientError(f"Ollama request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LlmClientError("Invalid JSON in Ollama response.") from exc
        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LlmClientError("Unexpected Ollama response format.") from exc

        cleaned = clean_llm_text(content)
        return LlmResult(
            provider="ollama",
            model=model or settings.llm_orchestrator,
            output=parse_llm_json(cleaned),
            raw_text=cleaned,
        )

    def _generate_gemini(
        self,
        prompt: str,
        *,
        system: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> LlmResult:
        if not settings.llm_api_key:
            raise LlmClientError("Missing LLM_API_KEY for Gemini API.")

        model_name = model or "gemini-2.0-flash-exp"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    url,
                    params={"key": settings.llm_api_key},
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LlmClientError(f"Gemini API request failed: {exc}") from exc

        try:
            data = response.json()
        except (json.JSONDecodeError, TypeError) as exc:
            raise LlmClientError(
                f"Invalid JSON in Gemini response: {exc}. Raw: {response.text[:500]}"
            ) from exc

        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmClientError(
                f"Unexpected Gemini response format: {str(data)[:500]}"
            ) from exc

        cleaned = clean_llm_text(content)
        return LlmResult(
            provider="gemini",
            model=model_name,
            output=parse_llm_json(cleaned),
            raw_text=cleaned,
        )



