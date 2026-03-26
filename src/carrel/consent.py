from __future__ import annotations

from carrel.models import ResearcherProfile


def resolve_cloud_consent(tool: str | None, profile: ResearcherProfile | None) -> bool:
    if tool and tool in {"mineru", "groq", "gemini"}:
        return True
    if profile and profile.cloud_consent:
        return True
    return False
