from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest
from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.errors import ConversionError, ToolNotInstalled
from carrel.google.export import ensure_gws_authenticated, export_target_for, parse_google_workspace_url
from carrel.models import ConvertTool

runner = CliRunner()


def _init_vault(path: Path) -> None:
    (path / ".carrel").mkdir(parents=True)
    (path / "papers").mkdir(parents=True)


def test_parse_google_workspace_url_variants() -> None:
    assert parse_google_workspace_url("https://docs.google.com/document/d/doc123/edit") == (
        "document",
        "doc123",
    )
    assert parse_google_workspace_url("https://docs.google.com/spreadsheets/d/sheet456/edit") == (
        "spreadsheets",
        "sheet456",
    )
    assert parse_google_workspace_url("https://docs.google.com/presentation/d/slide789/edit") == (
        "presentation",
        "slide789",
    )


def test_export_target_for_creates_vault_local_export_path(tmp_path) -> None:
    file_id, mime_type, output_path = export_target_for(
        "https://docs.google.com/document/d/doc123/edit",
        "docx",
        tmp_path / "vault",
    )

    assert file_id == "doc123"
    assert mime_type.endswith("document")
    assert output_path == (tmp_path / "vault" / ".carrel" / "exports" / "doc123.docx").resolve()


def test_google_export_converts_exported_file(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)
    exported_path = vault / ".carrel" / "exports" / "doc123.docx"

    async def fake_export(url: str, workspace: Path, export_format: str = "docx") -> Path:
        assert url == "https://docs.google.com/document/d/doc123/edit"
        assert workspace == vault.resolve()
        assert export_format == "docx"
        exported = exported_path
        exported.parent.mkdir(parents=True, exist_ok=True)
        exported.write_bytes(b"docx-bytes")
        return exported

    async def fake_convert(
        file_path: Path,
        vault_path: Path,
        profile,
        sensitivity,
        tool,
    ) -> tuple[ConvertTool, str, dict]:
        assert file_path.name == "doc123.docx"
        assert vault_path == vault.resolve()
        assert profile is None
        assert sensitivity is None
        assert tool is None
        return (
            ConvertTool.MARKDOWNIFY,
            "# Shared Draft\n\nConverted body.",
            {"title": "Shared Draft", "authors": "Ada Lovelace", "year": "1843"},
        )

    monkeypatch.setattr("carrel.cli.google.export_from_google_workspace", fake_export)
    monkeypatch.setattr("carrel.cli.google.run_convert_pipeline", fake_convert)

    result = runner.invoke(
        app,
        ["google", "export", "https://docs.google.com/document/d/doc123/edit", "--vault", str(vault)],
    )

    assert result.exit_code == 0
    stored = frontmatter.load(vault / "papers" / "lovelace-1843" / "paper.md")
    assert stored["title"] == "Shared Draft"
    assert stored["converter"] == "markdownify"
    assert stored["source_file"] == "doc123.docx"
    assert "Converted body." in stored.content
    assert not exported_path.exists()


def test_google_export_keep_export_preserves_raw_file(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)
    exported_path = vault / ".carrel" / "exports" / "doc123.docx"

    async def fake_export(url: str, workspace: Path, export_format: str = "docx") -> Path:
        assert url == "https://docs.google.com/document/d/doc123/edit"
        assert workspace == vault.resolve()
        assert export_format == "docx"
        exported_path.parent.mkdir(parents=True, exist_ok=True)
        exported_path.write_bytes(b"docx-bytes")
        return exported_path

    async def fake_convert(
        file_path: Path,
        vault_path: Path,
        profile,
        sensitivity,
        tool,
    ) -> tuple[ConvertTool, str, dict]:
        assert file_path == exported_path
        assert vault_path == vault.resolve()
        assert profile is None
        assert sensitivity is None
        assert tool is None
        return (
            ConvertTool.MARKDOWNIFY,
            "# Shared Draft\n\nConverted body.",
            {"title": "Shared Draft", "authors": "Ada Lovelace", "year": "1843"},
        )

    monkeypatch.setattr("carrel.cli.google.export_from_google_workspace", fake_export)
    monkeypatch.setattr("carrel.cli.google.run_convert_pipeline", fake_convert)

    result = runner.invoke(
        app,
        [
            "google",
            "export",
            "https://docs.google.com/document/d/doc123/edit",
            "--vault",
            str(vault),
            "--keep-export",
        ],
    )

    assert result.exit_code == 0
    assert exported_path.exists()


def test_google_export_failure_keeps_raw_file(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)
    exported_path = vault / ".carrel" / "exports" / "doc123.docx"

    async def fake_export(url: str, workspace: Path, export_format: str = "docx") -> Path:
        assert url == "https://docs.google.com/document/d/doc123/edit"
        assert workspace == vault.resolve()
        assert export_format == "docx"
        exported_path.parent.mkdir(parents=True, exist_ok=True)
        exported_path.write_bytes(b"docx-bytes")
        return exported_path

    async def fake_convert(
        file_path: Path,
        vault_path: Path,
        profile,
        sensitivity,
        tool,
    ) -> tuple[ConvertTool, str, dict]:
        assert file_path == exported_path
        assert vault_path == vault.resolve()
        assert profile is None
        assert sensitivity is None
        assert tool is None
        raise ConversionError("conversion failed")

    monkeypatch.setattr("carrel.cli.google.export_from_google_workspace", fake_export)
    monkeypatch.setattr("carrel.cli.google.run_convert_pipeline", fake_convert)

    result = runner.invoke(
        app,
        ["google", "export", "https://docs.google.com/document/d/doc123/edit", "--vault", str(vault)],
    )

    assert result.exit_code == 1
    assert exported_path.exists()


def test_google_export_blocks_high_sensitivity_before_export(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    async def fake_export(url: str, workspace: Path, export_format: str = "docx") -> Path:  # noqa: ARG001
        raise AssertionError("export should not run for high sensitivity")

    monkeypatch.setattr("carrel.cli.google.export_from_google_workspace", fake_export)

    result = runner.invoke(
        app,
        [
            "google",
            "export",
            "https://docs.google.com/document/d/doc123/edit",
            "--vault",
            str(vault),
            "--sensitivity",
            "high",
        ],
    )

    assert result.exit_code == 1
    assert "HIGH sensitivity blocks Google Workspace export" in result.output


def test_google_export_without_gws_shows_install_hint(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    async def fake_export(url: str, workspace: Path, export_format: str = "docx") -> Path:  # noqa: ARG001
        raise ToolNotInstalled("gws", "brew install googleworkspace-cli && gws auth login -s drive")

    monkeypatch.setattr("carrel.cli.google.export_from_google_workspace", fake_export)

    result = runner.invoke(
        app,
        ["google", "export", "https://docs.google.com/document/d/doc123/edit", "--vault", str(vault)],
    )

    assert result.exit_code == 1
    assert "brew install googleworkspace-cli && gws auth login -s drive" in result.output


@pytest.mark.asyncio
async def test_ensure_gws_authenticated_raises_conversion_error_for_auth_failure(monkeypatch) -> None:
    async def fake_run_gws(args: list[str], timeout: int) -> tuple[bytes, bytes, int]:  # noqa: ARG001
        return b"", b"login required", 1

    monkeypatch.setattr("carrel.google.export._run_gws", fake_run_gws)

    with pytest.raises(ConversionError) as exc:
        await ensure_gws_authenticated()

    assert exc.value.message == "gws not authenticated"
    assert exc.value.hint == "login required"
