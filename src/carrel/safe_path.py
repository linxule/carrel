from __future__ import annotations

import tempfile
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


def assert_safe_write_target(vault: Path, path: Path) -> Path:
    """Return a normalized in-vault file target or fail before any write."""

    root = vault.expanduser().resolve()
    target = path.expanduser()
    if not target.is_absolute():
        target = root / target
    if target.is_symlink():
        raise CarrelError(
            "Path escapes vault root",
            hint=f"Refusing to write through symlink {target}",
        )
    try:
        target.resolve(strict=False).relative_to(root)
        target.parent.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise CarrelError(
            "Path escapes vault root",
            hint=f"Refusing to write outside {root}",
        ) from error
    if target.exists() and not target.is_file():
        raise CarrelError(
            "Invalid vault file target",
            hint=f"Expected a regular file: {target}",
        )
    return target


def safe_atomic_write(vault: Path, path: Path, content: str) -> None:
    """Atomically write a regular file without following a path outside the vault."""

    target = assert_safe_write_target(vault, path)

    tmp_path: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            delete=False,
        ) as handle:
            handle.write(content)
            tmp_path = Path(handle.name)
        tmp_path.replace(target)
    except OSError as error:
        raise CarrelError(
            "Could not write vault file",
            hint=f"{target}: {error}",
        ) from error
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
