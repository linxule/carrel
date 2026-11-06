# Cross-Host Feature Parity Assessment

**Date:** 2026-11-06
**Status:** Assessment; Phase 1 implemented, Phases 2–4 planned
**Scope:** Claude Code, Codex, GitHub Copilot, Kimi Code, and other Agent Skills / Agent Plugins hosts

## Executive Assessment

Carrel should target **behavioral parity for its research workflows**, not identical
plugin components on every host. Claude Code's native plugin is the richest
adapter: it provides slash commands, lifecycle hooks, agents, and the typed
`carrel` CLI. Other hosts expose different capabilities and execution
environments. Agent Plugins 1.0 standardizes the portable package surface, but
does not make host-specific components or permissions portable.

The shared capability source is `skills/carrel/`: its skill instructions,
references, templates, and stdlib-only Python runtime. `plugins/carrel/` packages
that canonical skill for Agent Plugins 1.0. The root Claude Code plugin remains
the native adapter and keeps its additional commands, hooks, agents, and typed
CLI. The generated portable package is an installable shared core, not a claim
that every feature of the Claude Code adapter is already available everywhere.

## Parity Definition

Carrel has parity when a researcher can complete the same **core task** on each
supported host and receives equivalent outputs and safety guarantees, even if
the invocation differs (natural-language skill, slash command, or host action).

Required invariants for shared workflows:

- Trust checks and explicit approval requirements are preserved.
- Sensitivity and cloud-consent decisions never become more permissive on a
  host that lacks a native hook.
- Writes remain vault-contained, with the same idempotency and overwrite
  expectations.
- Missing tools or host capabilities are reported as unavailable; they are not
  represented as successful operations.
- Host limitations are disclosed before relying on local files, networking,
  scheduling, or external providers.

Labels used below:

- **Shared**: implemented in the portable Carrel skill/runtime.
- **Adapter**: implemented only by a host-specific integration or native
  capability.
- **Partial**: workflow exists, but an execution capability, automation, or
  provider is conditional on the host.
- **Not verified**: no current evidence to claim support on that host.

## Capability Inventory

| Researcher capability | Shared implementation | Claude Code native adapter | Current parity assessment |
|---|---|---|---|
| Onboarding and profile capture | `onboarding.md`, `vault init`, environment profile | `/carrel-setup`, `setup-interviewer`, setup-state CLI | **Partial** — same interview/scaffold intent; resumable setup state is Claude-adapter-only. |
| Environment audit, validation, repair | `env-doctor`, setup/repair workflows, portable `env doctor/validate/fix` | `/carrel-status`, `/carrel-fix`, typed CLI and hooks | **Partial** — repair and validation are shared; audits depend on tools detectable in each host environment. |
| PDF/document conversion | `convert` workflow and portable `convert file` / `batch convert` | `/carrel-convert`, `/carrel-batch`, typed router and adapters | **Partial** — local adapter availability and optional cloud converters differ; the portable runtime does not include typed CLI cloud-provider adapters. |
| Audio/video transcription | `transcribe` workflow and portable transcript/batch operations | `/carrel-transcribe`, `/carrel-batch`, typed CLI adapters | **Partial** — transcript filing is shared; transcription engines and YouTube caption fetching are adapter-dependent. |
| Web capture | `web-capture` workflow and portable `capture url` | `/carrel-capture`, typed CLI adapters | **Partial** — content capture/file safety is shared; fetching and extraction require an available host adapter/tool. |
| Google Docs export | ingestion workflow and portable `google export` | Typed CLI Google adapter and setup guidance | **Partial** — depends on `gws`, authentication, and host networking. |
| Vault operations and note creation | `vault-ops`, templates, runtime-safe writes | `research-partner`, `/carrel-cheatsheet`, typed CLI surfaces | **Shared core / adapter UX** — analysis and safe persistence are portable; generated dashboards and command affordances differ. |
| Research partner and knowledge wiki | portable research/wiki workflows, trust checks, wiki protocol | `research-partner` agent, `knowledge-wiki` skill, hook context | **Shared workflow / adapter UX** — agent invocation and context injection are Claude-specific; wiki operations remain approval/trust-gated. |
| Automation configuration and prompt | automation workflow, profile write, prompt generation | `/carrel-automate`, session-start context, Cowork scheduling instructions | **Partial** — profile and prompt are shared; actual scheduling and lifecycle-triggered briefs are host-owned. |
| Reflection, feedback, and mirror | portable reflection/feedback workflows and deterministic writers | `/carrel-reflect`, session-end reflection hook | **Partial** — manual workflow and persistence are shared; automatic session-end prompting is Claude-specific. |
| Collaborator handoff | collaborator workflow and portable handoff writer | `/carrel-share` and native plugin integration | **Shared**, subject to file access and local runtime capability. |
| Trust and sensitivity enforcement | portable trust checks, routing decisions, safe writers | typed CLI gates plus Claude `PreToolUse` sensitivity hook | **Shared invariant required** — hooks add UX, but must not be the only enforcement boundary. |
| Migration and plugin version state | Not in portable runtime | `/carrel-migrate`, migrations registry, plugin-state | **Adapter only** — tied to plugin lifecycle/version state. |
| Setup phase state and Claude marker sync | Not in portable runtime by design | `setup-state` CLI, `CLAUDE.md` marker commands | **Adapter only** — intentionally tied to Claude-specific files and flow. |
| Model teammate installation | Portable use cases, sensitivity guidance, profile preference | `model-teammates` skill and `/carrel-teammates` | **Adapter only** — provider installation and delegation APIs vary by host. |

