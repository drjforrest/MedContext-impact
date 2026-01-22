from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelegramIngestResult:
    status: str
    detail: str
    metadata: dict[str, Any]


def process_update(payload: dict[str, Any]) -> TelegramIngestResult:
    """Parse a Telegram update payload into a lightweight summary."""
    message = payload.get("message") or payload.get("channel_post") or {}
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    photos = message.get("photo") or []

    photo_file_ids = [
        photo.get("file_id") for photo in photos if isinstance(photo, dict)
    ]

    metadata = {
        "update_id": payload.get("update_id"),
        "message_id": message.get("message_id"),
        "chat_id": chat.get("id"),
        "chat_title": chat.get("title") or chat.get("username"),
        "sender": sender.get("username") or sender.get("id"),
        "text": message.get("text"),
        "caption": message.get("caption"),
        "photo_file_ids": [file_id for file_id in photo_file_ids if file_id],
        "payload_keys": list(payload.keys()),
    }

    return TelegramIngestResult(
        status="accepted",
        detail="telegram update accepted (stub)",
        metadata=metadata,
    )
