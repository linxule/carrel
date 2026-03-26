from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, resolve_vault
from carrel.cli.output import OutputFormat
from carrel.env.audit import audit
from carrel.env.profile import read_profile, write_profile
from carrel.errors import CarrelError
from carrel.models import ResearcherProfile

app = typer.Typer(help="Environment audit and profile management")
console = Console()


@app.command("doctor")
def doctor_command(
    project_path: Path | None = typer.Option(None, "--project-path"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        result = asyncio.run(audit(project_path))
        failures = [
            name for name, info in result.tools.binaries.items() if not info.installed
        ] + [
            name for name, info in result.tools.api_keys.items() if not info.configured
        ]

        if fmt == OutputFormat.QUIET:
            raise typer.Exit(code=1 if failures else 0)
        if fmt == OutputFormat.JSON:
            console.print(result.model_dump_json())
        elif fmt == OutputFormat.HUMAN:
            for name, info in result.tools.binaries.items():
                status = "OK" if info.installed else "X"
                detail = info.version or info.path or "missing"
                console.print(f"{name:10} {status} {detail}")
            for name, info in result.tools.api_keys.items():
                status = "OK" if info.configured else "X"
                detail = "configured" if info.configured else f"{info.env_var} not set"
                console.print(f"{name:10} {status} {detail}")
            if result.tools.mcp_servers:
                console.print(f"mcp servers: {', '.join(result.tools.mcp_servers)}")
        raise typer.Exit(code=1 if failures else 0)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("profile")
def profile_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = read_profile(vault_path) or ResearcherProfile()
        profile_path = write_profile(vault_path, profile)
        if fmt == OutputFormat.QUIET:
            console.print(profile_path)
            return
        if fmt == OutputFormat.JSON:
            console.print(profile.model_dump_json())
            return
        console.print(json.dumps({"path": str(profile_path), **profile.model_dump(mode="json")}, indent=2))
    except CarrelError as error:
        emit_carrel_error(error)
