import json

import pytest

from carrel.models import ResearcherProfile
from carrel.vault.scaffold import scaffold_vault
from carrel.vault.templates import read_template


def test_scaffold_vault_creates_structure_and_profile(tmp_path) -> None:
    result = scaffold_vault(tmp_path / "vault")

    assert result.vault.exists()
    assert result.profile_path == result.vault / ".carrel" / "environment.json"
    assert result.profile_path.exists()
    assert (result.vault / "_templates" / "paper.md").exists()
    assert (result.vault / "_templates" / "paper-notes.md").exists()
    assert (result.vault / ".obsidian" / "app.json").exists()
    assert (result.vault / "_meta" / "cheat_sheet.md").exists()

    profile = json.loads(result.profile_path.read_text(encoding="utf-8"))
    assert profile["sensitivity"] == "medium"
    assert profile["cloud_consent"] is False
    assert profile["comfort_level"] == "beginner"


def test_scaffold_creates_dashboard_and_capability_log(tmp_path) -> None:
    result = scaffold_vault(tmp_path / "vault")

    assert (result.vault / "_meta" / "my-environment.md").exists()
    assert (result.vault / "_meta" / "capability-log.md").exists()
    assert (result.vault / "_meta" / "local").is_dir()
    cheat_sheet = (result.vault / "_meta" / "cheat_sheet.md").read_text(encoding="utf-8")
    assert "## Configured tools" in cheat_sheet
    assert "## Common workflows" in cheat_sheet
    assert "## Next steps" in cheat_sheet


def test_scaffold_cheat_sheet_uses_natural_language_wiki_copy(tmp_path) -> None:
    profile = ResearcherProfile(wiki_enabled=True)
    result = scaffold_vault(tmp_path / "vault", profile=profile)

    cheat_sheet = (result.vault / "_meta" / "cheat_sheet.md").read_text(encoding="utf-8")
    assert "- Knowledge wiki: ask Claude about your field map; pages live in `wiki/`." in cheat_sheet
    assert "/carrel-research" not in cheat_sheet


def test_scaffold_always_includes_reading_progress_base(tmp_path) -> None:
    result = scaffold_vault(tmp_path / "vault")

    base = result.vault / "reading-progress.base"
    assert base.exists()
    content = base.read_text(encoding="utf-8")
    assert "carrel-template: reading-progress" in content


def test_scaffold_includes_bases_for_qualitative_profile(tmp_path) -> None:
    profile = ResearcherProfile(
        preferences={"qualitative": True, "many_papers": True},
    )
    result = scaffold_vault(tmp_path / "vault", profile=profile)

    assert (result.vault / "reading-progress.base").exists()
    assert (result.vault / "interview-tracker.base").exists()
    assert (result.vault / "paper-tracker.base").exists()


@pytest.mark.parametrize(
    ("preference", "tracker"),
    [
        ("many_papers", "paper-tracker.base"),
        ("literature_review", "paper-tracker.base"),
        ("qualitative", "interview-tracker.base"),
        ("interviews", "interview-tracker.base"),
        ("writing", "writing-tracker.base"),
        ("thesis", "writing-tracker.base"),
        ("dissertation", "writing-tracker.base"),
    ],
)
def test_scaffold_profile_preferences_select_expected_tracker(
    tmp_path,
    preference: str,
    tracker: str,
) -> None:
    profile = ResearcherProfile(preferences={preference: True})

    result = scaffold_vault(tmp_path / preference, profile=profile)

    assert (result.vault / "reading-progress.base").exists()
    assert (result.vault / tracker).exists()


def test_scaffold_skips_existing_base_files(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    custom = vault / "reading-progress.base"
    custom.write_text("# custom content\n", encoding="utf-8")

    result = scaffold_vault(vault)

    assert custom.read_text(encoding="utf-8") == "# custom content\n"
    assert "reading-progress.base" in result.skipped
    assert result.unversioned_templates == ["reading-progress.base"]


def test_scaffold_reports_outdated_base_without_overwriting(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    current = read_template("reading-progress.base")
    outdated = current.replace(
        current.splitlines()[0],
        "# carrel-template: reading-progress v0.0.1",
    )
    target = vault / "reading-progress.base"
    target.write_text(outdated, encoding="utf-8")

    result = scaffold_vault(vault)

    assert result.outdated_templates == ["reading-progress.base"]
    assert result.unversioned_templates == []
    assert target.read_text(encoding="utf-8") == outdated
