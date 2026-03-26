from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from carrel.errors import ToolNotInstalled, TranscriptionError
from carrel.env.install import install_command_for


def extract_youtube_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "youtu.be" in host:
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return parts[0]
    if "youtube.com" in host:
        query = parse_qs(parsed.query)
        if query.get("v"):
            return query["v"][0]
        parts = [part for part in parsed.path.split("/") if part]
        for index, part in enumerate(parts):
            if part in {"embed", "shorts", "live"} and index + 1 < len(parts):
                return parts[index + 1]
    raise TranscriptionError(
        "could not extract YouTube video id",
        hint="Use a standard youtube.com or youtu.be URL",
    )


def _format_timestamp(seconds: float) -> str:
    total_seconds = max(int(seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


async def transcribe_with_youtube_captions(url: str) -> tuple[str, dict]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ModuleNotFoundError as exc:
        raise ToolNotInstalled(
            "youtube-transcript-api",
            install_command_for("youtube-transcript-api") or "install youtube-transcript-api",
        ) from exc

    video_id = extract_youtube_video_id(url)
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
    except Exception as exc:  # pragma: no cover - library exception classes vary by version
        raise TranscriptionError(
            "youtube captions unavailable",
            hint="This video may not have captions. Use --tool gemini if cloud transcription is allowed.",
        ) from exc

    lines: list[str] = []
    for snippet in fetched:
        text = str(snippet.text).strip()
        if not text:
            continue
        lines.append(f"[{_format_timestamp(float(snippet.start))}] {text}")

    if not lines:
        raise TranscriptionError(
            "youtube captions were empty",
            hint="This video may not expose usable captions. Use --tool gemini if needed.",
        )

    return "\n".join(lines), {"video_id": video_id}
