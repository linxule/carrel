# Carrel

Research environment toolkit for academics. Two layers: a Python core library (`carrel` CLI) and a Claude Code plugin (skills, agents, hooks, commands).

## Quick Commands

```bash
# Core library
uv run pytest                                    # 275 tests
uv run carrel env doctor                         # Hardware + tools audit
uv run carrel env validate --vault .            # Validate environment.json + drift markers
uv run carrel env fix --safe --vault .          # Apply safe environment.json repairs
uv run carrel vault init /tmp/test               # Scaffold a vault
uv run carrel paper convert paper.pdf            # Convert PDF (liteparse default)
uv run carrel transcript create rec.m4a          # Transcribe audio (coli default)
uv run carrel capture url https://example.com    # Web capture (defuddle)
uv run carrel google export <google-docs-url>    # Google Docs export (gws)
uv run carrel vault cheatsheet --vault . --force # Regenerate _meta/cheat_sheet.md
uv run carrel vault dashboard --vault . --force  # Regenerate _meta/my-environment.md
uv run carrel vault automation-prompt --vault . --force # Regenerate _meta/automation-prompt.md
uv run carrel vault check-sync --vault .         # Check CLAUDE.md profile markers for drift
uv run carrel vault add-markers --vault .        # Append profile markers to CLAUDE.md
uv run carrel setup-state show --vault .         # Inspect setup phase (v0.5.3+)
uv run carrel setup-state advance --phase N      # Move to next phase atomically
uv run carrel setup-state complete --vault .     # Mark setup complete (idempotent)
uv run carrel trust check automation:propose --vault .  # Check if action allowed at current trust level
uv run carrel trust list --vault .  # See what current trust unlocks
uv run carrel paper convert foo.pdf --explain    # Print routing decision + rationale without executing
uv run carrel vault feedback export --redact-list redact.txt --vault . # Anonymized feedback digest (v0.9.0)
uv run carrel vault mirror --write --from-stdin --vault . # Idempotent dated mirror file (v0.9.0)
uv run carrel vault reflect-log --append --from-stdin --vault . # Atomic append to dated reflect-log (v0.9.0)
uv run carrel vault share generate --mode quick --for alice --sensitivity medium --vault . # Collaborator handbook (v0.9.0)
uv run carrel batch convert <folder> [--unattended] --vault . # Sequential PDF batch (v0.9.0)
uv run carrel batch transcribe <folder> [--unattended] --vault . # Sequential audio/YouTube batch (v0.9.0)
uv run carrel automate configure --enabled true --trust-level consultative --schedule daily --review-cadence weekly --vault . # Typed-flag automation config, no prompts (v0.9.0)
uv run carrel migrate apply [--plugin-root <path>] --vault . # Walk migrations registry, update plugin-state.json (v0.9.0)
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
│   ├── cli/              # typer CLI (paper, transcript, vault, env, capture, google, setup-state, trust)
│   ├── convert/          # PDF/doc conversion (router, adapters, filer, pipeline)
│   ├── transcribe/       # Audio/video transcription (router, adapters, filer)
│   ├── google/           # Google Workspace export (gws CLI integration)
│   ├── vault/            # Vault scaffold, organize, templates, markers, dashboard, automation_prompt
│   ├── env/              # Audit, profile, install, validation, healing, platform
│   ├── policy/           # Sensitivity routing (16-row matrix) + trust enforcement
│   ├── models.py         # Pydantic models (options, results, enums, AutomationConfig, ResearcherProfile, SetupState)
│   ├── safe_path.py      # Vault containment helper
│   ├── youtube_url.py    # Unified YouTube URL parser
│   ├── source_hash.py    # Unified source-hash helper for idempotency
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
├── install.ps1           # Windows installer (first-class as of v0.7.0)
└── pyproject.toml        # pydantic + typer + rich + httpx + markitdown + defuddle + youtube-transcript-api
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

## Model Teammates (v0.8.1)

`/carrel-teammates` brings Codex (ChatGPT), Gemini, and Kimi into Claude Code via community plugins (`openai/codex-plugin-cc`, `thepushkarp/cc-gemini-plugin`, `linxule/kimi-plugin-cc`). Profile field `model_teammates: dict[str, ModelTeammateStatus]`. Skill: `skills/model-teammates/SKILL.md`. Spec: `planning/specs/013-model-teammates.md`.

Vocabulary: **teammates** ≠ Claude-side `agents/` (setup-interviewer, research-partner) ≠ human `collaborators` (co-authors/RAs via `/carrel-share`).

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

## Architecture Normalization (v0.9.0)

Spec 014 (CC-only re-scope) normalizes the three-layer rule for 7 high-value command paths. Deterministic file I/O moved to `carrel <subcmd>`; orchestration moved into skills; slash commands shrunk to thin `!carrel <subcmd> ${ARGS}` wrappers.

- **7 new CLI subcommands**: `vault {feedback export, mirror, reflect-log, share generate}`, `batch {convert, transcribe}`, `migrate apply`, `automate configure`. All typed-flag, no prompting; `--explain` dry-run where routing applies.
- **7 wrapper shrinks** (564 → 35 body lines): `/carrel-{feedback,migrate,mirror,reflect,share,batch,automate}`. Convention: `${ARGS}` (skill-constructed) vs `$ARGUMENTS` (raw user input) documented in `commands/CONVENTIONS.md`.
- **Skill enrichments** absorbed the freed orchestration prose: `automation` (10-step flow + Desktop App walkthrough + unattended-batch contract), `convert`+`transcribe` (pre-batch routing), `collaborator-onboarding` (mode + sensitivity tiers), `self-improve` (migrate orchestration), `research-partner` (mirror 5-dimension synthesis), new `session-reflection` skill (reflect + feedback read/write symmetry).
- **3 CC plugin feature adds**: marketplace metadata (keywords, category, license, repository); `UserPromptSubmit` hook (`hooks/inject-context.js`) for per-turn vault context; `PreToolUse` Bash matcher (`hooks/sensitivity-gate.js`) for sensitivity ask-gate before cloud subprocesses (bypass via `# bypass-gate` comment).

