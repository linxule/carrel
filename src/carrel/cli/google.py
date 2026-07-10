from __future__ import annotations

import asyncio
import os
import shutil
import time
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, resolve_cloud_consent, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.convert.filer import file_paper
from carrel.convert.pipeline import run_convert_pipeline
from carrel.env.profile import read_profile
from carrel.errors import CarrelError, ConversionError
from carrel.google.export import (
    GOOGLE_WORKSPACE_EXPORTS,
    export_from_google_workspace,
    parse_google_workspace_url,
)
from carrel.models import ConvertResult, ConvertTool, Sensitivity
from carrel.policy.sensitivity import PolicyDecision, select_tool
from carrel.safe_path import safe_vault_join

app = typer.Typer(help="Google Workspace commands")
console = Console()


def _explain_export_target(url: str, export_format: str, vault_path: Path) -> Path:
    """Resolve the export destination purely, without creating .carrel/exports/.

    Keeps `--explain` free of filesystem side effects; the real run creates the
    directory inside export_from_google_workspace().
    """
    kind, file_id = parse_google_workspace_url(url)
    try:
        _mime_type, suffix = GOOGLE_WORKSPACE_EXPORTS[kind][export_format]
    except KeyError as exc:
        raise ConversionError(
            "unsupported export format",
            hint=f"{kind} files do not support --export-format {export_format}",
        ) from exc
    return safe_vault_join(vault_path, ".carrel", "exports", f"{file_id}{suffix}")


def _google_export_policy_decision(
    export_path: Path,
    profile,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> PolicyDecision:
    effective_sensitivity = sensitivity or (profile.sensitivity if profile else Sensitivity.MEDIUM)
    available_tools: list[ConvertTool] = []
    if export_path.suffix.lower() != ".pdf":
        available_tools.append(ConvertTool.MARKDOWNIFY)
    else:
        if tool == ConvertTool.MARKDOWNIFY:
            available_tools.append(ConvertTool.MARKDOWNIFY)
        if shutil.which("lit"):
            available_tools.append(ConvertTool.LITEPARSE)
        if os.environ.get("MINERU_API_KEY"):
            available_tools.append(ConvertTool.MINERU)
        if os.environ.get("MISTRAL_API_KEY"):
            available_tools.append(ConvertTool.MISTRAL_OCR)
    return select_tool(
        requested_tool=tool,
        available_tools=available_tools,
        sensitivity=effective_sensitivity,
        cloud_consent=resolve_cloud_consent(tool.value if tool else None, profile),
        tool_class="convert",
    )


@app.command("export")
def export_command(
    url: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    export_format: str = typer.Option("docx", "--export-format", help="docx|pdf|txt|html"),
    keep_export: bool = typer.Option(
        False,
        "--keep-export",
        help="Keep the raw exported file in .carrel/exports/ after conversion",
    ),
    tool: ConvertTool | None = typer.Option(None, "--tool"),
    sensitivity: Sensitivity | None = typer.Option(None, "--sensitivity"),
    explain: bool = typer.Option(False, "--explain"),
    force: bool = typer.Option(False, "--force"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = read_profile(vault_path)
        effective_sensitivity = sensitivity or (profile.sensitivity if profile else Sensitivity.MEDIUM)
        if explain:
            if effective_sensitivity == Sensitivity.HIGH:
                # A real run always errors on the HIGH gate below, so report the
                # block itself — not a phantom tool selection that never executes.
                console.print(
                    "HIGH sensitivity blocks Google Workspace export "
                    "(contacting Google Drive would send data). No tool would run."
                )
            else:
                export_path = _explain_export_target(url, export_format, vault_path)
                console.print(
                    _google_export_policy_decision(export_path, profile, sensitivity, tool)
                )
            return
        if effective_sensitivity == Sensitivity.HIGH:
            raise CarrelError(
                "HIGH sensitivity blocks Google Workspace export",
                hint="Export locally yourself or lower sensitivity explicitly before contacting Google Drive.",
            )
        started = time.perf_counter()
        async def _export_and_convert():
            exported = await export_from_google_workspace(url, vault_path, export_format)
            selected_tool, content, metadata = await run_convert_pipeline(
                exported, vault_path, profile, sensitivity, tool
            )
            return exported, selected_tool, content, metadata

        exported, selected_tool, content, metadata = asyncio.run(_export_and_convert())
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
        if not keep_export:
            exported.unlink()
            if fmt == OutputFormat.HUMAN:
                console.print(f"Cleaned up raw export: {exported}")
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
