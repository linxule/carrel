from __future__ import annotations

import json
from pathlib import Path

from carrel.models import ResearcherProfile

TEMPLATE_FILES = [
    "paper.md",
    "paper-notes.md",
    "meeting.md",
    "reflection.md",
    "daily.md",
    "vault-scaffold.json",
    "obsidian-config.json",
]


def template_root() -> Path:
    return Path(__file__).resolve().parents[3] / "templates"


def read_template(name: str) -> str:
    path = template_root() / name
    return path.read_text(encoding="utf-8")


def copy_template(name: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(read_template(name), encoding="utf-8")
    return destination


def load_obsidian_config() -> dict:
    return json.loads(read_template("obsidian-config.json"))


def load_scaffold_config() -> dict:
    return json.loads(read_template("vault-scaffold.json"))


def render_cheat_sheet(vault: Path, profile: ResearcherProfile) -> str:
    tools = profile.tools_configured
    name = profile.name or "Researcher"
    vault_name = vault.name
    return f"""# Carrel - Your AI Research Environment

Customized for: {name}
Vault: {vault_name}

## Setup

- Obsidian vault: `{vault}`
- Cloud consent: `{str(profile.cloud_consent).lower()}`
- Sensitivity: `{profile.sensitivity.value}`
- Audio transcription: `{"enabled" if tools.get("coli") or tools.get("groq") else "available later"}`

## Folders

- `inbox/`
- `papers/`
- `notes/`
- `transcripts/`
- `drafts/`
- `talks/`
- `admin/`
- `_meta/`
- `_templates/`
"""
