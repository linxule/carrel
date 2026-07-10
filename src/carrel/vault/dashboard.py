from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from carrel.models import AuditResult, ModelTeammateStatus, ResearcherProfile, TrustLevel
from carrel.vault.templates import read_template


def _teammates_summary(profile: ResearcherProfile) -> str:
    if not profile.model_teammates:
        return "none"
    items: list[str] = []
    for name in sorted(profile.model_teammates):
        status = profile.model_teammates[name]
        value = status.value if isinstance(status, ModelTeammateStatus) else str(status)
        items.append(f"{name}={value}")
    return ", ".join(items)

try:
    from carrel.policy.trust import list_actions as policy_list_actions
except ImportError:  # pragma: no cover - fallback for partial installs
    policy_list_actions = None


class ActivityStats(BaseModel):
    papers: int
    transcripts: int
    inbox: int


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for child in path.rglob("*") if child.is_file())


def collect_activity_stats(vault: Path) -> ActivityStats:
    return ActivityStats(
        papers=_count_files(vault / "papers"),
        transcripts=_count_files(vault / "transcripts"),
        inbox=_count_files(vault / "inbox"),
    )


def _enabled_tools(profile: ResearcherProfile) -> list[str]:
    return sorted(tool for tool, enabled in profile.tools_configured.items() if enabled)


def _trust_unlocked_actions(trust_level: TrustLevel) -> list[str]:
    if policy_list_actions is not None:
        return [
            action
            for action, (_, allowed) in policy_list_actions(trust_level).items()
            if allowed
        ]

    fallback = {
        TrustLevel.ADVISORY: [],
        TrustLevel.CONSULTATIVE: [
            "automation:propose",
            "automation:write-prompt",
            "wiki:propose",
            "wiki:apply-approved",
        ],
        TrustLevel.DELEGATED: [
            "automation:propose",
            "automation:execute",
            "automation:write-prompt",
            "wiki:propose",
            "wiki:apply-approved",
            "wiki:write",
            "vault:move-file",
        ],
        TrustLevel.PARTNERSHIP: [
            "automation:propose",
            "automation:execute",
            "automation:write-prompt",
            "wiki:propose",
            "wiki:apply-approved",
            "wiki:write",
            "vault:move-file",
            "vault:reorganize",
        ],
    }
    return fallback[trust_level]


def render_dashboard(
    profile: ResearcherProfile,
    audit: AuditResult | None,
    activity: ActivityStats | None,
) -> str:
    enabled_tools = _enabled_tools(profile)
    stats = activity or ActivityStats(papers=0, transcripts=0, inbox=0)
    unlocked_actions = _trust_unlocked_actions(profile.automation.trust_level)
    audit_line = (
        f"- Audit snapshot: {audit.platform.value} / {audit.hardware_capability.value}"
        if audit is not None
        else "- Audit snapshot: unavailable"
    )
    tools_lines = (
        "\n".join(f"- `{tool}`" for tool in enabled_tools)
        if enabled_tools
        else "- None configured yet"
    )
    unlocked_lines = (
        "\n".join(f"- `{action}`" for action in unlocked_actions)
        if unlocked_actions
        else "- No write actions unlocked at this trust level"
    )
    wiki_status = "enabled" if profile.wiki_enabled else "disabled"
    template = read_template("dashboard.md")
    return (
        template.replace(
            "{{setup_block}}",
            "\n".join(
                [
                    f"- Name: {profile.name or 'Unknown'}",
                    f"- Field: {profile.field or 'Unknown'}",
                    "- Vault path: `(set by CLI at write time)`",
                    f"- Trust level: `{profile.automation.trust_level.value}`",
                    f"- Sensitivity: `{profile.sensitivity.value}`",
                    f"- Cloud consent: `{str(profile.cloud_consent).lower()}`",
                    f"- Model teammates: {_teammates_summary(profile)}",
                    audit_line,
                ]
            ),
        )
        .replace("{{configured_tools}}", tools_lines)
        .replace(
            "{{activity_stats}}",
            "\n".join(
                [
                    f"- Papers: {stats.papers}",
                    f"- Transcripts: {stats.transcripts}",
                    f"- Inbox items: {stats.inbox}",
                ]
            ),
        )
        .replace("{{trust_unlocked_actions}}", unlocked_lines)
        .replace("{{wiki_status}}", wiki_status)
    )
