from __future__ import annotations

import asyncio
import os
import shutil
import time
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, normalize_path, resolve_cloud_consent, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.convert.filer import file_paper
from carrel.convert.pipeline import run_convert_pipeline, select_convert_tool_only
from carrel.convert.router import CLOUD_CONVERT_SUFFIXES
from carrel.env.profile import read_profile
from carrel.errors import CarrelError
from carrel.models import ConvertResult, ConvertTool, Sensitivity
from carrel.policy.sensitivity import PolicyDecision, select_tool

app = typer.Typer(help="Paper conversion and listing")
console = Console()


def _convert_policy_decision(
    file_path: Path,
    profile,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> PolicyDecision:
    effective_sensitivity = sensitivity or (profile.sensitivity if profile else Sensitivity.MEDIUM)
    suffix = file_path.suffix.lower()
    # Mirror convert/router.select_convert_tool so --explain matches the real run:
    # an explicit cloud OCR tool on an unsupported suffix is a hard error there, so
    # surface it here too (the sensitivity-gate hook shells out to --explain).
    if tool in CLOUD_CONVERT_SUFFIXES and suffix not in CLOUD_CONVERT_SUFFIXES[tool]:
        supported = ", ".join(sorted(CLOUD_CONVERT_SUFFIXES[tool]))
        raise CarrelError(
            f"{tool.value} does not support '{suffix or file_path.name}' files",
            hint=f"{tool.value} handles {supported}. Use --tool markdownify for other document types.",
        )
    available_tools: list[ConvertTool] = []
    if suffix == ".pdf":
        if tool == ConvertTool.MARKDOWNIFY:
            available_tools.append(ConvertTool.MARKDOWNIFY)
        if shutil.which("lit"):
            available_tools.append(ConvertTool.LITEPARSE)
        if os.environ.get("MINERU_API_KEY"):
            available_tools.append(ConvertTool.MINERU)
        if os.environ.get("MISTRAL_API_KEY"):
            available_tools.append(ConvertTool.MISTRAL_OCR)
    else:
        available_tools.append(ConvertTool.MARKDOWNIFY)
        # Only an explicit cloud request pulls a cloud OCR tool into a non-PDF
        # conversion (suffix support already checked above); the sensitivity
        # matrix still governs whether it is actually selected.
        if tool == ConvertTool.MINERU and os.environ.get("MINERU_API_KEY"):
            available_tools.append(ConvertTool.MINERU)
        if tool == ConvertTool.MISTRAL_OCR and os.environ.get("MISTRAL_API_KEY"):
            available_tools.append(ConvertTool.MISTRAL_OCR)
    return select_tool(
        requested_tool=tool,
        available_tools=available_tools,
        sensitivity=effective_sensitivity,
        cloud_consent=resolve_cloud_consent(tool.value if tool else None, profile),
        tool_class="convert",
    )

@app.command("convert")
def convert_command(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    vault: Path | None = typer.Option(None, "--vault"),
    tool: ConvertTool | None = typer.Option(None, "--tool"),
    sensitivity: Sensitivity | None = typer.Option(None, "--sensitivity"),
    explain: bool = typer.Option(False, "--explain"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        file_path = normalize_path(file)
        vault_path = resolve_vault(vault)
        profile = read_profile(vault_path)
        if explain:
            console.print(_convert_policy_decision(file_path, profile, sensitivity, tool))
            return
        if dry_run:
            selected_tool = asyncio.run(select_convert_tool_only(file_path, vault_path, profile, sensitivity, tool))
            result = ConvertResult(
                path=None,
                tool=selected_tool,
                duration_seconds=0.0,
                metadata={"dry_run": True},
            )
            if fmt == OutputFormat.HUMAN:
                locality = "cloud" if result.tool in {ConvertTool.MINERU, ConvertTool.MISTRAL_OCR} else "local"
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
            run_convert_pipeline(file_path, vault_path, profile, sensitivity, tool)
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
