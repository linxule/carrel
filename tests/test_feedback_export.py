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
    # All four İ/ı/I/i variants fold to "i" under IGNORECASE (the body).
    assert "X X X X" in digest
    # The directory prefix in the heading is NOT redacted, so the "i"s inside
    # "friction-log" are not counted — only the four body matches are.
    assert payload["redactions_applied"] == 4
    assert "## _meta/friction-log/sample.md" in digest  # intact relative dir prefix


def test_feedback_export_auto_name_redaction_matches_whole_words_only(tmp_path) -> None:
    """A short profile name must not corrupt words that merely contain it.

    Repro from the fix: the auto-injected rule for name "Ann" rewrote
    "Planning the annual review" into garbage because it matched "ann" as an
    unbounded substring. The auto name rule now matches whole words only; a
    standalone "Ann" is still redacted. User-supplied rules keep substring
    semantics (covered elsewhere).
    """

    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / "_meta" / "friction-log").mkdir(parents=True)
    (vault / "_meta" / "friction-log" / "notes.md").write_text(
        "Planning the annual review. Ann joined the lab.\n",
        encoding="utf-8",
    )
    (vault / ".carrel" / "environment.json").write_text(
        ResearcherProfile(name="Ann").model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )
    redact = tmp_path / "redact.txt"
    redact.write_text("", encoding="utf-8")  # only the auto name rule applies

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
    assert "Planning the annual review" in digest  # neither word corrupted
    assert "Researcher joined the lab" in digest  # standalone "Ann" redacted
    assert "PlResearcher" not in digest  # the exact reported corruption is gone
    assert payload["redactions_applied"] == 1


def test_feedback_export_skips_unreadable_source_and_excludes_it_from_count(tmp_path) -> None:
    """An unreadable file is dropped from sources and every count, tracked separately."""

    from carrel.feedback.exporter import export_feedback

    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    friction_dir = vault / "_meta" / "friction-log"
    friction_dir.mkdir(parents=True)
    (friction_dir / "good.md").write_text("Acme Lab was here.\n", encoding="utf-8")
    (friction_dir / "bad.md").write_bytes(b"\xff\xfe not valid utf-8 \xff")
    redact = tmp_path / "redact.txt"
    redact.write_text("Acme Lab\n", encoding="utf-8")

    out = vault / "_meta" / f"feedback-digest-{date.today().isoformat()}.md"
    result = export_feedback(vault=vault, redact_list=redact, output_path=out)

    assert {p.name for p in result.sources} == {"good.md"}
    assert {p.name for p in result.skipped} == {"bad.md"}
    digest = out.read_text(encoding="utf-8")
    assert "good.md" in digest
    assert "bad.md" not in digest  # unreadable file never reaches the digest
    assert result.redacted_terms == 1  # only good.md's "Acme Lab" is counted


def test_feedback_export_disambiguates_same_basename_across_subdirs(tmp_path) -> None:
    """Same-basename files in different _meta subdirs get distinct headings."""

    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / "_meta" / "friction-log").mkdir(parents=True)
    (vault / "_meta" / "reflections").mkdir(parents=True)
    (vault / "_meta" / "friction-log" / "2026.md").write_text(
        "friction body\n", encoding="utf-8"
    )
    (vault / "_meta" / "reflections" / "2026.md").write_text(
        "reflection body\n", encoding="utf-8"
    )
    redact = tmp_path / "redact.txt"
    redact.write_text("nothingmatches\n", encoding="utf-8")

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
    digest = Path(json.loads(result.stdout)["path"]).read_text(encoding="utf-8")
    # Previously both collapsed to "## 2026.md"; now each carries its subdir.
    assert "## _meta/friction-log/2026.md" in digest
    assert "## _meta/reflections/2026.md" in digest
    assert "friction body" in digest
    assert "reflection body" in digest


def test_feedback_export_redacts_user_named_subdir_but_not_structural_prefix(tmp_path) -> None:
    """Leak regression: a codename in a user-named nested subdir must be redacted.

    The heading carries the vault-relative path, so a project codename living in
    a user-created directory under a sweep dir (`_meta/reflections/AcmeCorp-notes/`)
    would otherwise leak into a digest built for anonymized sharing. The fixed
    structural prefix (`_meta/reflections/`) stays intact; everything below it,
    including the codename subdir, is redacted.
    """

    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    nested = vault / "_meta" / "reflections" / "AcmeCorp-notes"
    nested.mkdir(parents=True)
    (nested / "x.md").write_text("Session notes.\n", encoding="utf-8")
    redact = tmp_path / "redact.txt"
    redact.write_text("AcmeCorp\n", encoding="utf-8")

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
    assert "AcmeCorp" not in digest  # the codename never leaks through the heading
    assert "## _meta/reflections/[REDACTED]-notes/x.md" in digest  # prefix intact, subdir redacted
    assert payload["redactions_applied"] == 1
