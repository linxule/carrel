from __future__ import annotations

import httpx

from carrel.errors import TranscriptionError


async def transcribe_with_gemini(
    youtube_url: str,
    api_key: str,
    prompt: str = "Transcribe this video with timestamps and speaker labels.",
    timeout: int = 300,
) -> str:
    body = {
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "video", "uri": youtube_url},
                ],
            }
        ],
        "model": "gemini-3.5-flash",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            headers={"x-goog-api-key": api_key},
            json=body,
        )
    if response.status_code >= 400:
        raise TranscriptionError(
            "gemini request failed",
            hint=f"Gemini returned HTTP {response.status_code}. Check GEMINI_API_KEY and URL access.",
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise TranscriptionError(
            "gemini returned invalid JSON",
            hint="may be rate-limited or returning an HTML error page; try again or check API status",
        ) from exc
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    try:
        return payload["output"][0]["content"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise TranscriptionError(
            "gemini response was missing transcript content",
            hint="Retry the request. Check that the YouTube URL is publicly accessible.",
        ) from exc
