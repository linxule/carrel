---
name: carrel
description: Portable AI-assisted research vault operations for setup, document ingestion, transcription, web capture, environment repair, trust and sensitivity routing, reflection, collaborator handoff, and feedback export. Use when an agent needs to create or maintain a Carrel-style research vault without relying on Claude Code plugin commands, hooks, or marketplace installation.
---

# Carrel

Use Carrel as a portable research-vault operating layer. Prefer the bundled
runtime in `scripts/carrel.py` for deterministic file writes, profile repair,
routing decisions, and artifact generation. Use the references only when the
task needs deeper workflow or contract context.

## Quick Start

Run the bundled runtime with Python 3 from this skill folder:

```bash
python3 scripts/carrel.py vault init <vault>
python3 scripts/carrel.py env validate --vault <vault> --format json
python3 scripts/carrel.py env doctor --project-path <vault> --format json
python3 scripts/carrel.py capture url https://example.com/article --vault <vault> --content "Article body"
```

The runtime is stdlib-first. External tools such as `lit`, `markitdown`,
`defuddle`, `coli`, `gws`, MinerU, Groq, Gemini, and YouTube transcript APIs are
optional adapters. If an adapter is missing, report the missing capability and
offer the relevant setup path instead of treating the skill as unavailable.

## Workflow Routing

- For first-time setup or vault repair, read
  `references/workflows/setup-and-repair.md`.
- For document conversion, transcription, web capture, and Google export, read
  `references/workflows/ingestion.md`.
- For automation, reflection, collaborator handoff, feedback export, and mirror
  synthesis, read `references/workflows/maintenance.md`.
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
- For research partner, wiki, and vault-note behavior, read
  `references/workflows/research-and-vault.md`.

## Runtime Boundary

Use `scripts/carrel.py` for low-freedom operations:

- `vault init`
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

This portable skill does not require slash commands, lifecycle hooks,
marketplace metadata, or host-specific memory files. If a host supports those
features, treat them as adapters over this skill:

- A Claude Code adapter may expose slash commands and hooks.
- A Codex adapter may symlink or install this skill folder.
- Other agents may read this `SKILL.md` and call `scripts/carrel.py` directly.

The canonical portable context file is `.carrel/agent-context.md`. Generate
host-specific files only when the host adapter requires them.