This inventory is grounded in `skills/carrel/references/contracts/surface-map.md`,
`skills/carrel/references/contracts/host-compatibility.md`, portable workflow
references, and the root `commands/`, `agents/`, and `hooks/` surfaces.

## Host Support Boundaries

| Host | Installable surface | What parity can currently be claimed |
|---|---|---|
| Claude Code | Existing native Carrel plugin; portable skill may also be installed alone | **Fullest adapter**, including native commands/hooks/agents. |
| Codex | Agent Plugins package / marketplace and skill installation | **Shared workflow core**; verify runtime access, permissions, and optional tool setup on each Codex surface. |
| GitHub Copilot app / CLI | Agent Plugins package / marketplace | **Shared workflow core**; Copilot-specific agents, commands, and hooks can be added as adapters, but are not yet part of this package. |
| Claude app / Cowork | Claude plugin or skill, depending on surface | **Partial**; local vault access, scripts, and scheduling depend on connected-folder and execution support. |
| Kimi Code CLI | `kimi.plugin.json` (repo root → packaged skill; also inside `plugins/carrel/`) | **Shared workflow core**; Kimi does not read Agent Plugins `plugin.json` and does not auto-discover `skills/`, so it has its own manifest with an explicit `skills` path. |
| OpenCode, Gemini CLI, Cursor, and other skill hosts | Agent Skill folder or host-specific plugin mechanism | **Skill-level only where verified**; do not imply Agent Plugins manifest, local scripts, or lifecycle support without host testing. |

The shared package and marketplace files are distribution plumbing. A package
appearing in a catalog is not proof that its workflow runs correctly on that
host.

## Known Behavioral Drift Risks

`tests/test_runtime_parity.py` compares the typed CLI and portable runtime on a
subset of shared deterministic surfaces. It currently documents these
differences:

1. Malformed `cloud_consent` values are rejected by the typed CLI schema gate,
   while the portable runtime treats only literal `true` as consent. Both paths
   must continue to fail closed; this is a policy equivalence, not byte parity.
2. `vault init` has an explicit, enumerated output divergence.

The previously observed first-of-day reflection seed and feedback digest
formatting differences were aligned in this pass. Tests now compare complete
reflection files after masking timestamps and byte-compare feedback digests
across multiple, including nested, sources.

These are not all blockers to distribution, but output and safety differences
must remain explicit and test-pinned rather than being described as exact parity.

## Implementation Plan

### Phase 1 — Publishable shared core (implemented)

- Package `skills/carrel/` under `plugins/carrel/` with an Agent Plugins 1.0
  manifest and Copilot/Codex marketplace entries, plus Kimi Code manifests
  (`kimi.plugin.json` at the repo root and in the package).
