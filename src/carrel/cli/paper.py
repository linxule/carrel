from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, normalize_path, resolve_cloud_consent, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.convert.adapters.liteparse import convert_with_liteparse
from carrel.convert.adapters.markdownify import convert_with_markdownify
from carrel.convert.adapters.mineru import convert_with_mineru
from carrel.convert.filer import file_paper
from carrel.convert.router import select_convert_tool
from carrel.env.audit import audit
from carrel.env.profile import read_profile
from carrel.errors import CarrelError, ToolNotConfigured
from carrel.models import ConvertResult, ConvertTool, Sensitivity

app = typer.Typer(help="Paper conversion and listing")
console = Console()


async def _convert(file: Path, tool: ConvertTool) -> tuple[str, dict]:
    if tool == ConvertTool.LITEPARSE:
        return await convert_with_liteparse(file)
    if tool == ConvertTool.MINERU:
        api_key = os.environ.get("MINERU_API_KEY")
        if not api_key:
            raise ToolNotConfigured("mineru", "MINERU_API_KEY")
        return await convert_with_mineru(file=file, api_key=api_key)
    return await convert_with_markdownify(file)


async def _select_convert_tool_only(
    file_path: Path,
    vault_path: Path,
    profile,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> ConvertTool:
    audit_result = await audit(vault_path)
    return select_convert_tool(
        file=file_path,
        sensitivity=sensitivity or (profile.sensitivity if profile else Sensitivity.MEDIUM),
        hardware=audit_result.hardware_capability,
        tools=audit_result.tools,
        cloud_consent=resolve_cloud_consent(tool.value if tool else None, profile),
        explicit_tool=tool,
    )


async def _run_convert_pipeline(
    file_path: Path,
    vault_path: Path,
    profile,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> tuple[ConvertTool, str, dict]:
    selected_tool = await _select_convert_tool_only(file_path, vault_path, profile, sensitivity, tool)
    content, metadata = await _convert(file_path, selected_tool)
    return selected_tool, content, metadata


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
            console.print([str(path) for path in papers])
        else:
            for path in papers:
                console.print(path)
    except CarrelError as error:
        emit_carrel_error(error)
