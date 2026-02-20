"""Backward-compatible wrapper around provider-specific MedGemma clients.

All existing callers continue to import from this module unchanged:
    from app.clinical.medgemma_client import MedGemmaClient, MedGemmaResult, MedGemmaClientError
"""

from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings
from app.clinical.factory import create_client, determine_provider
from app.clinical.types import (
    BaseMedGemmaClient,
    MedGemmaClientError,
    MedGemmaResult,
)

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ["MedGemmaClient", "MedGemmaClientError", "MedGemmaResult"]


class MedGemmaClient:
    """Facade that delegates to the appropriate provider client.

    Preserves the original constructor signature so all callers work unchanged.
    """

    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model or settings.medgemma_model
        self.provider = determine_provider(self.model)
        self._client: BaseMedGemmaClient = create_client(self.provider)

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> MedGemmaResult:
        current_model = model or self.model
        current_provider = determine_provider(current_model) if model else self.provider

        # If the requested provider differs from our cached client, create a new one
        client = self._client
        if current_provider != self.provider:
            client = create_client(current_provider)

        try:
            return client.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                model=current_model,
            )
        except MedGemmaClientError:
            fallback_provider = settings.medgemma_fallback_provider or None
            if not fallback_provider or fallback_provider == current_provider:
                raise
            try:
                fallback_client = create_client(fallback_provider)
            except MedGemmaClientError:
                logger.warning(
                    "Invalid fallback provider %r, re-raising original error",
                    fallback_provider,
                )
                raise  # re-raises the ORIGINAL primary provider error
            return fallback_client.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                model=None,
            )
