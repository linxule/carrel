import pytest

from carrel.errors import CarrelError
from carrel.transcribe.youtube_url import extract_video_id, is_youtube_url, slug_for_filename


def test_is_youtube_url_accepts_supported_hosts() -> None:
    assert is_youtube_url("https://www.youtube.com/watch?v=abc123") is True
    assert is_youtube_url("https://youtu.be/abc123") is True
    assert is_youtube_url("https://m.youtube.com/shorts/abc123") is True
    assert is_youtube_url("https://example.com/watch?v=abc123") is False


def test_extract_video_id_handles_supported_url_forms() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=abc123") == "abc123"
    assert extract_video_id("https://youtu.be/xyz789") == "xyz789"
    assert extract_video_id("https://www.youtube.com/embed/embed456") == "embed456"
    assert extract_video_id("https://www.youtube.com/shorts/short456") == "short456"
    assert extract_video_id("https://www.youtube.com/live/live456") == "live456"
    assert extract_video_id("https://example.com/watch?v=abc123") is None


def test_slug_for_filename_falls_back_to_video_id() -> None:
    assert slug_for_filename("https://www.youtube.com/watch?v=AbC-123_xyz") == "abc-123-xyz"


def test_slug_for_filename_raises_on_youtube_url_without_video_id() -> None:
    # A YouTube URL that parses but yields no id must fail loudly instead of
    # slugging to a colliding "watch" filename.
    with pytest.raises(CarrelError, match="could not extract a YouTube video id"):
        slug_for_filename("https://www.youtube.com/watch")


def test_slug_for_filename_leaves_non_youtube_urls_unaffected() -> None:
    assert slug_for_filename("https://example.com/articles/my-post") == "my-post"
    assert slug_for_filename("https://example.com/") == "video"
