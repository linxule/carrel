from __future__ import annotations

import pytest

from carrel.vault.markers import ensure_markers, parse_markers, update_marker


def test_parse_markers_extracts_all_values() -> None:
    text = """
Intro.
<!-- carrel:sensitivity -->medium<!-- /carrel:sensitivity -->
<!-- carrel:cloud_consent -->false<!-- /carrel:cloud_consent -->
"""

    assert parse_markers(text) == {
        "sensitivity": "medium",
        "cloud_consent": "false",
    }


def test_parse_markers_returns_empty_dict_when_absent() -> None:
    assert parse_markers("# CLAUDE\n\nNo markers here.") == {}


def test_update_marker_preserves_surrounding_content() -> None:
    text = (
        "# CLAUDE\n"
        "Before\n"
        "<!-- carrel:sensitivity -->medium<!-- /carrel:sensitivity -->\n"
        "After\n"
    )

    updated = update_marker(text, "sensitivity", "high")

    assert updated == (
        "# CLAUDE\n"
        "Before\n"
        "<!-- carrel:sensitivity -->high<!-- /carrel:sensitivity -->\n"
        "After\n"
    )


def test_update_marker_raises_when_marker_missing() -> None:
    with pytest.raises(ValueError, match="Marker 'sensitivity' not found"):
        update_marker("No markers", "sensitivity", "low")


def test_ensure_markers_appends_only_missing_and_is_idempotent() -> None:
    initial = (
        "# CLAUDE\n\n"
        "<!-- carrel:sensitivity -->medium<!-- /carrel:sensitivity -->\n"
    )

    once = ensure_markers(
        initial,
        {
            "sensitivity": "medium",
            "cloud_consent": "false",
        },
    )
    twice = ensure_markers(
        once,
        {
            "sensitivity": "medium",
            "cloud_consent": "false",
        },
    )

    assert once == (
        "# CLAUDE\n\n"
        "<!-- carrel:sensitivity -->medium<!-- /carrel:sensitivity -->\n\n"
        "<!-- carrel:cloud_consent -->false<!-- /carrel:cloud_consent -->\n"
    )
    assert twice == once


def test_marker_values_with_special_characters_round_trip() -> None:
    value = "liteparse, coli & defuddle <enabled>\nsecond line"
    text = ensure_markers("Base text", {"tools_configured": value})

    assert parse_markers(text) == {"tools_configured": value}
    assert update_marker(text, "tools_configured", value) == text
