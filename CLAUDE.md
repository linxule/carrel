# Carrel

Research environment toolkit for academics. Two layers: a Python core library (`carrel` CLI) and a Claude Code plugin (skills, agents, hooks, commands).

## Quick Commands

```bash
# Core library
uv run pytest                                    # 143 tests
uv run carrel env doctor                         # Hardware + tools audit
uv run carrel vault init /tmp/test               # Scaffold a vault
uv run carrel paper convert paper.pdf            # Convert PDF (liteparse default)
uv run carrel transcript create rec.m4a          # Transcribe audio (coli default)
uv run carrel capture url https://example.com    # Web capture (defuddle)
uv run carrel google export <google-docs-url>    # Google Docs export (gws)
uv run carrel vault cheatsheet --vault . --force # Regenerate _meta/cheat_sheet.md
uv run carrel setup-state show --vault .         # Inspect setup phase (v0.5.3+)
uv run carrel setup-state advance --phase N      # Move to next phase atomically
uv run carrel setup-state complete --vault .     # Mark setup complete (idempotent)
uv run carrel trust check automation:propose --vault .  # Check if action allowed at current trust level
uv run carrel trust list --vault .  # See what current trust unlocks
```

## Architecture

```
Skills (markdown)     → human judgment, loaded by any AI
Core library (Python) → deterministic operations, no AI
Transports (thin)     → plugin, CLI, MCP, agent SDK apps
```

The core library NEVER asks questions or makes judgment calls. Skills handle that. If a required parameter is missing, the library returns an actionable error.

## Directory Structure

```
carrel/
├── src/carrel/           # Python core library
│   ├── cli/              # typer CLI (paper, transcript, vault, env, capture, google)
│   ├── convert/          # PDF/doc conversion (router, adapters, filer, pipeline)
│   ├── transcribe/       # Audio/video transcription (router, adapters, filer)
│   ├── google/           # Google Workspace export (gws CLI integration)
│   ├── vault/            # Vault scaffold, organize, templates
│   ├── env/              # Audit, profile, install commands
│   ├── models.py         # Pydantic models (options, results, enums, AutomationConfig, ResearcherProfile)
│   └── errors.py         # CarrelError with actionable hints
├── tests/                # pytest suite
├── templates/            # Vault templates (loaded by vault/templates.py)
├── skills/               # Plugin skills (convert, transcribe, vault-ops, environment-setup, automation, knowledge-wiki, etc.)
├── agents/               # Plugin agents (setup-interviewer, research-partner)
├── hooks/                # Plugin hooks (session start/end)
├── commands/             # Plugin slash commands (/carrel-*)
├── planning/             # Specs, reviews, prompts, reports (multi-model review workflow)
├── bootstrap.sh          # Mac-focused machine prep (legacy; install.sh preferred)
├── install.sh            # macOS/Linux one-line installer (curl | bash)
├── install.ps1           # Windows installer (see Gotchas re: partial Windows support)
└── pyproject.toml        # pydantic + typer + rich + httpx + markitdown
```

## Tool Routing

### PDF conversion
`liteparse` (local default) > `mineru` (cloud, explicit `--tool mineru`) > `markitdown` (non-PDF only)

No markdownify fallback for PDFs. Missing liteparse → clear error with install command.

### Audio transcription
`coli` (local default) > `groq` (cloud, explicit `--tool groq`)

No markdownify fallback for audio. Missing coli → clear error.

### YouTube
`youtube_captions` (local default, fetches existing captions with timestamps) > `gemini` (cloud, explicit `--tool gemini` or cloud_consent)

### Web pages
`defuddle` (local default, smart content extraction) > `markitdown` (fallback if defuddle not installed)

## Key Design Rules

- **Cloud consent**: `--tool <cloud-tool>` IS consent. No separate `--cloud` flag. Profile `cloud_consent` controls auto-routing only.
- **Idempotency**: SHA-256 source hash in output frontmatter. Re-run = skip. `--force` to overwrite.
- **Filesystem**: Write only inside vault. Read from anywhere.
- **Subprocesses**: `asyncio.create_subprocess_exec` (never `shell=True`). Configurable timeouts.
- **No AI imports**: Core library is deterministic. AI lives in the transport/skill layer.
- **Router validation**: Routers validate tool+input combinations, not just enum membership. `--tool gemini` on a local file or `--tool coli` on a YouTube URL is rejected with an actionable error. The router is the validation boundary — transports trust it.

