from __future__ import annotations

from pathlib import Path

import frontmatter
from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.errors import ConversionError, ToolNotInstalled

runner = CliRunner()


def _init_vault(path: Path) -> None:
    (path / ".carrel").mkdir(parents=True)
    (path / "inbox").mkdir(parents=True)


def test_capture_url_saves_frontmatter(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    async def fake_capture(url: str) -> tuple[str, dict]:
        assert url == "https://example.com/posts/test"
        return (
            "# Clean article\n\nBody text.",
            {
                "title": "Example Article",
                "author": "Ada Lovelace",
                "published": "2026-03-01",
                "domain": "example.com",
            },
        )

    monkeypatch.setattr("carrel.cli.capture.capture_with_defuddle", fake_capture)

    result = runner.invoke(
        app,
        ["capture", "url", "https://example.com/posts/test", "--vault", str(vault)],
    )

    assert result.exit_code == 0
    stored = frontmatter.load(vault / "inbox" / "example-article.md")
    assert stored["title"] == "Example Article"
    assert stored["source_url"] == "https://example.com/posts/test"
    assert stored["author"] == "Ada Lovelace"
    assert stored["published"] == "2026-03-01"
    assert stored["domain"] == "example.com"
    assert stored["capture_tool"] == "defuddle"
    assert "Body text." in stored.content


def test_capture_url_dry_run_shows_destination(tmp_path) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    result = runner.invoke(
        app,
        [
            "capture",
            "url",
            "https://example.com/posts/test",
            "--vault",
            str(vault),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Would capture https://example.com/posts/test" in result.output
    assert "inbox/test.md" in result.output.replace("\\", "/")
    assert not (vault / "inbox" / "test.md").exists()


def test_capture_url_falls_back_to_markitdown(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    async def fake_defuddle(url: str) -> tuple[str, dict]:  # noqa: ARG001
        raise ToolNotInstalled("defuddle", "bun add -g defuddle")

    async def fake_markitdown(url: str) -> tuple[str, dict]:
        assert url == "https://example.com/fallback"
        return ("Fallback body", {"title": "Fallback Capture", "domain": "example.com"})

    monkeypatch.setattr("carrel.cli.capture.capture_with_defuddle", fake_defuddle)
    monkeypatch.setattr("carrel.cli.capture.capture_with_markitdown_url", fake_markitdown)

    result = runner.invoke(
        app,
        ["capture", "url", "https://example.com/fallback", "--vault", str(vault)],
    )

    assert result.exit_code == 0
    stored = frontmatter.load(vault / "inbox" / "fallback-capture.md")
    assert stored["capture_tool"] == "markitdown"
    assert stored.content == "Fallback body"


def test_capture_url_falls_back_on_defuddle_runtime_error(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    async def fake_defuddle(url: str) -> tuple[str, dict]:  # noqa: ARG001
        raise ConversionError("defuddle timed out", hint="Retry")

    async def fake_markitdown(url: str) -> tuple[str, dict]:
        assert url == "https://example.com/slow-site"
        return ("Recovered body", {"title": "Recovered Page", "domain": "example.com"})

    monkeypatch.setattr("carrel.cli.capture.capture_with_defuddle", fake_defuddle)
    monkeypatch.setattr("carrel.cli.capture.capture_with_markitdown_url", fake_markitdown)

    result = runner.invoke(
        app,
        ["capture", "url", "https://example.com/slow-site", "--vault", str(vault)],
    )

    assert result.exit_code == 0
    stored = frontmatter.load(vault / "inbox" / "recovered-page.md")
    assert stored["capture_tool"] == "markitdown"
    assert stored.content == "Recovered body"
