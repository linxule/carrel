from __future__ import annotations

import tomllib
from pathlib import Path

from carrel.vault.templates import template_root


ROOT = Path(__file__).resolve().parents[1]


def test_wheel_configuration_includes_vault_template_data() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    data_files = pyproject["tool"]["setuptools"]["data-files"]

    assert data_files["share/carrel/templates"] == ["templates/*"]
    assert template_root() == ROOT / "templates"
    assert {path.name for path in template_root().iterdir() if path.is_file()} >= {
        "CLAUDE.md",
        "automation-prompt.md",
        "vault-scaffold.json",
        "obsidian-config.json",
        "reading-progress.base",
    }
