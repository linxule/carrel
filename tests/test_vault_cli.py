from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app

runner = CliRunner()


def test_vault_cheatsheet_wraps_invalid_profile_errors(tmp_path) -> None:
    vault = tmp_path / "vault"
    carrel_dir = vault / ".carrel"
    carrel_dir.mkdir(parents=True)
    (carrel_dir / "environment.json").write_text('{"name": "Ada", "sensitivity": "prefer_local"}', encoding="utf-8")

    result = runner.invoke(app, ["vault", "cheatsheet", "--vault", str(vault)])

    assert result.exit_code == 1
    assert "Could not parse" in result.stderr
    assert "/carrel-setup" in result.stderr


def test_env_profile_wraps_corrupted_profile_errors(tmp_path) -> None:
    vault = tmp_path / "vault"
    carrel_dir = vault / ".carrel"
    carrel_dir.mkdir(parents=True)
    (carrel_dir / "environment.json").write_text("{not json}", encoding="utf-8")

    result = runner.invoke(app, ["env", "profile", "--vault", str(vault)])

    assert result.exit_code == 1
    assert "Could not parse" in result.stderr
    assert "Run /carrel-setup to regenerate it." in result.stderr


def test_vault_status_quiet_prints_only_vault_path(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)

    result = runner.invoke(app, ["vault", "status", "--vault", str(vault), "--format", "quiet"])

    assert result.exit_code == 0
    assert result.stdout == f"{vault.resolve()}\n"
    assert Path(result.stdout.strip()).resolve() == vault.resolve()


def test_vault_new_creates_note_file(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)

    result = runner.invoke(app, ["vault", "new", "Weekly Sync", "--vault", str(vault)])

    assert result.exit_code == 0
    assert (vault / "notes" / "weekly_sync.md").exists()


def test_vault_new_rejects_path_traversal_name(tmp_path) -> None:
    vault = tmp_path / "vault"
    outside = tmp_path / "escape.md"
    (vault / ".carrel").mkdir(parents=True)

    result = runner.invoke(app, ["vault", "new", "../escape", "--vault", str(vault)])

    assert result.exit_code == 1
    assert "Path traversal is not allowed" in result.stderr
    assert not outside.exists()


def test_vault_search_handles_empty_vault(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)

    result = runner.invoke(app, ["vault", "search", "query", "--vault", str(vault)])

    assert result.exit_code == 0


def test_vault_status_human_and_quiet_succeed(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)

    human = runner.invoke(app, ["vault", "status", "--vault", str(vault)])
    quiet = runner.invoke(app, ["vault", "status", "--vault", str(vault), "--format", "quiet"])

    assert human.exit_code == 0
    assert "Vault:" in human.stdout
    assert "papers/ 0 files" in human.stdout
    assert quiet.exit_code == 0
    assert quiet.stdout == f"{vault.resolve()}\n"


def test_vault_organize_handles_empty_vault(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)

    result = runner.invoke(app, ["vault", "organize", "--vault", str(vault)])

    assert result.exit_code == 0