Spec: `planning/specs/014-cc-plugin-v090.md`. Cross-CLI port (Codex + Kimi) parked as future work; investigation artifacts preserved.

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
- Cross-platform (v0.7.0): all Tier 1 tools work on macOS, Linux, Windows. Install paths are platform-keyed in `env/install.py`; audit detects the platform in `audit.py`; decision-tree and cheatsheet render OS-aware.
- Setup-state changes go through `carrel setup-state` (added v0.5.3) — never edit `.carrel/setup-state.json` by hand. The CLI is the validation boundary.
- Sensitivity gate (v0.7.0): the full 16-row (sensitivity × cloud_consent × requested_tool) matrix is implemented in `src/carrel/policy/sensitivity.py:select_tool`. HIGH blocks cloud regardless of consent (gws included — Google API calls send data). MEDIUM requires explicit `--tool <cloud>` to route to cloud. LOW defaults local-first; `cloud_consent=True` auto-routes when local unavailable. `consent.py:resolve_cloud_consent` is now a thin backward-compat wrapper around `policy.sensitivity`. Use `--explain` on `carrel paper convert` / `transcript create` / `google export` to see the routing decision + rationale without executing.
- Vault writes go through `safe_path.safe_vault_join` (v0.5.4) — resolves the path and rejects anything escaping the vault root. Used by all filers + scaffold + google export.
- Trust enforcement (v0.6.0): writes that require Consultative+ trust now go through `carrel trust check <action>` — see `spec 008-trust-enforcement.md` and `carrel trust list --vault .` for the action matrix. The check is the single boundary; never bypass it.
- Environment drift (v0.7.0, spec 006): `carrel env validate --vault .` is the full validator and `carrel env fix --safe --vault .` applies deterministic repairs to `.carrel/environment.json` only. Hook runs `env validate` once per 24h and surfaces `/carrel-fix` when drift needs review.
- Profile sync (v0.7.0): `_meta/my-environment.md` and `_meta/automation-prompt.md` are now deterministic (regenerate via `carrel vault dashboard|automation-prompt --force`). Vault `CLAUDE.md` uses HTML-comment markers (`<!-- carrel:field -->value<!-- /carrel:field -->`); `carrel vault check-sync` still exists for marker-only inspection.

## Capability Absorption

Carrel grows by absorbing capabilities from the ecosystem (skills repos, MCP servers, CLI tools) and by learning from what researchers actually need. The `self-improve` skill owns this process — see `skills/self-improve/SKILL.md` for the full evaluation criteria, absorption process, and tracking mechanism.

**One-plugin policy**: researchers install Carrel, everything works. No companion dependencies. We absorb and curate, not delegate.

**Registry**: `skills/self-improve/references/capability-registry.md` tracks what's been absorbed, from where, and when to review upstream.

## Relationship to ItDepends

Carrel is the on-ramp to ItDepends (abductive research agent). Same Python + pydantic + typer + rich stack. Carrel modules may become ItDepends components (profile → Mneme, vault papers → Scholia).

## Spec & Review Process

Each spec gets adversarial reviews before implementation. Default reviewer set: **Codex (deep adversarial pass) + Kimi (independent second-pair-of-eyes) + a feasibility/architect pass**. Some specs go through multiple rounds. Spec "Open Questions" must be locked (decision + rationale) before delegated implementation.

Full work log — every spec, review, report, research artifact with one-line summary — lives in [`planning/README.md`](planning/README.md). Don't duplicate it here.
