from __future__ import annotations

from pathlib import Path

import pytest

from carrel.convert.adapters.mineru import convert_with_mineru
from carrel.errors import ConversionError, TranscriptionError
from carrel.transcribe.adapters.gemini import transcribe_with_gemini
from carrel.transcribe.adapters.groq import transcribe_with_groq


class _BadJsonResponse:
    status_code = 200

    def json(self):
        raise ValueError("not json")


class _FakeAsyncClient:
    def __init__(self, *args, **kwargs):  # noqa: D401, ARG002
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False

    async def post(self, *args, **kwargs):  # noqa: ARG002
        return _BadJsonResponse()


@pytest.mark.asyncio
async def test_convert_with_mineru_rejects_invalid_json(tmp_path, monkeypatch) -> None:
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr("carrel.convert.adapters.mineru.httpx.AsyncClient", _FakeAsyncClient)

    with pytest.raises(ConversionError) as exc:
        await convert_with_mineru(source, api_key="configured")

    assert exc.value.message == "mineru returned invalid JSON"
    assert "HTML error page" in exc.value.hint


@pytest.mark.asyncio
async def test_transcribe_with_groq_rejects_invalid_json(tmp_path, monkeypatch) -> None:
    source = tmp_path / "audio.wav"
    source.write_bytes(b"audio")
    monkeypatch.setattr("carrel.transcribe.adapters.groq.httpx.AsyncClient", _FakeAsyncClient)

    with pytest.raises(TranscriptionError) as exc:
        await transcribe_with_groq(source, api_key="configured")

    assert exc.value.message == "groq returned invalid JSON"
    assert "HTML error page" in exc.value.hint


@pytest.mark.asyncio
async def test_transcribe_with_gemini_rejects_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr("carrel.transcribe.adapters.gemini.httpx.AsyncClient", _FakeAsyncClient)

    with pytest.raises(TranscriptionError) as exc:
        await transcribe_with_gemini("https://www.youtube.com/watch?v=abc123", api_key="configured")

    assert exc.value.message == "gemini returned invalid JSON"
    assert "HTML error page" in exc.value.hint
