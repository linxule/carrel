from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from .constants import (
    AUTOMATION_MODELS,
    AUTOMATION_REVIEW_CADENCES,
    AUTOMATION_SCHEDULES,
    SENSITIVITY,
    TRUST_LEVELS,
)
from .core import (
    CarrelError,
    default_profile,
    safe_atomic_write,
    safe_read_text,
    safe_vault_join,
)

_SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
_TEMPLATE_MARKER = re.compile(
    r"^#\s*carrel-template:\s*(?P<name>[a-z0-9-]+)\s+v(?P<version>\d+\.\d+\.\d+)\s*$",
    re.MULTILINE,
)
_AUTOMATION_FLAGS = {
    "enabled",
    "inbox_processing",
    "vault_health",
    "cross_linking_suggestions",
    "gap_analysis",
    "draft_feedback",
    "reflection_synthesis",
    "wiki_maintenance",
}


def _invalid(path: str, message: str) -> None:
    raise CarrelError("Invalid researcher profile", hint=f"{path}: {message}")


def _require_type(value: object, expected: type, path: str) -> None:
    if not isinstance(value, expected):
        _invalid(path, f"must be {expected.__name__}")


def _require_optional_string(value: object, path: str) -> None:
    if value is not None and not isinstance(value, str):
        _invalid(path, "must be a string or null")


def _require_iso_date(value: object, path: str) -> None:
    _require_optional_string(value, path)
    if value is not None:
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            _invalid(path, "must be an ISO date (YYYY-MM-DD)")
            raise AssertionError from exc  # pragma: no cover


def normalize_profile(payload: object) -> dict:
    """Build and validate the complete portable/full shared profile shape."""

    if not isinstance(payload, dict):
        _invalid("$", "must be a JSON object")
    profile = default_profile()
    profile.update({key: value for key, value in payload.items() if key in profile})
    version = payload.get("version")
    if version is not None:
        profile["version"] = version
    supplied_automation = payload.get("automation", {})
    if not isinstance(supplied_automation, dict):
        _invalid("automation", "must be an object")
    automation_defaults = default_profile()["automation"]
    profile["automation"] = {
        **automation_defaults,
        **{
            key: value
            for key, value in supplied_automation.items()
            if key in automation_defaults
        },
    }

    for field in ("name", "field", "wiki_preference", "team_context"):
        _require_optional_string(profile.get(field), field)
    _require_optional_string(profile.get("claude_code_familiarity"), "claude_code_familiarity")
    _require_type(profile.get("comfort_level"), str, "comfort_level")
    for field in ("cloud_consent", "wiki_enabled"):
        _require_type(profile.get(field), bool, field)
    collaborators = profile.get("collaborators")
    if collaborators is not None and not isinstance(collaborators, bool):
        _invalid("collaborators", "must be boolean or null")
    if profile.get("sensitivity") not in SENSITIVITY:
        _invalid("sensitivity", "must be high, medium, or low")
    familiarity = profile.get("claude_code_familiarity")
    if familiarity not in {None, "new", "some", "experienced"}:
        _invalid("claude_code_familiarity", "must be new, some, experienced, or null")
    _require_iso_date(profile.get("wiki_proposal_deferred_until"), "wiki_proposal_deferred_until")

    version = profile.get("version")
    _require_optional_string(version, "version")
    if version is not None and not _SEMVER.fullmatch(version):
        _invalid("version", "must be a semantic version")

    for field in ("tools_configured", "preferences", "model_teammates", "_unknown_keys"):
        _require_type(profile.get(field), dict, field)
    if any(not isinstance(value, bool) for value in profile["tools_configured"].values()):
        _invalid("tools_configured", "values must be boolean")
    teammate_states = {"configured", "interested", "skipped"}
    if any(value not in teammate_states for value in profile["model_teammates"].values()):
        _invalid("model_teammates", "values must be configured, interested, or skipped")

    automation = profile["automation"]
    for field in _AUTOMATION_FLAGS:
        _require_type(automation.get(field), bool, f"automation.{field}")
    if automation.get("trust_level") not in TRUST_LEVELS:
        _invalid("automation.trust_level", "is invalid")
    if automation.get("model") not in AUTOMATION_MODELS:
        _invalid("automation.model", "must be sonnet or opus")
    if automation.get("schedule") not in AUTOMATION_SCHEDULES:
        _invalid("automation.schedule", "must be daily, weekdays, or weekly")
    if automation.get("review_cadence") not in AUTOMATION_REVIEW_CADENCES:
        _invalid("automation.review_cadence", "must be monthly, quarterly, or biannual")
    _require_iso_date(automation.get("last_reviewed"), "automation.last_reviewed")
    return profile


