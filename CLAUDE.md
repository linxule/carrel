# Carrel

Research environment toolkit for academics. Two layers: a Python core library (`carrel` CLI) and a Claude Code plugin (skills, agents, hooks, commands).

## Quick Commands

```bash
# Core library
uv run pytest                                    # 49 tests
uv run carrel env doctor                         # Hardware + tools audit
uv run carrel vault init /tmp/test               # Scaffold a vault
uv run carrel paper convert paper.pdf            # Convert PDF (liteparse default)
uv run carrel transcript create rec.m4a          # Transcribe audio (coli default)
uv run carrel capture url https://example.com    # Web capture (defuddle)
uv run carrel google export <google-docs-url>    # Google Docs export (gws)
uv run carrel vault cheatsheet --vault . --force # Regenerate _meta/cheat_sheet.md
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
- **setup-state.json** (`.carrel/setup-state.json`, added v0.5.2) → tracks `last_completed_phase` so `/carrel-setup` can pause and resume. Written by `carrel vault init` (initial: phase 4); Claude updates as phases complete; `completed_at` set at phase 9. Hook surfaces a resume prompt if paused.

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
- Cheat sheet regeneration: `carrel vault cheatsheet --vault <path> --force` (added v0.5.2; the legacy `generate-cheatsheet.js` was removed)
- youtube-transcript-api >= 1.0 uses `.fetch()` not `.get()`, returns objects not dicts
- Wiki preference fields (`wiki_preference`, `wiki_proposal_deferred_until`) are on the Pydantic model but read by Claude via skill instructions, not enforced by hooks — consistent with all carrel preferences
- Windows support is partial: `install.ps1` works, but `env/audit.py` uses macOS `mdfind` (won't detect Obsidian/Zotero on Windows), `env/install.py` constants are all `brew`, and `decision-tree.md` recommends `brew install` unconditionally. Windows users complete install but hit walls during `/carrel-setup`. See `planning/specs/007-cross-platform-support.md` (when written) for the fix plan.

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
| `planning/specs/006-environment-validation-and-self-healing.md` | v0.6 spec: schema validation, lint, doctor agent (pre-review) |
| `planning/specs/007-cross-platform-support.md` | v0.7 spec: Windows + Linux first-class support; platform-aware audit, install, decision tree (pre-review) |
