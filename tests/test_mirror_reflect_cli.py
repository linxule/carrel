from __future__ import annotations

from datetime import date

from typer.testing import CliRunner

from carrel.cli.main import app

runner = CliRunner()


def _seed_vault(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    return vault


def test_vault_mirror_writes_dated_file_from_stdin(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        ["vault", "mirror", "--write", "--from-stdin", "--vault", str(vault)],
        input="# Mirror\n\nReading: institutional theory.\n",
    )
    assert result.exit_code == 0, result.stderr
    # Mirror uses monthly filename for same-month idempotency, per the
    # research-partner skill contract. Re-runs in the same month update the
    # existing file rather than creating one per day.
    target = vault / "_meta" / "mirror" / f"{date.today().strftime('%Y-%m')}.md"
    assert target.exists()
    assert "institutional theory" in target.read_text(encoding="utf-8")


def test_vault_mirror_is_idempotent_on_identical_input(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    body = "# Mirror\n\nSame content.\n"

    first = runner.invoke(
        app,
        ["vault", "mirror", "--write", "--from-stdin", "--vault", str(vault)],
        input=body,
    )
    second = runner.invoke(
        app,
        ["vault", "mirror", "--write", "--from-stdin", "--vault", str(vault)],
        input=body,
    )
    assert first.exit_code == 0, first.stderr
    assert second.exit_code == 0, second.stderr
    assert "skipped" in second.stdout.lower()


def test_vault_mirror_rejects_empty_stdin(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        ["vault", "mirror", "--write", "--from-stdin", "--vault", str(vault)],
        input="",
    )
    assert result.exit_code == 1
    assert "Empty mirror body" in result.stderr


def test_vault_reflect_log_appends_to_dated_file(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    first = runner.invoke(
        app,
        ["vault", "reflect-log", "--append", "--from-stdin", "--vault", str(vault)],
        input="Felt slow on PDF conversion today.",
    )
    second = runner.invoke(
        app,
        ["vault", "reflect-log", "--append", "--from-stdin", "--vault", str(vault)],
        input="Realized I should batch convert.",
    )
    assert first.exit_code == 0, first.stderr
    assert second.exit_code == 0, second.stderr
    # Reflect-log writes to _meta/reflections/reflection-<date>.md, matching
    # the session-reflection skill contract + legacy /carrel-reflect convention.
    target = (
        vault / "_meta" / "reflections" / f"reflection-{date.today().isoformat()}.md"
    )
    body = target.read_text(encoding="utf-8")
    assert "Felt slow on PDF conversion today." in body
    assert "Realized I should batch convert." in body
    # Two timestamped entries means two `## ` headers under the title.
    assert body.count("## ") >= 2


def test_vault_reflect_log_requires_flags(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        ["vault", "reflect-log", "--vault", str(vault)],
    )
    assert result.exit_code == 1
    assert "requires --append" in result.stderr
