from __future__ import annotations

import asyncio
import json
import re
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from carrel.cli import emit_carrel_error, normalize_path, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.env.audit import audit
from carrel.env.platform import detect_platform
from carrel.env.profile import read_profile
from carrel.errors import CarrelError
from carrel.models import FileResult
from carrel.vault.automation_prompt import render_automation_prompt
from carrel.vault.dashboard import collect_activity_stats, render_dashboard
from carrel.vault.markers import ensure_markers, parse_markers
from carrel.vault.organize import sort_inbox
from carrel.vault.scaffold import scaffold_vault
from carrel.vault.sync import compare_markers, marker_values
from carrel.vault.templates import read_template, render_cheat_sheet

app = typer.Typer(help="Vault setup and management")
console = Console()


def _safe_slug(name: str) -> str:
    if ".." in name or "/" in name or "\\" in name:
        raise CarrelError(
            "Invalid note name",
            hint="Path traversal is not allowed. Use a note name, not a path.",
        )
    normalized = (
        name.lower().replace(" ", "_").replace("/", "").replace("\\", "").replace(".", "")
    )
    normalized = normalized.strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    if not normalized:
        raise CarrelError(
            "Invalid note name",
            hint="Use letters, numbers, or spaces so Carrel can create a safe filename.",
        )
    return normalized


def _require_profile(vault_path: Path):
    profile_path = vault_path / ".carrel" / "environment.json"
    if not profile_path.exists():
        raise CarrelError(
            "No ResearcherProfile found",
            hint=f"Expected {profile_path}. Run `carrel vault init` first.",
        )
    profile = read_profile(vault_path)
    if profile is None:
        raise CarrelError(
            "No ResearcherProfile found",
            hint=f"Expected {profile_path}. Run `carrel vault init` first.",
        )
    return profile


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f"{path.name}.tmp"
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def _render_drift_table(drifts: list[dict[str, str]]) -> None:
    table = Table()
    table.add_column("Field")
    table.add_column("CLAUDE.md")
    table.add_column("environment.json")
    for drift in drifts:
        table.add_row(drift["field"], drift["marker"], drift["profile"])
    console.print(table)


