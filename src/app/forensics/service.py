from __future__ import annotations

from uuid import uuid4

from app.forensics.deepfake import run_deepfake_layers


def run_forensics(image_bytes: bytes, layers: list[str] | None = None) -> dict:
    response = {
        "job_id": uuid4(),
        "status": "queued",
        "detail": "forensics analysis queued",
    }
    if layers:
        response["layers"] = list(layers)
        response["results"] = {
            layer: result.__dict__
            for layer, result in run_deepfake_layers(image_bytes, layers).items()
        }
    return response
