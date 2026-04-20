# Cheat Sheet Output Guide

This file describes the markdown produced by `src/carrel/vault/templates.py::render_cheat_sheet()`. It is not a Mustache template.
The renderer uses the current platform (or the explicitly supplied `platform` argument) to choose install commands.

## Header

- Title: `# Carrel - Your AI Research Environment`
- Researcher line: `Customized for: <profile.name or "Researcher">`
- Vault line: `Vault: <vault folder name>`

## Setup

Lists four quick facts:
- Obsidian vault path: the resolved vault path passed into `render_cheat_sheet()`
- Cloud consent: lowercase string form of `profile.cloud_consent`
- Sensitivity: `profile.sensitivity.value`
- Audio transcription status: `enabled` if `coli` or `groq` is configured, otherwise `available later`

## Folders

Always lists the standard vault folders exactly as rendered:
- `inbox/`
- `papers/`
- `notes/`
- `transcripts/`
- `drafts/`
- `talks/`
- `admin/`
- `_meta/`
- `_templates/`

## Configured Tools

Derived from `profile.tools_configured`.

- If no tools are enabled, the section contains one fallback line saying no tool-specific workflows are configured yet.
- If tools are enabled, each enabled tool gets:
  - `### <tool name>`
  - Optional `- Install: <platform-specific command>` when Carrel knows the right install command for that tool
  - A short list of command examples from `TOOL_COMMAND_EXAMPLES`

## Common Workflows

Starts with a default daily-check bullet, then conditionally adds bullets from the profile:

- `profile.wiki_enabled` adds the knowledge wiki bullet.
- `profile.cloud_consent` chooses between cloud-enabled vs local-default guidance.
- `profile.preferences.many_papers` or `profile.preferences.literature_review` adds the paper pipeline bullet.
- `profile.preferences.qualitative` or `profile.preferences.interviews` adds the interview workflow bullet.
- `profile.automation.enabled` adds the overnight automation bullet.
- `profile.collaborators` adds the collaborator handoff bullet.

## Next Steps

Always ends with three bullets:
- Run `/carrel-status`
- Use `/carrel-share` for a collaborator-ready handbook
- Use `/carrel-migrate` for update review and migrations
