from __future__ import annotations

from uuid import UUID, uuid4


def build_provenance(image_id: UUID | str, image_bytes: bytes) -> dict:
    return {
        "job_id": uuid4(),
        "status": "queued",
        "detail": f"provenance build queued for {image_id}",
    }
