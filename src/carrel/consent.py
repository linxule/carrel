from __future__ import annotations

from carrel.models import ResearcherProfile, Sensitivity


def resolve_cloud_consent(tool: str | None, profile: ResearcherProfile | None) -> bool:
    if tool and tool in {"mineru", "groq", "gemini"}:
        if profile and profile.sensitivity == Sensitivity.HIGH:
            return False
        return bool(profile and profile.cloud_consent)
    if profile and profile.sensitivity == Sensitivity.HIGH:
        return False
    if profile and profile.cloud_consent:
        return True
    return False
