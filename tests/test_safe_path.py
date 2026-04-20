from __future__ import annotations

import pytest

from carrel.errors import CarrelError
from carrel.safe_path import safe_vault_join


def test_safe_vault_join_accepts_normal_inside_path(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    result = safe_vault_join(vault, "notes", "daily.md")

    assert result == (vault / "notes" / "daily.md").resolve()


def test_safe_vault_join_rejects_parent_escape(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(CarrelError, match="Path escapes vault root"):
        safe_vault_join(vault, "..", "escape.md")


def test_safe_vault_join_rejects_symlink_pointing_outside_vault(tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (vault / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(CarrelError, match="Path escapes vault root"):
        safe_vault_join(vault, "linked", "note.md")
