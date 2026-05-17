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
