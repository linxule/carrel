# Carrel — Portable Research-Vault Skill

An [Agent Skill](https://agentskills.io) for AI-assisted academic research vaults: setup, document ingestion, transcription, web capture, environment repair, trust & sensitivity routing, reflection, collaborator handoff, and feedback export. Ships a bundled **stdlib-only** Python runtime (`scripts/carrel.py`, Python 3.10+) — no pip installs, no dependencies, runs anywhere the skill folder lands.

## Install

In GitHub Copilot, Codex and Kimi Code, install Carrel as a plugin from [linxule/carrel](https://github.com/linxule/carrel#use-carrel-in-other-ai-apps) instead: it packages this same skill.

- Copilot (app, VS Code or CLI): add the `linxule/carrel` marketplace, then install `carrel@carrel`
- Codex: `codex plugin marketplace add linxule/carrel`, then install Carrel from **Plugins** or `/plugins`
- Kimi Code: `/plugins install https://github.com/linxule/carrel`, or **Settings** > **Plugins** in the desktop app

To install the skill on its own:

| Client | Command |
|--------|---------|
| Any `npx skills`-compatible client | `npx skills add linxule/carrel-skill` |
| Codex / Cursor / OpenCode / Gemini CLI | copy this folder to `.agents/skills/carrel` (or `~/.agents/skills/carrel`) |
| Kimi Code CLI | copy to `~/.kimi-code/skills/carrel` |
| Claude Code (standalone, without the Carrel plugin) | copy to `~/.claude/skills/carrel` |
| Claude (web or desktop app) | download [carrel.zip](https://github.com/linxule/carrel/releases/download/skill-latest/carrel.zip), then upload it in **Customize → Skills → + → Create skill → Upload a skill** (turn on code execution first). Do not upload GitHub's "Download ZIP" of this repo: its folder name does not match the skill name. |

Always install the **entire folder** — the runtime needs `scripts/carrel_core/` and vault setup needs `assets/templates/`. See `references/contracts/host-compatibility.md` for per-host notes.

## Quick start

```bash
python3 scripts/carrel.py vault init <vault>
python3 scripts/carrel.py env doctor --vault <vault> --format json
```

Start with `SKILL.md`; workflows and contracts live under `references/`.

## Relationship to the Carrel plugin

This pack is the **standalone engine for non-plugin hosts** and a strict subset of the full [Carrel](https://github.com/linxule/carrel) Claude Code plugin (which adds slash commands, hooks, agents, cloud adapters, and migrations via its typed CLI). If you use Claude Code with the Carrel plugin installed, you don't need this pack — the plugin's runtime takes precedence.

## Security note

Agent Skills have no signing or checksum mechanism. This pack is small, stdlib-only, and auditable — read the code before installing, as you should for any skill that ships executable scripts.

## Contributing

**This repository is a generated publish target** — the canonical source is [`linxule/carrel`](https://github.com/linxule/carrel) under `skills/carrel/`, published here via `git subtree`. Please open issues and PRs against [linxule/carrel](https://github.com/linxule/carrel); direct changes here will be overwritten by the next sync.

MIT © Xule Lin
