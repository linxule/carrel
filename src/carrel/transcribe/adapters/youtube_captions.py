from __future__ import annotations

import asyncio
from functools import partial

from carrel.errors import ToolNotInstalled, TranscriptionError
from carrel.env.install import install_command_for
from carrel.transcribe.youtube_url import extract_video_id


def _format_timestamp(seconds: float) -> str:
    total_seconds = max(int(seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


async def transcribe_with_youtube_captions(url: str) -> tuple[str, dict]:
    try:
        import youtube_transcript_api as ytt_api_module
    except ModuleNotFoundError as exc:
        raise ToolNotInstalled(
            "youtube-transcript-api",
            install_command_for("youtube-transcript-api") or "install youtube-transcript-api",
        ) from exc

    YouTubeTranscriptApi = ytt_api_module.YouTubeTranscriptApi
    TranscriptsDisabled = getattr(ytt_api_module, "TranscriptsDisabled", type("TranscriptsDisabled", (Exception,), {}))
    NoTranscriptFound = getattr(ytt_api_module, "NoTranscriptFound", type("NoTranscriptFound", (Exception,), {}))
    VideoUnavailable = getattr(ytt_api_module, "VideoUnavailable", type("VideoUnavailable", (Exception,), {}))

    video_id = extract_video_id(url)
    if video_id is None:
        raise TranscriptionError(
            "could not extract YouTube video id",
            hint="Use a standard youtube.com or youtu.be URL",
        )
    try:
        ytt_api = YouTubeTranscriptApi()
        loop = asyncio.get_running_loop()
        fetched = await loop.run_in_executor(None, partial(ytt_api.fetch, video_id))
    except TranscriptsDisabled as exc:
        raise TranscriptionError(
            "youtube captions are disabled",
            hint="This video has captions disabled. Use --tool gemini if cloud transcription is allowed.",
        ) from exc
    except NoTranscriptFound as exc:
        raise TranscriptionError(
            "youtube captions unavailable",
            hint="No transcript was found for this video. Try --tool gemini if cloud transcription is allowed.",
        ) from exc
    except VideoUnavailable as exc:
        raise TranscriptionError(
            "youtube video unavailable",
            hint="Check that the YouTube URL is correct and the video is publicly accessible.",
        ) from exc
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
