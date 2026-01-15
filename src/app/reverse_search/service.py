from __future__ import annotations

from uuid import UUID, uuid4


def run_reverse_search(image_id: UUID | str, image_bytes: bytes) -> dict:
    return {
        "job_id": uuid4(),
        "status": "queued",
        "detail": f"reverse search queued for {image_id}",
    }


def get_reverse_search_results(image_id: UUID | str) -> dict:
    return {
        "job_id": uuid4(),
        "status": "completed",
        "detail": f"results ready for {image_id}",
    }
