from __future__ import annotations

from carrel.models import AuditResult, ResearcherProfile


def sync_tools_configured(
    profile: ResearcherProfile,
    audit_result: AuditResult,
) -> ResearcherProfile:
    tools_configured = dict(profile.tools_configured)

    for tool in sorted(profile.tools_configured):
        tools_configured[tool] = audit_result.tool_matrix.is_available(
            tool,
            audit_result.platform,
        )

    for tool in sorted(audit_result.tool_matrix.matrix):
        if tool not in tools_configured:
            tools_configured[tool] = audit_result.tool_matrix.is_available(
                tool,
                audit_result.platform,
            )

    return profile.model_copy(update={"tools_configured": tools_configured})
