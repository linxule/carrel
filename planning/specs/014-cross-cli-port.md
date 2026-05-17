# Spec 014: Cross-CLI Port — Architecture Normalization + Multi-Host Adapter

**Status**: Locked (2026-05-17) — implementation-ready; Empirical Prerequisites EP-1 through EP-4 deferred to Phase 1 implementer
**Origin**: User request — make carrel work as a plugin for Codex CLI and Kimi CLI in addition to Claude Code
**Reviews**: Codex (adversarial) + Kimi (second-pair-of-eyes) + code-architect (feasibility) — Round 1 complete; amendments applied; Round 2 not run (user judgment: spec is sound, implementation will surface real gaps faster than another review round)

---

## Problem

Carrel ships as a Claude Code plugin (15 commands + 12 skills + 2 agents + 2 hooks + 0 MCP). Two adjacent CLIs now justify a port:

- **Codex CLI** (`openai/codex`) — has a plugin system structurally close to Claude Code (`plugin.json` manifest, marketplaces, first-class MCP, same hook event names; the marketplace even accepts `.claude-plugin/marketplace.json` for legacy compat). One real gap: no user-defined `commands/*.md` surface.
- **Kimi CLI** (Moonshot) — plugin system is a tool-execution registry, not a Claude-style bundle. Strong overlap on skills (Kimi reads `.claude/skills/` natively). Commands, agents, hooks-in-plugin, MCP bundling all degrade to "install scripts + manual config edits." Feature request #1714 proposes a Claude-compat layer; status TBD (see Open Questions).

Investigation hypothesis (data-confirmed): **carrel's 15 slash commands are mostly ergonomic shortcuts**. A command-to-skill mapping pass found 47% REDUNDANT (skill fully covers), 27% PARTIAL (skill covers intent, command adds orchestration), 27% UNIQUE (no skill owns the logic — `/feedback`, `/migrate`, `/mirror`, `/reflect`). The UNIQUE four all do deterministic file I/O — work that architecturally belongs in the Python CLI, not in markdown command files.

This spec proposes a **two-phase** approach:

- **Phase 1 — Architecture normalization** (host-independent). Extract command logic into `carrel <subcommand>` calls. Shrink slash commands to thin `!carrel <subcmd> $ARGS` wrappers. Resolve `${CLAUDE_PLUGIN_ROOT}` out of carrel's core. Update skills to invoke CLI subcommands. Ship as v0.9.0 with no port yet — valuable on its own because it aligns commands with carrel's stated architecture ("skills = judgment, CLI = ops, transports = thin").
- **Phase 2 — Multi-host adapter** (`src/carrel/host/`). Build pipeline emits per-host plugin bundles from a single canonical source. New CLI subcommand `carrel build <host>`. Ship as v0.10.0 with Codex CLI + Kimi CLI builds alongside the Claude Code build.

## Locked Decisions

| Question | Decision | Rationale |
|---|---|---|
| Single repo vs split repos? | **Single repo, build per host** | Lower release ceremony, prevents drift, one PR touches all hosts |
| Adapter at build-time or runtime? | **Build-time only** | Keeps Python core host-agnostic; installed plugins are inspectable; decouples carrel releases from host quirks |
| Where does `carrel build` live? | **Subcommand in main carrel CLI** | Discoverable, reuses typer infra, no extra install for contributors |
| How aggressive on commands? | **Translate all command logic → `carrel <subcmd>`**; commands directory becomes Claude-Code-only | Confirms carrel's three-layer architecture, eliminates `${CLAUDE_PLUGIN_ROOT}` dependency, makes Codex/Kimi ports symmetric |
| Phase ordering | **Phase 1 ships before Phase 2** | Phase 1 has standalone value; reviewers can stress-test architecture changes before porting churn |
| Backward compatibility for CC build | **Byte-for-byte reproduction required** | Existing users get zero disruption; CI diffs the CC build against current state |
| Module naming | **`src/carrel/build/`** (not `host/`) | Avoids vocabulary collision with carrel's existing tool/transport/adapter/teammate/collaborator; matches user-facing `carrel build` command (architect review) |
| Builder shape | **Functional dispatch dict** (`BUILDERS: dict[Target, Callable]`) | Matches carrel's pattern across `env/install.py`, `policy/sensitivity.py`, `convert/adapters/`. ABC+subclasses over-engineers 3 mostly-mechanical build targets (architect review) |
| Templates location | **`src/carrel/templates/`** loaded via `importlib.resources` | Decouples from repo layout; removes fragile `parents[3]` path math; templates are core not plugin (architect review) |
| `setup-interviewer` agent | **State machine extracted to `carrel setup interview --phase N` CLI; interview prose stays in `environment-setup` skill** | Honors three-layer architecture; addresses Codex+Kimi reviewers' concern that passive-skill translation loses 9-phase state logic. Skill drives, CLI executes deterministic phase transitions. |
| Marketplace path | **CC build writes to repo root** (preserves `marketplace.json` source `"./"`); **Codex+Kimi to `dist/<target>/`** | No disruption to existing `claude plugin update carrel` flows; satisfies byte-for-byte CC backward-compat (architect review) |
| Wrapper args convention | **`${ARGS}` (skill-constructed) for PARTIAL command wrappers**; **`$ARGUMENTS` (raw user input) only for REDUNDANT commands** | Shell wrappers cannot have conditionals; orchestration moves to skills, which construct the arg list (architect + Codex review) |
| Reviewer factuality note | **15 commands confirmed** | Codex reviewer claimed 16 with `carrel-migrate.md` missing from inventory. Verified false: `ls commands/ | wc -l` = 15; `carrel-migrate` classified UNIQUE at spec line 16 and has CLI subcommand row. Recording as evidence that adversarial review claims need verification, not auto-trust. |

