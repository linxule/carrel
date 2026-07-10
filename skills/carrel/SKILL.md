---
name: carrel
description: Portable AI-assisted research vault operations for setup, document ingestion, transcription, web capture, environment repair, trust and sensitivity routing, reflection, collaborator handoff, and feedback export. This is the standalone engine for hosts without the Carrel Claude Code plugin, such as Cowork, Codex, Kimi Code, Gemini CLI, OpenCode, and Claude.ai skill uploads. Do not use when the Carrel Claude Code plugin or the installed carrel CLI is available; that plugin drives the typed CLI as its runtime, not this pack.
license: MIT
compatibility: Requires Python 3.10 or newer on the host
---

# Carrel

Use Carrel as a portable research-vault operating layer. Prefer the bundled
runtime in `scripts/carrel.py` for deterministic file writes, profile repair,
routing decisions, and artifact generation. Use the references only when the
task needs deeper workflow or contract context.

## Quick Start

Run the bundled runtime with Python 3.10 or newer from this skill folder:

```bash
python3 scripts/carrel.py vault init <vault> --profile-file <profile.json>
python3 scripts/carrel.py env validate --vault <vault> --format json
python3 scripts/carrel.py env doctor --vault <vault> --format json
python3 scripts/carrel.py capture url https://example.com/article --vault <vault> --content "Article body"
```

The runtime is stdlib-first. Public tool ids include `liteparse`,
`markdownify`, `defuddle`, `coli`, `gws`, `mineru`, `mistral_ocr`, `groq`, and
`gemini`. Executable names such as `lit` and `markitdown` are adapter
implementation details. If an adapter is missing, report the missing capability
and offer the relevant setup path instead of treating the skill as unavailable.

YouTube caption or audio *fetching* is typed-CLI or host-adapter territory: the
bundled runtime never calls the network for transcripts. It recognizes YouTube
URLs only to slug the artifact by video id (so two distinct videos never
collide on the shared `watch` stem) — supply the transcript itself with
`--content`, or let a host adapter fetch captions.

## Workflow Routing

- For first-time onboarding, setup interviews, or researcher profile updates, read
  `references/workflows/onboarding.md`.
- For vault scaffolding, existing vault setup, or vault repair, read
  `references/workflows/setup-and-repair.md`.
- For document conversion, transcription, web capture, and Google export, read
  `references/workflows/ingestion.md`.
- For automation setup, unattended runs, pending decisions, and morning briefs,
  read `references/workflows/automation.md`.
- For reflection, feedback export, and mirror synthesis, read
  `references/workflows/reflection-and-feedback.md`.
- For collaborator handoff, read `references/workflows/collaborator-handoff.md`.
- For field-map or knowledge-wiki work, read
  `references/workflows/field-map.md`.
- For note creation, Obsidian-facing vault work, analytical threads, and
  databases, read `references/workflows/vault-ops.md`.
- For a compact maintenance command overview, read
  `references/workflows/maintenance.md`.
- For the persisted file layout, read `references/contracts/vault-contract.md`.
- For local/cloud routing, read `references/contracts/routing-policy.md`.
- For profile fields and repair behavior, read
  `references/contracts/environment-profile.md`.
- For trust-gated operations, read `references/contracts/trust-levels.md`.
- For deciding whether behavior belongs in the runtime or agent proposal, read
  `references/contracts/determinism-boundary.md`.
- For legacy CLI parity and portable-skill disposition, read
  `references/contracts/surface-map.md`.
- For cross-harness install and invocation notes, read
  `references/contracts/host-compatibility.md`.
- For optional external tools and host adapters, read
  `references/contracts/optional-adapters.md`.
- For scheduled upstream refresh of external packages, API endpoints, and host
  harness claims, read `references/contracts/external-refresh.json`.
- For source-link lookup and deciding when to visit upstream docs beyond the
  captured skill contracts, read `references/contracts/external-help.md`.
- For research partner, wiki, and vault-note behavior, read
  `references/workflows/research-and-vault.md`.
- For model teammate (Codex, Gemini, Kimi) preferences and the sensitivity gate
  before delegating to another model, read
  `references/workflows/research-and-vault.md`.

## Runtime Boundary

Use `scripts/carrel.py` for low-freedom operations:

- `vault init`
- `vault automation-prompt`
- `env validate`
- `env fix`
- `env doctor`
- `policy explain`
- `capture url`
- `convert file`
- `google export`
- `batch convert`
- `batch transcribe`
- `transcript create`
- `trust check`
- `trust list`
- `trust show`
- `reflection append`
- `mirror write`
- `feedback export`
- `share generate`
- `automation configure`

Keep intellectual synthesis in the agent. Pipe finished prose into the runtime
when persistence needs to be deterministic, dated, idempotent, or vault-safe.

## Host Adapters

This portable skill is the runtime engine for hosts without the Carrel Claude
Code plugin: Cowork, Codex, Kimi Code, Gemini CLI, OpenCode, and Claude.ai skill
uploads. It does not require slash commands, lifecycle hooks, marketplace
metadata, or host-specific memory files. If a host supports those features,
treat them as adapters over this skill:

- The Carrel Claude Code plugin is separate. Its commands and hooks call the
  installed typed `carrel` CLI, not this pack. Use this skill only when that
  plugin is not installed.
- A Codex, Kimi Code, Gemini CLI, or OpenCode adapter may symlink or install
  this skill folder and call `scripts/carrel.py`.
- Other agents may read this `SKILL.md` and call `scripts/carrel.py` directly.

The canonical portable context file is `.carrel/agent-context.md`. Generate
host-specific files only when the host adapter requires them.
