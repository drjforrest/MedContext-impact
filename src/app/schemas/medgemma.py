from typing import Any

from pydantic import BaseModel


class MedGemmaResponse(BaseModel):
    provider: str
    model: str
    output: Any
