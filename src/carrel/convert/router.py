from __future__ import annotations

from pathlib import Path

from carrel.errors import ToolNotInstalled
from carrel.env.install import install_command_for
from carrel.models import ConvertTool, HardwareCapability, Sensitivity, ToolAvailability


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
        return explicit_tool
    if file.suffix.lower() != ".pdf":
        return ConvertTool.MARKDOWNIFY
    if tools.binaries.get("lit") and tools.binaries["lit"].installed:
        return ConvertTool.LITEPARSE
    if cloud_consent and tools.api_keys.get("mineru") and tools.api_keys["mineru"].configured:
        return ConvertTool.MINERU
    raise ToolNotInstalled("liteparse", install_command_for("liteparse") or "install liteparse")
