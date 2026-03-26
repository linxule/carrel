from __future__ import annotations

import os
from pathlib import Path

import typer

from carrel.errors import CarrelError, VaultNotFound
from carrel.models import ResearcherProfile


def normalize_path(path: Path) -> Path:
    return path.expanduser().resolve()


def resolve_vault(vault: Path | None = None) -> Path:
    if vault is not None:
        return normalize_path(vault)

    env_vault = os.environ.get("CARREL_VAULT")
    if env_vault:
        return normalize_path(Path(env_vault))

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".carrel").exists():
            return candidate
    raise VaultNotFound()


def resolve_cloud_consent(tool: str | None, profile: ResearcherProfile | None) -> bool:
    if tool and tool in {"mineru", "groq", "gemini"}:
        return True
    if profile and profile.cloud_consent:
        return True
    return False


def emit_carrel_error(error: CarrelError) -> None:
    typer.echo(f"Error: {error.message}", err=True)
    if error.hint:
        typer.echo(f"  {error.hint}", err=True)
    raise typer.Exit(code=1)
