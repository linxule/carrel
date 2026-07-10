from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from carrel.errors import CarrelError


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "video"


def _is_youtube_host(host: str) -> bool:
    normalized = host.lower()
    return normalized == "youtu.be" or normalized.endswith(".youtu.be") or normalized == "youtube.com" or normalized.endswith(".youtube.com")


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc and _is_youtube_host(parsed.netloc))


def extract_video_id(url: str) -> str | None:
    if not is_youtube_url(url):
        return None

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host == "youtu.be" or host.endswith(".youtu.be"):
        parts = [part for part in parsed.path.split("/") if part]
        return parts[0] if parts else None

    query = parse_qs(parsed.query)
    if query.get("v"):
        return query["v"][0]

    parts = [part for part in parsed.path.split("/") if part]
    for index, part in enumerate(parts):
        if part in {"embed", "shorts", "live"} and index + 1 < len(parts):
            return parts[index + 1]
    return None


def slug_for_filename(url: str) -> str:
    if is_youtube_url(url):
        video_id = extract_video_id(url)
        if video_id is None:
            raise CarrelError(
                "could not extract a YouTube video id from the URL",
                hint="Use a standard youtube.com/watch?v=..., youtu.be/..., or /embed|/shorts|/live URL.",
            )
        return _slugify(video_id)

    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if parts:
        return _slugify(parts[-1])
    return "video"
