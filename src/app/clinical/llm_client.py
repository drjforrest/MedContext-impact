from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.core.config import settings


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

        # Use OPENROUTER_API_KEY if available, otherwise fall back to LLM_API_KEY
        api_key = settings.llm_api_key
        if not api_key:
            raise LlmClientError(
                "Missing OPENROUTER_API_KEY or LLM_API_KEY for OpenRouter."
            )

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

        cleaned = self._clean_text(content)
        return LlmResult(
            provider="openrouter",
            model=model or settings.llm_orchestrator,
            output=self._parse_json(cleaned),
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

        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LlmClientError(f"OpenAI-compatible request failed: {exc}") from exc

        try:
            data = response.json()
        except (json.JSONDecodeError, TypeError) as exc:
            raise LlmClientError(
                "Invalid JSON in OpenAI-compatible response: "
                f"{exc}. Raw response: {response.text}"
            ) from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmClientError(
                "Unexpected OpenAI-compatible response format."
            ) from exc

        cleaned = self._clean_text(content)
        return LlmResult(
            provider="openai_compatible",
            model=model or settings.llm_orchestrator,
            output=self._parse_json(cleaned),
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

        cleaned = self._clean_text(content)
        return LlmResult(
            provider="ollama",
            model=model or settings.llm_orchestrator,
            output=self._parse_json(cleaned),
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

        cleaned = self._clean_text(content)
        return LlmResult(
            provider="gemini",
            model=model_name,
            output=self._parse_json(cleaned),
            raw_text=cleaned,
        )

    def _clean_text(self, content: str) -> str:
        import re

        cleaned = content.strip()
        cleaned = cleaned.lstrip("|").strip()

        # Remove leading "JSON" markers
        cleaned = re.sub(r"^JSON\s*\n+", "", cleaned, flags=re.IGNORECASE)

        # Remove common prefixes from model thinking/explanation
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

        # Try to extract JSON from markdown code fences first
        json_fence = re.search(
            r"```json\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        if json_fence:
            return json_fence.group(1).strip()

        # Try any code fence
        any_fence = re.search(r"```\s*(.*?)```", cleaned, flags=re.DOTALL)
        if any_fence:
            potential = any_fence.group(1).strip()
            if potential.startswith("{"):
                return potential

        # If content has reasoning before JSON, try to extract just the JSON part
        # by finding the first { and using bracket matching
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
        import json
        import re

        def _try_load(raw: str) -> Any:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None

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

        # Try to find outermost JSON object with simple regex as fallback
        for match in re.finditer(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, flags=re.DOTALL
        ):
            candidate = match.group(0).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded

        # Last resort: find any {...} pattern
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match:
            candidate = match.group(0).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded
            # Attempt to unescape if the JSON blob was double-escaped in text.
            unescaped = (
                candidate.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
            )
            loaded = _try_load(unescaped)
            if loaded is not None:
                return loaded

        return {"text": content}