- Keep `skills/carrel/` as the sole source of truth; check the packaged copy
  byte-for-byte in tests.
- Keep Claude's root plugin and its existing marketplace untouched.
- Make installation and support claims distinguish the shared core from native
  Claude-only components.

**Exit criteria:** plugin/catalog JSON parses, all manifest versions agree,
packaged files match the canonical skill, and current packaging/runtime tests
pass. These criteria are met in this change.

### Phase 2 — Behavioral parity contract

- Turn the invariants above into a shared workflow test matrix covering
  onboarding, environment repair, ingestion, vault-safe writes, trust, and
  sensitivity routing.
- Extend typed-vs-portable differential tests for the highest-risk shared
  deterministic operations. Every divergence must be either fixed or named and
  justified in the test allowlist.
- Add representative skill-level scenarios for judgment workflows; compare
  expected actions and approval boundaries, not exact prose.
- Close the known reflection and feedback-format drifts where doing so does not
  break existing vault compatibility.

**Exit criteria:** tests demonstrate equal safety decisions and equivalent
observable outcomes for all shared runtime surfaces; intentional differences
are explicitly documented.

### Phase 3 — Host adapters, only where they improve the workflow

- Preserve the Claude native plugin as the full-feature adapter.
- Add Copilot namespaced components only for gaps users need (for example
  custom-agent entry points or safe hook UX); do not duplicate core policy in
  hooks.
- Use Codex plugin facilities for skill invocation and optional supported
  integrations; do not assume Claude hooks or agents map one-to-one.
- Keep host scheduling, authentication, permission UX, and provider-specific
  teammates in adapters.

**Exit criteria:** each adapter maps back to shared capability IDs and calls
the canonical workflows/runtime rather than reimplementing business logic.

### Phase 4 — Host verification and release claims

- Run install and smoke tests in Claude Code, Codex, and Copilot separately.
- Verify Python version, skill discovery, bundled assets, vault read/write
  access, and tool permission behavior.
- Exercise onboarding, one local conversion or content capture, trust-gated
  writes, and a high-sensitivity/cloud-consent denial.
- Record tested host surfaces and versions; mark unsupported surfaces
  **Not verified** rather than inferring compatibility from a shared manifest.

**Exit criteria:** release notes publish a per-host matrix backed by executed
smoke tests, and no "feature parity" claim exceeds that evidence.

## Immediate Implementation State

- The portable Agent Plugins package and Copilot/Codex marketplace catalogs
  have been added to the worktree.
- `scripts/sync-agent-plugin.py` regenerates the packaged skill from
  `skills/carrel/`; the packaging test fails when the copy drifts.
- Shared reflection and feedback-export formatting now match the typed CLI;
  portable feedback export also recursively collects nested sources and emits
  the same JSON action field.
- The full test suite passes, including exact cross-runtime reflection and
  multi-source feedback output comparisons.
- Host-specific parity, especially Copilot adapter components and actual
  cross-host smoke testing, remains future work under Phases 2–4.

## Host Manifest Matrix (checked against host docs, 2026-11-06)

| Host | Manifest read | Skills discovery | Catalog |
|---|---|---|---|
| Copilot CLI / VS Code | root `plugin.json` with Agent Plugins `$schema` (wins over `.claude-plugin/plugin.json`) | fixed `skills/` | `.github/plugin/marketplace.json` (`name`, `owner`, `plugins[].source` string) |
| Codex | root `plugin.json` (Agent Plugins); `.codex-plugin/plugin.json` is a legacy fallback | fixed `skills/` | `.agents/plugins/marketplace.json` (`source: {source: local, path}`, `policy`, `category`) |
| Kimi Code | `kimi.plugin.json` or `.kimi-plugin/plugin.json` only | explicit `skills` path required | `/plugins install <github-url>` (no subdirectory form) |
| Claude Code | `.claude-plugin/plugin.json` (repo root = native plugin) | `skills/`, plus commands/hooks/agents | `.claude-plugin/marketplace.json` |

`tests/test_packaging_contract.py` pins these rules so a manifest edit cannot
silently drop a host.
