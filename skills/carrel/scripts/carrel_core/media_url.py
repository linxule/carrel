from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .constants import GOOGLE_WORKSPACE_EXPORTS
from .core import CarrelError, safe_vault_join, slugify

# Stdlib-only port of src/carrel/transcribe/youtube_url.py. The portable pack
# must stay standalone (no `carrel` import), so the YouTube URL forms handled
# there — watch?v=, youtu.be/, shorts/, live/, embed/ — are reimplemented here.


def _is_youtube_host(host: str) -> bool:
    normalized = host.lower()
    return (
        normalized == "youtu.be"
        or normalized.endswith(".youtu.be")
        or normalized == "youtube.com"
        or normalized.endswith(".youtube.com")
    )


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


def slug_for_source(source: str, *, fallback: str = "untitled") -> str:
    # Deterministic filename slug for an ingestion source. YouTube URLs slug by
    # video id (youtube-<id>) so distinct videos never collide on the shared
    # path stem "watch" (which silently overwrote the first video under
    # --force). Other URLs and local paths slug by path/name stem. A YouTube URL
    # with no extractable video id raises rather than producing a colliding
    # slug — the caller can pass --title (capture) or --content with an explicit
    # name to override.
    parsed = urlparse(source)
    is_url = bool(parsed.scheme and parsed.netloc)
    if is_url and _is_youtube_host(parsed.netloc):
        video_id = extract_video_id(source)
        if not video_id:
            raise CarrelError(
                "Could not extract a YouTube video id from the URL",
                hint=(
                    "Pass a watch?v=, youtu.be/, shorts/, live/, or embed/ URL, "
                    "or name the artifact yourself (--title for capture, or "
                    "--content with an explicit target)."
                ),
            )
        return slugify(f"youtube-{video_id}", fallback=fallback)
    if is_url:
        stem = Path(parsed.path).stem or parsed.netloc
        return slugify(stem, fallback=fallback)
    return slugify(Path(source).stem, fallback=fallback)


def parse_google_workspace_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "docs.google.com":
        raise CarrelError("Unsupported Google Workspace URL", hint="Use a docs.google.com/document, spreadsheets, or presentation URL.")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[1] != "d":
        raise CarrelError("Unsupported Google Workspace URL", hint="Expected docs.google.com/<kind>/d/<id>/edit.")
    kind = parts[0]
    if kind not in GOOGLE_WORKSPACE_EXPORTS:
        raise CarrelError("Unsupported Google Workspace file type", hint="Supported kinds: document, spreadsheets, presentation.")
    return kind, parts[2]


def google_export_target(vault: Path, url: str, export_format: str) -> tuple[str, str, Path]:
    kind, file_id = parse_google_workspace_url(url)
    try:
        mime_type, suffix = GOOGLE_WORKSPACE_EXPORTS[kind][export_format]
    except KeyError as exc:
        supported = ", ".join(sorted(GOOGLE_WORKSPACE_EXPORTS[kind]))
        raise CarrelError(
            f"{kind} files do not support --export-format {export_format}",
            hint=f"Supported --export-format for {kind}: {supported}.",
        ) from exc
    target = safe_vault_join(vault, ".carrel", "exports", f"{file_id}{suffix}")
    return file_id, mime_type, target
