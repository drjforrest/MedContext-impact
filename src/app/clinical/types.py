from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


class MedGemmaClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class MedGemmaResult:
    provider: str
    model: str
    output: Any
    raw_text: Optional[str] = None


class BaseMedGemmaClient(ABC):
    """Abstract base for all MedGemma provider clients."""

    provider_name: str

    @abstractmethod
    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult: ...

    @abstractmethod
    async def check_health(self) -> bool: ...

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]: ...
