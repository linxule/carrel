from __future__ import annotations

from pathlib import Path

from carrel.errors import CarrelError


def safe_vault_join(vault: Path, *parts: str) -> Path:
    root = vault.expanduser().resolve()
    target = root.joinpath(*parts).resolve()

    try:
        target.relative_to(root)
    except ValueError as error:
        raise CarrelError(
            "Path escapes vault root",
            hint=f"Refusing to write outside {root}",
        ) from error
    return target
