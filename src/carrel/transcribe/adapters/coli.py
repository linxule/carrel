from __future__ import annotations

import asyncio
from pathlib import Path

from carrel.errors import ToolNotInstalled, TranscriptionError
from carrel.env.install import install_command_for


async def transcribe_with_coli(
    file: Path,
    model: str = "sensevoice",
    json_output: bool = False,
    timeout: int = 300,
) -> str:
    args = ["coli", "asr", str(file), "--model", model]
    if json_output:
        args.append("--json")

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ToolNotInstalled("coli", install_command_for("coli") or "install coli") from exc

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise TranscriptionError("coli timed out", hint="Retry with --timeout for long recordings") from exc

    if proc.returncode != 0:
        raise TranscriptionError(
            "coli failed",
            hint=stderr.decode().strip() or "Check ffmpeg, input format, and local model availability",
        )
    return stdout.decode().strip()
