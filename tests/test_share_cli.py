from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import ResearcherProfile, Sensitivity

runner = CliRunner()


def _seed_vault(
    tmp_path: Path,
    *,
    name: str | None = "Ada",
    field: str | None = "biology",
    sensitivity: Sensitivity = Sensitivity.MEDIUM,
) -> Path:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    profile = ResearcherProfile(name=name, field=field, sensitivity=sensitivity)
    (vault / ".carrel" / "environment.json").write_text(
        profile.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )
    # Seed some structure for a richer full-mode handbook.
    (vault / "papers").mkdir()
    (vault / "notes" / "threads").mkdir(parents=True)
    (vault / "notes" / "threads" / "boundary-conditions.md").write_text(
        "status: active\n\nWhere does the framework apply?",
        encoding="utf-8",
    )
    (vault / "_meta").mkdir(exist_ok=True)
    (vault / "_meta" / "friction_log.md").write_text(
        "## 2026-04-01\n\nAcme Lab specific frustration around scanned PDFs.\n",
        encoding="utf-8",
    )
    return vault


def test_share_generate_writes_dated_handbook(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "full",
            "--for",
            "jane",
            "--sensitivity",
            "low",
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 0, result.stderr
    target = vault / "_meta" / "handbook" / f"{date.today().isoformat()}-for-jane.md"
    assert target.exists()
    body = target.read_text(encoding="utf-8")
    assert "Ada" in body
    assert "biology" in body
    assert "boundary-conditions.md" in body


def test_share_generate_high_sensitivity_redacts_researcher_and_threads(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "full",
            "--for",
            "New RA",
            "--sensitivity",
            "high",
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["sensitivity"] == "high"
    redactions = payload["redactions_applied"]
    assert "researcher-field-omitted" in redactions
    assert "friction-log-omitted" in redactions
    assert "threads-section-omitted" in redactions
    target = Path(payload["path"])
    assert target.exists()
    body = target.read_text(encoding="utf-8")
    assert "Ada" not in body
    assert "boundary-conditions.md" not in body
    assert "Acme Lab" not in body


def test_share_generate_medium_sensitivity_keeps_thread_titles_only(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "full",
            "--for",
            "co-author",
            "--sensitivity",
            "medium",
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    redactions = payload["redactions_applied"]
    assert "threads-contents-omitted" in redactions
    body = Path(payload["path"]).read_text(encoding="utf-8")
    assert "boundary-conditions.md" in body  # title preserved
    assert "Where does the framework apply?" not in body  # contents redacted


def test_share_generate_rejects_invalid_collaborator_name(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "quick",
            "--for",
            "../escape",
            "--sensitivity",
            "low",
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 1
    assert "Invalid collaborator name" in result.stderr


def test_share_generate_from_stdin_preserves_exact_body_and_canonical_copy(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    approved = "\n# Approved handbook\n\nKeep trailing whitespace.  \n\n"

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "full",
            "--for",
            "New RA",
            "--sensitivity",
            "high",
            "--vault",
            str(vault),
            "--from-stdin",
            "--canonical",
            "--format",
            "json",
        ],
        input=approved,
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    target = Path(payload["path"])
    canonical = Path(payload["canonical_path"])
    assert target.read_text(encoding="utf-8") == approved
    assert canonical == vault / "_meta" / "lab-handbook.md"
    assert canonical.read_text(encoding="utf-8") == approved
    assert payload["redactions_applied"] == []
    assert "Ada" not in approved


def test_share_generate_preflights_canonical_before_dated_write(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    canonical = vault / "_meta" / "lab-handbook.md"
    canonical.mkdir()
    dated = (
        vault
        / "_meta"
        / "handbook"
        / f"{date.today().isoformat()}-for-new-ra.md"
    )

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "full",
            "--for",
            "New RA",
            "--sensitivity",
            "high",
            "--vault",
            str(vault),
            "--from-stdin",
            "--canonical",
        ],
        input="# Approved handbook\n",
    )

    assert result.exit_code == 1
    assert "Invalid vault file target" in result.stderr
    assert canonical.is_dir()
    assert not dated.exists()


def test_share_generate_from_stdin_explain_does_not_write(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    approved = "# Approved handbook\n"

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "full",
            "--for",
            "jane",
            "--sensitivity",
            "medium",
            "--vault",
            str(vault),
            "--from-stdin",
            "--canonical",
            "--explain",
            "--format",
            "json",
        ],
        input=approved,
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["from_stdin"] is True
    assert payload["bytes"] == len(approved.encode("utf-8"))
    assert not Path(payload["would_write"]).exists()
    assert not Path(payload["canonical_would_write"]).exists()


def test_share_generate_from_stdin_rejects_empty_body_and_unknown_mode(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    base_args = [
        "vault",
        "share",
        "generate",
        "--for",
        "jane",
        "--sensitivity",
        "medium",
        "--vault",
        str(vault),
        "--from-stdin",
    ]

    empty = runner.invoke(app, [*base_args, "--mode", "full"], input=" \n")
    unknown = runner.invoke(app, [*base_args, "--mode", "interactive"], input="body")

    assert empty.exit_code == 1
    assert "Empty collaborator handbook received on stdin" in empty.stderr
    assert unknown.exit_code == 1
    assert "Unknown share mode: interactive" in unknown.stderr


def test_share_generate_slug_transliterates_accents_without_collision() -> None:
    """'José' transliterates to 'jose' (NFKD) rather than colliding with 'Jos'."""

    from carrel.share.synthesizer import slug_name

    assert slug_name("José") == "jose"
    assert slug_name("Jos") == "jos"
    assert slug_name("José") != slug_name("Jos")
    # A name that is only accented characters still yields a usable slug.
    assert slug_name("Renée") == "renee"


def test_share_generate_accented_name_produces_transliterated_filename(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "quick",
            "--for",
            "José",
            "--sensitivity",
            "low",
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["path"]).name == f"{date.today().isoformat()}-for-jose.md"


def test_share_generate_without_stdin_can_write_canonical_copy(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "vault",
            "share",
            "generate",
            "--mode",
            "quick",
            "--for",
            "jane",
            "--sensitivity",
            "low",
            "--vault",
            str(vault),
            "--canonical",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["canonical_path"]).read_text(encoding="utf-8") == Path(
        payload["path"]
    ).read_text(encoding="utf-8")