@app.command("init")
def init_command(
    path: Path = typer.Argument(...),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        result = scaffold_vault(normalize_path(path))
        if fmt == OutputFormat.HUMAN:
            console.print(f"Created vault at {result.vault}")
            console.print(f"  profile: {result.profile_path}")
            console.print(f"  created: {len(result.created)}")
            console.print(f"  skipped: {len(result.skipped)}")
        else:
            print_result(result, fmt, quiet_field="vault")
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("new")
def new_command(
    name: str = typer.Argument(...),
    template: str = typer.Option("meeting", "--template"),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        mapping = {
            "paper-notes": vault_path / "notes",
            "meeting": vault_path / "notes",
            "reflection": vault_path / "_meta" / "reflections",
            "daily": vault_path / "notes",
        }
        template_name = f"{template}.md"
        body = read_template(template_name).replace("{{date}}", date.today().isoformat())
        target_dir = mapping.get(template, vault_path / "notes")
        target = target_dir / f"{_safe_slug(name)}.md"
        if target.exists():
            result = FileResult(path=target, action="skipped", reason="already exists")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            result = FileResult(path=target, action="created")
        print_result(result, fmt)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("search")
def search_command(
    query: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        matches = []
        for path in sorted(vault_path.rglob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if query.lower() in text.lower():
                matches.append(str(path))
        if fmt == OutputFormat.JSON:
            console.print(json.dumps(matches))
        else:
            for match in matches:
                console.print(match)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("status")
def status_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        counts = {
            "papers": len(list((vault_path / "papers").glob("*/paper.md"))),
            "notes": len(list((vault_path / "notes").glob("*.md"))),
            "transcripts": len(list((vault_path / "transcripts").glob("*.md"))),
            "inbox": len(list((vault_path / "inbox").glob("*"))),
        }
        if fmt == OutputFormat.QUIET:
            typer.echo(str(vault_path))
            return
        if fmt == OutputFormat.JSON:
            console.print(json.dumps({"vault": str(vault_path), **counts}))
            return
        console.print(f"Vault: {vault_path}")
        for name, count in counts.items():
            console.print(f"  {name}/ {count} files")
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("organize")
def organize_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        suggestions = sort_inbox(vault_path)
        if fmt == OutputFormat.JSON:
            console.print(json.dumps(suggestions))
            return
        for suggestion in suggestions:
            if fmt == OutputFormat.QUIET:
                console.print(suggestion["destination"])
            else:
                console.print(f'{suggestion["source"]} -> {suggestion["destination"]}')
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("cheatsheet")
def cheatsheet_command(
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing cheat sheet"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Regenerate _meta/cheat_sheet.md from the current ResearcherProfile."""
    try:
        vault_path = resolve_vault(vault)
        profile_path = vault_path / ".carrel" / "environment.json"
        if not profile_path.exists():
            raise CarrelError(
                "No ResearcherProfile found",
                hint=f"Expected {profile_path}. Run `carrel vault init` first.",
            )
        profile = read_profile(vault_path)
        if profile is None:
            raise CarrelError(
                "No ResearcherProfile found",
                hint=f"Expected {profile_path}. Run `carrel vault init` first.",
            )
        cheat_sheet = vault_path / "_meta" / "cheat_sheet.md"
        existed = cheat_sheet.exists()
        if existed and not force:
            result = FileResult(
                path=cheat_sheet,
                action="skipped",
                reason="cheat sheet already exists; pass --force to overwrite",
            )
        else:
            cheat_sheet.parent.mkdir(parents=True, exist_ok=True)
            try:
                cheat_sheet_platform = asyncio.run(audit(vault_path)).platform
            except Exception:
                cheat_sheet_platform = detect_platform()
            cheat_sheet.write_text(
                render_cheat_sheet(vault_path, profile, cheat_sheet_platform),
                encoding="utf-8",
            )
            result = FileResult(path=cheat_sheet, action="updated" if existed else "created")
        print_result(result, fmt)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("dashboard")
def dashboard_command(
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing dashboard"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        dashboard_path = vault_path / "_meta" / "my-environment.md"
        existed = dashboard_path.exists()
        if existed and not force:
            raise CarrelError(
                "Dashboard already exists",
                hint=f"{dashboard_path} exists; pass --force to overwrite.",
            )

        audit_result = asyncio.run(audit(vault_path))
        activity = collect_activity_stats(vault_path)
        content = render_dashboard(profile, audit_result, activity).replace(
            "`(set by CLI at write time)`",
            f"`{vault_path}`",
        )
        _atomic_write(dashboard_path, content)
        print_result(
            FileResult(path=dashboard_path, action="updated" if existed else "created"),
            fmt,
        )
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("automation-prompt")
def automation_prompt_command(
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing prompt"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        prompt_path = vault_path / "_meta" / "automation-prompt.md"
        existed = prompt_path.exists()
        if existed and not force:
            raise CarrelError(
                "Automation prompt already exists",
                hint=f"{prompt_path} exists; pass --force to overwrite.",
            )

        _atomic_write(prompt_path, render_automation_prompt(profile, profile.automation))
        print_result(
            FileResult(path=prompt_path, action="updated" if existed else "created"),
            fmt,
        )
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("check-sync")
def check_sync_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        claude_path = vault_path / "CLAUDE.md"
        if not claude_path.exists():
            raise CarrelError(
                "No CLAUDE.md found",
                hint=f"Expected {claude_path}. Run `/carrel-setup` or create it first.",
            )

        markers = parse_markers(claude_path.read_text(encoding="utf-8"))
        if not markers:
            if fmt != OutputFormat.QUIET:
                console.print(
                    "No carrel markers found. Run `carrel vault add-markers` to enable sync checking."
                )
            raise typer.Exit(code=0)

        drifts = compare_markers(profile, markers)

        if fmt == OutputFormat.JSON:
            console.print(json.dumps({"drift": drifts, "ok": not drifts}))
        elif fmt == OutputFormat.HUMAN:
            if drifts:
                console.print("Profile drift detected between CLAUDE.md markers and environment.json.")
                _render_drift_table(drifts)
            else:
                console.print("No profile drift detected.")

        raise typer.Exit(code=1 if drifts else 0)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("add-markers")
def add_markers_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        claude_path = vault_path / "CLAUDE.md"
        if not claude_path.exists():
            raise CarrelError(
                "No CLAUDE.md found",
                hint=f"Expected {claude_path}. Run `/carrel-setup` or create it first.",
            )

        original = claude_path.read_text(encoding="utf-8")
        updated = ensure_markers(original, marker_values(profile))
        action = "updated" if updated != original else "skipped"
        if updated != original:
            _atomic_write(claude_path, updated)
        print_result(
            FileResult(
                path=claude_path,
                action=action,
                reason=None if action == "updated" else "all markers already present",
            ),
            fmt,
        )
    except CarrelError as error:
        emit_carrel_error(error)
