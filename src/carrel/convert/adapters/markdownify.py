from __future__ import annotations

import asyncio
from pathlib import Path

from carrel.errors import ConversionError
from carrel.env.install import install_command_for


async def convert_with_markdownify(source: Path, timeout: int = 30) -> tuple[str, dict]:
    source_path = source.expanduser().resolve()

    try:
        proc = await asyncio.create_subprocess_exec(
            "markitdown",
            str(source_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ConversionError(
            "markitdown is not installed",
            hint=f"Install it: {install_command_for('markitdown')}",
        ) from exc

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise ConversionError("markdownify timed out", hint="Retry with a smaller input or a different tool") from exc

    if proc.returncode != 0:
        raise ConversionError(
            "markitdown failed",
            hint=stderr.decode().strip() or "Check that the source exists and markitdown is installed",
        )
    return stdout.decode().strip(), {}
