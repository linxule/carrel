from __future__ import annotations

import asyncio
import time
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, normalize_path, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.convert.filer import file_paper
from carrel.convert.pipeline import (
    run_convert_pipeline as run_convert_pipeline_for_file,
)
from carrel.convert.pipeline import (
    select_convert_tool_only as select_convert_tool_only_for_file,
)
from carrel.env.profile import read_profile
from carrel.errors import CarrelError
from carrel.models import ConvertResult, ConvertTool, Sensitivity

app = typer.Typer(help="Paper conversion and listing")
console = Console()


async def _select_convert_tool_only(
    file_path: Path,
    vault_path: Path,
    profile,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> ConvertTool:
    return await select_convert_tool_only_for_file(file_path, vault_path, profile, sensitivity, tool)


async def _run_convert_pipeline(
    file_path: Path,
    vault_path: Path,
    profile,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> tuple[ConvertTool, str, dict]:
    return await run_convert_pipeline_for_file(file_path, vault_path, profile, sensitivity, tool)


@app.command("convert")
def convert_command(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    vault: Path | None = typer.Option(None, "--vault"),
    tool: ConvertTool | None = typer.Option(None, "--tool"),
    sensitivity: Sensitivity | None = typer.Option(None, "--sensitivity"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        file_path = normalize_path(file)
        vault_path = resolve_vault(vault)
        profile = read_profile(vault_path)
        if dry_run:
            selected_tool = asyncio.run(
                _select_convert_tool_only(file_path, vault_path, profile, sensitivity, tool)
            )
            result = ConvertResult(
                path=None,
                tool=selected_tool,
                duration_seconds=0.0,
                metadata={"dry_run": True},
            )
            if fmt == OutputFormat.HUMAN:
                locality = "cloud" if result.tool == ConvertTool.MINERU else "local"
                console.print(
                    f"Would convert {file_path.name} -> papers/<extracted-name>/paper.md "
                    f"({result.tool.value}, {locality})\n"
                    f"Destination determined after metadata extraction"
                )
            else:
                print_result(result, fmt)
            return

        started = time.perf_counter()
        selected_tool, content, metadata = asyncio.run(
            _run_convert_pipeline(file_path, vault_path, profile, sensitivity, tool)
        )
        filed = file_paper(
            content=content,
            metadata=metadata,
            vault=vault_path,
            source_file=file_path,
            tool=selected_tool,
            force=force,
        )
        result = ConvertResult(
            path=filed.path,
            tool=selected_tool,
            pages=metadata.get("pages"),
            duration_seconds=round(time.perf_counter() - started, 3),
            skipped=filed.action == "skipped",
            metadata={"action": filed.action, "reason": filed.reason, **metadata},
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


@app.command("list")
def list_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        papers = sorted((vault_path / "papers").glob("*/paper.md"))
        if fmt == OutputFormat.JSON:
            import json
            print(json.dumps([str(path) for path in papers]))
        else:
            for path in papers:
                console.print(path)
    except CarrelError as error:
        emit_carrel_error(error)
