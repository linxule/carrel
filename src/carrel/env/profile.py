from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from carrel.errors import CarrelError
from carrel.models import ResearcherProfile
from carrel.safe_path import safe_vault_join


def _profile_path(vault: Path) -> Path:
    return safe_vault_join(vault, ".carrel", "environment.json")


def read_profile(vault: Path) -> ResearcherProfile | None:
    """Read .carrel/environment.json. Returns None if not found."""

    path = _profile_path(vault)
    if not path.exists():
        return None
    try:
        return ResearcherProfile.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (ValidationError, json.JSONDecodeError, OSError) as error:
        raise CarrelError(
            f"Could not parse {path}",
            hint="Run /carrel-setup to regenerate it.",
        ) from error


def write_profile(vault: Path, profile: ResearcherProfile) -> Path:
    """Write profile. Creates .carrel/ if needed."""

    path = _profile_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    return path
