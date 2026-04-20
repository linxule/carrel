from __future__ import annotations

from pathlib import Path

from carrel.models import (
    ApiKeyStatus,
    AuditResult,
    AutomationConfig,
    BinaryInfo,
    HardwareCapability,
    PlatformToolMatrix,
    ResearcherProfile,
    Sensitivity,
    ToolAvailability,
    TrustLevel,
)
from carrel.vault.dashboard import ActivityStats, collect_activity_stats, render_dashboard


def _sample_profile() -> ResearcherProfile:
    return ResearcherProfile(
        name="Ada Lovelace",
        field="Computational humanities",
        sensitivity=Sensitivity.MEDIUM,
        cloud_consent=False,
        wiki_enabled=True,
        tools_configured={"liteparse": True, "coli": True, "gws": False},
        automation=AutomationConfig(trust_level=TrustLevel.DELEGATED),
    )


def _sample_audit() -> AuditResult:
    return AuditResult(
        os="macOS",
        platform="macos",
        arch="arm64",
        hardware_capability=HardwareCapability.HIGH,
        tools=ToolAvailability(
            binaries={"liteparse": BinaryInfo(installed=True, version="1.0.0")},
            api_keys={"groq": ApiKeyStatus(configured=False, env_var="GROQ_API_KEY")},
            mcp_servers=["obsidian"],
        ),
        tool_matrix=PlatformToolMatrix(matrix={}),
    )


def test_render_dashboard_includes_expected_sections() -> None:
    rendered = render_dashboard(
        _sample_profile(),
        _sample_audit(),
        ActivityStats(papers=4, transcripts=2, inbox=1),
    )

    assert "# My Research Environment" in rendered
    assert "## Setup" in rendered
    assert "- Name: Ada Lovelace" in rendered
    assert "- Field: Computational humanities" in rendered
    assert "- Trust level: `delegated`" in rendered
    assert "- Sensitivity: `medium`" in rendered
    assert "- Cloud consent: `false`" in rendered
    assert "- Wiki status: `enabled`" in rendered
    assert "## Configured tools" in rendered
    assert "- `coli`" in rendered
    assert "- `liteparse`" in rendered
    assert "## Activity stats" in rendered
    assert "- Papers: 4" in rendered
    assert "- Transcripts: 2" in rendered
    assert "- Inbox items: 1" in rendered
    assert "## Trust-unlocked actions" in rendered
    assert "- `vault:move-file`" in rendered
    assert "- `automation:write-prompt`" in rendered
    assert "Regenerate via `carrel vault dashboard --force`" in rendered


def test_collect_activity_stats_returns_zeros_for_empty_vault(tmp_path) -> None:
    stats = collect_activity_stats(tmp_path / "vault")

    assert stats == ActivityStats(papers=0, transcripts=0, inbox=0)


def test_collect_activity_stats_handles_missing_folders_gracefully(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / "papers" / "alpha").mkdir(parents=True)
    (vault / "papers" / "alpha" / "paper.md").write_text("paper", encoding="utf-8")
    (vault / "inbox").mkdir(parents=True)
    (vault / "inbox" / "item.pdf").write_text("file", encoding="utf-8")

    stats = collect_activity_stats(vault)

    assert stats == ActivityStats(papers=1, transcripts=0, inbox=1)
