from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from carrel.errors import ConversionError

MISTRAL_API_BASE = "https://api.mistral.ai/v1"
MISTRAL_OCR_MODEL = "mistral-ocr-latest"
MISTRAL_MAX_FILE_BYTES = 512 * 1024 * 1024


async def convert_with_mistral_ocr(file: Path, api_key: str, timeout: int = 120) -> tuple[str, dict]:
    headers = {"Authorization": f"Bearer {api_key}"}
    if file.stat().st_size > MISTRAL_MAX_FILE_BYTES:
        raise ConversionError(
            "mistral ocr file too large",
            hint="Mistral OCR accepts PDFs up to 512 MB; split or compress the file before retrying.",
        )
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            file_id = await _upload_file(client, file, headers)
            try:
                signed_url = await _signed_url(client, file_id, headers)
                ocr_response = await client.post(
                    f"{MISTRAL_API_BASE}/ocr",
                    headers={**headers, "Content-Type": "application/json"},
                    json={
                        "model": MISTRAL_OCR_MODEL,
                        "document": {"type": "document_url", "document_url": signed_url},
                        "table_format": "markdown",
                        "include_image_base64": False,
                    },
                )
                payload = _json_or_raise(ocr_response)
                markdown = _markdown_from_payload(payload)
                usage_info = (
                    payload.get("usage_info") if isinstance(payload.get("usage_info"), dict) else {}
                )
            except Exception:
                # Best-effort cleanup of the uploaded file. Guard it so an
                # unexpected error while deleting can never replace the original
                # OCR failure that we re-raise below.
                try:
                    await _delete_file(client, file_id, headers, raise_on_failure=False)
                except Exception:
                    pass
                raise
            cleanup = await _delete_file(client, file_id, headers)
            return markdown, {
                "model": payload.get("model") if isinstance(payload.get("model"), str) else MISTRAL_OCR_MODEL,
                "file_id": file_id,
                "pages": _usage_pages(usage_info) or _page_count(payload),
                "usage_info": usage_info,
                "cleanup": cleanup,
            }
    except httpx.HTTPError as exc:
        raise ConversionError(
            "mistral ocr request failed",
            hint="Mistral OCR request could not complete. Check connectivity, MISTRAL_API_KEY, and provider status.",
        ) from exc


async def _upload_file(client: httpx.AsyncClient, file: Path, headers: dict[str, str]) -> str:
    with file.open("rb") as handle:
        response = await client.post(
            f"{MISTRAL_API_BASE}/files",
            headers=headers,
            data={"purpose": "ocr", "visibility": "user"},
            files={"file": (file.name, handle, "application/pdf")},
        )
    payload = _json_or_raise(response)
    file_id = payload.get("id")
    if not isinstance(file_id, str):
        raise ConversionError(
            "mistral ocr upload response was missing file id",
            hint="Mistral did not return an id for the uploaded PDF.",
        )
    return file_id


async def _signed_url(client: httpx.AsyncClient, file_id: str, headers: dict[str, str]) -> str:
    response = await client.get(
        f"{MISTRAL_API_BASE}/files/{file_id}/url",
        headers=headers,
        params={"expiry": 24},
    )
    payload = _json_or_raise(response)
    url = _first_string(payload, "url", "signed_url", "signedUrl")
    if url is None:
        raise ConversionError(
            "mistral ocr signed URL response was missing url",
            hint="Mistral did not return a document URL for the uploaded PDF.",
        )
    return url


async def _delete_file(
    client: httpx.AsyncClient,
    file_id: str,
    headers: dict[str, str],
    *,
    raise_on_failure: bool = True,
) -> dict[str, bool | str | int | None]:
    try:
        response = await client.delete(f"{MISTRAL_API_BASE}/files/{file_id}", headers=headers)
    except (httpx.HTTPError, RuntimeError) as exc:
        if raise_on_failure:
            raise ConversionError(
                "mistral ocr cleanup failed",
                hint=(
                    "OCR succeeded, but Carrel could not confirm deletion of the uploaded file. "
                    "Delete it from Mistral manually or retry cleanup."
                ),
            ) from exc
        return {"deleted": False, "status_code": None, "warning": "cleanup request failed"}
    if response.status_code >= 400:
        if raise_on_failure:
            raise ConversionError(
                "mistral ocr cleanup failed",
                hint=(
                    f"Mistral returned HTTP {response.status_code} while deleting the uploaded file. "
                    "Delete it from Mistral manually before treating this run as complete."
                ),
            )
        return {"deleted": False, "status_code": response.status_code, "warning": "cleanup returned error"}
    payload = _json_or_empty(response)
    deleted = payload.get("deleted") if payload else True
    if deleted is not True:
        if raise_on_failure:
            raise ConversionError(
                "mistral ocr cleanup failed",
                hint="Mistral did not confirm deletion of the uploaded file; delete it manually.",
            )
        return {"deleted": False, "status_code": response.status_code, "warning": "cleanup not confirmed"}
    return {"deleted": True, "status_code": response.status_code}


def _json_or_raise(response: httpx.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        raise ConversionError(
            "mistral ocr request failed",
            hint=f"Mistral returned HTTP {response.status_code}. Check MISTRAL_API_KEY and request limits.",
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise ConversionError(
            "mistral ocr returned invalid JSON",
            hint="Mistral may be rate-limited or returning an HTML error page; try again or check API status.",
        ) from exc
    if not isinstance(payload, dict):
        raise ConversionError("mistral ocr returned invalid JSON", hint="Expected a JSON object response.")
    return payload


def _json_or_empty(response: httpx.Response) -> dict[str, Any]:
    if not response.content:
        return {}
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _markdown_from_payload(payload: dict[str, Any]) -> str:
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise ConversionError(
            "mistral ocr returned no pages",
            hint="Expected the OCR response to include a pages array.",
        )
    markdown_pages: list[str] = []
    for page in pages:
        if isinstance(page, dict) and isinstance(page.get("markdown"), str):
            text = page["markdown"].strip()
            if text:
                markdown_pages.append(text)
    if not markdown_pages:
        raise ConversionError(
            "mistral ocr returned no markdown",
            hint="Expected at least one OCR page with markdown content.",
        )
    return "\n\n".join(markdown_pages)


def _first_string(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _page_count(payload: dict[str, Any]) -> int | None:
    pages = payload.get("pages")
    if isinstance(pages, list):
        return len(pages)
    return None


def _usage_pages(usage_info: dict[str, Any]) -> int | None:
    pages = usage_info.get("pages_processed")
    return pages if isinstance(pages, int) else None
