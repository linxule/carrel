from __future__ import annotations

from pathlib import Path

import httpx

from carrel.errors import ConversionError


async def convert_with_mineru(file: Path, api_key: str, timeout: int = 120) -> tuple[str, dict]:
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (file.name, file.read_bytes(), "application/pdf")}
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post("https://api.mineru.net/v1/parse", headers=headers, files=files)
    if response.status_code >= 400:
        raise ConversionError(
            "mineru request failed",
            hint=f"Mineru returned HTTP {response.status_code}. Check MINERU_API_KEY and file contents.",
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise ConversionError(
            "mineru returned invalid JSON",
            hint="may be rate-limited or returning an HTML error page; try again or check API status",
        ) from exc
    return payload.get("markdown") or payload.get("text") or "", payload
