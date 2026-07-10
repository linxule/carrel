from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import ResearcherProfile

runner = CliRunner()


def _write_profile(path: Path, **updates: object) -> ResearcherProfile:
    profile = ResearcherProfile(**updates)
    path.write_text(profile.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    return profile


def test_vault_init_profile_file_selects_all_requested_trackers(tmp_path) -> None:
    profile_path = tmp_path / "profile.json"
    profile = _write_profile(
        profile_path,
        name="Ada",
        preferences={
            "many_papers": True,
            "interviews": True,
            "dissertation": True,
        },
    )
    vault = tmp_path / "vault"

    result = runner.invoke(
        app,
        [
            "vault",
            "init",
            str(vault),
            "--profile-file",
            str(profile_path),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["outdated_templates"] == []
    assert payload["unversioned_templates"] == []
    stored = ResearcherProfile.model_validate_json(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )
    assert stored == profile
    for tracker in [
        "reading-progress.base",
        "paper-tracker.base",
        "interview-tracker.base",
        "writing-tracker.base",
    ]:
        assert (vault / tracker).exists()


def test_vault_init_reuses_existing_profile_when_option_is_absent(tmp_path) -> None:
    profile_path = tmp_path / "profile.json"
    _write_profile(profile_path, preferences={"literature_review": True})
    vault = tmp_path / "vault"
    first = runner.invoke(
        app,
        ["vault", "init", str(vault), "--profile-file", str(profile_path)],
    )
    assert first.exit_code == 0, first.stderr
    tracker = vault / "paper-tracker.base"
    tracker.unlink()

    second = runner.invoke(app, ["vault", "init", str(vault), "--format", "json"])

    assert second.exit_code == 0, second.stderr
    assert tracker.exists()


def test_vault_init_accepts_identical_profile_and_rejects_conflict(tmp_path) -> None:
    original_path = tmp_path / "original.json"
    original = _write_profile(original_path, name="Ada", preferences={"many_papers": True})
    vault = tmp_path / "vault"
    first = runner.invoke(
        app,
        ["vault", "init", str(vault), "--profile-file", str(original_path)],
    )
    assert first.exit_code == 0, first.stderr

    identical_path = tmp_path / "identical.json"
    identical_path.write_text(original.model_dump_json(), encoding="utf-8")
    identical = runner.invoke(
        app,
        [
            "vault",
            "init",
            str(vault),
            "--profile-file",
            str(identical_path),
            "--format",
            "json",
        ],
    )
    assert identical.exit_code == 0, identical.stderr
    assert json.loads(identical.stdout)["created"] == []

    conflict_path = tmp_path / "conflict.json"
    _write_profile(conflict_path, name="Grace", preferences={"writing": True})
    conflict = runner.invoke(
        app,
        ["vault", "init", str(vault), "--profile-file", str(conflict_path)],
    )

    assert conflict.exit_code == 1
    assert "Profile conflicts with existing vault profile" in conflict.stderr
    assert not (vault / "writing-tracker.base").exists()
    stored = ResearcherProfile.model_validate_json(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )
    assert stored == original


def test_vault_init_invalid_profile_does_not_create_partial_vault(tmp_path) -> None:
    profile_path = tmp_path / "invalid.json"
    profile_path.write_text('{"sensitivity": "extreme"}', encoding="utf-8")
    vault = tmp_path / "vault"

    result = runner.invoke(
        app,
        ["vault", "init", str(vault), "--profile-file", str(profile_path)],
    )

    assert result.exit_code == 1
    assert "Could not parse profile file" in result.stderr
    assert not vault.exists()


def test_vault_init_invalid_existing_profile_does_not_extend_vault(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / ".carrel" / "environment.json").write_text(
        '{"sensitivity": "extreme"}',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 1
    assert "Could not parse existing profile" in result.stderr
    assert sorted(path.relative_to(vault) for path in vault.rglob("*")) == [
        Path(".carrel"),
        Path(".carrel/environment.json"),
    ]


def test_vault_init_repairable_profile_hint_points_to_env_fix(tmp_path) -> None:
    """Parseable-but-invalid JSON is repairable: hard-fail, but point at the tools."""
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / ".carrel" / "environment.json").write_text(
        '{"sensitivity": "extreme"}',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 1
    assert "Could not parse existing profile" in result.stderr
    assert "carrel env validate" in result.stderr
    assert "carrel env fix --safe" in result.stderr
    # Left in place for the researcher to repair — not backed up.
    assert not list((vault / ".carrel").glob("environment.json.corrupt-*"))
    assert (vault / ".carrel" / "environment.json").read_text(encoding="utf-8") == (
        '{"sensitivity": "extreme"}'
    )


def test_vault_init_recovers_from_corrupt_existing_profile(tmp_path) -> None:
    """Unparseable JSON is unrepairable: back it up and proceed with a fresh profile."""
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / ".carrel" / "environment.json").write_text("{not valid json", encoding="utf-8")

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 0, result.stderr
    # Corrupt file moved aside (not left in place, not overwritten silently).
    backups = list((vault / ".carrel").glob("environment.json.corrupt-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "{not valid json"
    # A fresh, valid default profile now exists.
    stored = ResearcherProfile.model_validate_json(
        (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    )
    assert stored.sensitivity.value == "medium"
    # The vault was actually scaffolded, not left half-built.
    assert (vault / "papers").is_dir()
    assert (vault / "_meta" / "cheat_sheet.md").exists()
    # Loud, actionable warning naming the backup surfaced on stderr.
    assert "was not valid JSON" in result.stderr
    assert "corrupt-" in result.stderr


def test_vault_init_corrupt_backup_does_not_overwrite_existing_backup(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / ".carrel" / "environment.json").write_text("{bad", encoding="utf-8")
    # A backup with today's timestamp could already exist from a prior recovery.
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    prior = vault / ".carrel" / f"environment.json.corrupt-{stamp}"
    prior.write_text("earlier backup", encoding="utf-8")

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 0, result.stderr
    assert prior.read_text(encoding="utf-8") == "earlier backup"
    backups = sorted((vault / ".carrel").glob("environment.json.corrupt-*"))
    assert len(backups) == 2


def test_vault_init_rejects_symlinked_profile_before_scaffold_mutation(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    outside_profile = tmp_path / "outside-profile.json"
    original = ResearcherProfile(name="Outside").model_dump_json(indent=2)
    outside_profile.write_text(original, encoding="utf-8")
    profile_link = vault / ".carrel" / "environment.json"
    profile_link.symlink_to(outside_profile)

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 1
    assert "Refusing symlinked vault profile path" in result.stderr
    assert profile_link.is_symlink()
    assert outside_profile.read_text(encoding="utf-8") == original
    assert sorted(path.relative_to(vault) for path in vault.rglob("*")) == [
        Path(".carrel"),
        Path(".carrel/environment.json"),
    ]


def test_vault_init_rejects_symlinked_tracker_without_external_read_or_writes(
    tmp_path,
    monkeypatch,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside.base"
    outside.write_text(
        "# carrel-template: reading-progress v0.0.1\nprivate\n",
        encoding="utf-8",
    )
    tracker = vault / "reading-progress.base"
    tracker.symlink_to(outside)
    original_read_text = Path.read_text

    def guarded_read_text(path: Path, *args, **kwargs):
        if path.resolve() == outside.resolve():
            raise AssertionError("external tracker was read")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 1
    assert not isinstance(result.exception, AssertionError)
    assert "Refusing symlinked init target" in result.stderr
    assert tracker.is_symlink()
    assert list(vault.iterdir()) == [tracker]
    assert outside.read_bytes().endswith(b"private\n")


def test_vault_init_preflights_file_where_directory_is_required(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    blocked = vault / "papers"
    blocked.write_text("researcher-owned file\n", encoding="utf-8")

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 1
    assert "Expected directory but found file" in result.stderr
    assert blocked.read_text(encoding="utf-8") == "researcher-owned file\n"
    assert sorted(vault.iterdir()) == [blocked]


def test_vault_init_preflights_late_symlink_before_any_scaffold_write(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside-templates"
    outside.mkdir()
    templates_link = vault / "_templates"
    templates_link.symlink_to(outside, target_is_directory=True)

    result = runner.invoke(app, ["vault", "init", str(vault)])

    assert result.exit_code == 1
    assert "Path escapes vault root" in result.stderr
    assert templates_link.is_symlink()
    assert list(outside.iterdir()) == []
    assert sorted(vault.iterdir()) == [templates_link]
