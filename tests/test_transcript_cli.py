from __future__ import annotations

from datetime import date
from pathlib import Path

import frontmatter
from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import ApiKeyStatus, AuditResult, BinaryInfo, HardwareCapability, ToolAvailability

runner = CliRunner()


def _init_vault(path: Path) -> None:
    (path / ".carrel").mkdir(parents=True)
    (path / "transcripts").mkdir(parents=True)


def _audit_result(*, gemini_key: bool = False) -> AuditResult:
    return AuditResult(
        os="macOS",
        arch="arm64",
        hardware_capability=HardwareCapability.HIGH,
        tools=ToolAvailability(
            binaries={"coli": BinaryInfo(installed=False)},
            api_keys={
                "groq": ApiKeyStatus(configured=False, env_var="GROQ_API_KEY"),
                "gemini": ApiKeyStatus(configured=gemini_key, env_var="GEMINI_API_KEY"),
            },
            mcp_servers=[],
        ),
    )


def test_transcript_create_falls_back_to_youtube_captions(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    async def fake_audit(project_path: Path | None = None) -> AuditResult:  # noqa: ARG001
        return _audit_result(gemini_key=False)

    async def fake_youtube(url: str) -> tuple[str, dict]:
        assert url == "https://www.youtube.com/watch?v=abc123"
        return ("[00:00:00] Hello", {"title": "Video Title"})

    monkeypatch.setattr("carrel.cli.transcript.audit", fake_audit)
    monkeypatch.setattr("carrel.cli.transcript.transcribe_with_youtube_captions", fake_youtube)

    result = runner.invoke(
        app,
        [
            "transcript",
            "create",
            "https://www.youtube.com/watch?v=abc123",
            "--vault",
            str(vault),
        ],
    )

    assert result.exit_code == 0
    stored = frontmatter.load(vault / "transcripts" / f"video-title-{date.today().isoformat()}.md")
    assert stored["transcriber"] == "youtube_captions"
    assert stored["source_file"] == "https://www.youtube.com/watch?v=abc123"
    assert "[00:00:00] Hello" in stored.content


def test_transcript_create_with_explicit_gemini_uses_gemini_adapter(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)
    calls: list[str] = []

    async def fake_audit(project_path: Path | None = None) -> AuditResult:  # noqa: ARG001
        return _audit_result(gemini_key=False)

    async def fake_gemini(url: str, api_key: str, prompt: str = "", timeout: int = 300) -> str:
        calls.append(url)
        assert api_key == "configured"
        assert timeout == 300
        return "[00:00:00] Gemini transcript"

    monkeypatch.setattr("carrel.cli.transcript.audit", fake_audit)
    monkeypatch.setattr("carrel.cli.transcript.transcribe_with_gemini", fake_gemini)
    monkeypatch.setenv("GEMINI_API_KEY", "configured")

    result = runner.invoke(
        app,
        [
            "transcript",
            "create",
            "https://www.youtube.com/watch?v=abc123",
            "--vault",
            str(vault),
            "--tool",
            "gemini",
        ],
    )

    assert result.exit_code == 0
    assert calls == ["https://www.youtube.com/watch?v=abc123"]
    stored = frontmatter.load(vault / "transcripts" / f"youtube-abc123-{date.today().isoformat()}.md")
    assert stored["transcriber"] == "gemini"
    assert "Gemini transcript" in stored.content
