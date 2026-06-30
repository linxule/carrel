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


def select_convert_tool(
    file: Path,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,
    cloud_consent: bool = False,
    explicit_tool: ConvertTool | None = None,
) -> ConvertTool:
    _ = sensitivity, hardware
    if explicit_tool is not None:
        if explicit_tool == ConvertTool.DEFUDDLE:
            raise CarrelError(
                "defuddle is for web capture, not file conversion",
                hint="Use 'carrel capture url <URL>' for web pages, or omit --tool for auto-detection.",
            )

    available_tools: list[ConvertTool] = []
    if file.suffix.lower() != ".pdf":
        available_tools.append(ConvertTool.MARKDOWNIFY)
    else:
        if explicit_tool == ConvertTool.MARKDOWNIFY:
            available_tools.append(ConvertTool.MARKDOWNIFY)
        if tools.binaries.get("lit") and tools.binaries["lit"].installed:
            available_tools.append(ConvertTool.LITEPARSE)
        if tools.api_keys.get("mineru") and tools.api_keys["mineru"].configured:
            available_tools.append(ConvertTool.MINERU)
        if tools.api_keys.get("mistral") and tools.api_keys["mistral"].configured:
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
    if explicit_tool in CONVERT_CLOUD_ENV_VARS:
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