def _read_json(path: Path, *, vault: Path | None = None) -> object:
    try:
        text = safe_read_text(vault, path, encoding="utf-8") if vault else path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CarrelError("Profile file not found", hint=str(path)) from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise CarrelError("Could not read profile file", hint=str(exc)) from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise CarrelError("Invalid researcher profile JSON", hint=f"{path}: {exc.msg}") from exc


def resolve_init_profile(vault: Path, profile_file: Path | None) -> dict:
    """Resolve a valid profile before vault init is allowed to mutate the target."""

    preflight_init_targets(
        vault,
        directories=[".carrel"],
        files=[".carrel/environment.json"],
    )
    profile_path = safe_vault_join(vault, ".carrel", "environment.json")
    existing = normalize_profile(_read_json(profile_path, vault=vault)) if profile_path.exists() else None
    supplied = None
    if profile_file is not None:
        supplied_path = profile_file.expanduser().resolve()
        supplied = normalize_profile(_read_json(supplied_path))
    if existing is not None and supplied is not None and existing != supplied:
        raise CarrelError(
            "Profile conflicts with existing environment.json",
            hint="Use the existing profile or make the supplied profile identical before rerunning init.",
        )
    return supplied or existing or normalize_profile({})


def _preflight_path(vault: Path, relative: str, *, expect_directory: bool) -> None:
    root = vault.expanduser().resolve()
    current = root
    parts = Path(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise CarrelError(
                "Path escapes vault root",
                hint=f"Refusing symlinked init target {current}",
            )
        try:
            current.resolve(strict=False).relative_to(root)
        except ValueError as exc:
            raise CarrelError(
                "Path escapes vault root",
                hint=f"Refusing init target outside {root}: {current}",
            ) from exc
        if index < len(parts) - 1 and current.exists() and not current.is_dir():
            raise CarrelError(
                "Invalid vault scaffold path",
                hint=f"Expected directory but found file: {current}",
            )
    if current.exists() and expect_directory and not current.is_dir():
        raise CarrelError(
            "Invalid vault scaffold path",
            hint=f"Expected directory but found file: {current}",
        )
    if current.exists() and not expect_directory and not current.is_file():
        raise CarrelError(
            "Invalid vault scaffold path",
            hint=f"Expected file but found directory: {current}",
        )


def preflight_init_targets(
    vault: Path,
    *,
    directories: list[str],
    files: list[str],
) -> None:
    """Reject all known init hazards before scaffolding creates anything."""

    if vault.exists() and not vault.is_dir():
        raise CarrelError("Invalid vault path", hint=f"Expected directory: {vault}")
    for relative in directories:
        _preflight_path(vault, relative, expect_directory=True)
    for relative in files:
        _preflight_path(vault, relative, expect_directory=False)


def _scaffold_config(skill_root: Path) -> dict:
    path = skill_root / "assets" / "templates" / "vault-scaffold.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def selected_bases(skill_root: Path, profile: dict) -> list[str]:
    databases = _scaffold_config(skill_root).get("databases", {})
    if not isinstance(databases, dict):
        databases = {}
    selected = set(databases.get("always", ["reading-progress.base"]))
    preferences = profile.get("preferences", {})
    if preferences.get("many_papers") or preferences.get("literature_review"):
        selected.update(databases.get("many_papers", ["paper-tracker.base"]))
    if preferences.get("qualitative") or preferences.get("interviews"):
        selected.update(databases.get("qualitative", ["interview-tracker.base"]))
    if preferences.get("writing") or preferences.get("thesis") or preferences.get("dissertation"):
        selected.update(databases.get("writing", ["writing-tracker.base"]))
    return sorted(name for name in selected if isinstance(name, str) and name.endswith(".base"))


def materialize_bases(vault: Path, skill_root: Path, profile: dict) -> list[str]:
    created: list[str] = []
    template_root = skill_root / "assets" / "templates"
    for name in selected_bases(skill_root, profile):
        source = template_root / name
        if not source.is_file():
            continue
        target = safe_vault_join(vault, name)
        if target.exists():
            continue
        safe_atomic_write(vault, target, source.read_text(encoding="utf-8"))
        created.append(name)
    return created


def detect_template_drift(vault: Path, skill_root: Path) -> tuple[list[str], list[str]]:
    outdated: list[str] = []
    unversioned: list[str] = []
    for source in sorted((skill_root / "assets" / "templates").glob("*.base")):
        current = _TEMPLATE_MARKER.search(source.read_text(encoding="utf-8"))
        target = safe_vault_join(vault, source.name)
        if current is None or not target.exists():
            continue
        try:
            installed = _TEMPLATE_MARKER.search(safe_read_text(vault, target, encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            installed = None
        if installed is None or installed.group("name") != current.group("name"):
            unversioned.append(source.name)
        elif tuple(int(part) for part in installed.group("version").split(".")) < tuple(
            int(part) for part in current.group("version").split(".")
        ):
            outdated.append(source.name)
    return outdated, unversioned
