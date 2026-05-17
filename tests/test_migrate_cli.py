from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app

runner = CliRunner()


def _seed_plugin_root(tmp_path: Path, version: str = "0.9.0") -> Path:
    plugin = tmp_path / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / "migrations").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "carrel", "version": version}),
        encoding="utf-8",
    )
    registry = {
        "migrations": [
            {
                "from": "0.7.1",
                "to": "0.8.1",
                "file": "0.7.1-to-0.8.1.md",
                "breaking": False,
                "summary": "Model teammates",
            },
            {
                "from": "0.8.1",
                "to": "0.9.0",
                "file": "0.8.1-to-0.9.0.md",
                "breaking": False,
                "summary": "CC plugin v0.9.0",
            },
        ]
    }
    (plugin / "migrations" / "registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )
    return plugin


def _seed_vault(tmp_path: Path, last_seen: str | None = None) -> Path:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    if last_seen is not None:
        (vault / ".carrel" / "plugin-state.json").write_text(
            json.dumps(
                {"plugin_version": last_seen, "install_source": "marketplace"}
            ),
            encoding="utf-8",
        )
    return vault


def test_migrate_apply_writes_plugin_state_and_reports_pending(tmp_path) -> None:
    plugin = _seed_plugin_root(tmp_path, version="0.9.0")
    vault = _seed_vault(tmp_path, last_seen="0.7.1")

    result = runner.invoke(
        app,
        [
            "migrate",
            "apply",
            "--plugin-root",
            str(plugin),
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["current_version"] == "0.9.0"
    assert payload["last_seen_version"] == "0.7.1"
    assert [m["to"] for m in payload["pending"]] == ["0.8.1", "0.9.0"]
    state_path = vault / ".carrel" / "plugin-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["plugin_version"] == "0.9.0"


def test_migrate_apply_errors_without_plugin_root_or_env(tmp_path, monkeypatch) -> None:
    vault = _seed_vault(tmp_path)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)

    result = runner.invoke(
        app,
        ["migrate", "apply", "--vault", str(vault)],
    )
    assert result.exit_code == 1
    assert "Plugin root not specified" in result.stderr


def test_migrate_apply_first_run_records_state_without_pending(tmp_path) -> None:
    plugin = _seed_plugin_root(tmp_path, version="0.9.0")
    vault = _seed_vault(tmp_path)  # no plugin-state yet

    result = runner.invoke(
        app,
        [
            "migrate",
            "apply",
            "--plugin-root",
            str(plugin),
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["first_run"] is True
    assert payload["pending"] == []
    state_path = vault / ".carrel" / "plugin-state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["plugin_version"] == "0.9.0"


def test_migrate_apply_picks_up_env_var_when_flag_omitted(tmp_path, monkeypatch) -> None:
    plugin = _seed_plugin_root(tmp_path, version="0.9.0")
    vault = _seed_vault(tmp_path, last_seen="0.8.1")
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin))

    result = runner.invoke(
        app,
        ["migrate", "apply", "--vault", str(vault), "--format", "json"],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["current_version"] == "0.9.0"
    assert [m["to"] for m in payload["pending"]] == ["0.9.0"]
