from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from carrel.transcribe.adapters.youtube_captions import (
    extract_youtube_video_id,
    transcribe_with_youtube_captions,
)


def test_extract_youtube_video_id_variants() -> None:
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=abc123") == "abc123"
    assert extract_youtube_video_id("https://youtu.be/xyz789") == "xyz789"
    assert extract_youtube_video_id("https://www.youtube.com/shorts/short456") == "short456"


@pytest.mark.asyncio
async def test_transcribe_with_youtube_captions_formats_timestamps(monkeypatch) -> None:
    # Mimic youtube-transcript-api >= 1.0: instance with .fetch() returning snippet objects
    class FakeSnippet:
        def __init__(self, text: str, start: float, duration: float):
            self.text = text
            self.start = start
            self.duration = duration

    class FakeApi:
        def fetch(self, video_id: str):
            assert video_id == "abc123"
            return [
                FakeSnippet("Hello world", 0.0, 1.2),
                FakeSnippet("Second line", 65.4, 2.0),
            ]

    monkeypatch.setitem(sys.modules, "youtube_transcript_api", SimpleNamespace(YouTubeTranscriptApi=FakeApi))

    text, metadata = await transcribe_with_youtube_captions("https://www.youtube.com/watch?v=abc123")

    assert text == "[00:00:00] Hello world\n[00:01:05] Second line"
    assert metadata == {"video_id": "abc123"}