## Empirical Prerequisites (before delegated implementation)

Four ~10-minute experiments resolve under-spec'd implementation details. Each must complete and be documented under `planning/reviews/014-empirical-<name>.md` before the corresponding builder ships.

| Check | Question | Method | Blocks |
|---|---|---|---|
| **EP-1: Codex `${CLAUDE_PLUGIN_ROOT}`** | Does Codex CLI actually inject `CLAUDE_PLUGIN_ROOT` into hook scripts as docs claim? | Build a minimal test plugin with a hook script that prints `env | grep CLAUDE_PLUGIN_ROOT`. Run `codex plugin install ./test/`, trigger the hook. Inspect output. | Codex builder hook emission strategy |
| **EP-2: Kimi skill auto-discovery** | Does Kimi auto-discover skills placed at `~/.kimi/skills/<n>/SKILL.md`, or does it require `~/.kimi/config.toml` `[skills]` registration? | Copy a test skill to `~/.kimi/skills/test-skill/SKILL.md`. Launch Kimi. Try `/skill:test-skill`. If unrecognized, repeat with `[[skills]]` entry in `config.toml`. | Kimi builder install script complexity |
| **EP-3: Marketplace path bump (canary)** | If `marketplace.json` source changes from `./` to `./dist/cc/`, what breaks for an existing `claude plugin update carrel` install? | On a test machine with carrel already installed, push a marketplace change, run `claude plugin marketplace refresh` + `claude plugin update carrel`. Document failure modes. | Marketplace strategy fallback path (if locked decision proves disruptive) |
| **EP-4: Kimi hook handler path resolution** | Does `~/.kimi/config.toml` resolve `$HOME` / `~` in `[[hooks]]` `command` paths, or require absolute paths? | Add a hook with `command = "~/test-script.sh"` (and a parallel `command = "/Users/.../test-script.sh"`). Trigger event. Check which fires. | Kimi install script — whether to substitute absolute paths at install time |

Resolution path: if EP-1 confirms positive, the Codex hook scripts ship unmodified; if negative, builder substitutes the env var at build time with absolute paths. If EP-2 requires registration, install script grows a `config.toml` patch step. If EP-3 reveals disruption beyond expected one-time refresh, fall back to keeping CC at repo root permanently (already the chosen path). If EP-4 requires absolute paths, install script resolves `$HOME` at install time and writes absolute paths into the user's config.

These prerequisites are testable in <1 hour total. None should block Phase 1.

## Open Questions (reviewer targets)

These are the bits where data is missing or judgment calls remain. Adversarial reviewers should hit these hardest.

### OQ-1 — Codex plugin root env var **[RESOLVED]**
Codex CLI injects `PLUGIN_ROOT` and `PLUGIN_DATA` into plugin-bundled hook scripts **and** maintains `CLAUDE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_DATA` for Claude Code compatibility. Carrel's existing `${CLAUDE_PLUGIN_ROOT}` references work in Codex unchanged. Source: `developers.openai.com/codex/plugins/build` lines 930–955, `developers.openai.com/codex/hooks` lines 789–808, `codex-rs/hooks/src/engine/discovery.rs` lines 2590–2687.

**Spec impact**: Phase 1's `${CLAUDE_PLUGIN_ROOT}` cleanup is **no longer required for Codex compat**. Kimi compat (OQ-4) may still motivate it — pending Kimi research. If Kimi #1714 lands with `CLAUDE_PLUGIN_ROOT` honoring, the cleanup becomes optional polish, not a hard requirement.

### OQ-2 — Codex agent TOML schema **[PARTIALLY RESOLVED]**
Schema confirmed (from `developers.openai.com/codex/subagents` lines 655–695):
- **Required**: `name`, `description`, `developer_instructions`
- **Optional**: `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`, `nickname_candidates`
- **No per-agent `tools` / `disallowedTools` allowlist** (differs from Claude Code)
- Invocation syntax undocumented (whether `@agent-name` works or only via `/agent`)

**Critical gap**: Codex agents are documented only at user/project level (`~/.codex/agents/` or `.codex/agents/`), **not as a plugin-bundled artifact**. The plugin manifest at `developers.openai.com/codex/plugins/build` lines 882–900 makes no mention of agents.

**Spec impact**: Phase 2's agent translator cannot bundle agents inside the Codex plugin directly. Two options:
(a) Codex builder emits TOML files into a separate `agents-install/` directory + post-install script that copies them to `~/.codex/agents/` (user-global, namespace prefixed: `carrel-research-partner`, `carrel-setup-interviewer`)
(b) Drop agents from the Codex build entirely — convert to skills like Kimi (carrel only has 2 agents, both could become skills without losing much)
Recommendation: **(b)** — simpler, symmetric with Kimi path, preserves the "thin plugin" architecture.

