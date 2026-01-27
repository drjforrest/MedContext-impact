from __future__ import annotations

from uuid import uuid4


def run_forensics(image_bytes: bytes, layers: list[str] | None = None) -> dict:
    response = {
        "job_id": uuid4(),
        "status": "skipped",
        "detail": "legacy deepfake layers removed",
    }
    if layers:
        response["layers"] = list(layers)
    return response
