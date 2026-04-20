from __future__ import annotations

import json
from datetime import date

from typer.testing import CliRunner

from carrel import __version__
from carrel.cli.main import app
from carrel.models import SetupState

runner = CliRunner()


def _write_setup_state(vault, state: SetupState | dict) -> None:
    carrel_dir = vault / ".carrel"
    carrel_dir.mkdir(parents=True, exist_ok=True)
    raw = state if isinstance(state, dict) else json.loads(state.model_dump_json())
    (carrel_dir / "setup-state.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")


def test_setup_state_complete_then_show_round_trip(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_setup_state(vault, SetupState(last_completed_phase=4, version=__version__))

    complete = runner.invoke(app, ["setup-state", "complete", "--vault", str(vault)])
    assert complete.exit_code == 0

    show = runner.invoke(app, ["setup-state", "show", "--vault", str(vault)])
    assert show.exit_code == 0
    assert '"last_completed_phase": 9' in show.stdout
    assert date.today().isoformat() in show.stdout


def test_setup_state_show_rejects_malformed_phase_two(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_setup_state(
        vault,
        {
            "last_completed_phase": 2,
            "version": __version__,
            "completed_at": None,
        },
    )

    result = runner.invoke(app, ["setup-state", "show", "--vault", str(vault)])

    assert result.exit_code == 1
    assert "Malformed setup state" in result.stderr


def test_setup_state_advance_rejects_regression_without_force(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_setup_state(vault, SetupState(last_completed_phase=7, version=__version__))

    result = runner.invoke(
        app,
        ["setup-state", "advance", "--phase", "5", "--vault", str(vault)],
    )

    assert result.exit_code == 1
    assert "Refusing to move from phase 7 to 5" in result.stderr


def test_setup_state_complete_is_idempotent(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_setup_state(vault, SetupState(last_completed_phase=8, version=__version__))

    first = runner.invoke(app, ["setup-state", "complete", "--vault", str(vault)])
    second = runner.invoke(app, ["setup-state", "complete", "--vault", str(vault)])

    assert first.exit_code == 0
    assert second.exit_code == 0
    stored = SetupState.model_validate_json(
        (vault / ".carrel" / "setup-state.json").read_text(encoding="utf-8")
    )
    assert stored.last_completed_phase == 9
    assert stored.completed_at == date.today().isoformat()
