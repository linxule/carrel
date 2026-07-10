from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import ResearcherProfile

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
    assert payload["redaction_rules"] == 0
    assert payload["redactions_applied"] == 0
    assert payload["zero_match_terms"] == []
    assert Path(payload["path"]).exists()


def test_feedback_export_supports_mappings_overlap_unicode_and_literal_replacements(
    tmp_path,
) -> None:
    vault = _seed_vault(tmp_path)
    source = vault / "_meta" / "friction-log" / "2026-04-01.md"
    source.write_text(
        "Alice visited ACME LAB, then Acme. Bob joined Alice.\n",
        encoding="utf-8",
    )
    redact = tmp_path / "redact.txt"
    redact.write_text(
        "# approved mappings\n"
        "Alice -> Researcher\\1\n"
        "Acme Lab → Institution\n"
        "Acme\n"
        "Bob -> Alice\n"
        "Never Seen\n",
        encoding="utf-8",
    )

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
    assert payload["redaction_rules"] == 5
    assert payload["redacted_terms"] == payload["redactions_applied"]
    assert payload["zero_match_terms"] == ["Never Seen"]
    body = Path(payload["path"]).read_text(encoding="utf-8")
    assert "Researcher\\1 visited Institution, then [REDACTED]" in body
    # Replacements are not fed back through later rules.
    assert "Alice joined Researcher\\1" in body


def test_feedback_export_automatically_protects_profile_name_unless_explicitly_mapped(
    tmp_path,
) -> None:
    vault = _seed_vault(tmp_path)
    profile = ResearcherProfile(name="Alice")
    (vault / ".carrel" / "environment.json").write_text(
        profile.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )
    redact = tmp_path / "redact.txt"
    redact.write_text("Acme Lab -> Institution\n", encoding="utf-8")

    automatic = runner.invoke(
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

    assert automatic.exit_code == 0, automatic.stderr
    automatic_payload = json.loads(automatic.stdout)
    automatic_body = Path(automatic_payload["path"]).read_text(encoding="utf-8")
    assert "Alice" not in automatic_body
    assert "Researcher" in automatic_body
    assert automatic_payload["redaction_rules"] == 2

    redact.write_text("Alice -> Principal Investigator\n", encoding="utf-8")
    explicit = runner.invoke(
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
    assert explicit.exit_code == 0, explicit.stderr
    explicit_body = Path(json.loads(explicit.stdout)["path"]).read_text(encoding="utf-8")
    assert "Principal Investigator" in explicit_body
    assert "Researcher" not in explicit_body


def test_feedback_export_rejects_empty_mapping_source_with_line_number(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    redact = tmp_path / "redact.txt"
    redact.write_text("# comment\n\n -> replacement\n", encoding="utf-8")

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

    assert result.exit_code == 1
    assert "line 3: empty source" in result.stderr


def test_feedback_export_rejects_symlinked_source_directory(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / "_meta").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leak.md").write_text("private material", encoding="utf-8")
    (vault / "_meta" / "reflections").symlink_to(outside, target_is_directory=True)
    redact = tmp_path / "redact.txt"
    redact.write_text("private\n", encoding="utf-8")

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

    assert result.exit_code == 1
    assert "Path escapes vault root" in result.stderr
    assert not list((vault / "_meta").glob("feedback-digest-*.md"))


def test_feedback_export_redacts_source_headings_and_counts_heading_hits(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    source_dir = vault / "_meta" / "friction-log"
    source_dir.mkdir(parents=True)
    (source_dir / "Alice-at-Acme Lab.md").write_text(
        "No identifying terms in this body.\n",
        encoding="utf-8",
    )
    (vault / ".carrel" / "environment.json").write_text(
        ResearcherProfile(name="Alice").model_dump_json(indent=2),
        encoding="utf-8",
    )
    redact = tmp_path / "redact.txt"
    redact.write_text("Acme Lab -> Institution\n", encoding="utf-8")

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
    digest = Path(payload["path"]).read_text(encoding="utf-8")
    assert "Alice" not in digest
    assert "Acme Lab" not in digest
    assert "Researcher-at-Institution.md" in digest
    assert payload["redacted_terms"] == 2
    assert payload["redactions_applied"] == 2
    assert payload["zero_match_terms"] == []


def test_feedback_export_handles_unicode_ignorecase_equivalents(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    source_dir = vault / "_meta" / "friction-log"
    source_dir.mkdir(parents=True)
    (source_dir / "sample.md").write_text("İ ı I i\n", encoding="utf-8")
    redact = tmp_path / "redact.txt"
    redact.write_text("i -> X\n", encoding="utf-8")

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
    digest = Path(payload["path"]).read_text(encoding="utf-8")
    assert "X X X X" in digest
    assert payload["redactions_applied"] == 4
