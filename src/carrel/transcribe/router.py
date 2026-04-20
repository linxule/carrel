from __future__ import annotations

from carrel.errors import CarrelError
from carrel.env.install import install_command_for
from carrel.models import HardwareCapability, Sensitivity, ToolAvailability, TranscribeTool
from carrel.policy.sensitivity import select_tool
from carrel.transcribe.youtube_url import is_youtube_url


def select_transcribe_tool(
    source: str,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,
    cloud_consent: bool = False,
    explicit_tool: TranscribeTool | None = None,
) -> TranscribeTool:
    _ = sensitivity, hardware
    is_yt = is_youtube_url(source)
    if explicit_tool is not None:
        if explicit_tool in {TranscribeTool.GEMINI, TranscribeTool.YOUTUBE_CAPTIONS} and not is_yt:
            raise CarrelError(
                f"{explicit_tool.value} only works with YouTube URLs",
                hint="For local audio files, use --tool coli (local) or --tool groq (cloud).",
            )
        if explicit_tool in {TranscribeTool.COLI, TranscribeTool.GROQ} and is_yt:
            raise CarrelError(
                f"{explicit_tool.value} only works with local audio files",
                hint="For YouTube URLs, use --tool gemini (cloud) or omit --tool for local captions.",
            )

    available_tools: list[TranscribeTool] = []
    if is_yt:
        available_tools.append(TranscribeTool.YOUTUBE_CAPTIONS)
        if tools.api_keys.get("gemini") and tools.api_keys["gemini"].configured:
            available_tools.append(TranscribeTool.GEMINI)
    else:
        if tools.binaries.get("coli") and tools.binaries["coli"].installed:
            available_tools.append(TranscribeTool.COLI)
        if tools.api_keys.get("groq") and tools.api_keys["groq"].configured:
            available_tools.append(TranscribeTool.GROQ)

    decision = select_tool(
        requested_tool=explicit_tool,
        available_tools=available_tools,
        sensitivity=sensitivity,
        cloud_consent=cloud_consent,
        tool_class="transcribe",
    )
    if decision.selected_tool is not None:
        return decision.selected_tool

    if not is_yt:
        raise CarrelError(
            decision.rationale,
            hint=(
                "Install it: "
                f"{install_command_for('coli') or 'install coli'}"
            ),
        )
    raise CarrelError(decision.rationale)
