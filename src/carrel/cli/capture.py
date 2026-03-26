from __future__ import annotations

import asyncio
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.convert.adapters.defuddle import capture_with_defuddle, capture_with_markitdown_url
from carrel.convert.frontmatter import render_frontmatter
from carrel.errors import CarrelError, ToolNotInstalled
from carrel.models import FileResult
from carrel.vault.organize import slugify

app = typer.Typer(help="Web capture commands")
console = Console()


def _capture_slug(url: str, title: str | None = None) -> str:
    if title:
        return slugify(title)
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if parts:
        return slugify(parts[-1])
    return slugify(parsed.netloc or url)


def _capture_path(vault: Path, url: str, title: str | None = None) -> Path:
    return (vault / "inbox" / f"{_capture_slug(url, title)}.md").expanduser().resolve()


async def _capture_url(url: str) -> tuple[str, dict, str]:
    try:
        content, metadata = await capture_with_defuddle(url)
        return content, metadata, "defuddle"
    except ToolNotInstalled:
        content, metadata = await capture_with_markitdown_url(url)
        return content, metadata, "markitdown"


@app.command("url")
def capture_url(
    url: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        predicted = _capture_path(vault_path, url)
        if dry_run:
            result = FileResult(path=predicted, action="dry-run", reason="destination preview")
            if fmt == OutputFormat.HUMAN:
                console.print(f"Would capture {url} -> {predicted}")
            else:
                print_result(result, fmt)
            return

        started = time.perf_counter()
        content, metadata, tool_name = asyncio.run(_capture_url(url))
        output_path = _capture_path(vault_path, url, metadata.get("title"))
        existed_before = output_path.exists()
        if existed_before and not force:
            result = FileResult(
                path=output_path,
                action="skipped",
                reason="capture already exists -- pass --force to overwrite",
            )
            if fmt == OutputFormat.HUMAN:
                console.print(f"-> skipped: {output_path} ({result.reason})")
            else:
                print_result(result, fmt)
            return

        payload = {
            "title": metadata.get("title") or output_path.stem.replace("-", " "),
            "source_url": url,
            "author": metadata.get("author"),
            "published": metadata.get("published"),
            "captured": date.today().isoformat(),
            "domain": metadata.get("domain"),
            "capture_tool": tool_name,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_frontmatter(content=content, metadata=payload), encoding="utf-8")
        result = FileResult(
            path=output_path,
            action="overwritten" if force and existed_before else "created",
        )
        if fmt == OutputFormat.HUMAN:
            duration = round(time.perf_counter() - started, 3)
            console.print(f"OK {output_path} ({tool_name}, {duration}s)")
        else:
            print_result(result, fmt)
    except CarrelError as error:
        emit_carrel_error(error)
