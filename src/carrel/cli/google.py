from __future__ import annotations

import asyncio
import time
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.convert.filer import file_paper
from carrel.convert.pipeline import run_convert_pipeline
from carrel.env.profile import read_profile
from carrel.errors import CarrelError
from carrel.google.export import export_from_google_workspace, export_target_for
from carrel.models import ConvertResult, ConvertTool, Sensitivity

app = typer.Typer(help="Google Workspace commands")
console = Console()


@app.command("export")
def export_command(
    url: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    export_format: str = typer.Option("docx", "--export-format", help="docx|pdf|txt|html"),
    tool: ConvertTool | None = typer.Option(None, "--tool"),
    sensitivity: Sensitivity | None = typer.Option(None, "--sensitivity"),
    force: bool = typer.Option(False, "--force"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = read_profile(vault_path)
        export_target_for(url, export_format, vault_path)
        started = time.perf_counter()
        exported = asyncio.run(export_from_google_workspace(url, vault_path, export_format))
        selected_tool, content, metadata = asyncio.run(
            run_convert_pipeline(exported, vault_path, profile, sensitivity, tool)
        )
        filed = file_paper(
            content=content,
            metadata={**metadata, "source_url": url},
            vault=vault_path,
            source_file=exported,
            tool=selected_tool,
            force=force,
        )
        result = ConvertResult(
            path=filed.path,
            tool=selected_tool,
            pages=metadata.get("pages"),
            duration_seconds=round(time.perf_counter() - started, 3),
            skipped=filed.action == "skipped",
            metadata={
                "action": filed.action,
                "reason": filed.reason,
                "exported_file": str(exported),
                "source_url": url,
                **metadata,
            },
        )
        if fmt == OutputFormat.HUMAN:
            if filed.action == "skipped":
                console.print(f"-> skipped: {filed.path} ({filed.reason})")
            else:
                suffix = " [overwritten]" if filed.action == "overwritten" else ""
                console.print(
                    f"OK {filed.path} ({selected_tool.value}, {result.duration_seconds}s){suffix}"
                )
        else:
            print_result(result, fmt)
    except CarrelError as error:
        emit_carrel_error(error)
