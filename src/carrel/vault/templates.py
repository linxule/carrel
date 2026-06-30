from __future__ import annotations

import json
from pathlib import Path

from carrel.env.install import install_command
from carrel.env.platform import Platform, detect_platform
from carrel.models import ResearcherProfile

# Registry of all template files shipped with the plugin.
# scaffold.py copies a subset during vault init; the rest are copied
# manually by Claude based on the decision tree (skills layer).
TEMPLATE_FILES = [
    "paper.md",
    "paper-notes.md",
    "meeting.md",
    "reflection.md",
    "daily.md",
    "my-environment.md",
    "vault-scaffold.json",
    "obsidian-config.json",
]

# Database templates — copied by Claude (not the CLI) based on the
# decision tree in skills/environment-setup/references/decision-tree.md.
BASE_TEMPLATES = [
    "paper-tracker.base",
    "interview-tracker.base",
    "reading-progress.base",
    "writing-tracker.base",
]

TOOL_COMMAND_EXAMPLES = {
    "liteparse": [
        "carrel paper convert paper.pdf --tool liteparse",
        "carrel paper convert paper.pdf --tool liteparse --dry-run",
        "carrel paper list --vault <vault>",
    ],
    "mineru": [
        "carrel paper convert paper.pdf --tool mineru",
        "carrel paper convert paper.pdf --tool mineru --force",
        "carrel google export https://docs.google.com/document/d/... --tool mineru",
    ],
    "mistral_ocr": [
        "carrel paper convert scanned.pdf --tool mistral_ocr",
        "carrel paper convert tables.pdf --tool mistral_ocr --force",
        "carrel google export https://docs.google.com/document/d/... --export-format pdf --tool mistral_ocr",
    ],
    "markdownify": [
        "carrel paper convert report.docx --tool markdownify",
        "carrel paper convert slides.pptx --tool markdownify",
        "carrel google export https://docs.google.com/document/d/... --tool markdownify",
    ],
    "defuddle": [
        "carrel capture url https://example.com/article",
        "carrel capture url https://example.com/article --dry-run",
        "carrel capture url https://example.com/article --force",
    ],
    "coli": [
        "carrel transcript create rec.m4a --tool coli",
        "carrel transcript create interview.wav --tool coli --kind interview",
        "carrel transcript create lecture.mp3 --tool coli --dry-run",
    ],
    "groq": [
        "carrel transcript create rec.m4a --tool groq",
        "carrel transcript create lecture.mp3 --tool groq --kind lecture",
        "carrel transcript create rec.m4a --tool groq --timeout 180",
    ],
    "gemini": [
        "carrel transcript create https://www.youtube.com/watch?v=... --tool gemini",
        "carrel transcript create https://youtu.be/... --tool gemini --kind lecture",
    ],
    "youtube_captions": [
        "carrel transcript create https://www.youtube.com/watch?v=... --tool youtube_captions",
        "carrel transcript create https://youtu.be/... --tool youtube_captions",
    ],
    "gws": [
        "carrel google export https://docs.google.com/document/d/...",
        "carrel google export https://docs.google.com/spreadsheets/d/... --export-format pdf",
        "carrel google export https://docs.google.com/presentation/d/... --tool markdownify",
    ],
    "obsidian": [
        "carrel vault init ~/Documents/Research",
        "carrel vault status --vault <vault>",
        "carrel vault cheatsheet --vault <vault> --force",
    ],
}


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


def _tool_command_examples(tool: str) -> list[str]:
    return TOOL_COMMAND_EXAMPLES.get(
        tool,
        [
            "carrel env doctor",
            "carrel env profile --vault <vault>",
            "carrel vault cheatsheet --vault <vault> --force",
        ],
    )


def _render_configured_tools(tools: dict[str, bool], platform: Platform) -> str:
    enabled_tools = sorted(tool for tool, enabled in tools.items() if enabled)
    if not enabled_tools:
        return "- No tool-specific workflows configured yet. Run `/carrel-status` after setup changes.\n"

    lines: list[str] = []
    for tool in enabled_tools:
        lines.append(f"### {tool}")
        install_hint = install_command(tool, platform)
        if install_hint:
            lines.append(f"- Install: `{install_hint}`")
        for command in _tool_command_examples(tool):
            lines.append(f"- `{command}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_common_workflows(profile: ResearcherProfile) -> str:
    prefs = profile.preferences
    workflows = [
        "- Daily check: run `/carrel-status` when something feels off or after adding tools.",
    ]
    if profile.wiki_enabled:
        workflows.append("- Knowledge wiki: ask Claude about your field map; pages live in `wiki/`.")
    if profile.cloud_consent:
        workflows.append(
            "- Cloud tools are enabled: `mineru`, `mistral_ocr`, `groq`, and `gemini` can be selected when useful."
        )
    else:
        workflows.append("- Cloud tools are disabled by default: keep workflows local unless you explicitly opt in.")
    if prefs.get("many_papers") or prefs.get("literature_review"):
        workflows.append("- Paper pipeline: use `/carrel-convert` for one file or `/carrel-batch` for an inbox sweep.")
    if prefs.get("qualitative") or prefs.get("interviews"):
        workflows.append("- Interview workflow: transcribe recordings, then link transcripts into notes and coding docs.")
    if profile.automation.enabled:
        workflows.append("- Overnight automation is on: review `_meta/briefs/` and update preferences via `/carrel-automate`.")
    if profile.collaborators:
        workflows.append("- Collaborator handoff: generate or refresh a handbook with `/carrel-share`.")
    return "\n".join(workflows) + "\n"


def render_cheat_sheet(
    vault: Path,
    profile: ResearcherProfile,
    platform: Platform | None = None,
) -> str:
    resolved_platform = detect_platform() if platform is None else platform
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

## Configured tools

{_render_configured_tools(tools, resolved_platform)}

## Common workflows

{_render_common_workflows(profile)}

## Next steps

- Run `/carrel-status` for a live environment check.
- Use `/carrel-share` when you need a collaborator-ready handbook for this vault.
- Use `/carrel-teammates` to add, remove, or review model teammates (Codex, Gemini, Kimi).
- Use `/carrel-migrate` to review updates and apply the migration system when Carrel changes.
"""
