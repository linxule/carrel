from __future__ import annotations

import json
import os
import subprocess
import sys
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


AGENT_PLUGINS_1_0_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_agent_plugin_manifest_and_marketplaces_point_to_package() -> None:
    """One package, every host's manifest rules (checked against host docs 2026-11).

    * Agent Plugins 1.0 (Copilot CLI/app, Codex): root ``plugin.json``, closed
      top-level schema, skills auto-discovered from ``skills/`` (no ``skills``
      field allowed).
    * Copilot marketplace: ``.github/plugin/marketplace.json`` needs ``name``,
      ``owner``, and ``plugins[].{name,source}``.
    * Codex marketplace: ``.agents/plugins/marketplace.json`` entries need
      ``policy.installation``, ``policy.authentication``, and ``category``;
      ``source.path`` must start with ``./``.
    """
    plugin_root = ROOT / "plugins" / "carrel"
    manifest = _json(plugin_root / "plugin.json")
    assert manifest["$schema"] == (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    )
    assert manifest["name"] == "carrel"
    assert set(manifest) <= AGENT_PLUGINS_1_0_FIELDS
    assert (plugin_root / "skills" / "carrel" / "SKILL.md").is_file()

    copilot_catalog = _json(ROOT / ".github" / "plugin" / "marketplace.json")
    assert copilot_catalog["name"] == "carrel"
    assert copilot_catalog["owner"]["name"]
    copilot_entry = copilot_catalog["plugins"][0]
    assert copilot_entry["name"] == manifest["name"]
    assert copilot_entry["source"] == "./plugins/carrel"

    codex_catalog = _json(ROOT / ".agents" / "plugins" / "marketplace.json")
    codex_entry = codex_catalog["plugins"][0]
    assert codex_entry["name"] == manifest["name"]
    assert codex_entry["source"] == {"source": "local", "path": "./plugins/carrel"}
    assert codex_entry["policy"]["installation"] in {
        "AVAILABLE",
        "INSTALLED_BY_DEFAULT",
        "NOT_AVAILABLE",
    }
    assert codex_entry["policy"]["authentication"]
    assert codex_entry["category"]


def test_kimi_manifests_expose_only_the_portable_skill() -> None:
    """Kimi Code reads ``kimi.plugin.json`` (not ``plugin.json``) and does NOT
    auto-discover ``skills/`` -- the ``skills`` path must be explicit.

    The repo-root manifest makes ``/plugins install https://github.com/linxule/carrel``
    work; it must point at the packaged portable skill only, never the root
    ``skills/`` tree, whose other skills assume Claude-only hooks/commands.
    """
    for manifest_path, skills_path in [
        (ROOT / "kimi.plugin.json", "./plugins/carrel/skills/"),
        (ROOT / "plugins" / "carrel" / "kimi.plugin.json", "./skills/"),
    ]:
        manifest = _json(manifest_path)
        assert manifest["name"] == "carrel"
        assert manifest["skills"] == skills_path
        skills_root = manifest_path.parent / skills_path
        assert [p.parent.name for p in skills_root.glob("*/SKILL.md")] == ["carrel"]


def test_agent_plugin_skill_copy_matches_canonical_source() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync-agent-plugin.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_skill_zip_matches_claude_upload_layout(tmp_path) -> None:
    """Claude.ai rejects an upload whose root folder name differs from the
    skill name, so the archive must hold exactly ``carrel/`` with SKILL.md in it.
    """
    import zipfile

    output = tmp_path / "carrel.zip"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build-skill-zip.py"), "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    names = zipfile.ZipFile(output).namelist()
    assert {name.split("/", 1)[0] for name in names} == {"carrel"}
    assert "carrel/SKILL.md" in names
    assert "carrel/scripts/carrel.py" in names
    assert not [n for n in names if "__pycache__" in n or n.endswith((".pyc", ".DS_Store"))]
    canonical = {
        p.relative_to(ROOT / "skills" / "carrel").as_posix()
        for p in (ROOT / "skills" / "carrel").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and p.name != ".DS_Store"
    }
    assert {name.removeprefix("carrel/") for name in names} == canonical


def test_portable_skill_does_not_defer_to_a_machine_wide_cli() -> None:
    """install.sh installs the typed CLI machine-wide. If the portable skill
    told agents to stand down whenever that CLI exists, Codex, Copilot, and Kimi
    users who ran the installer would get a skill that refuses to run.
    """
    text = (ROOT / "skills" / "carrel" / "SKILL.md").read_text(encoding="utf-8")
    description = text.split("description:", 1)[1].split("\n", 1)[0]
    assert "installed carrel CLI is available" not in description
    assert "even if the carrel CLI is installed" in description
