from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DeepfakeLayerResponse(BaseModel):
    verdict: str
    confidence: float
    details: dict[str, Any]


class DeepfakeDetectionResponse(BaseModel):
    final_verdict: str
    confidence: float
    layer_1: DeepfakeLayerResponse
    layer_2: DeepfakeLayerResponse
    layer_3: DeepfakeLayerResponse
