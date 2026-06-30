from __future__ import annotations

import io
import json
import zipfile

import pytest

from carrel.convert.adapters.defuddle import capture_with_defuddle
from carrel.convert.adapters.liteparse import convert_with_liteparse
from carrel.convert.adapters.mistral_ocr import convert_with_mistral_ocr
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


class _JsonResponse:
    def __init__(self, payload: dict | None = None, *, status_code: int = 200, content: bytes = b""):
        self._payload = payload or {}
        self.status_code = status_code
        self.content = content

    def json(self):
        return self._payload


class _FakeProcess:
    def __init__(self, stdout: bytes, stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self):
        return self._stdout, self._stderr

    def kill(self) -> None:
        self.returncode = -9


def _zip_bytes(name: str, body: str) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr(name, body)
    return out.getvalue()


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
async def test_convert_with_mineru_uses_v4_upload_poll_and_result_zip(tmp_path, monkeypatch) -> None:
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"pdf")
    calls: list[tuple[str, str, dict]] = []

    class FakeMineruClient:
        def __init__(self, *args, **kwargs):  # noqa: D401, ARG002
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
            return False

        async def post(self, url: str, **kwargs):
            calls.append(("post", url, kwargs))
            return _JsonResponse(
                {"data": {"batch_id": "batch-1", "file_urls": ["https://upload.example/paper"]}}
            )

        async def put(self, url: str, **kwargs):
            calls.append(("put", url, kwargs))
            return _JsonResponse()

        async def get(self, url: str, **kwargs):
            calls.append(("get", url, kwargs))
            if "extract-results" in url:
                return _JsonResponse(
                    {"data": {"extract_result": [{"full_zip_url": "https://download.example/result.zip"}]}}
                )
            return _JsonResponse(content=_zip_bytes("paper/full.md", "# Parsed\n\nBody"))

    monkeypatch.setattr("carrel.convert.adapters.mineru.httpx.AsyncClient", FakeMineruClient)

    markdown, metadata = await convert_with_mineru(source, api_key="configured")

    assert markdown == "# Parsed\n\nBody"
    assert metadata["data"]["extract_result"][0]["full_zip_url"] == "https://download.example/result.zip"
    assert calls[0][1] == "https://api.mineru.net/api/v4/file-urls/batch"
    assert calls[0][2]["json"]["files"][0]["name"] == "paper.pdf"
    assert calls[1] == ("put", "https://upload.example/paper", {"content": b"pdf"})
    assert calls[2][1] == "https://api.mineru.net/api/v4/extract-results/batch/batch-1"


@pytest.mark.asyncio
async def test_convert_with_mistral_ocr_rejects_invalid_json(tmp_path, monkeypatch) -> None:
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr("carrel.convert.adapters.mistral_ocr.httpx.AsyncClient", _FakeAsyncClient)

    with pytest.raises(ConversionError) as exc:
        await convert_with_mistral_ocr(source, api_key="configured")

    assert exc.value.message == "mistral ocr returned invalid JSON"
    assert "HTML error page" in exc.value.hint


