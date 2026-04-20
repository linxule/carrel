from __future__ import annotations

import pytest
from pydantic import ValidationError

from carrel.consent import resolve_cloud_consent
from carrel.models import ResearcherProfile, Sensitivity, SetupState


def test_setup_state_accepts_incomplete_phase_four() -> None:
    state = SetupState(last_completed_phase=4, version="0.5.2")

    assert state.last_completed_phase == 4
    assert state.completed_at is None


def test_setup_state_accepts_completed_phase_nine() -> None:
    state = SetupState(last_completed_phase=9, version="0.5.2", completed_at="2026-04-20")

    assert state.last_completed_phase == 9
    assert state.completed_at == "2026-04-20"


def test_setup_state_rejects_phase_below_persisted_range() -> None:
    with pytest.raises(ValidationError):
        SetupState(last_completed_phase=2, version="0.5.2")


def test_setup_state_rejects_invalid_version_string() -> None:
    with pytest.raises(ValidationError):
        SetupState(last_completed_phase=4, version="version-0.5.2")


def test_setup_state_rejects_invalid_completed_at_format() -> None:
    with pytest.raises(ValidationError):
        SetupState(last_completed_phase=9, version="0.5.2", completed_at="20-04-2026")


def test_setup_state_rejects_phase_nine_without_completed_at() -> None:
    with pytest.raises(ValidationError):
        SetupState(last_completed_phase=9, version="0.5.2")


def test_setup_state_rejects_completed_at_before_phase_nine() -> None:
    with pytest.raises(ValidationError):
        SetupState(last_completed_phase=8, version="0.5.2", completed_at="2026-04-20")


def test_resolve_cloud_consent_blocks_cloud_tools_for_high_sensitivity() -> None:
    profile = ResearcherProfile(sensitivity=Sensitivity.HIGH, cloud_consent=True)

    assert resolve_cloud_consent("mineru", profile) is False


def test_resolve_cloud_consent_allows_cloud_tools_with_lower_sensitivity_and_consent() -> None:
    profile = ResearcherProfile(sensitivity=Sensitivity.MEDIUM, cloud_consent=True)

    assert resolve_cloud_consent("mineru", profile) is True


def test_resolve_cloud_consent_blocks_without_consent_regardless_of_sensitivity() -> None:
    profile = ResearcherProfile(sensitivity=Sensitivity.LOW, cloud_consent=False)

    assert resolve_cloud_consent("mineru", profile) is False
