from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from carrel.cli import emit_carrel_error, resolve_vault
from carrel.env.profile import read_profile
from carrel.errors import CarrelError
from carrel.models import TrustLevel
from carrel.trust import is_allowed, list_actions, required_trust

app = typer.Typer(help="Inspect and enforce vault trust permissions")
console = Console()


class TrustOutputFormat(str, Enum):
    HUMAN = "human"
    JSON = "json"


def _current_trust_level(vault: Path) -> TrustLevel:
    profile = read_profile(vault)
    if profile is None:
        path = vault / ".carrel" / "environment.json"
        raise CarrelError(
            "No environment.json found",
            hint=f"Expected {path}. Run `carrel vault init` or `/carrel-setup` first.",
        )
    return profile.automation.trust_level


@app.command("check")
def check_command(
    action: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: TrustOutputFormat = typer.Option(TrustOutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        current = _current_trust_level(vault_path)
        required = required_trust(action)
        allowed = is_allowed(action, current)
        if not allowed:
            raise CarrelError(
                f"Action '{action}' requires trust level '{required.value}'; current is '{current.value}'",
                hint=f"To enable, raise trust to {required.value} via /carrel-automate.",
            )
        if fmt == TrustOutputFormat.JSON:
            console.print(
                json.dumps(
                    {
                        "action": action,
                        "allowed": True,
                        "required_trust": required.value,
                        "trust_level": current.value,
                    }
                )
            )
            return
        console.print(f"Allowed: {action} ({current.value} >= {required.value})")
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("list")
def list_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: TrustOutputFormat = typer.Option(TrustOutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        current = _current_trust_level(vault_path)
        actions = list_actions(current)
        if fmt == TrustOutputFormat.JSON:
            console.print(
                json.dumps(
                    {
                        action: {
                            "required_trust": required.value,
                            "allowed": allowed,
                        }
                        for action, (required, allowed) in actions.items()
                    }
                )
            )
            return

        table = Table()
        table.add_column("Action")
        table.add_column("Required")
        table.add_column("Allowed")
        for action, (required, allowed) in actions.items():
            table.add_row(action, required.value, "yes" if allowed else "no")
        console.print(table)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("show")
def show_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: TrustOutputFormat = typer.Option(TrustOutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        current = _current_trust_level(vault_path)
        if fmt == TrustOutputFormat.JSON:
            console.print(json.dumps({"trust_level": current.value}))
            return
        console.print(f"trust_level: {current.value}")
    except CarrelError as error:
        emit_carrel_error(error)
