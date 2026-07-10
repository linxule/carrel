from __future__ import annotations

from pathlib import Path

from carrel.errors import CarrelError
from carrel.env.install import install_command_for
from carrel.models import ConvertTool, HardwareCapability, Sensitivity, ToolAvailability
from carrel.policy.sensitivity import select_tool

CONVERT_CLOUD_ENV_VARS = {
    ConvertTool.MINERU: "MINERU_API_KEY",
    ConvertTool.MISTRAL_OCR: "MISTRAL_API_KEY",
}

# Suffixes each cloud OCR service accepts as input. MinerU and Mistral OCR both
# handle far more than PDF, so an explicit request for one of these on a supported
# non-PDF document is honored (default routing for non-PDF stays local-first).
MINERU_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".ppt", ".pptx"}
MISTRAL_OCR_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".webp", ".avif", ".docx", ".pptx"}
CLOUD_CONVERT_SUFFIXES = {
    ConvertTool.MINERU: MINERU_SUFFIXES,
    ConvertTool.MISTRAL_OCR: MISTRAL_OCR_SUFFIXES,
}


def select_convert_tool(
    file: Path,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,
    cloud_consent: bool = False,
    explicit_tool: ConvertTool | None = None,
) -> ConvertTool:
    _ = hardware
    suffix = file.suffix.lower()
    if explicit_tool is not None:
        if explicit_tool == ConvertTool.DEFUDDLE:
            raise CarrelError(
                "defuddle is for web capture, not file conversion",
                hint="Use 'carrel capture url <URL>' for web pages, or omit --tool for auto-detection.",
            )
        if explicit_tool in CLOUD_CONVERT_SUFFIXES and suffix not in CLOUD_CONVERT_SUFFIXES[explicit_tool]:
            supported = ", ".join(sorted(CLOUD_CONVERT_SUFFIXES[explicit_tool]))
            raise CarrelError(
                f"{explicit_tool.value} does not support '{suffix or file.name}' files",
                hint=f"{explicit_tool.value} handles {supported}. Use --tool markdownify for other document types.",
            )

    is_pdf = suffix == ".pdf"
    available_tools: list[ConvertTool] = []
    if is_pdf:
        if explicit_tool == ConvertTool.MARKDOWNIFY:
            available_tools.append(ConvertTool.MARKDOWNIFY)
        if tools.binaries.get("lit") and tools.binaries["lit"].installed:
            available_tools.append(ConvertTool.LITEPARSE)
        if tools.api_keys.get("mineru") and tools.api_keys["mineru"].configured:
            available_tools.append(ConvertTool.MINERU)
        if tools.api_keys.get("mistral") and tools.api_keys["mistral"].configured:
            available_tools.append(ConvertTool.MISTRAL_OCR)
    else:
        available_tools.append(ConvertTool.MARKDOWNIFY)
        # Only an explicit cloud request pulls a cloud OCR tool into a non-PDF
        # conversion; the sensitivity matrix still governs whether it is selected.
        if (
            explicit_tool == ConvertTool.MINERU
            and tools.api_keys.get("mineru")
            and tools.api_keys["mineru"].configured
        ):
            available_tools.append(ConvertTool.MINERU)
        if (
            explicit_tool == ConvertTool.MISTRAL_OCR
            and tools.api_keys.get("mistral")
            and tools.api_keys["mistral"].configured
        ):
            available_tools.append(ConvertTool.MISTRAL_OCR)

    decision = select_tool(
        requested_tool=explicit_tool,
        available_tools=available_tools,
        sensitivity=sensitivity,
        cloud_consent=cloud_consent,
        tool_class="convert",
    )
    if decision.selected_tool is not None:
        return decision.selected_tool

    # selected_tool is None: an explicit cloud tool that is present in
    # `available_tools` (credentials configured, suffix supported) but still not
    # selected was blocked by the sensitivity matrix -- not a missing credential.
    if explicit_tool in CONVERT_CLOUD_ENV_VARS:
        if explicit_tool in available_tools:
            raise CarrelError(
                decision.rationale,
                hint="HIGH sensitivity keeps conversion local. Use --tool liteparse, or lower the vault sensitivity.",
            )
        raise CarrelError(
            decision.rationale,
            hint=f"Configure {CONVERT_CLOUD_ENV_VARS[explicit_tool]} or choose an available local tool.",
        )

    raise CarrelError(
        decision.rationale,
        hint=(
            "Install it: "
            f"{install_command_for('liteparse') or 'install liteparse'}"
        ),
    )
