from __future__ import annotations

import asyncio
import json
from pathlib import Path

from carrel.errors import ConversionError, ToolNotInstalled
from carrel.env.install import install_command_for


async def convert_with_liteparse(file: Path, timeout: int = 30) -> tuple[str, dict]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "lit",
            "parse",
            str(file),
            "--format",
            "markdown",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ToolNotInstalled(
            "liteparse", install_command_for("liteparse") or "install liteparse"
        ) from exc

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise ConversionError(
            "liteparse timed out",
            hint="Retry with a smaller file or try --tool mineru / --tool mistral_ocr when cloud OCR is allowed.",
        ) from exc

    if proc.returncode != 0:
        raise ConversionError(
            "liteparse failed",
            hint=(stderr.decode().strip() or "Check that the input file is a readable PDF"),
        )

    text = stdout.decode().strip()
    metadata = {"pages": None}
    if text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text, metadata
        content = payload.get("markdown") or payload.get("text") or text
        metadata["pages"] = payload.get("pages")
        return content, metadata
    return text, metadata