### OQ-3 — Codex subagent surface beyond plugin-defined agents **[RESOLVED]**
Codex has a built-in subagent runtime with types `default`, `worker`, `explorer`, plus `/agent` thread management and an experimental `spawn_agents_on_csv`. **But plugins have no documented imperative control** — they cannot request Codex spawn subagents on their behalf. Hook handlers of type `agent` are parsed but skipped today. Source: `developers.openai.com/codex/subagents` lines 615–645, 770–801; `developers.openai.com/codex/hooks` lines 739–745.

**Spec impact**: The "Codex orchestrates its own sub-agents to verify all files" capability — which the user flagged as valuable — happens at the **Codex agent runtime layer**, not at the plugin layer. Carrel cannot trigger it from a slash command, skill, or hook. The capability is available to a user running Codex who happens to have carrel installed, not to carrel itself.

For the spec **review** workflow (separate from runtime): yes, the user can run Codex CLI with the carrel plugin installed, and Codex will spontaneously spawn subagents to read the spec + carrel files. That's the intended review-time use, and it works regardless of this spec.

### OQ-4 — Kimi #1714 status **[RESOLVED — proceed assuming non-merge]**
Issue [MoonshotAI/kimi-cli#1714](https://github.com/MoonshotAI/kimi-cli/issues/1714) is **open** as of mid-May 2026. Working fork: `GTC2080/kimi-cli@GTC/claude-plugin-compat` — 99 passing tests, clean ruff/pyright, no PR opened yet. Marked a "hot issue" in the April 2026 community digest but **no maintainer commitment** to merge.

Proposed surface (if it lands):
- `--plugin-dir /path/to/plugin` CLI flag (session-scoped)
- Auto-discovery from `~/.kimi/claude-plugins/`
- Reads `.claude-plugin/plugin.json`
- Best-effort: `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `settings.json` (only `agent` key)
- Capability summary injected into model context for skill/command routing
- Explicit non-goals: no marketplace, no `.lsp.json`, no mutation of `~/.kimi/mcp.json`
- **Critical limitation**: hooks + MCP stay session-scoped only — no cross-session persistence
- **Not specified**: env vars like `${KIMI_PLUGIN_ROOT}` or honoring `${CLAUDE_PLUGIN_ROOT}` — path rewriting is undocumented

**Spec impact**: Don't bet Phase 2's Kimi builder on #1714 landing. Build assuming the native Kimi plugin system (tool registry + 1 SKILL.md + user-global hooks). If #1714 lands later, the Kimi builder gets a second mode (`--target kimi-compat`) that emits a `.claude-plugin/` shaped output. Path rewriting remains an open question for the Kimi-compat target — likely safest to resolve absolute paths at build time rather than rely on env vars.

### OQ-5 — Kimi subagent surface **[RESOLVED]**
Earlier intel was inaccurate. Kimi CLI does **not** ship built-in `coder`/`explore`/`plan` subagent types. The actual surface:

- **Built-in agents** (selectable at startup via `--agent`): `default` and `okabe` (experimental)
- **Subagents are user-defined YAML** under an agent's `subagents:` key — each points to a sibling YAML file via `path:` and gets a `description:`
- **Invocation**: built-in **`Task` tool** (`kimi_cli.tools.multiagent:Task`) dispatches to `subagent_name` with `description` + `prompt`; returns result to parent
- **Dynamic creation**: `CreateSubagent` tool (not enabled by default; must be added to agent's `tools` list) lets the AI define new subagent types at runtime; persisted with session
- **Parallelism**: explicitly supported — "multiple independent tasks can be processed in parallel" via `Task`; `LaborMarket` registry manages available types
- **Per-subagent model selection**: **not currently possible** — subagents inherit parent session model. Issue [#6651](https://github.com/MoonshotAI/kimi-cli/issues/6651) requests this capability (18 comments, 24 up-votes early 2026), no commitment
- **Plugin coupling**: plugin/hook docs don't mention subagents; subagent config lives entirely in Agent Spec YAML layer; "plugin-defined Claude agent" is not yet auto-loadable as a Kimi subagent (would depend on #1714)
- **Conceptual distinction**: a Kimi "skill" is a `SKILL.md` slash command (not a runtime subagent); a "subagent" is an isolated context window + toolset dispatched via `Task`

**Spec impact**: Same constraint as Codex (OQ-2/OQ-3) — plugins can't bundle subagents that auto-discover. Carrel's 2 agents → skills strategy (locked in OQ-2's resolution) holds for Kimi too. The "Codex/Kimi orchestrates its own subagents to verify the spec" capability the user flagged is available at **runtime** for review purposes regardless of this spec.

**Notable correction to record**: any prior spec sections that referenced Kimi's "built-in `coder`/`explore`/`plan` subagents" were based on an inaccurate earlier kimi-ask report. The actual built-ins are `default` and `okabe`. This spec corrects that.

### OQ-6 — Hook output schema portability **[RESOLVED]**
Decision: option (a) for Kimi (drop structured stderr, degrade to plain stderr — captured in Phase 2 transformation table). Codex parses similarly to Claude Code per OQ-1 evidence, so structured JSON is preserved there. The hook handler emits the canonical JSON unchanged; per-host translation happens at the build layer — Kimi build strips/converts the structured fields, Codex+CC ship as-is. This avoids in-handler `if host == 'kimi'` conditionals.

### OQ-7 — Memory file convention **[RESOLVED]**
Decision: `carrel vault init` continues to emit only `CLAUDE.md` (current behavior). For Codex+Kimi users, `vault init` accepts `--memory-file {claude,agents,both}` flag. The build pipeline does **not** touch vault memory files — that's a vault concern, not a plugin concern. Plugin manifests reference the appropriate convention per host but don't write to user vaults. Adds 1 new `vault init` flag; backward compatible.

### OQ-8 — Marketplace publishing surface **[RESOLVED]**
Decision: Single `marketplace.json` at repo root for CC (unchanged source `"./"`). Codex marketplace ships as `dist/codex/.claude-plugin/marketplace.json` (Codex accepts the `.claude-plugin/` legacy compat path). Kimi has no marketplace — install script is the install path. Documented in Phase 2's Marketplace Strategy section above. EP-3 (Empirical Prerequisites) canaries this before locking.

### OQ-9 — Skill discovery for Kimi **[RESOLVED — pending EP-2]**
Decision: option (a) — install script copies skills to `~/.kimi/skills/carrel-<name>/` with namespace prefix. EP-2 (Empirical Prerequisites) verifies whether file presence alone is sufficient or `config.toml` registration is required. Install script becomes more invasive if registration required; either way the strategy is "user-global + namespace prefix." Uninstall: `kimi plugin remove carrel` + `rm -rf ~/.kimi/skills/carrel-*`. Kimi reviewer flagged probabilistic routing risk for state-transition workflows — mitigated by CI residue grep (Verification #1) ensuring no `/carrel-*` references leak into Kimi skills, plus skill `description` frontmatter explicitly listing natural-language trigger phrasings (Verification #3).

### OQ-10 — Test surface **[RESOLVED]**
Final target: **234 → ~290 tests** (architect-corrected from 280).
- Phase 1: +30 (8 subcommands × ~3 cases = 24, 4 skill enrichments = 4, wrapper validation = 1, plugin-state schema = 1, hook-JS bun infrastructure = 5 → realistic ~35; budget ~30 conservative)
- Phase 2: +40 (3 builders × 5 = 15, 3 translators × 3 = 9, canonicalization = 4, byte-diff = 3, build infrastructure = 5, residue grep + structural = 4)
- `importlib.resources` templates migration: +5–8

Hook-JS testing infrastructure is new for carrel (currently zero JS tests). Built via `bun test` per `~/.claude/rules/toolchain.md`.

## Implementation

### Phase 1: Architecture normalization + skill enrichment (v0.9.0)

**New CLI subcommands** (`src/carrel/cli/`) — naming per architect review (drops duplicate `setup advance`, uses existing group names where data lives):

| New surface | Replaces | Why CLI not skill |
|---|---|---|
| `carrel vault feedback export --redact-list <path>` | `/carrel-feedback` (file write) | Deterministic anonymization via explicit redact list |
| `carrel migrate apply --plugin-root <path>` | `/carrel-migrate` (registry walk + state write) | File I/O; arg replaces env-var coupling |
| `carrel vault mirror --write --from-stdin` | `/carrel-mirror` (file persistence) | Skill produces synthesis; CLI persists idempotently with dated filename |
| `carrel vault reflect-log --append --from-stdin` | `/carrel-reflect` (file persistence) | Skill conducts conversation; CLI appends to dated file atomically |
| `carrel batch convert <folder>` / `carrel batch transcribe <folder>` (both accept `--unattended`) | `/carrel-batch` (folder enumeration) | Two verbs match `convert`/`transcribe` groups; `--unattended` writes `_meta/pending-decisions.md` instead of asking |
| `carrel automate configure` (typed flags only, no prompting) | `/carrel-automate` (file writes) | Calls `policy.trust.is_allowed()` internally as gate; skill carries interview prose |
| `carrel vault share generate` | `/carrel-share` (canonical-copy + redaction) | Deterministic file emission |
| `carrel setup interview --phase N` | `/carrel-setup`'s `setup-interviewer` agent state machine | **NEW from reviewer feedback**: extracts the 9-phase state machine from `agents/setup-interviewer.md` into deterministic CLI. Skill carries interview prose + per-phase questions; CLI handles phase advancement, `setup-state.json` writes, conditional branching. Resolves the agent → skill translation gap flagged by Codex + Kimi reviewers. |

`carrel setup advance` (initially proposed) is **dropped** — `setup-state advance` already exists at `src/carrel/cli/setup_state.py:63-88` and is the validation boundary. `/carrel-setup` continues to call `setup-state advance` unchanged.

**Skill enrichment** (named deliverable, not implicit) — the 4 PARTIAL command absorptions:

| PARTIAL command | Absorbed into skill | What moves into skill body |
|---|---|---|
| `/carrel-setup` (orchestration) | `environment-setup` | Phase-by-phase checkpoint prose; per-phase question framings; calls `carrel setup interview --phase N` for state machine |
| `/carrel-automate` (orchestration) | `automation` | 10-step flow narrative; trust explanation; Desktop App walkthrough; calls `carrel automate configure --enabled ... --trust-level ... --schedule ...` for writes |
| `/carrel-batch` (routing confirmation) | `convert` + `transcribe` (interactive path); `automation` (UNATTENDED-mode contract) | "Ready to start?" prompts, route confirmations, summary prose stay in skills; CLI handles enumeration + execution |
| `/carrel-share` (Quick mode + sensitivity) | `collaborator-onboarding` | Mode-selection prose; sensitivity rule application; calls `carrel vault share generate` for file emission |

**Slash command shrinkage**: All 15 commands collapse to wrappers. **Wrappers take Claude-constructed args, not user-typed `$ARGUMENTS` verbatim** — the calling skill (or Claude reading the skill) constructs the typed flag list so the wrapper can stay a single line without conditionals:

```markdown
---
description: Run carrel batch processing
argument-hint: convert <folder> [--unattended]
---
!carrel batch ${ARGS}
```

The skill (not the wrapper) decides between `convert`/`transcribe` and whether to add `--unattended` based on calling context. Spec convention: `${ARGS}` denotes skill-constructed args; `$ARGUMENTS` (raw user input) is reserved for commands where direct user input is the contract.

**`${CLAUDE_PLUGIN_ROOT}` handling**: References in `commands/carrel-migrate.md`, `hooks/check-version.js`, and `hooks/hooks.json` get replaced with explicit `--plugin-root` arguments. Codex honors `${CLAUDE_PLUGIN_ROOT}` natively (OQ-1) but the CLI-arg form is portable to any caller — CI scripts, MCP servers, plain shell invocations. **Empirical verification required** (see Empirical Prerequisites section): confirm via test plugin install that Codex actually injects the env var as the docs claim.

**Pydantic models**: no schema changes to `AutomationConfig`, `ResearcherProfile`, `SetupState`. New optional field on `.carrel/plugin-state.json`: `host: Literal["claude-code", "codex", "kimi"] | None = None` — populated at install time for forward-compat with Phase 2 host-aware migrations. Backward-compatible (None for existing installs).

**Tests**: ~30 new tests for Phase 1 (architect-corrected from 26):
- 8 subcommand tests × ~3 cases each = 24
- 4 skill-enrichment integration tests = 4
- Wrapper structural validation (`tests/test_command_wrappers.py` — every `commands/*.md` is a valid wrapper template) = 1
- `plugin-state.json` schema migration test = 1

Plus new hook-JS test infrastructure (carrel has none today): ~5 tests via `bun test` covering `check-environment.js`, `session-reflect.js`, `check-version.js`. Counted toward Phase 1 total: **~35 tests**.

**Migration file**: `migrations/0.8.1-to-0.9.0.md` — slash commands keep working; skill enrichment is user-invisible (just better defaults); `plugin-state.json` gets optional `host` field on next session-start.

### Phase 2: Multi-host adapter (v0.10.0)

**Canonical sources** — new `plugin-source/` directory at repo root:

```
plugin-source/
├── manifest.toml          # canonical manifest (single source of truth)
├── skills/<name>/SKILL.md # already portable
├── agents/<name>.md       # canonical (translated per host)
├── commands/<name>.md     # canonical — emitted only for Claude Code build
└── hooks/
    ├── handlers/*.js      # canonical scripts (no ${CLAUDE_PLUGIN_ROOT}; build subs path)
    └── hooks.toml         # canonical hook registration
```

**Templates relocation** (architect catch): `templates/` at repo root today is consumed by `src/carrel/vault/templates.py:86` via `Path(__file__).resolve().parents[3] / "templates"` — fragile path math that breaks under the `plugin-source/` reorganization. Move templates **into the package** at `src/carrel/templates/` and load via `importlib.resources`. This decouples templates from repo layout entirely and removes the `parents[3]` coupling. Templates are core (vault scaffold concern), not plugin (build concern).

**Build pipeline** (`src/carrel/build/` — renamed from `host/` per architect; `host` collided with carrel's existing tool/transport/adapter/teammate/collaborator vocabulary):

```
src/carrel/build/
├── __init__.py
├── targets.py             # Target enum (CLAUDE_CODE | CODEX | KIMI), capability matrix
├── conventions.py         # Per-target paths, env vars, schemas (frozen dataclasses)
├── builders.py            # BUILDERS: dict[Target, Callable[[BuildContext], BuildResult]] — functional dispatch, no ABC
├── claude_code.py         # build_claude_code(ctx) — reproduces current shape byte-for-byte
├── codex.py               # build_codex(ctx)
├── kimi.py                # build_kimi(ctx)
├── canonicalize.py        # frozen timestamps, sorted listings, canonical JSON — for build determinism
└── translators.py         # translate_manifest, translate_agent, translate_hook — free functions
```

**Why dispatch dict, not ABC** (architect catch): carrel's established pattern for per-variant logic is a functional dispatch table — `env/install.py:6` (per-platform installs), `policy/sensitivity.py:11` (per-tool-class allowlists), `vault/templates.py:33` (per-tool command examples), `convert/adapters/` (function-per-tool). 3 build targets with mostly-mechanical file copies do not justify `PluginBuilder` ABC + concrete subclasses. Matches the rest of carrel; halves the LOC.

**New CLI surface**:

```bash
carrel build claude-code            # writes to repo root (preserves marketplace.json source path)
carrel build codex --output dist/codex/
carrel build kimi  --output dist/kimi/
carrel build all                    # CC to root, others to dist/
```

**Marketplace strategy** (architect catch): `marketplace.json:14` currently has `"source": "./"`. Byte-for-byte CC backward-compat requires this path to keep working. Resolution: **CC build writes to repo root (default, no `--output` flag); Codex and Kimi builds write to `dist/<target>/`**. `marketplace.json` at repo root continues serving CC. Codex marketplace entry (Codex accepts `.claude-plugin/marketplace.json` for legacy compat) ships at `dist/codex/.claude-plugin/marketplace.json`. Kimi has no marketplace — install script handles it. No disruption to existing `claude plugin update carrel` flows.

**Per-host transformation table** (updated per Kimi review):

| Component | Claude Code build | Codex build | Kimi build |
|---|---|---|---|
| Manifest | `.claude-plugin/plugin.json` | `plugin.json` | `plugin.json` (tool-registry shape) |
| Skills (12) | copy into `skills/<n>/SKILL.md` | copy into `.agents/skills/<n>/SKILL.md` | copy + emit install script that copies to `~/.kimi/skills/carrel-<n>/`. **Empirical check required** (Empirical Prerequisites): determine whether Kimi auto-discovers from filesystem or requires `~/.kimi/config.toml` `[skills]` registration. If registration required, install script must patch `config.toml` atomically. |
| Agents (2) | copy md+YAML as-is — **except** `setup-interviewer`, whose state machine is in Phase 1's `carrel setup interview --phase N` CLI; the remaining agent prose stays as agent | translate to skill (Codex doesn't support plugin-bundled agents; see OQ-2) | translate to skill |
| Commands (15) | copy as-is (Phase 1 wrappers) | **DROP** — rely on skill discovery + CI residue grep (see CI Verifications) | **DROP** — rely on skill discovery + CI residue grep |
| Hooks | emit `hooks/hooks.json` + handlers | emit equivalent + handlers | emit `kimi-hooks.toml` snippet + handlers + install instructions. **Handler paths must be absolute or PATH-resolvable** — `~/.kimi/config.toml` does not resolve `$HOME` at parse time; install script resolves to absolute paths at install time. |
| Hook output schema (SessionEnd) | structured stderr JSON (`{code, severity, next_commands, next_skills, can_bypass}`) | structured stderr JSON (Codex parses similarly) | **plain stderr only — structured JSON dropped** (Kimi doesn't honor the schema; resolves OQ-6 for Kimi) |
| MCP | empty (carrel ships none) | empty | empty |
| Memory file | none (vault `CLAUDE.md` handled separately) | optional `AGENTS.md` emit | optional `AGENTS.md` emit |
| Install command | `claude plugin install` (existing path) | `codex plugin install ./dist/codex/` OR `codex plugin marketplace add <repo>` | `bash dist/kimi/install.sh` (install script) |

**CI Verifications** (resolves Codex+Kimi reviewers' "skill-discovery fallback hand-wavy" concern):

1. **Residue grep** — for every non-CC build, CI greps the emitted bundle for `/carrel-*` slash command references (in skills, agents, READMEs, hook handlers). Any hit fails CI — Codex/Kimi users can't invoke slash commands.
2. **Wrapper structural validation** — every `commands/*.md` in the CC build matches the wrapper template (frontmatter + single `!carrel ...` line, no conditionals, no embedded prose).
3. **Skill discoverability check** — for each skill, verify its `description` frontmatter contains the natural-language phrasings documented as Codex/Kimi invocation paths.
4. **Build determinism** — `carrel build all` produces identical bytes on two consecutive runs (canonical JSON via `canonicalize.py`, sorted directory listings, frozen template timestamps).
5. **Backward-compat byte-diff** — `carrel build claude-code` reproduces current shipped plugin (sans intentionally-modified files per Phase 1 changeset).

**Tests**: builder unit tests per host, translator unit tests, determinism, byte-diff, residue grep. Target (architect-corrected from 20): **~40 tests**.
- 3 builders × 5 tests each = 15
- 3 translators × 3 tests each (manifest, agent, hook) = 9
- Canonicalization tests = 4
- Backward-compat byte-diff = 3
- New `tests/build/` infrastructure (fixtures, golden files) = 5
- CI residue grep + structural validation = 4

Plus `importlib.resources` templates migration tests = 5–8.

**Migration file**: `migrations/0.9.0-to-0.10.0.md` — Claude Code users see no change (CC build still at repo root); new install instructions for Codex (`codex plugin marketplace add <repo>` or `codex plugin install ./dist/codex/`) and Kimi (`bash dist/kimi/install.sh`).

**#1714 watch**: Before the Kimi native build ships, re-check MoonshotAI/kimi-cli#1714 status. If a PR has opened, hold native Kimi build for 4 weeks — the compat path (kimi-compat target, currently scheduled for v0.11+) is lower long-term maintenance.

## Optional future targets (v0.11+, out of scope for this spec)

These follow naturally from the adapter once Phase 2 lands, but are not committed:

- **Kimi-compat target** (`carrel build kimi-compat`) — if MoonshotAI/kimi-cli#1714 ships, emit a `.claude-plugin/`-shaped bundle for users running the compat-layer Kimi. Builder reuses most of the Claude Code builder's output with path-rewriting adjustments. Still subject to #1714's session-scoped hook limitation.
- **Kimi subagent YAML target** — instead of (or in addition to) translating carrel's 2 agents to skills for Kimi, optionally emit Kimi `subagents:` YAML referencing them from a parent `default` agent override. Lets carrel users invoke `setup-interviewer` via the `Task` tool with full isolated context. Blocked on whether per-subagent model selection (issue #6651) ever lands.
- **Gemini CLI target** — Gemini's plugin/skill surface area is less developed than Codex/Kimi. Re-evaluate after Phase 2 stabilizes.

## Non-goals

- No runtime host detection in the Python core — keep it host-agnostic
- No translation of slash commands to non-CC ergonomic equivalents — Codex/Kimi users invoke via natural language (skill auto-discovery) or directly via the bash tool (`carrel batch run ...`)
- No bundled MCP servers (carrel ships none today; not in scope)
- No support for older Claude Code plugin schemas — current schema only
- No automatic detection of which CLI is running — `carrel build <host>` is explicit
- No Gemini CLI port in this spec (separate work — Gemini's plugin/skill surface area is less developed)

## Risks and mitigations

- **Risk**: Phase 1 breaks existing slash commands for current users.
  **Mitigation**: Wrapper-style slash commands keep identical surface. Migration test (`tests/test_command_wrappers.py`) validates every `commands/*.md` is a valid wrapper template. Each wrapper exercised through Claude Code as a manual smoke test before v0.9.0 release.

- **Risk**: Codex's command gap means carrel UX degrades for Codex users.
  **Mitigation**: Skills are written so a Codex user can say "convert this paper" and the agent auto-loads the convert skill, which knows to call `carrel paper convert <path>`. Skill `description` frontmatter explicitly lists natural-language trigger phrasings (CI Verification #3 enforces). Codex build README documents these.

- **Risk**: Kimi's skill-discovery limit (1 per plugin) is the actual blocker, not commands.
  **Mitigation**: Install script copies skills to `~/.kimi/skills/carrel-<name>/`. Namespace prefix prevents conflicts. EP-2 (Empirical Prerequisites) determines whether `config.toml` registration is also required. Documented uninstall: `kimi plugin remove carrel` + `rm -rf ~/.kimi/skills/carrel-*`.

- **Risk** (Kimi reviewer): Probabilistic skill routing for state-transition workflows (setup, migration) could corrupt `setup-state.json` if the wrong skill fires.
  **Mitigation**: State-machine logic lives in deterministic CLI (`carrel setup interview --phase N`, `carrel migrate apply`), not in skills. A wrong skill firing produces an error or no-op, not a corrupted state file. CI Verification #1 (residue grep) prevents `/carrel-*` references from leaking into Kimi/Codex skills.

- **Risk** (Kimi reviewer): Kimi subagents require pre-registration in parent agent YAML at session start. Plugins cannot inject subagents into a running `LaborMarket`.
  **Mitigation**: Carrel's 2 agents are translated to skills for Kimi (Phase 2 transformation table), not to subagents. Future Kimi subagent YAML target (v0.11+) would require user to specify `--agent <custom-yaml>` at Kimi startup — documented as a manual install step if/when added.

- **Risk** (architect): `${CLAUDE_PLUGIN_ROOT}` removal in Phase 1 breaks something subtle in hook fallback paths.
  **Mitigation**: Each removal is paired with explicit replacement (CLI arg, absolute path resolution, or removal as dead code). EP-1 confirms Codex's claimed support. `hooks/check-version.js` currently has a fallback `path.resolve(__dirname, '..')` that breaks under `plugin-source/` reorganization — fix is to make the hook always require the env var (no fallback), with the build pipeline guaranteeing it's present.

- **Risk** (architect): `commands/*.md` content shrinkage (12-50 lines → 4 lines) breaks anyone who referenced the prose externally (custom skills, forks, automation prompts).
  **Mitigation**: Original prose absorbed into the corresponding skill body. Migration file `0.8.1-to-0.9.0.md` documents the rehome (which prose lives where now). Forks may need an update; documented as known migration.

- **Risk**: Two phases ship as one (impatience).
  **Mitigation**: Phase 1 has its own release tag, its own migration file, its own review cycle. Phase 2 cannot start until Phase 1 is shipped and stable for ≥1 week. Kimi reviewer concurred — collapse risk is asymmetric (a Kimi install script bug in a combined release rolls back Phase 1 improvements too).

- **Risk** (Codex reviewer): Adversarial review claims need verification, not auto-trust.
  **Mitigation**: This spec records the Codex 16-commands false claim (it's 15, verified by `ls commands/`) as a Locked Decision footnote. Future reviewer claims about file counts or specific line numbers should be verified before accepting.

## Round 2 review targets (if dispatched)

If a Round 2 review is run on the amended spec, reviewers should focus on what's *new* since Round 1:

1. **Verify amendments addressed Round 1 concerns**: does the `setup interview --phase N` extraction actually preserve the 9-phase state machine? Does the CI residue grep + skill description audit actually prevent skill-discovery failures? Does `${ARGS}` vs `$ARGUMENTS` convention work in practice?
2. **Stress-test new Locked Decisions**: marketplace strategy (CC at repo root), `setup-interviewer` extraction, templates `importlib.resources` migration, dispatch dict pattern.
3. **Validate Empirical Prerequisites**: are EP-1 through EP-4 actually 10-minute checks, or do they need scoping?
4. **Sanity-check test sizing** at ~290 — is the hook-JS infrastructure assumption sound, or does it need its own mini-spec?

## Review arc + amendment history

**Round 1 (2026-05-17)**: Three parallel reviews of the draft spec.

- `planning/reviews/014-review-codex.md` — Codex adversarial pass. Found: one factually wrong claim (16 commands; verified 15), one contradiction with prior codex-deep-gaps research (`${CLAUDE_PLUGIN_ROOT}` verification; resolved via EP-1), two valid concerns (skill-discovery fallback bounded, `setup-interviewer` state-machine loss). Verdict: proceed with revisions.
- `planning/reviews/014-review-kimi.md` — Kimi second-pair-of-eyes with Kimi-specific stress tests. Found: skill auto-discovery mechanism unconfirmed (resolved via EP-2), subagent pre-registration barrier (Kimi can't inject at runtime — added as risk), hook handler path resolution gap (resolved via EP-4 + Phase 2 install script), Phase 1 missing skill-enrichment as named deliverable. #1714 forecast: 25–30% in 6 months. Verdict: proceed with revisions.
- `planning/reviews/014-review-internal.md` — code-architect feasibility pass against carrel's existing patterns. Found: 8 CLI naming issues (corrected per architect renames), `host/` collides with carrel vocabulary (renamed to `build/`), `PluginBuilder` ABC over-engineers (replaced with dispatch dict), `plugin-source/` move breaks templates + marketplace (resolved via `importlib.resources` + CC-at-repo-root strategy), test sizing underestimated (corrected to ~290). Verdict: proceed with three required amendments (all applied).

**Amendments applied** (post-review):
- Phase 1 renamed "Architecture normalization + skill enrichment"; 4 PARTIAL skill absorptions named as explicit deliverables
- CLI subcommand naming corrected per architect (`vault feedback export`, `migrate apply`, `vault mirror`, `vault reflect-log`, `batch convert/transcribe`, `automate configure`, `vault share generate`, `setup interview --phase N`)
- `setup advance` removed (duplicate of existing `setup-state advance`)
- `setup-interviewer` state machine extracted to `carrel setup interview --phase N` CLI; agent prose stays in `environment-setup` skill
- `host/` → `build/` rename
- `PluginBuilder` ABC → `BUILDERS: dict[Target, Callable]` functional dispatch
- Templates moved to `src/carrel/templates/` via `importlib.resources`
- Marketplace strategy locked: CC at repo root, Codex+Kimi at `dist/<target>/`
- Wrapper convention locked: `${ARGS}` (skill-constructed) for PARTIAL, `$ARGUMENTS` (user-typed) for REDUNDANT
- 4 Empirical Prerequisites added (EP-1 through EP-4)
- 5 CI Verifications added (residue grep, wrapper validation, skill discoverability, build determinism, byte-diff)
- OQ-6 through OQ-10 resolved with explicit decisions
- Test sizing updated to ~290 with hook-JS infrastructure (new for carrel)
- Risks expanded with 4 new entries from reviewers
- Locked Decision added: "reviewer factuality note" recording the 16-commands false claim as evidence that adversarial review claims need verification

**Pending**: human review (Xule) — decisions on whether the amended spec is ready for delegated implementation, or whether a Round 2 review is needed.

## Investigation artifacts

All source material lives under `planning/reviews/`:

- `014-investigation-feasibility.md` — feasibility synthesis (Claude Code / Codex / Kimi comparison + porting verdict)
- `014-investigation-codex-plugins.md` — initial Codex CLI plugin system survey
- `014-investigation-codex-deep-gaps.md` — Codex plugin root env var + agent TOML + subagent surface (resolves OQ-1, OQ-2, OQ-3)
- `014-investigation-kimi-gaps.md` — Kimi #1714 status + subagent surface (resolves OQ-4, OQ-5)
- `014-investigation-carrel-mapping.md` — carrel plugin component inventory + Claude Code plugin spec summary
- `014-investigation-commands-vs-skills.md` — command-to-skill coverage map (47% redundant, 27% partial, 27% unique)
