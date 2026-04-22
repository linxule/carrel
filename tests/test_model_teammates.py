from __future__ import annotations

import pytest
from pydantic import ValidationError

from carrel.models import ModelTeammateStatus, ResearcherProfile
from carrel.vault.dashboard import ActivityStats, render_dashboard


def test_model_teammate_status_values() -> None:
    assert {s.value for s in ModelTeammateStatus} == {
        "configured",
        "interested",
        "skipped",
    }


def test_profile_round_trips_model_teammates() -> None:
    profile = ResearcherProfile(
        model_teammates={
            "codex": "configured",
            "gemini": "interested",
            "kimi": "skipped",
        }
    )

    reloaded = ResearcherProfile.model_validate_json(profile.model_dump_json())

    assert reloaded.model_teammates == {
        "codex": ModelTeammateStatus.CONFIGURED,
        "gemini": ModelTeammateStatus.INTERESTED,
        "kimi": ModelTeammateStatus.SKIPPED,
    }


def test_profile_rejects_invalid_teammate_status() -> None:
    with pytest.raises(ValidationError):
        ResearcherProfile(model_teammates={"codex": "removed"})


def test_profile_accepts_unknown_teammate_key() -> None:
    """Keys are free-form so new teammates (grok, etc.) slot in without schema changes."""
    profile = ResearcherProfile(model_teammates={"grok": "interested"})

    assert profile.model_teammates["grok"] == ModelTeammateStatus.INTERESTED


def test_dashboard_shows_teammates_summary_in_setup_block() -> None:
    profile = ResearcherProfile(
        name="Ada",
        model_teammates={"codex": "configured", "gemini": "interested"},
    )

    rendered = render_dashboard(profile, audit=None, activity=ActivityStats(papers=0, transcripts=0, inbox=0))

    assert "- Model teammates: codex=configured, gemini=interested" in rendered


def test_dashboard_shows_none_when_no_teammates() -> None:
    profile = ResearcherProfile(name="Ada")

    rendered = render_dashboard(profile, audit=None, activity=ActivityStats(papers=0, transcripts=0, inbox=0))

    assert "- Model teammates: none" in rendered
