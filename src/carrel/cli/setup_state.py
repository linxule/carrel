from __future__ import annotations

from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from carrel import __version__
from carrel.cli import emit_carrel_error, resolve_vault
from carrel.errors import CarrelError
from carrel.models import SetupState

app = typer.Typer(help="Manage resumable /carrel-setup state")
console = Console()
VALID_PHASES = {5, 6, 7, 8, 9}
SETUP_STATE_NAME = "setup-state.json"


def _setup_state_path(vault: Path) -> Path:
    return vault / ".carrel" / SETUP_STATE_NAME


def _read_setup_state(vault: Path) -> SetupState:
    path = _setup_state_path(vault)
    if not path.exists():
        raise CarrelError(
            "No setup-state.json found",
            hint=f"Expected {path}. Run `carrel vault init` or `/carrel-setup` first.",
        )
    state = SetupState.model_validate_json(path.read_text(encoding="utf-8"))
    if state.last_completed_phase < 4:
        raise CarrelError(
            f"Malformed setup state at {path}",
            hint="`last_completed_phase` must be between 4 and 9. Run `carrel setup-state reset --confirm` to recover.",
        )
    return state


def _write_setup_state(vault: Path, state: SetupState) -> Path:
    path = _setup_state_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f"{path.name}.tmp"
    tmp_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    tmp_path.replace(path)
    return path


def _append_capability_log(vault: Path, message: str) -> None:
    capability_log = vault / "_meta" / "capability-log.md"
    if not capability_log.exists():
        return
    with capability_log.open("a", encoding="utf-8") as handle:
        handle.write(f"\n- {date.today().isoformat()}: {message}\n")


def _completed_at_for_phase(phase: int) -> str | None:
    return date.today().isoformat() if phase == 9 else None


@app.command("advance")
def advance_command(
    phase: int = typer.Option(..., "--phase", min=5, max=9),
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force", help="Allow rewinding or reapplying the current phase"),
) -> None:
    try:
        if phase not in VALID_PHASES:
            raise CarrelError("Invalid phase", hint="Use one of: 5, 6, 7, 8, 9.")
        vault_path = resolve_vault(vault)
        current = _read_setup_state(vault_path)
        if phase <= current.last_completed_phase and not force:
            raise CarrelError(
                f"Refusing to move from phase {current.last_completed_phase} to {phase}",
                hint="Pass `--force` only when you are intentionally repairing or rewinding setup state.",
            )
        updated = current.model_copy(
            update={
                "last_completed_phase": phase,
                "completed_at": _completed_at_for_phase(phase),
            }
        )
        path = _write_setup_state(vault_path, updated)
        console.print(f"Updated {path} to phase {updated.last_completed_phase}")
    except (CarrelError, ValueError) as error:
        emit_carrel_error(error if isinstance(error, CarrelError) else CarrelError(str(error)))


@app.command("complete")
def complete_command(
    vault: Path | None = typer.Option(None, "--vault"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        current = _read_setup_state(vault_path)
        updated = current.model_copy(
            update={
                "last_completed_phase": 9,
                "completed_at": date.today().isoformat(),
            }
        )
        path = _write_setup_state(vault_path, updated)
        console.print(f"Marked setup complete in {path}")
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("show")
def show_command(
    vault: Path | None = typer.Option(None, "--vault"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        state = _read_setup_state(vault_path)
        console.print_json(state.model_dump_json(indent=2))
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("reset")
def reset_command(
    vault: Path | None = typer.Option(None, "--vault"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm reset back to the post-scaffold state"),
) -> None:
    try:
        if not confirm:
            raise CarrelError(
                "Reset requires explicit confirmation",
                hint="Re-run with `carrel setup-state reset --confirm`.",
            )
        vault_path = resolve_vault(vault)
        previous = _read_setup_state(vault_path)
        updated = SetupState(last_completed_phase=4, version=__version__, completed_at=None)
        path = _write_setup_state(vault_path, updated)
        _append_capability_log(
            vault_path,
            "Reset setup-state.json for recovery "
            f"(from phase {previous.last_completed_phase}, completed_at={previous.completed_at!r}).",
        )
        console.print(f"Reset {path} to phase 4")
    except CarrelError as error:
        emit_carrel_error(error)
