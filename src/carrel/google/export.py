from __future__ import annotations

import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

from carrel.errors import ConversionError, ToolNotInstalled
from carrel.env.install import install_command_for
from carrel.safe_path import safe_vault_join

GOOGLE_WORKSPACE_EXPORTS: dict[str, dict[str, tuple[str, str]]] = {
    "document": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/plain", ".txt"),
        "html": ("text/html", ".html"),
    },
    "spreadsheets": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/csv", ".csv"),
        "html": ("text/html", ".html"),
    },
    "presentation": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/plain", ".txt"),
    },
}


def parse_google_workspace_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "docs.google.com":
        raise ConversionError(
            "unsupported Google Workspace URL",
            hint="Use a docs.google.com URL for a Google Doc, Sheet, or Slides file",
        )

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[1] != "d":
        raise ConversionError(
            "unsupported Google Workspace URL",
            hint="Expected a URL like docs.google.com/document/d/<id>/edit",
        )

    kind = parts[0]
    if kind not in GOOGLE_WORKSPACE_EXPORTS:
        raise ConversionError(
            "unsupported Google Workspace file type",
            hint="Supported types are Google Docs, Sheets, and Slides",
        )
    return kind, parts[2]


def export_target_for(url: str, export_format: str, workspace: Path) -> tuple[str, str, Path]:
    kind, file_id = parse_google_workspace_url(url)
    try:
        mime_type, suffix = GOOGLE_WORKSPACE_EXPORTS[kind][export_format]
    except KeyError as exc:
        raise ConversionError(
            "unsupported export format",
            hint=f"{kind} files do not support --export-format {export_format}",
        ) from exc

    export_root = safe_vault_join(workspace, ".carrel", "exports")
    export_root.mkdir(parents=True, exist_ok=True)
    output_path = safe_vault_join(workspace, ".carrel", "exports", f"{file_id}{suffix}")
    return file_id, mime_type, output_path


async def _run_gws(args: list[str], timeout: int) -> tuple[bytes, bytes, int]:
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ToolNotInstalled("gws", install_command_for("gws") or "install gws") from exc

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise ConversionError(
            "gws timed out",
            hint="Retry the export. If authentication just changed, re-run gws auth login -s drive first.",
        ) from exc
    return stdout, stderr, proc.returncode


async def ensure_gws_authenticated(timeout: int = 20) -> None:
    _, stderr, returncode = await _run_gws(
        [
            "gws",
            "drive",
            "about",
            "get",
            "--params",
            json.dumps({"fields": "user"}),
        ],
        timeout=timeout,
    )
    if returncode != 0:
        raise ConversionError(
            "gws not authenticated",
            hint=stderr.decode().strip() or "Run: gws auth login -s drive",
        )


async def export_from_google_workspace(
    url: str,
    workspace: Path,
    export_format: str = "docx",
    timeout: int = 60,
) -> Path:
    file_id, mime_type, output_path = export_target_for(url, export_format, workspace)
    await ensure_gws_authenticated()
    _, stderr, returncode = await _run_gws(
        [
            "gws",
            "drive",
            "files",
            "export",
            "--params",
            json.dumps({"fileId": file_id, "mimeType": mime_type}),
            "-o",
            str(output_path),
        ],
        timeout=timeout,
    )
    if returncode != 0:
        raise ConversionError(
            "gws export failed",
            hint=stderr.decode().strip() or "Check the file URL, Drive permissions, and gws auth",
        )
    return output_path
