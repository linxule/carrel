from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, normalize_path, resolve_vault
from carrel.cli.output import OutputFormat
from carrel.errors import CarrelError
from carrel.migrate.runner import plan_migrations, write_plugin_state

app = typer.Typer(help="Apply plugin migrations + update plugin-state.json")
console = Console()


def _resolve_plugin_root(plugin_root: Path | None) -> Path:
    if plugin_root is not None:
        return normalize_path(plugin_root)
    env_value = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_value:
        return normalize_path(Path(env_value))
    raise CarrelError(
        "Plugin root not specified",
        hint="Pass --plugin-root /path/to/plugin, or set CLAUDE_PLUGIN_ROOT in your environment.",
    )


@app.command("apply")
def apply_command(
    plugin_root: Path | None = typer.Option(
        None,
        "--plugin-root",
        help="Path to the installed plugin (defaults to $CLAUDE_PLUGIN_ROOT)",
    ),
    vault: Path | None = typer.Option(None, "--vault"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the migration plan without writing plugin-state.json",
    ),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Compute the pending migration list; write plugin-state.json on success."""
    try:
        vault_path = resolve_vault(vault)
        plugin_root_path = _resolve_plugin_root(plugin_root)
        plan = plan_migrations(vault_path, plugin_root_path)

        payload = {
            "current_version": plan.current_version,
            "last_seen_version": plan.last_seen_version,
            "first_run": plan.first_run,
            "pending": [
                {
                    "from": entry.from_version,
                    "to": entry.to_version,
                    "file": entry.file,
                    "breaking": entry.breaking,
                    "summary": entry.summary,
                }
                for entry in plan.pending
            ],
        }

        if not dry_run:
            state_path = write_plugin_state(vault_path, plan.current_version)
            payload["plugin_state_path"] = str(state_path)

        if fmt == OutputFormat.JSON:
            typer.echo(json.dumps(payload))
            return

        if fmt == OutputFormat.QUIET:
            typer.echo(plan.current_version)
            return

        if plan.first_run:
            console.print(
                f"First run with version tracking. Recorded plugin_version={plan.current_version}."
            )
        elif not plan.pending:
            console.print(
                f"Up to date (plugin_version={plan.current_version}; last_seen={plan.last_seen_version})."
            )
        else:
            console.print(
                f"Pending migrations: {plan.last_seen_version} -> {plan.current_version}"
            )
            for entry in plan.pending:
                breaking = " [breaking]" if entry.breaking else ""
                summary = f" — {entry.summary}" if entry.summary else ""
                console.print(f"  - {entry.from_version} -> {entry.to_version}{breaking}{summary}")
        if dry_run:
            console.print("(dry-run: plugin-state.json was NOT written)")
    except CarrelError as error:
        emit_carrel_error(error)
