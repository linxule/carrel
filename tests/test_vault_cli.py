from __future__ import annotations

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
