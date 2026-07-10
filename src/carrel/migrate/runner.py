"""Migration registry walker + plugin-state writer.

Reads ``migrations/registry.json`` from the plugin-root, compares against
``.carrel/plugin-state.json`` in the vault, returns the ordered list of
pending migrations, and (after the caller acknowledges) writes the new
plugin-state.json atomically.

Per-migration narration (the prose researchers should read) stays in the
calling skill — this module just walks the registry and updates state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from carrel.errors import CarrelError
from carrel.vault.template_drift import detect_template_drift

PLUGIN_MANIFEST = Path(".claude-plugin") / "plugin.json"
REGISTRY_FILE = Path("migrations") / "registry.json"
PLUGIN_STATE = Path(".carrel") / "plugin-state.json"


@dataclass(frozen=True)
class MigrationEntry:
    from_version: str
    to_version: str
    file: str
    breaking: bool
    summary: str


@dataclass(frozen=True)
class MigrationPlan:
    current_version: str
    last_seen_version: str | None
    pending: list[MigrationEntry]
    first_run: bool
    outdated_templates: list[str]
    unversioned_templates: list[str]


def _parse_version_tuple(version: str) -> tuple[int, ...]:
    parts = version.split("-")[0].split("+")[0].split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError as error:
        raise CarrelError(
            f"Invalid version string: {version}",
            hint="Expected semver like 0.9.0 (numeric segments only before -/+).",
        ) from error


def _read_plugin_version(plugin_root: Path) -> str:
    manifest_path = plugin_root / PLUGIN_MANIFEST
    if not manifest_path.exists():
        raise CarrelError(
            f"Plugin manifest not found: {manifest_path}",
            hint="Pass --plugin-root pointing at the installed plugin directory.",
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise CarrelError(
            f"Could not parse {manifest_path}",
            hint="Re-install the plugin to restore a valid manifest.",
        ) from error
    version = manifest.get("version")
    if not isinstance(version, str):
        raise CarrelError(
            f"plugin.json missing 'version' field: {manifest_path}",
            hint="The plugin's manifest must include a semver `version` string.",
        )
    return version


def _read_registry(plugin_root: Path) -> list[MigrationEntry]:
    registry_path = plugin_root / REGISTRY_FILE
    if not registry_path.exists():
        raise CarrelError(
            f"Migration registry not found: {registry_path}",
            hint="The plugin appears incomplete. Re-install or pass --plugin-root.",
        )
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise CarrelError(
            f"Could not parse {registry_path}",
            hint="The registry file is corrupted; restore from a fresh plugin install.",
        ) from error
    entries: list[MigrationEntry] = []
    for raw in payload.get("migrations", []):
        try:
            entries.append(
                MigrationEntry(
                    from_version=str(raw["from"]),
                    to_version=str(raw["to"]),
                    file=str(raw["file"]),
                    breaking=bool(raw.get("breaking", False)),
                    summary=str(raw.get("summary", "")),
                )
            )
        except KeyError as error:
            raise CarrelError(
                f"Malformed migration entry in {registry_path}: missing {error}",
                hint="Each entry must include `from`, `to`, and `file`.",
            ) from error
    return entries


def _read_plugin_state(vault: Path) -> dict | None:
    state_path = vault / PLUGIN_STATE
    if not state_path.exists():
        return None
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise CarrelError(
            f"Could not parse {state_path}",
            hint="Delete .carrel/plugin-state.json to treat the vault as a fresh install.",
        ) from error


def plan_migrations(vault: Path, plugin_root: Path) -> MigrationPlan:
    """Read manifest + registry + plugin-state and return the ordered pending list."""

    current = _read_plugin_version(plugin_root)
    registry = _read_registry(plugin_root)
    state = _read_plugin_state(vault)
    last_seen = (state or {}).get("plugin_version") if state else None
    template_drift = detect_template_drift(
        vault,
        source_root=plugin_root / "templates",
    )

    if last_seen is None:
        # Fresh install: no migrations to apply (state file will simply be created).
        return MigrationPlan(
            current_version=current,
            last_seen_version=None,
            pending=[],
            first_run=True,
            outdated_templates=template_drift.outdated_templates,
            unversioned_templates=template_drift.unversioned_templates,
        )

    if last_seen == current:
        return MigrationPlan(
            current_version=current,
            last_seen_version=last_seen,
            pending=[],
            first_run=False,
            outdated_templates=template_drift.outdated_templates,
            unversioned_templates=template_drift.unversioned_templates,
        )

    try:
        last_tuple = _parse_version_tuple(last_seen)
        current_tuple = _parse_version_tuple(current)
    except CarrelError:
        # Re-raise — _parse_version_tuple already produced an actionable hint.
        raise

    pending = [
        entry
        for entry in registry
        if last_tuple < _parse_version_tuple(entry.to_version) <= current_tuple
    ]
    pending.sort(key=lambda entry: _parse_version_tuple(entry.to_version))

    return MigrationPlan(
        current_version=current,
        last_seen_version=last_seen,
        pending=pending,
        first_run=False,
        outdated_templates=template_drift.outdated_templates,
        unversioned_templates=template_drift.unversioned_templates,
    )


def write_plugin_state(
    vault: Path,
    plugin_version: str,
    *,
    install_source: str = "marketplace",
    today: str | None = None,
) -> Path:
    """Atomically write ``.carrel/plugin-state.json``."""

    state_path = vault / PLUGIN_STATE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "plugin_version": plugin_version,
        "last_migrated": today or date.today().isoformat(),
        "install_source": install_source,
    }
    tmp = state_path.parent / f"{state_path.name}.tmp"
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(state_path)
    return state_path
