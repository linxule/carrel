from __future__ import annotations

import json
import tomllib
from pathlib import Path

from carrel import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_all_packaged_versions_match() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    agent_plugin = json.loads(
        (ROOT / "plugins" / "carrel" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    copilot_marketplace = json.loads(
        (ROOT / ".github" / "plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    kimi_manifests = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (ROOT / "kimi.plugin.json", ROOT / "plugins" / "carrel" / "kimi.plugin.json")
    ]

    versions = {
        pyproject["project"]["version"],
        __version__,
        plugin["version"],
        agent_plugin["version"],
        marketplace["plugins"][0]["version"],
        copilot_marketplace["plugins"][0]["version"],
        *(manifest["version"] for manifest in kimi_manifests),
    }

    assert len(versions) == 1


def test_current_version_has_a_registered_migration_note() -> None:
    """The release workflow publishes this note as the release body and refuses
    to release without it; catch a missing note at PR time instead."""
    registry = json.loads((ROOT / "migrations" / "registry.json").read_text(encoding="utf-8"))
    entries = [e for e in registry["migrations"] if e["to"] == __version__]
    assert len(entries) == 1, f"add one migrations/registry.json entry with to={__version__}"
    note = ROOT / "migrations" / entries[0]["file"]
    assert note.is_file(), note
    assert note.read_text(encoding="utf-8").strip()
