from __future__ import annotations

import os
from pathlib import Path

from carrel.consent import resolve_cloud_consent
from carrel.convert.adapters.liteparse import convert_with_liteparse
from carrel.convert.adapters.markdownify import convert_with_markdownify
from carrel.convert.adapters.mistral_ocr import convert_with_mistral_ocr
from carrel.convert.adapters.mineru import convert_with_mineru
from carrel.convert.router import select_convert_tool
from carrel.env.audit import audit
from carrel.errors import ToolNotConfigured
from carrel.models import ConvertTool, ResearcherProfile, Sensitivity


async def convert_file(file: Path, tool: ConvertTool) -> tuple[str, dict]:
    if tool == ConvertTool.LITEPARSE:
        return await convert_with_liteparse(file)
    if tool == ConvertTool.MINERU:
        api_key = os.environ.get("MINERU_API_KEY")
        if not api_key:
            raise ToolNotConfigured("mineru", "MINERU_API_KEY")
        return await convert_with_mineru(file=file, api_key=api_key)
    if tool == ConvertTool.MISTRAL_OCR:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ToolNotConfigured("mistral_ocr", "MISTRAL_API_KEY")
        return await convert_with_mistral_ocr(file=file, api_key=api_key)
    return await convert_with_markdownify(file)


async def select_convert_tool_only(
    file_path: Path,
    vault_path: Path,
    profile: ResearcherProfile | None,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> ConvertTool:
    audit_result = await audit(vault_path)
    return select_convert_tool(
        file=file_path,
        sensitivity=sensitivity or (profile.sensitivity if profile else Sensitivity.MEDIUM),
        tools=audit_result.tools,
        cloud_consent=resolve_cloud_consent(tool.value if tool else None, profile),
        explicit_tool=tool,
    )


async def run_convert_pipeline(
    file_path: Path,
    vault_path: Path,
    profile: ResearcherProfile | None,
    sensitivity: Sensitivity | None,
    tool: ConvertTool | None,
) -> tuple[ConvertTool, str, dict]:
    selected_tool = await select_convert_tool_only(file_path, vault_path, profile, sensitivity, tool)
    content, metadata = await convert_file(file_path, selected_tool)
    return selected_tool, content, metadata
