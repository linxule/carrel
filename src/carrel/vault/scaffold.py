from __future__ import annotations

import json
from pathlib import Path

from carrel.models import ResearcherProfile, ScaffoldResult
from carrel.vault.templates import copy_template, load_obsidian_config, load_scaffold_config, render_cheat_sheet

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


def scaffold_vault(path: Path, profile: ResearcherProfile | None = None) -> ScaffoldResult:
    vault = path.expanduser().resolve()
    scaffold = load_scaffold_config()
    obsidian = load_obsidian_config()["files"]
    active_profile = profile or DEFAULT_PROFILE
    created: list[str] = []
    skipped: list[str] = []

    for folder in scaffold["folders"]:
        folder_path = vault / folder["path"]
        if folder_path.exists():
            skipped.append(_safe_relative(folder_path, vault))
        else:
            folder_path.mkdir(parents=True, exist_ok=True)
            created.append(_safe_relative(folder_path, vault))

    obsidian_dir = vault / ".obsidian"
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
        target = vault / "_templates" / name
        if target.exists():
            skipped.append(_safe_relative(target, vault))
        else:
            copy_template(name, target)
            created.append(_safe_relative(target, vault))

    profile_path = vault / ".carrel" / "environment.json"
    if profile_path.exists():
        skipped.append(_safe_relative(profile_path, vault))
    else:
        profile_path.write_text(active_profile.model_dump_json(indent=2), encoding="utf-8")
        created.append(_safe_relative(profile_path, vault))

    cheat_sheet = vault / "_meta" / "cheat_sheet.md"
    action, raw_path = _safe_write(cheat_sheet, render_cheat_sheet(vault, active_profile))
    (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    friction_log = vault / "_meta" / "friction_log.md"
    action, raw_path = _safe_write(
        friction_log,
        "# Friction Log\n\nA running log of issues encountered while using the research environment.\n",
    )
    (created if action == "created" else skipped).append(_safe_relative(Path(raw_path), vault))

    return ScaffoldResult(vault=vault, profile_path=profile_path, created=created, skipped=skipped)
