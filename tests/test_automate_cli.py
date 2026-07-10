from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import (
    AutomationConfig,
    AutomationModel,
    AutomationSchedule,
    ResearcherProfile,
    TrustLevel,
)

runner = CliRunner()


def _seed_vault(tmp_path: Path, trust_level: TrustLevel) -> Path:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    profile = ResearcherProfile(
        name="Ada",
        automation=AutomationConfig(trust_level=trust_level),
    )
    (vault / ".carrel" / "environment.json").write_text(
        profile.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )
    return vault


def test_automate_configure_writes_atomic_block_at_consultative(tmp_path) -> None:
    vault = _seed_vault(tmp_path, TrustLevel.CONSULTATIVE)

    result = runner.invoke(
        app,
        [
            "automate",
            "configure",
            "--enabled",
            "--trust-level",
            "consultative",
            "--schedule",
            "daily",
            "--review-cadence",
            "quarterly",
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 0, result.stderr
    profile_data = json.loads(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )
    automation = profile_data["automation"]
    assert automation["enabled"] is True
    assert automation["trust_level"] == "consultative"
    assert automation["schedule"] == "daily"
    assert automation["review_cadence"] == "quarterly"
    assert automation["last_reviewed"] == date.today().isoformat()
    assert not (vault / "_meta" / "automation-prompt.md").exists()
    assert not (vault / "_meta" / "pending-decisions.md").exists()
    assert not (vault / "_meta" / "pending-approvals.md").exists()


def test_automate_configure_denies_advisory_jump_to_delegated(tmp_path) -> None:
    vault = _seed_vault(tmp_path, TrustLevel.ADVISORY)

    result = runner.invoke(
        app,
        [
            "automate",
            "configure",
            "--enabled",
            "--trust-level",
            "delegated",
            "--schedule",
            "daily",
            "--review-cadence",
            "monthly",
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 1
    assert "advisory" in result.stderr
    assert "consultative" in result.stderr
    # Profile is unchanged.
    profile_data = json.loads(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )
    assert profile_data["automation"]["enabled"] is False
    assert profile_data["automation"]["trust_level"] == "advisory"


def test_automate_configure_bootstraps_advisory_to_consultative(tmp_path) -> None:
    # INTENDED CONTRACT (decision 2026-07-10, advisory bootstrap): the
    # Advisory->Consultative transition succeeds with no approval artifact on
    # disk — the skill's interview-approval flow is the contract of record, and
    # the CLI is the mechanical writer. This is the documented exception to
    # "the trust check is the single boundary"; the assertions below (exit 0,
    # trust persisted, no pending-approvals.md) codify that on purpose, not a
    # bug. See src/carrel/cli/automate.py and skills/automation/SKILL.md.
    vault = _seed_vault(tmp_path, TrustLevel.ADVISORY)

    result = runner.invoke(
        app,
        [
            "automate",
            "configure",
            "--enabled",
            "--trust-level",
            "consultative",
            "--schedule",
            "weekly",
            "--review-cadence",
            "quarterly",
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 0, result.stderr
    profile_data = json.loads(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )
    assert profile_data["automation"]["trust_level"] == "consultative"
    assert profile_data["automation"]["enabled"] is True
    assert profile_data["automation"]["schedule"] == "weekly"
    assert profile_data["automation"]["last_reviewed"] == date.today().isoformat()
    assert not (vault / "_meta" / "automation-prompt.md").exists()
    assert not (vault / "_meta" / "pending-decisions.md").exists()
    assert not (vault / "_meta" / "pending-approvals.md").exists()


def test_automate_configure_preserves_existing_capability_booleans(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    seed_profile = ResearcherProfile(
        name="Ada",
        automation=AutomationConfig(
            trust_level=TrustLevel.DELEGATED,
            gap_analysis=True,
            draft_feedback=True,
            schedule=AutomationSchedule.WEEKLY,
            model=AutomationModel.OPUS,
        ),
    )
    (vault / ".carrel" / "environment.json").write_text(
        seed_profile.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "automate",
            "configure",
            "--no-enabled",
            "--trust-level",
            "consultative",
            "--schedule",
            "daily",
            "--review-cadence",
            "biannual",
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 0, result.stderr
    profile_data = json.loads(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )
    automation = profile_data["automation"]
    # Capability booleans seeded on the original profile survive the rewrite.
    assert automation["gap_analysis"] is True
    assert automation["draft_feedback"] is True
    # Model defaults to sonnet (CLI flag default) when not passed.
    assert automation["model"] == "sonnet"
    assert automation["enabled"] is False
    assert automation["schedule"] == "daily"


def test_automate_configure_accepts_capability_boolean_flags(tmp_path) -> None:
    """Skill→CLI contract: automate configure must accept the 7 capability
    booleans the automation SKILL.md documents in its calling pattern.

    Locks the fix for the v0.9.0 contract mismatch where the CLI rejected
    every documented capability flag with Typer's "no such option" error,
    silently breaking any skill-constructed invocation that tried to toggle
    a capability.
    """
    vault = _seed_vault(tmp_path, TrustLevel.CONSULTATIVE)

    result = runner.invoke(
        app,
        [
            "automate",
            "configure",
            "--enabled",
            "--trust-level",
            "consultative",
            "--schedule",
            "daily",
            "--review-cadence",
            "monthly",
            "--inbox-processing",
            "--vault-health",
            "--no-cross-linking",
            "--gap-analysis",
            "--no-draft-feedback",
            "--reflection-synthesis",
            "--no-wiki-maintenance",
            "--vault",
            str(vault),
        ],
    )
    assert result.exit_code == 0, result.stderr
    automation = json.loads(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )["automation"]
    assert automation["inbox_processing"] is True
    assert automation["vault_health"] is True
    assert automation["cross_linking_suggestions"] is False
    assert automation["gap_analysis"] is True
    assert automation["draft_feedback"] is False
    assert automation["reflection_synthesis"] is True
    assert automation["wiki_maintenance"] is False


def test_automate_configure_rejects_symlinked_profile_directory(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside-profile"
    outside.mkdir()
    profile = ResearcherProfile(
        name="Outside",
        automation=AutomationConfig(trust_level=TrustLevel.CONSULTATIVE),
    )
    profile_path = outside / "environment.json"
    original = profile.model_dump_json(indent=2, by_alias=True)
    profile_path.write_text(original, encoding="utf-8")
    (vault / ".carrel").symlink_to(outside, target_is_directory=True)

    result = runner.invoke(
        app,
        [
            "automate",
            "configure",
            "--enabled",
            "--trust-level",
            "consultative",
            "--schedule",
            "daily",
            "--review-cadence",
            "quarterly",
            "--vault",
            str(vault),
        ],
    )

    assert result.exit_code == 1
    assert "Path escapes vault root" in result.stderr
    assert profile_path.read_text(encoding="utf-8") == original
    assert list(outside.iterdir()) == [profile_path]
