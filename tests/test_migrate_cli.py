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


def test_migrate_first_run_dry_run_reports_future_write_without_state(tmp_path) -> None:
    plugin = _seed_plugin_root(tmp_path, version="0.9.0")
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        [
            "migrate",
            "apply",
            "--plugin-root",
            str(plugin),
            "--vault",
            str(vault),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Would record plugin_version=0.9.0" in result.stdout
    assert "plugin-state.json was NOT written" in result.stdout
    assert not (vault / ".carrel" / "plugin-state.json").exists()


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


def test_migrate_plan_reports_template_drift_without_overwriting(tmp_path) -> None:
    plugin = _seed_plugin_root(tmp_path, version="0.9.0")
    templates = plugin / "templates"
    templates.mkdir()
    (templates / "reading-progress.base").write_text(
        "# carrel-template: reading-progress v0.4.0\ncurrent\n",
        encoding="utf-8",
    )
    (templates / "paper-tracker.base").write_text(
        "# carrel-template: paper-tracker v0.4.0\ncurrent\n",
        encoding="utf-8",
    )
    vault = _seed_vault(tmp_path, last_seen="0.9.0")
    reading = vault / "reading-progress.base"
    reading.write_text(
        "# carrel-template: reading-progress v0.3.0\ncustom reading\n",
        encoding="utf-8",
    )
    paper = vault / "paper-tracker.base"
    paper.write_text("# custom paper tracker\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "migrate",
            "apply",
            "--plugin-root",
            str(plugin),
            "--vault",
            str(vault),
            "--dry-run",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["outdated_templates"] == ["reading-progress.base"]
    assert payload["unversioned_templates"] == ["paper-tracker.base"]
    assert reading.read_text(encoding="utf-8").endswith("custom reading\n")
    assert paper.read_text(encoding="utf-8") == "# custom paper tracker\n"
    assert not (vault / ".carrel" / "plugin-state.json.tmp").exists()


def test_migrate_rejects_symlinked_tracker_without_external_read_or_state_write(
    tmp_path,
    monkeypatch,
) -> None:
    plugin = _seed_plugin_root(tmp_path, version="0.9.0")
    templates = plugin / "templates"
    templates.mkdir()
    (templates / "reading-progress.base").write_text(
        "# carrel-template: reading-progress v0.4.0\ncurrent\n",
        encoding="utf-8",
    )
    vault = _seed_vault(tmp_path, last_seen="0.8.1")
    state_path = vault / ".carrel" / "plugin-state.json"
    original_state = state_path.read_bytes()
    outside = tmp_path / "outside.base"
    outside.write_text(
        "# carrel-template: reading-progress v0.3.0\nprivate\n",
        encoding="utf-8",
    )
    (vault / "reading-progress.base").symlink_to(outside)
    original_read_text = Path.read_text

    def guarded_read_text(path: Path, *args, **kwargs):
        if path.resolve() == outside.resolve():
            raise AssertionError("external tracker was read")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    result = runner.invoke(
        app,
        [
            "migrate",
            "apply",
            "--plugin-root",
            str(plugin),
            "--vault",
            str(vault),
        ],
    )

    assert result.exit_code == 1
    assert not isinstance(result.exception, AssertionError)
    assert "Refusing symlinked vault template" in result.stderr
    assert state_path.read_bytes() == original_state
    assert outside.read_bytes().endswith(b"private\n")
