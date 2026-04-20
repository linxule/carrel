from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, normalize_path, resolve_cloud_consent, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.env.audit import audit
from carrel.env.profile import read_profile
from carrel.errors import CarrelError, ToolNotConfigured
from carrel.models import Sensitivity, TranscribeResult, TranscribeTool
from carrel.transcribe.adapters.coli import transcribe_with_coli
from carrel.transcribe.adapters.gemini import transcribe_with_gemini
from carrel.transcribe.adapters.groq import transcribe_with_groq
from carrel.transcribe.adapters.youtube_captions import transcribe_with_youtube_captions
from carrel.transcribe.filer import file_transcript
from carrel.transcribe.router import select_transcribe_tool
from carrel.vault.organize import transcript_filename

app = typer.Typer(help="Transcript creation and listing")
console = Console()


def _is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


async def _transcribe(
    source: str,
    tool: TranscribeTool,
    timeout: int | None,
    speakers: int | None,
) -> tuple[str, dict]:
    effective_timeout = timeout or (
        300 if tool in {TranscribeTool.COLI, TranscribeTool.GROQ, TranscribeTool.GEMINI} else 120
    )
    if tool == TranscribeTool.COLI:
        text = await transcribe_with_coli(Path(source), speakers=speakers, timeout=effective_timeout)
        return text, {}
    if tool == TranscribeTool.GROQ:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ToolNotConfigured("groq", "GROQ_API_KEY")
        text = await transcribe_with_groq(Path(source), api_key=api_key, timeout=effective_timeout)
        return text, {}
    if tool == TranscribeTool.GEMINI:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ToolNotConfigured("gemini", "GEMINI_API_KEY")
        text = await transcribe_with_gemini(source, api_key=api_key, timeout=effective_timeout)
        return text, {}
    if tool == TranscribeTool.YOUTUBE_CAPTIONS:
        return await transcribe_with_youtube_captions(source)
    raise CarrelError(f"Unknown transcribe tool: {tool}")


@app.command("create")
def create_command(
    source: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    tool: TranscribeTool | None = typer.Option(None, "--tool"),
    sensitivity: Sensitivity | None = typer.Option(None, "--sensitivity"),
    kind: str = typer.Option("recording", "--kind"),
    speakers: int | None = typer.Option(None, "--speakers"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    timeout: int | None = typer.Option(None, "--timeout"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        resolved_source = source if _is_url(source) else str(normalize_path(Path(source)))
        vault_path = resolve_vault(vault)
        profile = read_profile(vault_path)
        predicted = vault_path / "transcripts" / transcript_filename(
            source=resolved_source,
            date=time.strftime("%Y-%m-%d"),
            kind=kind,
        )
        if dry_run:
            audit_result = asyncio.run(audit(vault_path))
            selected_tool = select_transcribe_tool(
                source=resolved_source,
                sensitivity=sensitivity or (profile.sensitivity if profile else Sensitivity.MEDIUM),
                hardware=audit_result.hardware_capability,
                tools=audit_result.tools,
                cloud_consent=resolve_cloud_consent(tool.value if tool else None, profile),
                explicit_tool=tool,
            )
            result = TranscribeResult(
                path=predicted,
                tool=selected_tool,
                duration_seconds=0.0,
                metadata={"dry_run": True},
            )
            if fmt == OutputFormat.HUMAN:
                console.print(f"Would transcribe {source} -> {predicted} ({selected_tool.value})")
            else:
                print_result(result, fmt)
            return

        started = time.perf_counter()
        audit_result = asyncio.run(audit(vault_path))
        selected_tool = select_transcribe_tool(
            source=resolved_source,
            sensitivity=sensitivity or (profile.sensitivity if profile else Sensitivity.MEDIUM),
            hardware=audit_result.hardware_capability,
            tools=audit_result.tools,
            cloud_consent=resolve_cloud_consent(tool.value if tool else None, profile),
            explicit_tool=tool,
        )
        content, metadata = asyncio.run(
            _transcribe(resolved_source, selected_tool, timeout, speakers)
        )
        filed = file_transcript(
            content=content,
            metadata=metadata,
            vault=vault_path,
            source=resolved_source,
            tool=selected_tool,
            kind=kind,
            force=force,
        )
        result = TranscribeResult(
            path=filed.path,
            tool=selected_tool,
            duration_seconds=round(time.perf_counter() - started, 3),
            source_duration=metadata.get("duration"),
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
        transcripts = sorted((vault_path / "transcripts").glob("*.md"))
        if fmt == OutputFormat.JSON:
            import json
            print(json.dumps([str(path) for path in transcripts]))
        else:
            for path in transcripts:
                console.print(path)
    except CarrelError as error:
        emit_carrel_error(error)
