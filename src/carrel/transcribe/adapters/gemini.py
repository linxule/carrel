from __future__ import annotations

import os

import httpx

from carrel.errors import TranscriptionError

# gemini-3.5-flash is GA (Google I/O 2026) and accepts video/audio input. Override
# with CARREL_GEMINI_MODEL to pin a different Interactions-API model id.
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"

# Interactions output items that carry model reasoning rather than the answer.
# They can lead the `output` array, so transcript text must skip past them.
_REASONING_ITEM_TYPES = {"reasoning", "thought", "thinking"}


async def transcribe_with_gemini(
    youtube_url: str,
    api_key: str,
    prompt: str = "Transcribe this video with timestamps and speaker labels.",
    timeout: int = 300,
    model: str | None = None,
) -> str:
    resolved_model = model or os.environ.get("CARREL_GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
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
        "model": resolved_model,
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

    transcript = _extract_interactions_text(payload)
    if transcript:
        return transcript
    raise TranscriptionError(
        "gemini response was missing transcript content",
        hint="Retry the request. Check that the YouTube URL is publicly accessible.",
    )


def _extract_interactions_text(payload: object) -> str:
    """Pull the assistant transcript out of an Interactions-API response.

    Prefers the top-level ``output_text`` convenience field; otherwise walks every
    ``output`` item and content part, preferring message items and skipping
    reasoning/thought items so a thought-first response does not mask the answer.
    """
    if not isinstance(payload, dict):
        return ""

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = payload.get("output")
    if not isinstance(output, list):
        return ""

    message_texts: list[str] = []
    other_texts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        if item.get("type") in _REASONING_ITEM_TYPES:
            continue
        texts = _texts_from_content(item.get("content"))
        if item.get("type") == "message" or item.get("role") == "assistant":
            message_texts.extend(texts)
        else:
            other_texts.extend(texts)

    chosen = message_texts or other_texts
    return "\n".join(text for text in chosen if text).strip()


def _texts_from_content(content: object) -> list[str]:
    if not isinstance(content, list):
        return []
    texts: list[str] = []
    for part in content:
        if isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
    return texts
