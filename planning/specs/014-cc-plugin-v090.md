# Spec 014: CC Plugin v0.9.0 — Architecture Normalization + Feature Adds

**Status**: Locked, CC-only scope (2026-05-17)
**Origin**: User request — make carrel work as a plugin for Codex CLI and Kimi CLI in addition to Claude Code. Cross-CLI investigation (Round 1) re-scoped to **Claude Code only** for v0.9.0. The cross-CLI port is parked as future work; the architecture-normalization half of that work stands alone as a CC-quality release.
**Reviews**: Codex (adversarial) + Kimi (second-pair-of-eyes) + code-architect (feasibility) — Round 1 complete; amendments applied. CC-only re-scope (2026-05-17): two follow-up reviews (`014-cc-only-trim.md` triages original Phase 1 by CC-vs-cross-CLI motivation; `014-cc-feature-gap.md` audits CC features carrel doesn't use). Both informed this rewrite.

---

## Problem

Carrel ships as a Claude Code plugin (15 commands + 12 skills + 2 agents + 2 hooks + 0 MCP). Two architectural issues drag on the CC experience:

1. **Three-layer violation in slash commands.** Carrel's stated architecture is *skills = judgment, CLI = ops, transports = thin*. A command-to-skill mapping pass found 47% REDUNDANT, 27% PARTIAL, 27% UNIQUE. The 4 UNIQUE commands (`/feedback`, `/migrate`, `/mirror`, `/reflect`) all do deterministic file I/O — work that belongs in the Python CLI, not in markdown command files. The PARTIAL commands mix orchestration prose (skill-territory) with shell invocation (CLI-territory).
2. **CC plugin surface underused.** Carrel uses 2 of ~29 hook events (SessionStart, SessionEnd), zero output styles, has marketplace metadata missing keywords/category/license/repository. Three concrete adds would meaningfully improve the per-turn UX without expanding scope.

The cross-CLI motivation that originally drove this spec (Codex CLI + Kimi CLI port) found that **most of the architecture normalization is valuable inside CC alone** — Codex/Kimi just made the architecture debt visible. The trim review (`planning/reviews/014-cc-only-trim.md`) separates "CC-quality wins" from "cross-CLI-only wins" and drops the latter.

## Scope (CC-only)

**A. Architecture normalization** — Extract deterministic ops from slash commands into `carrel <subcommand>`. Shrink the corresponding ~7 slash commands to thin `!carrel <subcmd> ${ARGS}` wrappers. Absorb the freed orchestration prose into the matching skills. No state-machine extraction for `setup-interviewer` (the agent stays as an agent — that extraction was cross-CLI motivated). No `${CLAUDE_PLUGIN_ROOT}` removal (CC uses it correctly; only Kimi needed it gone).

**B. CC feature adds** — Three high-leverage CC plugin features carrel doesn't use: marketplace metadata expansion, `UserPromptSubmit` hook (per-turn context injection), `PreToolUse` Bash matcher (sensitivity ask-gate before cloud-routing subprocesses).

**Out of scope for v0.9.0** — Codex CLI port, Kimi CLI port, `src/carrel/build/` multi-host adapter, `setup-interviewer` → CLI extraction, `${CLAUDE_PLUGIN_ROOT}` removal, optional `host` field on `plugin-state.json`, hook-JS test infrastructure, EP-1 through EP-4 (all probe Codex/Kimi). See **Future Work** section below for the parked cross-CLI plan.

## Locked Decisions

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | CC-only or full cross-CLI in v0.9.0? | **CC-only** | Ship the architecture-quality wins now; let multi-CLI port wait for actual user demand. Half the effort, none of the multi-host risk. |
| 2 | Wrapper args convention | **`${ARGS}` (skill-constructed) for PARTIAL command wrappers; `$ARGUMENTS` (raw) reserved for commands whose contract is direct user input** | Shell wrappers cannot have conditionals; orchestration moves to skills, which construct the typed-flag arg list. Convention documented in `commands/CONVENTIONS.md`. |
| 3 | `setup-interviewer` state-machine extraction | **Drop** (was cross-CLI motivated) | The agent works fine in CC. Extraction was needed only because Codex/Kimi can't bundle agents. Revisit if/when port resumes. |
| 4 | `${CLAUDE_PLUGIN_ROOT}` migration | **Drop** (was Kimi-motivated) | CC injects the env var correctly; existing usage in `hooks/check-version.js` + `commands/carrel-migrate.md` is idiomatic. New `migrate apply --plugin-root <path>` CLI defaults to `${CLAUDE_PLUGIN_ROOT}` so no caller needs to change. |
| 5 | Optional `host` field on `.carrel/plugin-state.json` | **Drop** (was Phase 2 forward-compat) | YAGNI for a CC-only release. Add later if cross-CLI work resumes. |
| 6 | Marketplace metadata fields | **Add `keywords`, `category`, `tags`, `license`, `repository` to `.claude-plugin/marketplace.json`** | Discoverability fix; zero behavior risk; 10-minute change. |
| 7 | `UserPromptSubmit` hook | **Adopt** — `~30-line Node script + 2-line `hooks.json` addition; reads `.carrel/environment.json` + `_meta/briefs/` and emits `additionalContext`** | Per-turn vault context (sensitivity, trust level, active brief) survives mid-session drift. Same shape as existing `check-environment.js`. |
| 8 | `PreToolUse` Bash matcher | **Adopt** — `~50-line script gated to `carrel ... --tool <cloud>` invocations; reuses `carrel trust check` + `--explain`** | Visual confirmation step before cloud subprocesses; reinforces the trust ladder without duplicating policy enforcement (which stays at the CLI boundary). |
| 9 | Wrapper shrinkage scope | **Only the ~7 commands whose CLI ships in v0.9.0** | The other 8 commands (capture, cheatsheet, convert, fix, setup, status, teammates, transcribe) already wrap existing CLI cleanly or are pure skill prompts. Shrink them in a future pass if they accumulate orchestration prose. |
| 10 | Migration file | **Required** — `migrations/0.8.1-to-0.9.0.md` documenting: skill enrichment is user-invisible; commands keep working; new hook adds; marketplace metadata visible on next refresh | Standard carrel release practice. |

## Implementation

### A. Architecture normalization

#### A.1 — Seven new CLI subcommands

Naming per architect review (drops duplicate `setup advance`; uses existing group names where data lives).

| New surface | Replaces | What CLI owns | What skill owns |
|---|---|---|---|
| `carrel vault feedback export --redact-list <path>` | `/carrel-feedback` (file write) | Deterministic anonymization via explicit redact list | Conversation guidance |
| `carrel migrate apply --plugin-root <path>` (defaults to `${CLAUDE_PLUGIN_ROOT}`) | `/carrel-migrate` (registry walk + state write) | Migration registry walk; `plugin-state.json` writes | Per-migration manual-step narration |
| `carrel vault mirror --write --from-stdin` | `/carrel-mirror` (file persistence) | Idempotent dated-filename emission | Mirror synthesis prose |
| `carrel vault reflect-log --append --from-stdin` | `/carrel-reflect` (file persistence) | Atomic append to dated reflect-log | Reflection prompts + framing |
| `carrel vault share generate` (typed flags: `--mode`, `--for`, `--sensitivity`) | `/carrel-share` (canonical copy + redaction) | Handbook synthesis emission; sensitivity-rule application | Quick-mode interview prose |
| `carrel batch convert <folder>` / `carrel batch transcribe <folder>` (both accept `--unattended`) | `/carrel-batch` (folder enumeration) | Folder walk + per-file CLI dispatch; `--unattended` writes `_meta/pending-decisions.md` instead of asking | Pre-batch confirmation prose; UNATTENDED-mode contract narration |
| `carrel automate configure` (typed flags only: `--enabled`, `--trust-level`, `--schedule`, `--review-cadence`) | `/carrel-automate` (file writes) | Calls `policy.trust.is_allowed()` internally as gate; writes `AutomationConfig` to `environment.json` | 10-step interview flow; trust-level explainer; Desktop App walkthrough |

All seven subcommands follow carrel's existing patterns:
- Pydantic models for typed arguments (no positional surprises)
- `safe_path.safe_vault_join` for vault writes
- `CarrelError` with actionable hints on failure
- `--explain` flag where routing/policy decisions happen (`vault share generate`, `batch convert/transcribe`)
- Source-hash idempotency where outputs are content-derived (`vault mirror`, `vault reflect-log`)

#### A.2 — Three skill enrichments

The orchestration prose freed from shrunk commands moves into the matching skill bodies. Skills become the orchestration owner; CLI does the file I/O.

| Skill | Absorbs | Calling pattern |
|---|---|---|
| `automation` | `/carrel-automate`'s 10-step flow + Desktop App walkthrough + trust-level explainer | Skill conducts interview, then calls `carrel automate configure --enabled ... --trust-level ... --schedule ...` once |
| `convert` + `transcribe` | `/carrel-batch`'s pre-batch confirmation + per-file routing summary (interactive path); `automation` skill absorbs the UNATTENDED-mode contract for scheduled-batch use | Skill confirms with user, then calls `carrel batch convert <folder>` or `carrel batch transcribe <folder>` |
| `collaborator-onboarding` | `/carrel-share`'s mode-selection prose + sensitivity-rule application narration | Skill resolves mode + sensitivity with user, then calls `carrel vault share generate --mode ... --for ... --sensitivity ...` |

No new skill files. Edits land in existing `skills/<name>/SKILL.md`.

#### A.3 — Wrapper shrinkage for 7 commands

The seven commands corresponding to the new CLI subcommands collapse to thin wrappers using `${ARGS}` (skill-constructed) — not `$ARGUMENTS` (raw user input). The calling skill constructs the typed-flag arg list so the wrapper stays single-line, no conditionals:

```markdown
---
description: Run carrel batch processing
argument-hint: convert <folder> [--unattended]
---
!carrel batch ${ARGS}
```

The 8 commands not in scope this release keep their current shape:
- `carrel-setup` (calls `setup-state` CLI; agent orchestrates)
- `carrel-capture` (thin wrap of `carrel capture`)
- `carrel-cheatsheet` (thin wrap of `carrel vault cheatsheet`)
- `carrel-convert` (thin wrap of `carrel paper convert`)
- `carrel-fix` (thin wrap of `carrel env fix`)
- `carrel-status` (thin wrap of `carrel env doctor`)
- `carrel-teammates` (skill-driven via `model-teammates`)
- `carrel-transcribe` (thin wrap of `carrel transcript create`)

These accumulate orchestration prose only if their CLI grows complex enough to warrant skill-side construction — at which point they get the same treatment in a future pass.

`commands/CONVENTIONS.md` documents the `${ARGS}` vs `$ARGUMENTS` convention.

### B. CC feature adds

#### B.1 — Marketplace metadata expansion

`.claude-plugin/marketplace.json` gains:
- `keywords`: `["research", "obsidian", "pdf", "transcription", "academic", "vault", "zotero", "knowledge-management"]`
- `category`: `"productivity"` (or `"research"` if the marketplace taxonomy supports it)
- `tags`: same shape as `keywords`, retained for compat with marketplace UI variants
- `license`: SPDX identifier matching the repository license
- `repository`: `https://github.com/linxule/carrel`

Zero behavior change. 10-minute edit. Shipped first because it's prerequisite-free.

#### B.2 — `UserPromptSubmit` hook

New `hooks/inject-context.js` (~30 lines):
- Reads `.carrel/environment.json` (sensitivity, cloud_consent, trust_level)
- Reads `_meta/briefs/` for any active automation brief (most recent file mtime)
- Emits hook output with `additionalContext` containing a 3-5 line vault-state summary
- Times out at 2s (conservative; hook is per-turn)

`hooks/hooks.json` gains:
```json
"UserPromptSubmit": [
  {
    "matcher": "*",
    "hooks": [
      { "type": "command", "command": "node ${CLAUDE_PLUGIN_ROOT}/hooks/inject-context.js", "timeout": 2 }
    ]
  }
]
```

#### B.3 — `PreToolUse` Bash matcher

New `hooks/sensitivity-gate.js` (~50 lines):
- Triggered only when `tool_name == "Bash"` AND `tool_input.command` matches `carrel\s+(paper|transcript|capture|google)\s+\S+\s+.*--tool\s+(mineru|groq|gemini)`
- Shells out to `carrel <subcmd> ... --explain` to get the routing decision
- If sensitivity policy says deny: returns `permissionDecision: "deny"` with the actionable hint
- If policy says allow but sensitivity is MEDIUM+: returns `permissionDecision: "ask"` with a one-line warning
- Otherwise passes through (no decision, default behavior)
- Times out at 3s

`hooks/hooks.json` gains:
```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      { "type": "command", "command": "node ${CLAUDE_PLUGIN_ROOT}/hooks/sensitivity-gate.js", "timeout": 3 }
    ]
  }
]
```

This does **not** replace `policy.sensitivity:select_tool` — that stays the authoritative enforcement at the CLI boundary. The hook is a UX layer giving researchers a visual checkpoint before a cloud subprocess fires.

### Tests

Target: **228 → ~250** (architect-corrected; no hook-JS test infra in scope).

| Surface | Tests |
|---|---|
| 7 CLI subcommands × ~3 cases each (happy + error + edge) | 21 |
| Wrapper structural validation (`tests/test_command_wrappers.py` — every command file with a `!carrel ...` line is a valid wrapper) | 1 |
| `automate configure` trust-gate invariants | 2 |
| `vault share generate` sensitivity rule application | 2 |
| **Total new** | **~26** |

Hook-JS test infrastructure (would have required `bun test` setup) is deferred until either Kimi compat resumes or a hook bug forces it.

### Migration

`migrations/0.8.1-to-0.9.0.md` documents:
- Slash commands keep working — wrappers reshape, behavior preserved
- Skill enrichment is user-invisible (better defaults, same surface)
- New CLI subcommands available; old shell-call patterns still work where they existed
- Marketplace metadata visible on next `claude plugin marketplace refresh`
- New `UserPromptSubmit` hook adds per-turn context — no opt-out needed (it's additive)
- New `PreToolUse` hook adds confirmation step before cloud subprocesses — can be bypassed by running CLI directly

`migrations/registry.json` updated.

### Version bump

- `.claude-plugin/plugin.json` → `0.9.0`
- `.claude-plugin/marketplace.json` → `0.9.0`
- `pyproject.toml` → `0.9.0`
- `src/carrel/__init__.py` → `0.9.0`

## Effort estimate

| Bucket | Size |
|---|---|
| A.1 — 7 CLI subcommands (5 small + 2 medium) | M |
| A.2 — 3 skill enrichments | M |
| A.3 — 7 wrapper shrinks + conventions doc | S |
| B.1 — marketplace metadata | XS |
| B.2 — UserPromptSubmit hook | S |
| B.3 — PreToolUse sensitivity gate | S |
| Tests (~26) | M |
| Migration doc + version bump | S |
| **Total** | **~1 large unit** (down from original Phase 1 ~2 units) |

## Risks and mitigations

- **Risk**: Wrapper shrinkage breaks an existing user invocation pattern.
  **Mitigation**: `tests/test_command_wrappers.py` validates every wrapper. Each of the 7 reshaped wrappers exercised through CC as a manual smoke test before v0.9.0 release. Migration file documents the rehome (which prose lives where now).

- **Risk**: Skill enrichment makes skill bodies too long; auto-loading degrades.
  **Mitigation**: Three enriched skills are `automation`, `convert`/`transcribe`, `collaborator-onboarding` — all currently <300 lines per `<500 lines` target. Absorbed prose is ~50-100 lines each. Stays under target.

- **Risk**: `UserPromptSubmit` hook fires every turn — performance drag.
  **Mitigation**: 2s timeout. Hook reads two small files (`environment.json` + most-recent brief). Shipped Node, no runtime install. Architect to validate latency in implementer testing; revert if it adds >100ms per turn.

- **Risk**: `PreToolUse` sensitivity gate fires false positives on non-cloud `carrel` invocations.
  **Mitigation**: Regex is gated to `--tool (mineru|groq|gemini)` substring; falls through silently for local-tool invocations. Researcher can append `# bypass-gate` comment if they need to suppress for a specific command (handled inside the hook script, ~3 lines).

- **Risk**: Marketplace metadata triggers re-indexing in CC clients that misbehaves.
  **Mitigation**: Fields are additive, not behavior-changing. Worst case: clients ignore unknown fields (per the CC plugin spec). No-rollback risk.

- **Risk** (carried from Round 1, still valid): `commands/*.md` content shrinkage (12-50 lines → 4 lines) breaks anyone who referenced the prose externally (custom skills, forks, automation prompts).
  **Mitigation**: Original prose absorbed into the corresponding skill body. Migration file documents the rehome.

## Future work — Cross-CLI port (parked)

The original Phase 2 of this spec proposed a multi-host adapter (`src/carrel/build/`) emitting Codex CLI and Kimi CLI plugin bundles from a single canonical source. **Parked indefinitely** pending demand signal (no current Codex/Kimi carrel user). The investigation artifacts (`planning/reviews/014-investigation-*.md`) and the Round 1 reviews (`014-review-{codex,kimi,internal}.md`) remain authoritative if/when this work resumes.

What stays valid when the port resumes:
- The Open Questions section's resolutions (OQ-1 through OQ-10 — see git history of this file pre-2026-05-17 amendment)
- The architect's `BUILDERS: dict[Target, Callable]` dispatch pattern recommendation
- The `src/carrel/templates/` + `importlib.resources` recommendation (independently a win; can be done earlier opportunistically)
- The CC-at-repo-root marketplace strategy
- The empirical prerequisites EP-1 through EP-4 (still ~10-minute checks)
- The CI verifications (residue grep, skill discoverability, build determinism, byte-diff)
- The risk register entries about probabilistic skill routing, Kimi subagent pre-registration, hook handler path resolution

What needs revisiting:
- Kimi #1714 status (re-check before any Kimi work)
- Whether the `setup-interviewer` state-machine extraction is the right resolution to the agent→skill translation problem, or whether Codex/Kimi will have grown plugin-bundled agents by then
- Whether `bin/carrel` shim (deferred from this spec) becomes valuable for the port

The full pre-amendment spec is available in the git history at commit `06df535` (or via the `spec/014-cross-cli-port` branch tip `10af267`).

## Review history

**Round 1 (2026-05-17)**: Three parallel reviews of cross-CLI draft. Codex (`014-review-codex.md`), Kimi (`014-review-kimi.md`), code-architect (`014-review-internal.md`). All amendments applied to the cross-CLI version of the spec.

**CC-only re-scope review (2026-05-17)**:
- `014-cc-only-trim.md` — triaged 24 original Phase 1 deliverables by CC-quality vs cross-CLI motivation. Verdict: 10 KEEP, 5 MODIFY, 9 DROP. Effort cut from ~2 large units to ~1.
- `014-cc-feature-gap.md` — audited CC plugin features carrel doesn't use. Top 3 surfaced: marketplace metadata, `UserPromptSubmit`, `PreToolUse` Bash matcher. All adopted in this rewrite.

**Pending**: implementation. Spec is implementation-ready as written.

## Investigation artifacts

Under `planning/reviews/`:

- `014-investigation-feasibility.md` — feasibility synthesis (CC / Codex / Kimi comparison + porting verdict)
- `014-investigation-codex-plugins.md` — initial Codex CLI plugin system survey
- `014-investigation-codex-deep-gaps.md` — Codex plugin root env var + agent TOML + subagent surface
- `014-investigation-kimi-gaps.md` — Kimi #1714 status + subagent surface
- `014-investigation-carrel-mapping.md` — carrel plugin component inventory
- `014-investigation-commands-vs-skills.md` — command-to-skill coverage map (47% redundant, 27% partial, 27% unique)
- `014-cc-only-trim.md` — CC-quality triage of original Phase 1 deliverables
- `014-cc-feature-gap.md` — CC plugin feature gap audit
