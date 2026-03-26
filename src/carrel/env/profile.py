from __future__ import annotations

import json
from pathlib import Path

from carrel.models import ResearcherProfile


def _profile_path(vault: Path) -> Path:
    return vault / ".carrel" / "environment.json"


def read_profile(vault: Path) -> ResearcherProfile | None:
    """Read .carrel/environment.json. Returns None if not found."""

    path = _profile_path(vault)
    if not path.exists():
        return None
    return ResearcherProfile.model_validate(json.loads(path.read_text(encoding="utf-8")))


def write_profile(vault: Path, profile: ResearcherProfile) -> Path:
    """Write profile. Creates .carrel/ if needed."""

    path = _profile_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    return path


def update_profile(vault: Path, **updates) -> ResearcherProfile:
    """Merge updates into existing profile."""

    current = read_profile(vault) or ResearcherProfile()
    merged = current.model_copy(update=updates)
    write_profile(vault, merged)
    return merged
