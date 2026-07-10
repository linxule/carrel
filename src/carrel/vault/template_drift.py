from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from carrel.errors import CarrelError
from carrel.safe_path import safe_vault_join
from carrel.vault.templates import BASE_TEMPLATES, template_root

_TEMPLATE_MARKER = re.compile(
    r"^#\s*carrel-template:\s*(?P<name>[a-z0-9-]+)\s+v(?P<version>\d+\.\d+\.\d+)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class TemplateDrift:
    outdated_templates: list[str]
    unversioned_templates: list[str]


def _marker(path: Path) -> tuple[str, tuple[int, int, int]] | None:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = _TEMPLATE_MARKER.search(content)
    if match is None:
        return None
    version = tuple(int(part) for part in match.group("version").split("."))
    return match.group("name"), version  # type: ignore[return-value]


def detect_template_drift(
    vault: Path,
    *,
    source_root: Path | None = None,
) -> TemplateDrift:
    """Report stale known root trackers without modifying vault content."""

    bundled_root = source_root or template_root()
    vault_root = vault.expanduser().resolve()
    outdated: list[str] = []
    unversioned: list[str] = []

    for filename in BASE_TEMPLATES:
        lexical_target = vault_root / filename
        if lexical_target.is_symlink():
            raise CarrelError(
                f"Refusing symlinked vault template: {lexical_target}",
                hint="Replace the symlink with a regular .base file inside the vault.",
            )
        target = safe_vault_join(vault_root, filename)
        source_marker = _marker(bundled_root / filename)
        if source_marker is None or not target.is_file():
            continue
        target_marker = _marker(target)
        if target_marker is None or target_marker[0] != source_marker[0]:
            unversioned.append(filename)
        elif target_marker[1] < source_marker[1]:
            outdated.append(filename)

    return TemplateDrift(
        outdated_templates=outdated,
        unversioned_templates=unversioned,
    )