## Scheduled Automation (v0.4)

Carrel can run overnight via Desktop App local scheduled tasks. The `automation` skill defines the contract; `/carrel-automate` configures it.

- **Trust levels**: Advisory (suggest only) → Consultative (propose, researcher approves) → Delegated (act on new items, experimental) → Partnership (reorganize, experimental)
- **AutomationConfig** in `models.py`: per-capability booleans, trust level, model, schedule, review cadence
- **Session-start hook**: surfaces morning briefs, active plans, pending decisions/approvals (gated on `_meta/briefs/` existence)
- **Generated prompt**: `_meta/automation-prompt.md` — per-researcher, uses vault detection (no absolute path)
- **Two-track sync**: `environment.json` + vault `CLAUDE.md` must both reflect automation preferences

Commands: `/carrel-batch` (sequential file processing), `/carrel-automate` (configure), `/carrel-mirror` (research self-portrait)

## Collaboration (v0.5.1)

`/carrel-share` generates a vault-specific handbook for an incoming collaborator (RA, co-author, lab member) by synthesizing friction log, capability log, reflections, configured tools, sensitivity rules, and active threads. Distinct from `/carrel-setup` (new researcher's own vault) and from Claude Code's `/team-onboarding` (generic Claude Code usage tips). Output: `_meta/handbook/[YYYY-MM-DD]-for-[name].md`.

Skill: `collaborator-onboarding`. Profile fields that drive it: `collaborators: bool`, `team_context: str | None`. Asked in setup interview; surfaced in Phase 9 handoff when `collaborators == true`.

## Knowledge Wiki

Optional synthesis layer: agent-maintained entity/concept pages that compound knowledge across sources. Adapted from [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) + [Hermes Agent](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md).

- **Trust-gated**: Advisory=off, Consultative=propose with approval, Delegated=autonomous. Activation implies at least consultative.
- **Folder mapping**: `papers/`, `transcripts/`, `inbox/` = source layer. `wiki/` = synthesis layer. No separate `raw/`.
- **Operations**: ingest, query (trust-gated filing), lint. See `skills/knowledge-wiki/SKILL.md`.
- **Dialogue**: researcher callouts (`> [!researcher]`) on wiki pages — agent reads, never overwrites. Wiki = field's voice; `notes/` = researcher's voice; gap = contribution.
- **Ephemeral agent**: log.md includes reasoning per decision (cross-instance handoff). Lazy orientation (full context only for writes).
- **Automation**: `wiki_maintenance` in AutomationConfig. At delegated trust, briefs include per-file revert instructions + one-sentence insight.
- **Model fields**: `wiki_enabled`, `wiki_preference`, `wiki_proposal_deferred_until` on ResearcherProfile. Read by Claude, not code-enforced.
- **Detection**: check `wiki/SCHEMA.md` existence (not just `wiki/`). Upstream in `capability-registry.md`.

## Feedback Loops

Interview preferences flow into two systems that must stay in sync:
- **environment.json** → CLI router (structured, mechanical). The CLI reads `cloud_consent`, `sensitivity`, etc.
- **Vault CLAUDE.md** → Claude's judgment (narrative, contextual). Claude reads this every session.
- **setup-state.json** (`.carrel/setup-state.json`, added v0.5.2) → tracks `last_completed_phase` so `/carrel-setup` can pause and resume. Written by `carrel vault init` (initial: phase 4); managed via the `carrel setup-state` CLI (added v0.5.3 — `advance --phase N`, `complete`, `show`, `reset`); `completed_at` set at phase 9. Hook surfaces a resume prompt if paused. The `SetupState` Pydantic model enforces `phase ∈ [4,9]`, semver `version`, ISO `completed_at`, and the mutual-implication invariant `phase == 9 ⟺ completed_at is set`.

The setup SKILL (Step 5) instructs Claude to write a personalized CLAUDE.md from the interview. When preferences change, update BOTH files. The session-start hook surfaces preferences so Claude has immediate context.

## Version & Migration

Plugin version is tracked in `.carrel/plugin-state.json` in each vault. The `/carrel-migrate` command compares this against the plugin's current version, assesses the environment, and suggests improvements.

Migration files live in `migrations/` with a `registry.json` index. Each migration is a markdown file describing what's new, automatic steps, and manual steps. Add new migrations when releasing breaking changes or significant features.

When bumping the plugin version in `.claude-plugin/plugin.json`, also update `.claude-plugin/marketplace.json` and `pyproject.toml` + `src/carrel/__init__.py` to match, and add a migration file if the update affects the user's vault or config. The `check-version.js` hook module reads `plugin_version` from plugin-state.json and is wired into the session-start hook.

## Gotchas

- `markitdown` (Microsoft's library) is the non-PDF converter — NOT the old MCP tool names
- `defuddle` is the web capture tool — much better than markitdown for URLs
- Install constants are centralized in `env/install.py` — don't duplicate
- coli install uses `bun add -g @marswave/coli` (not npm)
- gws (Google Workspace CLI) requires Google Cloud project + OAuth — high friction setup, see `references/gws-setup-guide.md`
- Cheat sheet regeneration: `carrel vault cheatsheet --vault <path> --force` (added v0.5.2; the legacy `generate-cheatsheet.js` was removed). Renderer beefed up in v0.5.3 with configured-tools matrix, common workflows, and next steps sections.
- youtube-transcript-api >= 1.0 uses `.fetch()` not `.get()`, returns objects not dicts
- Wiki preference fields (`wiki_preference`, `wiki_proposal_deferred_until`) are on the Pydantic model but read by Claude via skill instructions, not enforced by hooks — consistent with all carrel preferences
- Windows support is partial. v0.5.3 added stopgap cross-platform guidance for `/carrel-setup` (OS-branched Obsidian install in Phase 6; `install_command_for(tool, platform)` helper in `env/install.py`; platform note at top of `decision-tree.md`). README now has a Platform Support matrix. But `env/audit.py` still uses macOS `mdfind` and most install constants remain brew-only — full fix is `planning/specs/007-cross-platform-support.md` (pre-implementation; locked-blocked on liteparse Windows + gws Windows research).
- Setup-state changes go through `carrel setup-state` (added v0.5.3) — never edit `.carrel/setup-state.json` by hand. The CLI is the validation boundary.
- Sensitivity gate (v0.5.4): `Sensitivity.HIGH` blocks ALL cloud tools (mineru, groq, gemini, gws) regardless of `cloud_consent`. Implemented in `consent.py:resolve_cloud_consent`. Stopgap until policy module (spec 010) lands. `gws` is treated as cloud since it's a Google API call.
- Vault writes go through `safe_path.safe_vault_join` (v0.5.4) — resolves the path and rejects anything escaping the vault root. Used by all filers + scaffold + google export.
- Trust enforcement (v0.6.0): writes that require Consultative+ trust now go through `carrel trust check <action>` — see `spec 008-trust-enforcement.md` and `carrel trust list --vault .` for the action matrix. The check is the single boundary; never bypass it.
- Profile data is asked to live in 5 surfaces (`environment.json`, vault `CLAUDE.md`, `_meta/my-environment.md`, `_meta/cheat_sheet.md`, sometimes `_meta/automation-prompt.md`). Only `_meta/cheat_sheet.md` has a deterministic generator. Spec 011-profile-sync-architecture.md tracks the deterministic-sync future.

## Capability Absorption

Carrel grows by absorbing capabilities from the ecosystem (skills repos, MCP servers, CLI tools) and by learning from what researchers actually need. The `self-improve` skill owns this process — see `skills/self-improve/SKILL.md` for the full evaluation criteria, absorption process, and tracking mechanism.

**One-plugin policy**: researchers install Carrel, everything works. No companion dependencies. We absorb and curate, not delegate.

**Registry**: `skills/self-improve/references/capability-registry.md` tracks what's been absorbed, from where, and when to review upstream.

## Relationship to ItDepends

Carrel is the on-ramp to ItDepends (abductive research agent). Same Python + pydantic + typer + rich stack. Carrel modules may become ItDepends components (profile → Mneme, vault papers → Scholia).

## Spec & Review History

Multi-model review process: each spec gets adversarial reviews before implementation. The default reviewer set is **Codex (deep adversarial pass) + Kimi (independent second-pair-of-eyes) + a feasibility/architect pass**. Some specs go through multiple rounds. All artifacts in `planning/`.

| File | Purpose |
|------|---------|
| `planning/specs/001-core-library-extraction-v3.md` | Core library spec (final) |
| `planning/specs/002-tool-expansion-and-cleanup.md` | Tool expansion: defuddle, YouTube captions, gws |
| `planning/reviews/003-implementation-review.md` | Post-implementation review |
| `planning/reports/002-report-codex.md` | Tool expansion report |
| `planning/reports/003-report-codex.md` | Core library fix report |
| `planning/specs/004-scheduled-automation-and-shared-agency.md` | v0.4 spec: scheduled automation + graduated trust |
| `planning/reviews/004-review-codex.md` | v0.4 adversarial review (Codex) |
| `planning/reviews/004-review-architect.md` | v0.4 feasibility review (architect) |
| `planning/reviews/004-review-implementation.md` | v0.4 post-implementation spec compliance |
| `planning/reviews/005-knowledge-wiki-review.md` | Knowledge wiki: internal + Codex adversarial reviews (2 rounds) |
| `planning/specs/006-environment-validation-and-self-healing.md` | v0.7 spec: schema validation, lint, doctor agent; consumes spec 007's PlatformToolMatrix (pre-implementation, sequenced after 007) |
| `planning/specs/007-cross-platform-support.md` | v0.7 spec: Windows + Linux first-class support; platform-aware audit, install, decision tree. **Locked 2026-04-20** (upstream blockers resolved — liteparse + gws both ship Windows support). Ready for implementation. |
| `planning/research/007-windows-tools-research.md` | Research that unblocked spec 007 (liteparse + gws Windows install paths; Web Clipper rejection; native Google Docs Markdown export tip) |
| `planning/reviews/008-deployment-readiness-triangulated.md` | Synthesis of Kimi + Codex + internal code-reviewer findings on the v0.5.0→v0.5.2 sprint; tiered fix plan — **fully implemented in v0.5.3** (B1, B2, A1-A7, S1-S3, H1-H3) |
| `planning/reviews/008-review-kimi.md` | Kimi rounds 1+2: schema drift findings + post-fix re-review |
| `planning/reviews/008-review-codex.md` | Codex fresh adversarial pass: 2 BLOCKERS + #1 recommendation (deterministic state-transition CLI) |
| `planning/reviews/008-review-internal.md` | Internal code-reviewer: 6 HIGH-confidence Python/JS issues |
| `planning/reviews/009-holistic-audit-triangulated.md` | Whole-repo audit synthesis: code quality + docs + plugin surface + Codex adversarial. Tier 0-3 **fully implemented in v0.5.4**. Headline insight: "markdown control plane" risk — A1/A2/A3 deferred to specs (trust enforcement, policy module, profile sync) |
| `planning/reviews/009-audit-code-quality.md` | Internal code-reviewer whole-repo pass: 2 critical, 8 HIGH, 10 MEDIUM (error contracts, dead code, idempotency) |
| `planning/reviews/009-audit-documentation.md` | Documentation coherence pass: 5 HIGH, 6 MEDIUM (skill drift, fictional Mustache template, hardware-audit schema mismatch) |
| `planning/reviews/009-audit-plugin-surface.md` | Plugin wiring integrity pass: 3 runtime bugs (session-reflect dead, /carrel-research nonexistent, cloud_consent display) + drift |
| `planning/reviews/009-audit-adversarial.md` | Codex 12-month-on-call lens: trust enforcement gap, sensitivity routing gap, narrative shadow state, 3 predicted bug classes |
| `planning/specs/008-trust-enforcement.md` | v0.6.0 spec: `carrel trust check` CLI gates writes by trust level — **fully implemented in v0.6.0** (closes 009 A1 / Codex §4) |
| `planning/specs/010-policy-module.md` | v0.6.x spec: `src/carrel/policy.py` owns sensitivity routing; `--explain` rationale flag (closes 009 A2 / Codex §2) |
| `planning/specs/011-profile-sync-architecture.md` | v0.6.x or 0.7.0 spec: regenerators for the 4 mirror surfaces (`my-environment.md`, `automation-prompt.md`); drift-check for vault `CLAUDE.md` (closes 009 A3 / Codex §3,§6) |
