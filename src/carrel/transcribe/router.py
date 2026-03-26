from __future__ import annotations

from urllib.parse import urlparse

from carrel.errors import CarrelError, ToolNotInstalled
from carrel.env.install import install_command_for
from carrel.models import HardwareCapability, Sensitivity, ToolAvailability, TranscribeTool


def _is_youtube_url(source: str) -> bool:
    parsed = urlparse(source)
    if not (parsed.scheme and parsed.netloc):
        return False
    host = parsed.netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def select_transcribe_tool(
    source: str,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,
    cloud_consent: bool = False,
    explicit_tool: TranscribeTool | None = None,
) -> TranscribeTool:
    _ = sensitivity, hardware
    if explicit_tool is not None:
        is_yt = _is_youtube_url(source)
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
        return explicit_tool
    if _is_youtube_url(source):
        if cloud_consent and tools.api_keys.get("gemini") and tools.api_keys["gemini"].configured:
            return TranscribeTool.GEMINI
        return TranscribeTool.YOUTUBE_CAPTIONS
    if tools.binaries.get("coli") and tools.binaries["coli"].installed:
        return TranscribeTool.COLI
    if cloud_consent and tools.api_keys.get("groq") and tools.api_keys["groq"].configured:
        return TranscribeTool.GROQ
    raise ToolNotInstalled("coli", install_command_for("coli") or "install coli")
