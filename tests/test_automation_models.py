import json

import pytest
from pydantic import ValidationError

from carrel.models import (
    AutomationConfig,
    AutomationModel,
    AutomationSchedule,
    ResearcherProfile,
    TrustLevel,
)


def test_automation_config_defaults() -> None:
    cfg = AutomationConfig()

    assert cfg.enabled is False
    assert cfg.inbox_processing is True
    assert cfg.vault_health is True
    assert cfg.cross_linking_suggestions is True
    assert cfg.gap_analysis is False
    assert cfg.draft_feedback is False
    assert cfg.reflection_synthesis is True
    assert cfg.wiki_maintenance is False
    assert cfg.trust_level == TrustLevel.ADVISORY
    assert cfg.model == AutomationModel.SONNET
    assert cfg.schedule == AutomationSchedule.DAILY
    assert cfg.review_cadence == "quarterly"
    assert cfg.last_reviewed is None


def test_researcher_profile_backward_compatibility() -> None:
    profile = ResearcherProfile.model_validate({})

    assert profile.automation.enabled is False


def test_researcher_profile_missing_automation_key() -> None:
    # Simulate an existing environment.json that predates the automation field
    raw = {"name": "Alice", "field": "biology", "cloud_consent": True}
    profile = ResearcherProfile.model_validate(raw)

    assert profile.automation.enabled is False
    assert profile.automation.trust_level == TrustLevel.ADVISORY
    assert profile.automation.wiki_maintenance is False
    assert profile.wiki_enabled is False
    assert profile.wiki_preference is None
    assert profile.wiki_proposal_deferred_until is None


def test_automation_config_roundtrip() -> None:
    cfg = AutomationConfig(
        enabled=True,
        gap_analysis=True,
        draft_feedback=True,
        trust_level=TrustLevel.DELEGATED,
        model=AutomationModel.OPUS,
        schedule=AutomationSchedule.WEEKLY,
        review_cadence="monthly",
        last_reviewed="2026-03-01",
    )
    profile = ResearcherProfile(name="Bob", automation=cfg)

    dumped = profile.model_dump()
    restored = ResearcherProfile.model_validate(dumped)

    assert restored.automation.enabled is True
    assert restored.automation.gap_analysis is True
    assert restored.automation.draft_feedback is True
    assert restored.automation.trust_level == TrustLevel.DELEGATED
    assert restored.automation.model == AutomationModel.OPUS
    assert restored.automation.schedule == AutomationSchedule.WEEKLY
    assert restored.automation.review_cadence == "monthly"
    assert restored.automation.last_reviewed == "2026-03-01"


def test_trust_level_invalid_value_raises() -> None:
    with pytest.raises(ValidationError):
        AutomationConfig(trust_level="unknown")  # type: ignore[arg-type]


def test_automation_model_invalid_value_raises() -> None:
    with pytest.raises(ValidationError):
        AutomationConfig(model="gpt4")  # type: ignore[arg-type]


def test_automation_schedule_invalid_value_raises() -> None:
    with pytest.raises(ValidationError):
        AutomationConfig(schedule="hourly")  # type: ignore[arg-type]


def test_researcher_profile_json_includes_automation() -> None:
    profile = ResearcherProfile(name="Carol")
    data = json.loads(profile.model_dump_json())

    assert "automation" in data
    assert data["automation"]["enabled"] is False
    assert data["automation"]["wiki_maintenance"] is False
    assert data["automation"]["trust_level"] == "advisory"
    assert data["automation"]["model"] == "sonnet"
    assert data["automation"]["schedule"] == "daily"
    assert data["wiki_enabled"] is False
