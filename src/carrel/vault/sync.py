from __future__ import annotations

from carrel.models import ResearcherProfile
from carrel.vault.markers import MARKER_FIELDS


def enabled_tools(profile: ResearcherProfile) -> str:
    tools = sorted(tool for tool, enabled in profile.tools_configured.items() if enabled)
    return ",".join(tools)


def marker_values(profile: ResearcherProfile) -> dict[str, str]:
    return {
        "sensitivity": profile.sensitivity.value,
        "cloud_consent": str(profile.cloud_consent).lower(),
        "trust_level": profile.automation.trust_level.value,
        "tools_configured": enabled_tools(profile),
        "wiki_enabled": str(profile.wiki_enabled).lower(),
    }


def compare_markers(
    profile: ResearcherProfile,
    markers: dict[str, str],
) -> list[dict[str, str]]:
    expected = marker_values(profile)
    return [
        {
            "field": field,
            "marker": markers.get(field, ""),
            "profile": expected[field],
        }
        for field in MARKER_FIELDS
        if markers.get(field) is not None and markers.get(field) != expected[field]
    ]
