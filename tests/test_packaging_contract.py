from __future__ import annotations

import os
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


def test_installers_provision_the_carrel_cli() -> None:
    # The plugin's hooks and slash commands all spawn an installed `carrel`
    # binary. No install path is complete unless it actually provisions it —
    # this guards against the CLI install step being dropped from either
    # platform script during future edits.
    install_uv_command = "uv tool install git+https://github.com/linxule/carrel.git"
    upgrade_uv_command = "uv tool upgrade carrel"

    install_sh = (ROOT / "install.sh").read_text(encoding="utf-8")
    assert install_uv_command in install_sh
    assert "command -v carrel" in install_sh
    assert upgrade_uv_command in install_sh

    install_ps1 = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert install_uv_command in install_ps1
    assert "Get-Command carrel" in install_ps1
    assert upgrade_uv_command in install_ps1


def test_sync_skill_repo_script_exists_and_is_executable() -> None:
    # skills/carrel is distributed to a dedicated repo via `git subtree push`
    # (same pattern as skills/inquiry -> linxule/inquiry-skill). This script
    # is the only place that command lives — guard against it disappearing
    # or losing the prefix it's scoped to.
    script = ROOT / "scripts" / "sync-skill-repo.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)

    content = script.read_text(encoding="utf-8")
    assert "--prefix=$PREFIX" in content or "--prefix=skills/carrel" in content
    assert 'PREFIX="skills/carrel"' in content
    assert "git subtree push" in content
