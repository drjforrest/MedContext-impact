from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import praw

from app.core.config import settings


class RedditClientError(RuntimeError):
    pass


class RedditClient:
    def __init__(self) -> None:
        if (
            not settings.reddit_client_id
            or not settings.reddit_client_secret
            or not settings.reddit_user_agent
        ):
            raise RedditClientError(
                "Missing Reddit credentials. Set REDDIT_CLIENT_ID, "
                "REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT."
            )
        self._client = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )

    def fetch_subreddit_posts(
        self, subreddit: str, *, limit: int = 25
    ) -> list[dict[str, Any]]:
        subreddit_ref = self._client.subreddit(subreddit)
        return [
            self._normalize_submission(item) for item in subreddit_ref.new(limit=limit)
        ]

    def search_keyword_posts(
        self, keyword: str, *, limit: int = 25
    ) -> list[dict[str, Any]]:
        submissions = self._client.subreddit("all").search(
            keyword, sort="new", limit=limit
        )
        return [self._normalize_submission(item) for item in submissions]

    def _normalize_submission(self, submission: Any) -> dict[str, Any]:
        title = submission.title or ""
        body = submission.selftext or ""
        context = "\n".join([part for part in (title, body) if part])
        media_urls = self._extract_media_urls(submission)
        created_dt = None
        if submission.created_utc:
            created_dt = datetime.fromtimestamp(
                float(submission.created_utc), tz=timezone.utc
            )

        return {
            "post_id": str(submission.id),
            "title": title or None,
            "body": body or None,
            "author": str(submission.author) if submission.author else None,
            "subreddit": str(submission.subreddit) if submission.subreddit else None,
            "created_utc": created_dt,
            "url": submission.url or None,
            "media_urls": media_urls,
            "context_text": context or None,
            "raw_payload": {
                "id": submission.id,
                "permalink": submission.permalink,
                "url": submission.url,
                "title": submission.title,
                "selftext": submission.selftext,
                "is_self": submission.is_self,
                "over_18": submission.over_18,
                "thumbnail": submission.thumbnail,
                "created_utc": submission.created_utc,
            },
        }

    def _extract_media_urls(self, submission: Any) -> list[str]:
        urls: list[str] = []
        if submission.url:
            urls.append(submission.url)
        preview = getattr(submission, "preview", None)
        if isinstance(preview, dict):
            images = preview.get("images") or []
            for image in images:
                source = image.get("source") or {}
                url = source.get("url")
                if isinstance(url, str):
                    urls.append(url.replace("&amp;", "&"))
        media = getattr(submission, "media_metadata", None)
        if isinstance(media, dict):
            for item in media.values():
                if not isinstance(item, dict):
                    continue
                src = item.get("s") or {}
                url = src.get("u")
                if isinstance(url, str):
                    urls.append(url.replace("&amp;", "&"))
        return list(dict.fromkeys(urls))


def parse_reddit_list(raw: str) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def ensure_iterable(value: Iterable[str] | None) -> list[str]:
    return list(value) if value else []
