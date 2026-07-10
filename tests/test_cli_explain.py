from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import ResearcherProfile, Sensitivity

runner = CliRunner()


def _init_vault(path: Path) -> None:
    (path / ".carrel").mkdir(parents=True)
    (path / "papers").mkdir(parents=True)
    (path / "transcripts").mkdir(parents=True)


def test_paper_convert_explain_prints_policy_decision_without_running_pipeline(
    tmp_path,
    monkeypatch,
) -> None:
    vault = tmp_path / "vault"
    source = tmp_path / "paper.pdf"
    _init_vault(vault)
    source.write_bytes(b"%PDF")

    def fail_pipeline(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("convert pipeline should not run for --explain")

    monkeypatch.setattr("carrel.cli.paper.select_convert_tool_only", fail_pipeline)
    monkeypatch.setattr(
        "carrel.cli.paper.read_profile",
        lambda vault_path: ResearcherProfile(sensitivity=Sensitivity.LOW, cloud_consent=True),  # noqa: ARG005
    )
    monkeypatch.setattr("carrel.cli.paper.shutil.which", lambda cmd: None)
    monkeypatch.setenv("MINERU_API_KEY", "configured")

    result = runner.invoke(
        app,
        ["paper", "convert", str(source), "--vault", str(vault), "--explain"],
    )

    normalized = result.output.replace("\n", "")
    assert result.exit_code == 0
    assert "PolicyDecision(" in result.output
    assert "selected_tool=<ConvertTool.MINERU: 'mineru'>" in result.output
    assert "No local tool available; cloud consent enabled so routing to cloud" in normalized


def test_paper_convert_explain_non_pdf_explicit_cloud_names_cloud_tool(
    tmp_path,
    monkeypatch,
) -> None:
    """--explain must agree with the router: a supported non-PDF + explicit cloud
    tool + configured key resolves to the cloud tool, not markdownify."""
    vault = tmp_path / "vault"
    source = tmp_path / "notes.docx"
    _init_vault(vault)
    source.write_bytes(b"docx")

    def fail_pipeline(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("convert pipeline should not run for --explain")

    monkeypatch.setattr("carrel.cli.paper.select_convert_tool_only", fail_pipeline)
    monkeypatch.setattr(
        "carrel.cli.paper.read_profile",
        lambda vault_path: ResearcherProfile(sensitivity=Sensitivity.MEDIUM),  # noqa: ARG005
    )
    monkeypatch.setattr("carrel.cli.paper.shutil.which", lambda cmd: None)
    monkeypatch.setenv("MINERU_API_KEY", "configured")

    result = runner.invoke(
        app,
        [
            "paper",
            "convert",
            str(source),
            "--vault",
            str(vault),
            "--tool",
            "mineru",
            "--explain",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "PolicyDecision(" in result.output
    assert "selected_tool=<ConvertTool.MINERU: 'mineru'>" in result.output


def test_paper_convert_explain_non_pdf_unsupported_cloud_suffix_errors_like_real_run(
    tmp_path,
    monkeypatch,
) -> None:
    """A suffix the cloud tool can't handle is a hard error in the real run, so
    --explain must error the same way rather than print a mismatched decision."""
    vault = tmp_path / "vault"
    source = tmp_path / "notes.txt"
    _init_vault(vault)
    source.write_text("plain", encoding="utf-8")

    monkeypatch.setattr(
        "carrel.cli.paper.read_profile",
        lambda vault_path: ResearcherProfile(sensitivity=Sensitivity.MEDIUM),  # noqa: ARG005
    )
    monkeypatch.setenv("MINERU_API_KEY", "configured")

    result = runner.invoke(
        app,
        [
            "paper",
            "convert",
            str(source),
            "--vault",
            str(vault),
            "--tool",
            "mineru",
            "--explain",
        ],
    )

    assert result.exit_code == 1
    assert "mineru does not support" in result.output + (result.stderr or "")


def test_transcript_create_explain_prints_policy_decision_without_audit(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    source = tmp_path / "meeting.wav"
    _init_vault(vault)
    source.write_bytes(b"audio")

    async def fail_audit(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("audit should not run for --explain")

    monkeypatch.setattr("carrel.cli.transcript.audit", fail_audit)
    monkeypatch.setattr("carrel.cli.transcript.shutil.which", lambda cmd: None)
    monkeypatch.setenv("GROQ_API_KEY", "configured")

    result = runner.invoke(
        app,
        [
            "transcript",
            "create",
            str(source),
            "--vault",
            str(vault),
            "--sensitivity",
            "medium",
            "--explain",
        ],
    )

    normalized = result.output.replace("\n", "")
    assert result.exit_code == 0
    assert "PolicyDecision(" in result.output
    assert "selected_tool=None" in result.output
    assert "Local tool missing; to use cloud, run with `--tool <cloud>`" in normalized


def test_google_export_explain_prints_policy_decision_without_export(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _init_vault(vault)

    async def fail_export(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("google export should not run for --explain")

    monkeypatch.setattr("carrel.cli.google.export_from_google_workspace", fail_export)
    monkeypatch.setattr("carrel.cli.google.shutil.which", lambda cmd: "/usr/bin/lit" if cmd == "lit" else None)

    result = runner.invoke(
        app,
        [
            "google",
            "export",
            "https://docs.google.com/document/d/doc123/edit",
            "--vault",
            str(vault),
            "--export-format",
            "pdf",
            "--explain",
        ],
    )

    assert result.exit_code == 0
    assert "PolicyDecision(" in result.output
    assert "selected_tool=<ConvertTool.LITEPARSE: 'liteparse'>" in result.output
    assert "Local tool selected by default" in result.output
