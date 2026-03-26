from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, normalize_path, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.errors import CarrelError
from carrel.models import FileResult
from carrel.vault.organize import sort_inbox
from carrel.vault.scaffold import scaffold_vault
from carrel.vault.templates import read_template

app = typer.Typer(help="Vault setup and management")
console = Console()


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
        target = target_dir / f"{name}.md"
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
