from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .core import CarrelError

MAX_ADAPTER_OUTPUT = 20 * 1024 * 1024


def _resolve_command(command: str) -> str:
    # Use the resolved path (not the bare name) as argv[0] so Windows .cmd
    # shims (bun/npm-installed tools like coli, defuddle) launch correctly
    # via CreateProcess. Falls back to the bare name when not found so the
    # existing FileNotFoundError -> "not installed" CarrelError still fires.
    return shutil.which(command) or command


def _reject_leading_dash(value: str, *, label: str) -> None:
    if value.startswith("-"):
        raise CarrelError(
            f"{label} starts with '-'",
            hint="Values starting with '-' can be parsed as adapter flags; rename or remove the leading dash.",
        )


def run_adapter(command: list[str], *, timeout: int, label: str) -> subprocess.CompletedProcess[str]:
    try:
        proc = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise CarrelError(f"{label} is not installed") from exc
    except subprocess.TimeoutExpired as exc:
        raise CarrelError(f"{label} timed out", hint=f"Timed out after {timeout}s.") from exc
    if len(proc.stdout.encode("utf-8", errors="replace")) > MAX_ADAPTER_OUTPUT:
        raise CarrelError(f"{label} produced too much output", hint="Run the adapter manually or use a smaller input.")
    if len(proc.stderr.encode("utf-8", errors="replace")) > MAX_ADAPTER_OUTPUT:
        raise CarrelError(f"{label} produced too much error output", hint="Run the adapter manually or use a smaller input.")
    if proc.returncode != 0:
        raise CarrelError(f"{label} failed", hint=proc.stderr.strip() or "Check the input and adapter installation.")
    return proc


def capture_url_with_adapter(url: str, *, title: str | None = None) -> tuple[str, dict, str]:
    _reject_leading_dash(url, label="URL")
    for tool, command in [("defuddle", "defuddle"), ("markitdown", "markitdown")]:
        resolved = shutil.which(command)
        if not resolved:
            continue
        argv = [resolved, "parse", url, "--markdown"] if tool == "defuddle" else [resolved, url]
        proc = run_adapter(argv, timeout=60, label=tool)
        if proc.stdout.strip():
            return proc.stdout, {"title": title or url, "domain": ""}, tool
    raise CarrelError("No capture adapter available", hint="Install defuddle/markitdown or pass --content.")


def convert_with_adapter(file_path: Path, tool: str) -> tuple[str, dict]:
    # ingestion.py resolves file_path to an absolute path today, so this
    # never fires in practice — kept as defense-in-depth for future callers
    # that pass a relative or unresolved path straight through.
    _reject_leading_dash(str(file_path), label="file path")
    if tool == "liteparse":
        proc = run_adapter(
            [_resolve_command("lit"), "parse", str(file_path), "--format", "markdown"],
            timeout=30,
            label="liteparse",
        )
        text = proc.stdout.strip()
        metadata = {"pages": None}
        if text.startswith("{"):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                return text, metadata
            metadata["pages"] = payload.get("pages")
            return payload.get("markdown") or payload.get("text") or text, metadata
        return text, metadata
    if tool == "markdownify":
        proc = run_adapter([_resolve_command("markitdown"), str(file_path)], timeout=30, label="markitdown")
        return proc.stdout.strip(), {}
    raise CarrelError(
        "Adapter execution not available in stdlib runtime",
        hint="Cloud adapters require a host adapter; pass --content or use a local tool.",
    )


def transcribe_with_adapter(source: str, tool: str) -> str:
    _reject_leading_dash(source, label="source")
    if tool == "coli":
        proc = run_adapter(
            [_resolve_command("coli"), "asr", source, "--model", "sensevoice"], timeout=300, label="coli"
        )
        return proc.stdout.strip()
    raise CarrelError(
        "Adapter execution not available in stdlib runtime",
        hint="Cloud transcription adapters require a host adapter; pass --content or use coli.",
    )