@pytest.mark.asyncio
async def test_convert_with_mistral_ocr_uploads_file_and_reads_page_markdown(tmp_path, monkeypatch) -> None:
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"pdf")
    calls: list[tuple[str, str, dict]] = []

    class FakeMistralClient:
        def __init__(self, *args, **kwargs):  # noqa: D401, ARG002
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
            return False

        async def post(self, url: str, **kwargs):
            calls.append(("post", url, kwargs))
            if url.endswith("/files"):
                return _JsonResponse({"id": "file-1"})
            return _JsonResponse(
                {
                    "model": "mistral-ocr-latest",
                    "pages": [
                        {"index": 0, "markdown": "# Page 1\n\nBody"},
                        {"index": 1, "markdown": "## Page 2"},
                    ],
                    "usage_info": {"pages_processed": 2, "doc_size_bytes": 3},
                }
            )

        async def get(self, url: str, **kwargs):
            calls.append(("get", url, kwargs))
            return _JsonResponse({"url": "https://signed.example/paper.pdf"})

        async def delete(self, url: str, **kwargs):
            calls.append(("delete", url, kwargs))
            return _JsonResponse({"deleted": True})

    monkeypatch.setattr("carrel.convert.adapters.mistral_ocr.httpx.AsyncClient", FakeMistralClient)

    markdown, metadata = await convert_with_mistral_ocr(source, api_key="configured")

    assert markdown == "# Page 1\n\nBody\n\n## Page 2"
    assert metadata["model"] == "mistral-ocr-latest"
    assert metadata["file_id"] == "file-1"
    assert metadata["pages"] == 2
    assert metadata["usage_info"] == {"pages_processed": 2, "doc_size_bytes": 3}
    assert "provider_response" not in metadata
    assert calls[0][0:2] == ("post", "https://api.mistral.ai/v1/files")
    assert calls[0][2]["data"] == {"purpose": "ocr"}
    assert calls[1] == (
        "get",
        "https://api.mistral.ai/v1/files/file-1/url",
        {"headers": {"Authorization": "Bearer configured"}, "params": {"expiry": 24}},
    )
    assert calls[2][0:2] == ("post", "https://api.mistral.ai/v1/ocr")
    assert calls[2][2]["json"]["document"] == {
        "type": "document_url",
        "document_url": "https://signed.example/paper.pdf",
    }
    assert calls[2][2]["json"]["table_format"] == "markdown"
    assert calls[2][2]["json"]["include_image_base64"] is False
    assert calls[3] == (
        "delete",
        "https://api.mistral.ai/v1/files/file-1",
        {"headers": {"Authorization": "Bearer configured"}},
    )


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


@pytest.mark.asyncio
async def test_transcribe_with_gemini_uses_interactions_video_request(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    class FakeGeminiClient:
        def __init__(self, *args, **kwargs):  # noqa: D401, ARG002
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
            return False

        async def post(self, url: str, **kwargs):
            calls.append((url, kwargs))
            return _JsonResponse({"output_text": "Transcript body"})

    monkeypatch.setattr("carrel.transcribe.adapters.gemini.httpx.AsyncClient", FakeGeminiClient)

    text = await transcribe_with_gemini("https://www.youtube.com/watch?v=abc123", api_key="configured")

    assert text == "Transcript body"
    assert calls[0][0] == "https://generativelanguage.googleapis.com/v1beta/interactions"
    assert calls[0][1]["headers"] == {"x-goog-api-key": "configured"}
    content = calls[0][1]["json"]["input"][0]["content"]
    assert {"type": "video", "uri": "https://www.youtube.com/watch?v=abc123"} in content


@pytest.mark.asyncio
async def test_liteparse_adapter_requests_markdown(monkeypatch, tmp_path) -> None:
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"pdf")
    calls: list[tuple[str, ...]] = []

    async def fake_exec(*args, **kwargs):  # noqa: ARG001
        calls.append(tuple(args))
        return _FakeProcess(b"# Markdown\n")

    monkeypatch.setattr("carrel.convert.adapters.liteparse.asyncio.create_subprocess_exec", fake_exec)

    text, _ = await convert_with_liteparse(source)

    assert text == "# Markdown"
    assert calls == [("lit", "parse", str(source), "--format", "markdown")]


@pytest.mark.asyncio
async def test_defuddle_adapter_accepts_current_markdown_content_field(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    async def fake_exec(*args, **kwargs):  # noqa: ARG001
        calls.append(tuple(args))
        payload = {"content": "# Captured", "title": "Captured"}
        return _FakeProcess(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr("carrel.convert.adapters.defuddle.asyncio.create_subprocess_exec", fake_exec)

    text, metadata = await capture_with_defuddle("https://example.com/post")

    assert text == "# Captured"
    assert metadata["title"] == "Captured"
    assert calls == [("defuddle", "parse", "https://example.com/post", "--json", "--markdown")]
