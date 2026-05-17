from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import ResearcherProfile, Sensitivity

runner = CliRunner()


def _seed_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    profile = ResearcherProfile(name="Ada", sensitivity=Sensitivity.LOW, cloud_consent=False)
    (vault / ".carrel" / "environment.json").write_text(
        profile.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )
    return vault


def test_batch_convert_empty_folder_succeeds_with_no_outcomes(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    result = runner.invoke(
        app,
        [
            "batch",
            "convert",
            str(inbox),
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout) == []


def test_batch_convert_missing_folder_errors(tmp_path) -> None:
    vault = _seed_vault(tmp_path)

    result = runner.invoke(
        app,
        ["batch", "convert", str(tmp_path / "does-not-exist"), "--vault", str(vault)],
    )
    assert result.exit_code == 1
    assert "Folder not found" in result.stderr


def test_batch_convert_unattended_defers_failing_file(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    # A bogus 'PDF' that has the right extension but will fail conversion.
    (inbox / "broken.pdf").write_text("not a pdf", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "batch",
            "convert",
            str(inbox),
            "--vault",
            str(vault),
            "--unattended",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload, "expected at least one outcome"
    assert payload[0]["action"] == "deferred"
    pending = vault / "_meta" / "pending-decisions.md"
    assert pending.exists()
    assert "broken.pdf" in pending.read_text(encoding="utf-8")


def test_batch_convert_unattended_deduplicates_pending_decisions(tmp_path) -> None:
    """Re-running the same unattended batch must not stack duplicate rows."""
    vault = _seed_vault(tmp_path)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "broken.pdf").write_text("not a pdf", encoding="utf-8")

    args = [
        "batch",
        "convert",
        str(inbox),
        "--vault",
        str(vault),
        "--unattended",
        "--format",
        "json",
    ]
    runner.invoke(app, args)
    runner.invoke(app, args)  # second identical run

    pending = vault / "_meta" / "pending-decisions.md"
    content = pending.read_text(encoding="utf-8")
    assert content.count("broken.pdf") == 1, (
        "expected dedupe by exact row match; second run should not append"
    )


def test_batch_transcribe_empty_folder_succeeds_with_no_outcomes(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    inbox = tmp_path / "inbox"
    inbox.mkdir()

    result = runner.invoke(
        app,
        [
            "batch",
            "transcribe",
            str(inbox),
            "--vault",
            str(vault),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    assert json.loads(result.stdout) == []


def test_batch_transcribe_rejects_non_directory(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    file = tmp_path / "single.m4a"
    file.write_text("", encoding="utf-8")

    result = runner.invoke(
        app,
        ["batch", "transcribe", str(file), "--vault", str(vault)],
    )
    assert result.exit_code == 1
    assert "Not a directory" in result.stderr


def test_batch_transcribe_unattended_defers_empty_url_list(tmp_path) -> None:
    vault = _seed_vault(tmp_path)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "urls.txt").write_text("# only a comment\n\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "batch",
            "transcribe",
            str(inbox),
            "--vault",
            str(vault),
            "--unattended",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload and payload[0]["action"] == "deferred"
    pending = vault / "_meta" / "pending-decisions.md"
    assert pending.exists()
    assert "URL list is empty" in pending.read_text(encoding="utf-8")


def test_batch_transcribe_forwards_kind_flag(tmp_path) -> None:
    """Skill→CLI contract: batch transcribe must accept --kind and forward
    it to each `carrel transcript create` subprocess. The transcribe SKILL.md
    documents `--kind interview|meeting|lecture|recording`."""
    vault = _seed_vault(tmp_path)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    # Bogus audio so the subprocess fails but we can still observe deferral.
    (inbox / "demo.m4a").write_bytes(b"not real audio")

    result = runner.invoke(
        app,
        [
            "batch",
            "transcribe",
            str(inbox),
            "--vault",
            str(vault),
            "--kind",
            "interview",
            "--unattended",
            "--format",
            "json",
        ],
    )
    # Exit code must be 0 — the kind flag must not be rejected by typer
    # (rejection would manifest as exit code 2 with "no such option").
    assert result.exit_code == 0, result.stderr


def test_batch_transcribe_recognizes_extended_audio_extensions(tmp_path) -> None:
    """Audio extensions list must include .mov .ogg .flac per the transcribe
    SKILL.md. Earlier builds silently skipped these formats."""
    vault = _seed_vault(tmp_path)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    for ext in (".mov", ".ogg", ".flac"):
        (inbox / f"clip{ext}").write_bytes(b"placeholder")

    result = runner.invoke(
        app,
        [
            "batch",
            "transcribe",
            str(inbox),
            "--vault",
            str(vault),
            "--unattended",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    seen_names = {Path(o["file"]).name for o in payload}
    assert {"clip.mov", "clip.ogg", "clip.flac"}.issubset(seen_names)
