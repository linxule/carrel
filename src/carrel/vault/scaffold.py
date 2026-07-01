from __future__ import annotations

import json
from pathlib import Path

from carrel import __version__
from carrel.models import ResearcherProfile, ScaffoldResult, SetupState
from carrel.safe_path import safe_vault_join
from carrel.vault.markers import ensure_markers
from carrel.vault.sync import marker_values
from carrel.vault.templates import (
    BASE_TEMPLATES,
    copy_template,
    load_obsidian_config,
    load_scaffold_config,
    read_template,
    render_cheat_sheet,
)


def _select_bases(scaffold: dict, profile: ResearcherProfile) -> list[str]:
    """Pick which .base templates to include based on profile and scaffold config."""
    db_config = scaffold.get("databases", {})
    bases = set(db_config.get("always", []))
    prefs = profile.preferences

    if prefs.get("many_papers") or prefs.get("literature_review"):
        bases.update(db_config.get("many_papers", []))
    if prefs.get("qualitative") or prefs.get("interviews"):
        bases.update(db_config.get("qualitative", []))
    if prefs.get("writing") or prefs.get("thesis") or prefs.get("dissertation"):
        bases.update(db_config.get("writing", []))

    return sorted(bases)


DEFAULT_PROFILE = ResearcherProfile(
    sensitivity="medium",
    cloud_consent=False,
    comfort_level="beginner",
    tools_configured={},
    preferences={},
)


def _safe_relative(path: Path, base: Path) -> str:
    return str(path.relative_to(base))


def _safe_write(path: Path, content: str) -> tuple[str, str]:
    if path.exists():
        return "skipped", str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created", str(path)


def _enabled_tools(profile: ResearcherProfile) -> str:
    return ",".join(sorted(tool for tool, enabled in profile.tools_configured.items() if enabled))


def _claude_marker_values(profile: ResearcherProfile) -> dict[str, str]:
    return marker_values(profile)


def _render_claude_template(profile: ResearcherProfile) -> str:
    rendered = (
        read_template("CLAUDE.md")
        .replace("{{name}}", profile.name or "Unknown")
        .replace("{{field}}", profile.field or "Unknown")
        .replace("{{sensitivity}}", profile.sensitivity.value)
        .replace("{{cloud_consent}}", str(profile.cloud_consent).lower())
        .replace("{{trust_level}}", profile.automation.trust_level.value)
        .replace("{{wiki_enabled}}", str(profile.wiki_enabled).lower())
        .replace("{{tools_configured}}", _enabled_tools(profile) or "none")
    )
    return ensure_markers(rendered, _claude_marker_values(profile))


def scaffold_vault(path: Path, profile: ResearcherProfile | None = None) -> ScaffoldResult:
    vault = path.expanduser().resolve()
    scaffold = load_scaffold_config()
    obsidian = load_obsidian_config()["files"]
    active_profile = profile or DEFAULT_PROFILE
    created: list[str] = []
    skipped: list[str] = []

    for folder in scaffold["folders"]:
        folder_path = safe_vault_join(vault, folder["path"])
        if folder_path.exists():
            skipped.append(_safe_relative(folder_path, vault))
        else:
            folder_path.mkdir(parents=True, exist_ok=True)
            created.append(_safe_relative(folder_path, vault))

    obsidian_dir = safe_vault_join(vault, ".obsidian")
    if obsidian_dir.exists():
        skipped.append(_safe_relative(obsidian_dir, vault))
    else:
        obsidian_dir.mkdir(parents=True, exist_ok=True)
        created.append(_safe_relative(obsidian_dir, vault))

    for filename, content in obsidian.items():
        rendered = json.dumps(content, indent=2) if not isinstance(content, str) else content
        action, raw_path = _safe_write(obsidian_dir / filename, rendered)
        (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    for name in ["paper.md", "paper-notes.md", "meeting.md", "reflection.md", "daily.md"]:
        target = safe_vault_join(vault, "_templates", name)
        if target.exists():
            skipped.append(_safe_relative(target, vault))
        else:
            copy_template(name, target)
            created.append(_safe_relative(target, vault))

    profile_path = safe_vault_join(vault, ".carrel", "environment.json")
    if profile_path.exists():
        skipped.append(_safe_relative(profile_path, vault))
    else:
        profile_path.write_text(active_profile.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
        created.append(_safe_relative(profile_path, vault))

    setup_state_path = safe_vault_join(vault, ".carrel", "setup-state.json")
    if setup_state_path.exists():
        skipped.append(_safe_relative(setup_state_path, vault))
    else:
        initial_state = SetupState(last_completed_phase=4, version=__version__)
        setup_state_path.write_text(initial_state.model_dump_json(indent=2) + "\n", encoding="utf-8")
        created.append(_safe_relative(setup_state_path, vault))

    cheat_sheet = safe_vault_join(vault, "_meta", "cheat_sheet.md")
    action, raw_path = _safe_write(cheat_sheet, render_cheat_sheet(vault, active_profile))
    (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    env_dashboard = safe_vault_join(vault, "_meta", "my-environment.md")
    action, raw_path = _safe_write(env_dashboard, read_template("my-environment.md"))
    (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    claude_md = safe_vault_join(vault, "CLAUDE.md")
    action, raw_path = _safe_write(claude_md, _render_claude_template(active_profile))
    (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    capability_log = safe_vault_join(vault, "_meta", "capability-log.md")
    action, raw_path = _safe_write(
        capability_log,
        "# Capability Log\n\nCustom capabilities created by Claude in this vault.\n",
    )
    (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    for base_name in _select_bases(scaffold, active_profile):
        target = safe_vault_join(vault, base_name)
        if target.exists():
            skipped.append(_safe_relative(target, vault))
        else:
            copy_template(base_name, target)
            created.append(_safe_relative(target, vault))

    friction_log = safe_vault_join(vault, "_meta", "friction_log.md")
    action, raw_path = _safe_write(
        friction_log,
        "# Friction Log\n\nA running log of issues encountered while using the research environment.\n",
    )
    (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    return ScaffoldResult(vault=vault, profile_path=profile_path, created=created, skipped=skipped)
