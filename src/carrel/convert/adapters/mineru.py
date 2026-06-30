from __future__ import annotations

import asyncio
import io
import zipfile
from pathlib import Path

import httpx

from carrel.errors import ConversionError


async def convert_with_mineru(file: Path, api_key: str, timeout: int = 120) -> tuple[str, dict]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        upload_ticket = await client.post(
            "https://api.mineru.net/api/v4/file-urls/batch",
            headers=headers,
            json={
                "files": [{"name": file.name, "data_id": file.stem}],
                "extra_formats": [],
                "model_version": "vlm",
            },
        )
        ticket = _json_or_raise(upload_ticket)
        data = _payload_data(ticket)
        batch_id = data.get("batch_id") or data.get("batchId")
        upload_url = _first_value(data, "file_urls", "fileUrls", "urls", "upload_urls", "uploadUrls")
        if not isinstance(batch_id, str) or not isinstance(upload_url, str):
            raise ConversionError(
                "mineru upload ticket was missing task data",
                hint="MinerU did not return both a batch id and signed upload URL.",
            )

        upload = await client.put(upload_url, content=file.read_bytes())
        if upload.status_code >= 400:
            raise ConversionError(
                "mineru file upload failed",
                hint=f"MinerU upload URL returned HTTP {upload.status_code}. Retry or check file size.",
            )

        result_payload = None
        for _ in range(60):
            result_response = await client.get(
                f"https://api.mineru.net/api/v4/extract-results/batch/{batch_id}",
                headers=headers,
            )
            result_payload = _json_or_raise(result_response)
            result_data = _payload_data(result_payload)
            full_zip_url = _first_result_value(result_data, "full_zip_url", "fullZipUrl", "zip_url", "zipUrl")
            state = str(result_data.get("state") or result_data.get("status") or "").lower()
            if isinstance(full_zip_url, str):
                zip_response = await client.get(full_zip_url)
                if zip_response.status_code >= 400:
                    raise ConversionError(
                        "mineru result download failed",
                        hint=f"MinerU result URL returned HTTP {zip_response.status_code}.",
                    )
                markdown = _markdown_from_zip(zip_response.content)
                return markdown, result_payload
            if state in {"failed", "error", "done_failed"}:
                raise ConversionError("mineru task failed", hint=str(result_data))
            await asyncio.sleep(2)

    raise ConversionError(
        "mineru task did not finish",
        hint="Timed out waiting for MinerU batch results. Retry later or use a local converter.",
    )


def _json_or_raise(response: httpx.Response) -> dict:
    if response.status_code >= 400:
        raise ConversionError(
            "mineru request failed",
            hint=f"MinerU returned HTTP {response.status_code}. Check MINERU_API_KEY and request limits.",
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise ConversionError(
            "mineru returned invalid JSON",
            hint="may be rate-limited or returning an HTML error page; try again or check API status",
        ) from exc
    if not isinstance(payload, dict):
        raise ConversionError("mineru returned invalid JSON", hint="Expected a JSON object response.")
    return payload


def _payload_data(payload: dict) -> dict:
    data = payload.get("data", payload)
    return data if isinstance(data, dict) else {}


def _first_value(payload: dict, *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list) and value and isinstance(value[0], str):
            return value[0]
    return None


def _first_result_value(payload: dict, *keys: str) -> str | None:
    value = _first_value(payload, *keys)
    if value:
        return value
    results = payload.get("extract_result") or payload.get("extractResult") or payload.get("results")
    if isinstance(results, list):
        for item in results:
            if isinstance(item, dict):
                value = _first_value(item, *keys)
                if value:
                    return value
    return None


def _markdown_from_zip(content: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for name in archive.namelist():
                if name.endswith(".md"):
                    return archive.read(name).decode("utf-8").strip()
    except zipfile.BadZipFile as exc:
        raise ConversionError("mineru result was not a zip file", hint="Retry the conversion.") from exc
    raise ConversionError("mineru result had no markdown", hint="Result zip did not include a .md file.")
