from __future__ import annotations

import asyncio
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, normalize_path, resolve_vault
from carrel.cli.output import OutputFormat
from carrel.errors import CarrelError
from carrel.safe_path import safe_vault_join

app = typer.Typer(help="Batch convert or transcribe a folder of files")
console = Console()

DOC_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".xlsx"}
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".mp4", ".webm", ".mov", ".ogg", ".flac"}
URL_LIST_EXTENSION = ".txt"

PENDING_DECISIONS = Path("_meta") / "pending-decisions.md"


@dataclass(frozen=True)
class BatchOutcome:
    file: Path
    action: str  # "converted" | "transcribed" | "skipped" | "failed" | "deferred"
    detail: str


def _carrel_executable() -> list[str]:
    """Return argv prefix for invoking the carrel CLI as a subprocess.

    Prefers an on-PATH ``carrel`` binary; falls back to invoking the typer
    app through the current Python interpreter (``python -c "...app()"``) so
    tests and isolated runners hit the same entrypoint without needing the
    console script installed.
    """
    binary = shutil.which("carrel")
    if binary:
        return [binary]
    return [
        sys.executable,
        "-c",
        "from carrel.cli.main import app; app()",
    ]


def _enumerate(folder: Path, extensions: set[str], *, include_url_lists: bool = False) -> list[Path]:
    files: list[Path] = []
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in extensions:
            files.append(path)
        elif include_url_lists and suffix == URL_LIST_EXTENSION:
            files.append(path)
    return files


async def _dispatch(argv: list[str], *, timeout: int = 600) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise CarrelError(
            f"Subprocess timed out after {timeout}s: {' '.join(argv)}",
            hint="Increase --timeout or run the file individually to investigate.",
        )
    return (
        proc.returncode if proc.returncode is not None else 1,
        stdout.decode("utf-8", errors="replace"),
        stderr.decode("utf-8", errors="replace"),
    )


def _append_pending_decision(vault: Path, today: str, body: str) -> None:
    """Append a pending-decision row, deduplicating by exact body match.

    Re-runs of `carrel batch ... --unattended` against the same failing
    inputs would otherwise stack duplicate checklist rows. We dedupe on
    the (date, body) pair: if an identical row already exists for today,
    skip the append. Cleared/checked-off rows from prior days are kept
    so the researcher's history stays auditable.
    """
    pending_path = safe_vault_join(vault, *PENDING_DECISIONS.parts)
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    header = "# Pending Decisions\n\n"
    row = f"- [ ] **{today}**: {body}\n"
    if pending_path.exists():
        existing = pending_path.read_text(encoding="utf-8")
        if row in existing:
            return
    else:
        pending_path.write_text(header, encoding="utf-8")
    with pending_path.open("a", encoding="utf-8") as handle:
        handle.write(row)


def _read_urls(path: Path) -> list[str]:
    urls: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return urls
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


async def _run_convert_batch(
    folder: Path,
    vault: Path,
    *,
    unattended: bool,
    timeout: int,
    explain: bool,
) -> list[BatchOutcome]:
    files = _enumerate(folder, DOC_EXTENSIONS)
    outcomes: list[BatchOutcome] = []
    today = date.today().isoformat()
    carrel = _carrel_executable()
    for file in files:
        argv = [*carrel, "paper", "convert", str(file), "--vault", str(vault)]
        if explain:
            argv.append("--explain")
        try:
            returncode, stdout, stderr = await _dispatch(argv, timeout=timeout)
        except CarrelError as error:
            if unattended:
                _append_pending_decision(vault, today, f"`{file.name}` — {error.message}")
                outcomes.append(BatchOutcome(file=file, action="deferred", detail=error.message))
                continue
            raise
        if returncode == 0:
            outcomes.append(
                BatchOutcome(file=file, action="converted", detail=stdout.strip() or "ok")
            )
        else:
            detail = (stderr or stdout).strip()
            if unattended:
                _append_pending_decision(vault, today, f"`{file.name}` — convert failed: {detail}")
                outcomes.append(BatchOutcome(file=file, action="deferred", detail=detail))
            else:
                outcomes.append(BatchOutcome(file=file, action="failed", detail=detail))
    return outcomes


