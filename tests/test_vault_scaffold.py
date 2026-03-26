import json

from carrel.vault.scaffold import scaffold_vault


def test_scaffold_vault_creates_structure_and_profile(tmp_path) -> None:
    result = scaffold_vault(tmp_path / "vault")

    assert result.vault.exists()
    assert result.profile_path == result.vault / ".carrel" / "environment.json"
    assert result.profile_path.exists()
    assert (result.vault / "_templates" / "paper.md").exists()
    assert (result.vault / ".obsidian" / "app.json").exists()
    assert (result.vault / "_meta" / "cheat_sheet.md").exists()

    profile = json.loads(result.profile_path.read_text(encoding="utf-8"))
    assert profile["sensitivity"] == "medium"
    assert profile["cloud_consent"] is False
    assert profile["comfort_level"] == "beginner"
