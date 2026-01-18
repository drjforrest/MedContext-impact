from __future__ import annotations

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
        max_tokens: int = 900,
    ) -> LlmResult:
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
        raise LlmClientError(f"Unsupported provider: {self.provider}")

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

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmClientError("Unexpected OpenAI-compatible response format.") from exc

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

        data = response.json()
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
        import json
        import re

        def _try_load(raw: str) -> Any:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None

        direct = _try_load(content)
        if direct is not None:
            return direct

        fenced = re.search(r"```json(.*?)```", content, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            candidate = fenced.group(1).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded

        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if match:
            candidate = match.group(0).strip()
            loaded = _try_load(candidate)
            if loaded is not None:
                return loaded
            # Attempt to unescape if the JSON blob was double-escaped in text.
            unescaped = (
                candidate.replace("\\n", "\n")
                .replace('\\"', '"')
                .replace("\\\\", "\\")
            )
            loaded = _try_load(unescaped)
            if loaded is not None:
                return loaded

        return {"text": content}
