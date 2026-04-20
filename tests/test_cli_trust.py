from __future__ import annotations

import json

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import AutomationConfig, ResearcherProfile, TrustLevel

runner = CliRunner()


def _write_profile(vault, trust_level: TrustLevel) -> None:
    carrel_dir = vault / ".carrel"
    carrel_dir.mkdir(parents=True, exist_ok=True)
    profile = ResearcherProfile(
        automation=AutomationConfig(trust_level=trust_level),
    )
    (carrel_dir / "environment.json").write_text(
        profile.model_dump_json(indent=2),
        encoding="utf-8",
    )


def test_trust_check_allows_consultative_action(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault, TrustLevel.CONSULTATIVE)

    result = runner.invoke(
        app,
        ["trust", "check", "automation:propose", "--vault", str(vault)],
    )

    assert result.exit_code == 0


def test_trust_check_rejects_action_below_current_trust(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault, TrustLevel.ADVISORY)

    result = runner.invoke(
        app,
        ["trust", "check", "automation:propose", "--vault", str(vault)],
    )

    assert result.exit_code == 1
    assert "automation:propose" in result.stderr
    assert "consultative" in result.stderr
    assert "advisory" in result.stderr


def test_trust_list_json_returns_all_actions(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault, TrustLevel.DELEGATED)

    result = runner.invoke(
        app,
        ["trust", "list", "--vault", str(vault), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload) == 7
    assert payload["vault:reorganize"] == {
        "required_trust": "partnership",
        "allowed": False,
    }


def test_trust_show_json_returns_current_trust_level(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault, TrustLevel.DELEGATED)

    result = runner.invoke(
        app,
        ["trust", "show", "--vault", str(vault), "--format", "json"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"trust_level": "delegated"}


def test_trust_commands_require_environment_json(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)

    result = runner.invoke(app, ["trust", "show", "--vault", str(vault)])

    assert result.exit_code == 1
    assert "No environment.json found" in result.stderr
