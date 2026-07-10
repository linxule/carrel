from __future__ import annotations

import asyncio
import json
from urllib.parse import urlparse

from carrel.errors import ConversionError, ToolNotInstalled
from carrel.env.install import install_command_for


async def capture_with_defuddle(url: str, timeout: int = 60) -> tuple[str, dict]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "defuddle",
            "parse",
            url,
            "--json",
            "--markdown",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ToolNotInstalled(
            "defuddle", install_command_for("defuddle") or "install defuddle"
        ) from exc

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise ConversionError(
            "defuddle timed out",
            hint="Retry with the URL again or fall back to markitdown for a simpler capture",
        ) from exc

    if proc.returncode != 0:
        raise ConversionError(
            "defuddle failed",
            hint=stderr.decode().strip() or "Check that the URL is reachable and defuddle is installed",
        )

    try:
        payload = json.loads(stdout.decode())
    except json.JSONDecodeError as exc:
        raise ConversionError(
            "defuddle returned invalid JSON",
            hint="Retry the capture. If the site is unusual, try the markitdown fallback.",
        ) from exc

    content = payload.get("contentMarkdown") or payload.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ConversionError(
            "defuddle returned no article content",
            hint="The page may block extraction. Retry or use the markitdown fallback.",
        )

    domain = urlparse(url).netloc.lower()
    metadata = {
        "title": payload.get("title"),
        "author": payload.get("author"),
        "published": payload.get("published"),
        "domain": domain,
        "schema_org_data": payload.get("schemaOrgData"),
    }
    return content.strip(), metadata


async def capture_with_markitdown_url(url: str, timeout: int = 60) -> tuple[str, dict]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "markitdown",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise ToolNotInstalled(
            "markitdown", install_command_for("markitdown") or "install markitdown"
        ) from exc

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise ConversionError(
            "markitdown timed out",
            hint="Retry the URL or install defuddle for cleaner article extraction",
        ) from exc

    if proc.returncode != 0:
        raise ConversionError(
            "markitdown failed",
            hint=stderr.decode().strip() or "Check that the URL is reachable and markitdown is installed",
        )

    content = stdout.decode().strip()
    if not content:
        raise ConversionError("markitdown returned no content", hint="Retry with a different URL")
    return content, {"domain": urlparse(url).netloc.lower()}
