from __future__ import annotations

from carrel.models import (
    AutomationConfig,
    AutomationModel,
    AutomationSchedule,
    ResearcherProfile,
    Sensitivity,
    TrustLevel,
)
from carrel.vault.automation_prompt import render_automation_prompt


def _profile() -> ResearcherProfile:
    return ResearcherProfile(
        name="Sarah",
        field="Sociology",
        sensitivity=Sensitivity.MEDIUM,
        cloud_consent=False,
    )


def test_render_automation_prompt_includes_header_trust_and_schedule() -> None:
    config = AutomationConfig(
        inbox_processing=True,
        vault_health=True,
        cross_linking_suggestions=True,
        reflection_synthesis=True,
        trust_level=TrustLevel.CONSULTATIVE,
        schedule=AutomationSchedule.WEEKDAYS,
        model=AutomationModel.OPUS,
    )

    rendered = render_automation_prompt(_profile(), config)

    assert "You are the Carrel overnight agent for Sarah." in rendered
    assert "- Trust level: `consultative`" in rendered
    assert "Write suggestions and proposed actions" in rendered
    assert "- Schedule: `weekdays`" in rendered
    assert "- Model: `opus`" in rendered
    assert "Find the vault root by locating `.carrel/environment.json`" in rendered


def test_render_automation_prompt_lists_only_enabled_capabilities() -> None:
    config = AutomationConfig(
        inbox_processing=True,
        vault_health=False,
        cross_linking_suggestions=False,
        gap_analysis=True,
        draft_feedback=False,
        reflection_synthesis=False,
        wiki_maintenance=True,
    )

    rendered = render_automation_prompt(_profile(), config)

    assert "**Inbox processing**" in rendered
    assert "**Gap analysis**" in rendered
    assert "**Wiki maintenance**" in rendered
    assert "**Vault health**" not in rendered
    assert "**Draft feedback**" not in rendered
    assert "**Reflection synthesis**" not in rendered


def test_render_automation_prompt_handles_no_enabled_capabilities() -> None:
    config = AutomationConfig(
        inbox_processing=False,
        vault_health=False,
        cross_linking_suggestions=False,
        gap_analysis=False,
        draft_feedback=False,
        reflection_synthesis=False,
        wiki_maintenance=False,
        schedule=AutomationSchedule.WEEKLY,
    )

    rendered = render_automation_prompt(_profile(), config)

    assert "No automation capabilities are enabled" in rendered
    assert "- Schedule: `weekly`" in rendered
