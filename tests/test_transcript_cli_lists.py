from __future__ import annotations

from typer.testing import CliRunner

from carrel.cli.main import app

runner = CliRunner()


def test_transcript_list_handles_empty_folder(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / "transcripts").mkdir(parents=True)

    result = runner.invoke(app, ["transcript", "list", "--vault", str(vault)])

    assert result.exit_code == 0
