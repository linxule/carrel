from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, resolve_vault
from carrel.cli.output import OutputFormat
from carrel.env.audit import audit
from carrel.env.validation import (
    EnvironmentValidationReport,
    detect_environment_drift,
    load_environment_payload,
    report_status,
    validate_environment_payload,
)
from carrel.env.profile import read_profile, write_profile
from carrel.errors import CarrelError
from carrel.models import ResearcherProfile

app = typer.Typer(help="Environment audit and profile management")
console = Console()


def _environment_path(vault_path: Path) -> Path:
    return vault_path / ".carrel" / "environment.json"


def _render_validation_report(
    report: EnvironmentValidationReport,
    environment_path: Path,
) -> None:
    marker_drift = [issue for issue in report.drift if issue.check == "markers"]
    environment_drift = [issue for issue in report.drift if issue.check != "markers"]

    console.print(f"Environment validation: {environment_path}")
    console.print("")

    schema_status = "INVALID" if report.errors else "VALID"
    console.print(f"Schema: {schema_status}")
    for issue in report.errors:
        console.print(f"  - {issue.path}: {issue.message}")

    drift_status = "DRIFT" if environment_drift else "VALID"
    console.print(f"Environment: {drift_status}")
    for issue in environment_drift:
        console.print(f"  - {issue.message}")

    marker_status = "DRIFT" if marker_drift else "VALID"
    console.print(f"CLAUDE.md markers: {marker_status}")
    for issue in marker_drift:
        console.print(f"  - {issue.message}")


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
            console.print(f"Platform: {result.os}")
            console.print("")
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


@app.command("validate")
def validate_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        environment_path = _environment_path(vault_path)
        if not environment_path.exists():
            raise CarrelError(
                "No ResearcherProfile found",
                hint=f"Expected {environment_path}. Run `carrel vault init` first.",
            )

        raw_data, payload_errors = load_environment_payload(environment_path)
        profile, validation_errors = validate_environment_payload(environment_path)
        errors = payload_errors or validation_errors

        drift = []
        if raw_data is not None and profile is not None:
            audit_result = asyncio.run(audit(vault_path))
            drift = detect_environment_drift(vault_path, raw_data, profile, audit_result)

        report = EnvironmentValidationReport(
            status=report_status(errors, drift),
            errors=errors,
            drift=drift,
        )

        if fmt == OutputFormat.JSON:
            typer.echo(report.model_dump_json())
        elif fmt == OutputFormat.HUMAN:
            _render_validation_report(report, environment_path)

        exit_code = 1 if report.errors else 2 if report.drift else 0
        raise typer.Exit(code=exit_code)
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
