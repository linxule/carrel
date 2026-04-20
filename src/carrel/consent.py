from __future__ import annotations

from carrel.models import ConvertTool, ResearcherProfile, Sensitivity, TranscribeTool

CLOUD_TOOLS = {
    ConvertTool.MINERU.value,
    TranscribeTool.GROQ.value,
    TranscribeTool.GEMINI.value,
    "gws",
}


def resolve_cloud_consent(tool: str | None, profile: ResearcherProfile | None) -> bool:
    if tool and tool in CLOUD_TOOLS:
        if profile and profile.sensitivity == Sensitivity.HIGH:
            return False
        return bool(profile and profile.cloud_consent)
    if profile and profile.sensitivity == Sensitivity.HIGH:
        return False
    if profile and profile.cloud_consent:
        return True
    return False
