from __future__ import annotations

from pathlib import Path

import httpx

from carrel.errors import TranscriptionError


async def transcribe_with_groq(file: Path, api_key: str, timeout: int = 120) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (file.name, file.read_bytes(), "application/octet-stream")}
    data = {"model": "whisper-large-v3-turbo"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
        )
    if response.status_code >= 400:
        raise TranscriptionError(
            "groq request failed",
            hint=f"Groq returned HTTP {response.status_code}. Check GROQ_API_KEY and file format.",
        )
    payload = response.json()
    return payload.get("text") or ""
