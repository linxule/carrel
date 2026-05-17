from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app

runner = CliRunner()


def _seed_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    meta = vault / "_meta"
    (meta / "friction-log").mkdir(parents=True)
    (meta / "capability-log").mkdir(parents=True)
    (meta / "reflections").mkdir(parents=True)
    (meta / "friction-log" / "2026-04-01.md").write_text(
        "## Friction\n\nAlice struggled with mineru retries at Acme Lab.\n",
        encoding="utf-8",
    )
    (meta / "capability-log" / "2026-04-02.md").write_text(
        "## Built\n\nAdded Alice's custom tracker.\n",
        encoding="utf-8",
    )
    (meta / "reflections" / "reflection-2026-04-03.md").write_text(
        "# Reflection\n\nAlice felt that mineru retries needed Acme Lab's input.\n",
        encoding="utf-8",
    )
    return vault


def test_feedback_export_writes_dated_digest_with_redactions(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    redact = tmp_path / "redact.txt"
    redact.write_text("Alice\nAcme Lab\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "vault",
            "feedback",
            "export",
            "--redact-list",
            str(redact),
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 0, result.stderr
    # Flat-file path matches the session-reflection skill contract +
    # legacy /carrel-feedback convention: _meta/feedback-digest-<date>.md.
    output = vault / "_meta" / f"feedback-digest-{date.today().isoformat()}.md"
    assert output.exists()
    body = output.read_text(encoding="utf-8")
    assert "Alice" not in body
    assert "Acme Lab" not in body
    assert "[REDACTED]" in body
    # Reflections were swept too (read/write symmetry with session-reflection):
    # the reflection file's content should appear (with redactions applied).
    assert "reflection-2026-04-03.md" in body


def test_feedback_export_errors_on_missing_redact_list(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "vault",
            "feedback",
            "export",
            "--redact-list",
            str(tmp_path / "missing.txt"),
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 1
    assert "Redact list not found" in result.stderr


def test_feedback_export_handles_empty_sources(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    redact = tmp_path / "redact.txt"
    redact.write_text("", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "vault",
            "feedback",
            "export",
            "--redact-list",
            str(redact),
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["sources"] == []
    assert payload["redacted_terms"] == 0
    assert Path(payload["path"]).exists()
