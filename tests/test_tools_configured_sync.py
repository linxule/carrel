from __future__ import annotations

from carrel.env.platform import Platform
from carrel.env.sync import sync_tools_configured
from carrel.models import (
    ApiKeyStatus,
    AuditResult,
    BinaryInfo,
    HardwareCapability,
    PlatformToolMatrix,
    ResearcherProfile,
    ToolAvailability,
)


def test_sync_tools_configured_updates_for_current_platform() -> None:
    profile = ResearcherProfile(
        tools_configured={
            "obsidian": True,
            "zotero": True,
        }
    )
    audit_result = AuditResult(
        os="Windows",
        platform=Platform.WINDOWS,
        arch="x86_64",
        hardware_capability=HardwareCapability.MEDIUM,
        tools=ToolAvailability(
            binaries={"ffmpeg": BinaryInfo(installed=True, version="6.0")},
            api_keys={"groq": ApiKeyStatus(configured=False, env_var="GROQ_API_KEY")},
            mcp_servers=[],
        ),
        tool_matrix=PlatformToolMatrix(
            matrix={
                "obsidian": {
                    Platform.MACOS: True,
                    Platform.WINDOWS: False,
                },
                "zotero": {
                    Platform.MACOS: True,
                    Platform.WINDOWS: False,
                },
                "ffmpeg": {
                    Platform.WINDOWS: True,
                },
            }
        ),
    )

    synced = sync_tools_configured(profile, audit_result)

    assert synced.tools_configured == {
        "ffmpeg": True,
        "obsidian": False,
        "zotero": False,
    }