async def _run_transcribe_batch(
    folder: Path,
    vault: Path,
    *,
    unattended: bool,
    timeout: int,
    explain: bool,
    kind: str | None,
) -> list[BatchOutcome]:
    files = _enumerate(folder, AUDIO_EXTENSIONS, include_url_lists=True)
    outcomes: list[BatchOutcome] = []
    today = date.today().isoformat()
    carrel = _carrel_executable()
    for file in files:
        sources: list[str] = []
        if file.suffix.lower() == URL_LIST_EXTENSION:
            urls = _read_urls(file)
            if not urls:
                if unattended:
                    _append_pending_decision(
                        vault, today, f"`{file.name}` — URL list is empty"
                    )
                    outcomes.append(
                        BatchOutcome(file=file, action="deferred", detail="empty URL list")
                    )
                else:
                    outcomes.append(
                        BatchOutcome(file=file, action="failed", detail="empty URL list")
                    )
                continue
            sources.extend(urls)
        else:
            sources.append(str(file))
        for source in sources:
            argv = [*carrel, "transcript", "create", source, "--vault", str(vault)]
            if kind:
                argv.extend(["--kind", kind])
            if explain:
                argv.append("--explain")
            try:
                returncode, stdout, stderr = await _dispatch(argv, timeout=timeout)
            except CarrelError as error:
                if unattended:
                    _append_pending_decision(
                        vault, today, f"`{source}` — {error.message}"
                    )
                    outcomes.append(
                        BatchOutcome(file=file, action="deferred", detail=error.message)
                    )
                    continue
                raise
            if returncode == 0:
                outcomes.append(
                    BatchOutcome(file=file, action="transcribed", detail=stdout.strip() or "ok")
                )
            else:
                detail = (stderr or stdout).strip()
                if unattended:
                    _append_pending_decision(
                        vault, today, f"`{source}` — transcribe failed: {detail}"
                    )
                    outcomes.append(BatchOutcome(file=file, action="deferred", detail=detail))
                else:
                    outcomes.append(BatchOutcome(file=file, action="failed", detail=detail))
    return outcomes


def _print_outcomes(outcomes: list[BatchOutcome], fmt: OutputFormat) -> None:
    if fmt == OutputFormat.JSON:
        typer.echo(
            json.dumps(
                [
                    {"file": str(o.file), "action": o.action, "detail": o.detail}
                    for o in outcomes
                ]
            )
        )
        return
    if fmt == OutputFormat.QUIET:
        for outcome in outcomes:
            typer.echo(str(outcome.file))
        return
    if not outcomes:
        console.print("No matching files found.")
        return
    for outcome in outcomes:
        console.print(f"[{outcome.action}] {outcome.file}: {outcome.detail}")


def _resolve_folder(folder: Path) -> Path:
    resolved = normalize_path(folder)
    if not resolved.exists():
        raise CarrelError(
            f"Folder not found: {resolved}",
            hint="Pass an existing folder path, e.g., the vault's inbox/.",
        )
    if not resolved.is_dir():
        raise CarrelError(
            f"Not a directory: {resolved}",
            hint="The batch CLI expects a folder, not a single file.",
        )
    return resolved


@app.command("convert")
def convert_command(
    folder: Path = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    unattended: bool = typer.Option(
        False,
        "--unattended",
        help="Write deferred routing decisions to _meta/pending-decisions.md instead of failing.",
    ),
    timeout: int = typer.Option(600, "--timeout", help="Per-file subprocess timeout (seconds)."),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Pass --explain to each carrel paper convert subprocess (no writes).",
    ),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        folder_path = _resolve_folder(folder)
        vault_path = resolve_vault(vault)
        outcomes = asyncio.run(
            _run_convert_batch(
                folder_path,
                vault_path,
                unattended=unattended,
                timeout=timeout,
                explain=explain,
            )
        )
        _print_outcomes(outcomes, fmt)
        if not unattended and any(o.action == "failed" for o in outcomes):
            raise typer.Exit(code=1)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("transcribe")
def transcribe_command(
    folder: Path = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    unattended: bool = typer.Option(
        False,
        "--unattended",
        help="Write deferred routing decisions to _meta/pending-decisions.md instead of failing.",
    ),
    timeout: int = typer.Option(900, "--timeout", help="Per-file subprocess timeout (seconds)."),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Pass --explain to each carrel transcript create subprocess (no writes).",
    ),
    kind: str | None = typer.Option(
        None,
        "--kind",
        help="Transcript kind forwarded to `carrel transcript create --kind`: interview | meeting | lecture | recording.",
    ),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        folder_path = _resolve_folder(folder)
        vault_path = resolve_vault(vault)
        outcomes = asyncio.run(
            _run_transcribe_batch(
                folder_path,
                vault_path,
                unattended=unattended,
                timeout=timeout,
                explain=explain,
                kind=kind,
            )
        )
        _print_outcomes(outcomes, fmt)
        if not unattended and any(o.action == "failed" for o in outcomes):
            raise typer.Exit(code=1)
    except CarrelError as error:
        emit_carrel_error(error)
