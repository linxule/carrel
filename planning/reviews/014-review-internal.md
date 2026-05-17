# 014 Review — code-architect (Internal Feasibility)

*Review date: 2026-05-17. Agent: code-architect. Architectural feasibility review of spec 014 against carrel's existing patterns. Saved from agent reply (agent followed its system prompt of not writing report files — this is the verbatim assessment).*

## Part 1 — Phase 1 Fit Assessment

### 1a. Typer pattern fit for the 8 new subcommands

**Concession**: The typer pattern at `src/carrel/cli/main.py:5-22` is genuinely uniform — each subcommand is a `typer.Typer` app added to the root via `app.add_typer(<app>, name="<group>")`. Existing groups (`paper`, `transcript`, `vault`, `env`, `capture`, `google`, `setup-state`, `trust`) all follow a single template: file at `src/carrel/cli/<group>.py` with `app = typer.Typer(help=...)` plus `@app.command("verb")` handlers that go through `emit_carrel_error`, `resolve_vault`, and `print_result(result, fmt)`. Adding 8 new subcommands is mechanically trivial.

**Objection**: The spec's proposed naming is internally inconsistent in ways that matter:

| Spec name | Issue | Existing precedent |
|---|---|---|
| `carrel feedback export` | New group `feedback` with a single verb. | Single-verb groups exist (`capture url`, `google export`) but those are noun verbs against a typed input. `feedback` is a noun against nothing. Cleaner as `carrel vault feedback export` since it operates on vault `_meta/`. |
| `carrel migrate run` | New top-level group `migrate`. | Reasonable — symmetric with `setup-state advance`. But "run" feels redundant; `carrel migrate apply --plugin-root <path>` matches the migration verb the registry uses. |
| `carrel vault mirror --write` | Fits `vault/` group correctly. | Consistent with `carrel vault dashboard --force` at `cli/vault.py:248-275`. Good fit. |
| `carrel vault reflect log` | Two-verb chain inside vault. | Awkward — no existing two-verb chains in vault. Cleaner as `carrel vault reflect-log` or `carrel reflect log` (top-level reflect group, mirroring `setup-state`). |
| `carrel batch run --kind {convert,transcribe}` | New top-level `batch`. | Fine as a group. But `--kind` as discriminator forces typer to validate enum membership at the CLI boundary. Spec doesn't say which model owns this enum. |
| `carrel automate configure` | New top-level `automate`. | Reasonable, parallels `setup-state`. Spec is silent on whether `automate configure` is interactive (which breaks the "core library NEVER asks questions" rule in `carrel/CLAUDE.md`) or accepts flags (which makes the orchestration prose belong in the skill, not the CLI). |
| `carrel share generate` | New top-level `share`. | Fits the existing template. |
| `carrel setup advance` | Replaces existing `setup-state advance`? | Spec is unclear. If the spec means rename, that's a breaking CLI change (existing `/carrel-setup` already calls `carrel setup-state advance` at line 24, 81, 98 of `commands/carrel-setup.md`). If it means a parallel group, that's redundant. |

**Fix**: Lock these names in the spec before implementation, with a single-line rationale per choice. Recommended renaming:
- `carrel vault feedback export` (not `carrel feedback export`)
- `carrel migrate apply --plugin-root <path>` (not `carrel migrate run`)
- `carrel vault mirror --write` (as proposed)
- `carrel vault reflect-log` (not `carrel vault reflect log`)
- `carrel batch convert <folder>` / `carrel batch transcribe <folder>` (two verbs, no `--kind`)
- `carrel automate configure` (with flags only — no prompting)
- `carrel vault share generate` (not `carrel share generate`)
- Drop `carrel setup advance` — `setup-state advance` already exists at `src/carrel/cli/setup_state.py:63-88` and is the validation boundary

This collapses to ~6 new groups instead of 8 and reuses existing groups where the data lives.

### 1b. Orchestration logic that does NOT translate cleanly

**`/carrel-batch` (`commands/carrel-batch.md`)**: Steps 2 (Route), 4 (Flag judgment calls), and 6 (Summary) all require **conversational confirmation with the researcher** — "Ready to start?", "want me to retry with mineru?", "want me to open any of the new files?". These cannot move into a deterministic CLI without losing the safety property. The UNATTENDED-mode branch (lines 98-116) writes to `_meta/pending-decisions.md` instead of asking — that's the part that fits a CLI. So `carrel batch run` cleanly owns the headless path, but the interactive path stays in the skill.

**Fix**: Two CLI verbs — `carrel batch convert <folder> --unattended` writes pending-decisions and returns a structured report. The interactive routing-confirmation prose stays in the skill. PARTIAL command is genuinely partial: skill prose + CLI executor.

**`/carrel-automate` (`commands/carrel-automate.md`)**: Step 2 (Interview) is a multi-turn conversation that adapts to researcher answers (lines 25-55). Step 7 calls `carrel trust check automation:write-prompt` as a gate (lines 96-103). Step 9 (Desktop App walkthrough, lines 122-134) is a 6-step instructional sequence Claude must read out loud. Only steps 4-8 (deterministic writes) translate to `carrel automate configure --enabled --trust-level <X> --schedule <Y> ...`. Steps 2, 3, 9, 10 stay in the skill.

**Fix**: `carrel automate configure` accepts a complete typed flag set (matching `AutomationConfig` fields exactly) and writes environment.json + automation-prompt.md + initializes pending-decisions/approvals. The interview, trust explanation, and scheduler walkthrough remain skill content.

**`/carrel-mirror` (`commands/carrel-mirror.md`)**: The synthesis (lines 22-31) is irreducibly judgment. Only the `--write` file-emission at `_meta/mirror/YYYY-MM.md` is deterministic.

**Fix**: `carrel vault mirror --write --content -` (reads from stdin) or `--from-file <path>`. The skill produces the content, CLI persists it idempotently with date-based filename.

**`/carrel-reflect`**: Same pattern. Steps 1, 2, 4 are conversational/judgment. Only Step 2's "append to `_meta/reflections/reflection-YYYY-MM-DD.md`" and Step 3's "update friction_log.md if issues reported" are file I/O.

**Fix**: `carrel vault reflect-log --append --content -`. Skill conducts the conversation; CLI appends to the dated file with template rendering and atomic write.

**`/carrel-feedback`**: The anonymization rules (lines 27-33) ARE deterministic — substring/regex replacement. But naive: replacing "[research topic]" requires the CLI to know what counts as a research topic, which requires AI.

**Fix**: `carrel vault feedback export` accepts `--redact-list <path>` pointing to a yaml/json with explicit substitutions. CLI applies them; skill curates the list per-researcher.

**`/carrel-migrate`**: Strongest CLI candidate. Steps 1, 4, 5, 7 are all deterministic file reads + version comparison + registry walk + plugin-state.json write. Step 6 (suggestions) requires judgment but spec correctly leaves that in skill. **However**: spec underestimates the `${CLAUDE_PLUGIN_ROOT}` removal complexity. Today, `commands/carrel-migrate.md` references it 4 times (lines 11, 21, 24, 25) and `hooks/check-version.js:18` falls back to `path.resolve(__dirname, '..')` if env var absent. The spec says replace with `--plugin-root <path>` but doesn't address: where does the hook (Phase 1 still on Claude Code) get the path from when invoking `carrel migrate apply --plugin-root <X>`? Answer is the hook still has `${CLAUDE_PLUGIN_ROOT}` available — but then the CLI argument is only useful for Codex/Kimi, which is Phase 2.

### 1c. Hidden dependencies in current commands

1. **`/carrel-setup` calls `setup-state advance` 4 times** (`commands/carrel-setup.md:81, 98`). Phase 1's `carrel setup advance` (if a rename, not parallel) breaks this. Recommendation: don't add this subcommand at all.

2. **`/carrel-automate` Step 7 already shells out to `carrel trust check`** (`commands/carrel-automate.md:96-103`). The spec's `carrel automate configure` would need to call the same trust gate internally OR delegate the gate to skill orchestration. Cleanest answer: `carrel automate configure` calls `policy.trust.is_allowed("automation:write-prompt", profile.automation.trust_level)` directly (already exported at `src/carrel/policy/trust.py`), making it an internal gate not a CLI roundtrip.

3. **`/carrel-batch` defers to "the automation skill" for the unattended-mode contract** (`commands/carrel-batch.md:116`). If `/carrel-batch` becomes a thin `!carrel batch run $ARGUMENTS` wrapper, the unattended-mode prose must move to the skill OR the CLI must accept `--unattended` and embed the contract there. **The spec's wrapper template is too thin** — it removes the conditional logic that triggers UNATTENDED mode. Wrappers need to accept a parameter Claude passes explicitly: `!carrel batch convert ${ARGS}` with `${ARGS}` populated by skill to include `--unattended` when context warrants. Spec needs to acknowledge wrappers are NOT verbatim.

## Part 2 — Phase 2 Fit Assessment

### 2a. `src/carrel/host/` placement

**Concession**: Peer placement to `convert/`, `transcribe/`, `vault/`, `env/`, `policy/`, `google/` fits the existing structure.

**Objection**: "host" is ambiguous in carrel's vocabulary. The CLAUDE.md already overloads:
- "Tool" (PDF converter, transcriber)
- "Transport" (plugin, CLI, MCP)
- "Adapter" (per-tool adapters under `convert/adapters/`, `transcribe/adapters/`)
- "Teammate" (Codex/Gemini/Kimi as model partners)
- "Collaborator" (human co-author/RA)

Now "host" enters as "the CLI we're targeting" — but a Claude Code user might reasonably read "host" as "the machine" (the env audit calls it `os`, `platform`).

**Fix**: Name it `src/carrel/build/` instead. This matches the user-facing command `carrel build <target>`, avoids the lexical overload, and frames the module as "build pipeline" (which it is).

```
src/carrel/build/
├── targets.py       # Target enum (CLAUDE_CODE / CODEX / KIMI), capability matrix
├── conventions.py   # Per-target paths, env vars, schemas
├── builders/
│   ├── base.py      # PluginBuilder ABC
│   ├── claude_code.py
│   ├── codex.py
│   └── kimi.py
└── translators/
    ├── manifest.py
    ├── agent.py
    └── hook.py
```

### 2b. Builders + translators vs existing patterns

**Concession**: The proposed `PluginBuilder` ABC + per-target builder + translator modules is structurally similar to `convert/adapters/`.

**Objection**: The spec over-engineers for 3 hosts. Look at `convert/adapters/`: 4 adapters (markdownify, liteparse, defuddle, mineru), and each is a SINGLE FUNCTION, not a class. The `policy/sensitivity.py:select_tool` does matrix-based selection in ~150 lines with one function and one `PolicyDecision` dataclass — no ABC.

For 3 build targets, an ABC adds ceremony without payoff. Carrel's existing precedent is **functional dispatch tables**:
- `src/carrel/env/install.py:6-62` — `INSTALLS: dict[str, dict[Platform, str | None]]`
- `src/carrel/policy/sensitivity.py:11-18` — `LOCAL_TOOLS`, `CLOUD_TOOLS` dicts keyed by class
- `src/carrel/vault/templates.py:33-82` — `TOOL_COMMAND_EXAMPLES: dict[str, list[str]]`

**Fix**: Replace the ABC + 3 builder classes with a single dispatch dict:

```python
BUILDERS: dict[Target, Callable[[BuildContext], BuildResult]] = {
    Target.CLAUDE_CODE: build_claude_code,
    Target.CODEX: build_codex,
    Target.KIMI: build_kimi,
}
```

Each `build_<target>` is a free function calling translators as needed. Translators stay as free functions. Matches `convert/`, `transcribe/`, `policy/` precedent. About half the LOC.

### 2c. `plugin-source/` migration story

This is where Phase 2 has the most user-facing churn the spec underestimates.

**Current state**:
- `.claude-plugin/plugin.json` — manifest
- `.claude-plugin/marketplace.json` — marketplace catalog
- `skills/` — 12 skills at repo root
- `agents/` — 2 agents at repo root
- `commands/` — 15 commands at repo root
- `hooks/hooks.json` + `hooks/*.js` — at repo root
- `templates/` — vault scaffold templates (NOT plugin-discovered; loaded by `vault/templates.py:86` via `Path(__file__).resolve().parents[3] / "templates"`)

**What breaks during the move to `plugin-source/`**:

1. **`marketplace.json` source path** (line 14): `"source": "./"` points to repo root. If `plugin-source/` becomes canonical, must point to `"./plugin-source/"` OR the built artifact. Existing users with `claude plugin marketplace refresh` see the path change.

2. **`templates/` location**: `Path(__file__).resolve().parents[3] / "templates"` resolves to repo root today. If `templates/` moves into `plugin-source/templates/`, the path math changes AND the path becomes plugin-source-relative which doesn't make sense for the Python core. **Templates are CORE concern (vault scaffold), not plugin concern.** Must stay at repo root, or move into the package (`src/carrel/templates/`) like a proper resource.

3. **Hook event resolution**: `process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..')`. Moving hooks to `plugin-source/hooks/` changes `__dirname` resolution. Fix is to never use the fallback (always require the env var).

4. **CI paths**: `bun run` / `uv run` invocations would need path updates.

5. **README + docs**: All `skills/`, `commands/`, `agents/` references in README, docs, and the 12 skill files become stale.

**Fix**: The migration story needs three concrete moves in spec language:

- **Move 1**: `skills/`, `agents/`, `commands/`, `hooks/` → `plugin-source/`. Templates STAY at repo root (they're core, not plugin).
- **Move 2**: `vault/templates.py:template_root()` becomes a function that ships templates inside the package at `src/carrel/templates/` and changes `template_root()` to `importlib.resources`. This decouples templates from repo layout entirely.
- **Move 3**: `marketplace.json` ships TWO entries — one pointing at `./dist/claude-code/` (built output) and one as legacy compat pointing to `./` for old installs. CI publishes built artifacts to a separate branch or to releases.

## Part 3 — Test Surface Assessment

**Concession**: Existing test patterns are clean. Patterns from `tests/test_vault_cli.py`, `tests/test_paper_cli.py`, `tests/test_env_validate.py`, `tests/test_setup_state.py`, `tests/test_cli_trust.py` use `typer.testing.CliRunner`, write fixtures to `tmp_path`, monkeypatch where needed. The 8 new subcommands map cleanly.

**Objection — gaps the spec doesn't mention**:

1. **No mention of testing `${CLAUDE_PLUGIN_ROOT}` removal**. The affected paths include JS hooks (`hooks/check-version.js`) — there is currently no test infrastructure for hook JS. Either inherits a tooling gap or needs new test infrastructure (e.g., bun test for hooks). Suggests +5 tests via a new `tests/hooks/` directory using bun.

2. **No backward-compat tests for the slash command wrappers**. Realistic test: `tests/test_command_wrappers.py` that asserts every `commands/*.md` file is a valid wrapper template (has `description:` frontmatter, body contains exactly one `!carrel <subcmd>` line, that subcommand exists in the typer app).

3. **No determinism test for `carrel build claude-code`**. Requires: frozen timestamps in output files, sorted directory listings, canonical JSON serialization. Spec doesn't specify canonicalization rules. Suggests a `build/canonicalize.py` module + 3-4 tests.

4. **No tests for the trust check integration in `carrel automate configure`**. Needs explicit `tests/test_automate_configure.py` covering: Advisory rejects, Consultative allows propose-only fields, Delegated allows all, write atomicity.

5. **Migration file tests**. `migrations/registry.json` has no schema test. A test should validate `registry.json` is well-formed, every entry's `file` exists, semver ordering is correct, no gaps in the version chain.

**Recommended adjusted target**: 234 → ~290 (Phase 1 +30, Phase 2 +25), not 280. Spec is ~10 tests light.

## Part 4 — Migration Story Assessment

### Migration registry pattern

Every migration is **additive** — no entry has `"breaking": true`. The pattern is "summary + what's new + automatic steps + manual steps + acceptance".

### v0.8.1 → v0.9.0 fit

**Concession**: Phase 1 is genuinely additive at the data-layer level: no `environment.json` schema changes, no `setup-state.json` schema changes, no new required fields on `ResearcherProfile`.

**Objection — what's NOT additive**:

1. **`commands/*.md` content changes**. Today they are 12-50 line orchestration prose. Tomorrow they are 4-line wrappers. Any user who has `commands/carrel-*.md` cached, forked, or referenced in their own automation loses the original content.

2. **`.carrel/plugin-state.json` invalidation check**: After v0.9.0, on first session start, hook surfaces `/carrel-migrate`. The user runs the wrapper, which calls the new CLI, which reads `.claude-plugin/plugin.json` for the current version. **This works for Claude Code users.** For Codex/Kimi users (Phase 2), `.claude-plugin/plugin.json` may not be the path they're running. The `--plugin-root` arg handles it, but the hook needs to pass the right path.

3. **`plugin-state.json` schema check**: v0.9.0 might want a `host` field (which build the user is running — `claude-code` / `codex` / `kimi`) so that subsequent migrations can be host-aware. If you add it later it's a schema migration; cheaper to add it in v0.9.0 as a non-breaking optional field.

### v0.9.0 → v0.10.0 fit

**Objection — underestimated churn**:

1. **Marketplace publishing surface (OQ-8, unresolved)**. Existing users with `claude plugin marketplace refresh` then `claude plugin update carrel` need the marketplace.json to point at a valid path.

2. **Codex marketplace entry**. Single marketplace.json works only if both targets agree on the source. Likely needs two entries — one per target.

3. **Repo size + git history**: `dist/` outputs committed to the repo (so marketplace can pull from raw GitHub) bloats history every release.

4. **First-time Codex/Kimi user install instructions**: The user gets the whole carrel repo for a plugin that's only `./dist/codex/`. The marketplace.json `source` field can point to a subdirectory.

### What Phase 1 invalidates in user state

After v0.9.0:
- `plugin_version` bumps to "0.9.0" — handled by `/carrel-migrate` wrapper
- `last_checked_at` cleared so hook re-runs drift check — handled
- `install_source` unchanged — fine

**No user state is invalidated**. The migration is genuinely zero-action for existing CC users. The risk is in CI / dev workflows that hardcode `commands/` paths.

## Top 3 Architectural Fit Issues

1. **Builder ABC over-engineers a dispatch table.** Carrel's established pattern is functional dispatch via dicts (`env/install.py:6`, `policy/sensitivity.py:11`, `vault/templates.py:33`), not OO inheritance. 3 build targets with mostly-mechanical file copies do not justify an ABC + concrete subclasses. Replace with `BUILDERS: dict[Target, Callable]` + free functions per target.

2. **`plugin-source/` move underestimates templates and marketplace coupling.** `templates/` is core (vault scaffold), not plugin — moving it breaks `vault/templates.py:86`'s `parents[3]` path math. `marketplace.json:14`'s `"source": "./"` cannot survive byte-for-byte CC reproduction without either keeping the source at repo root OR a marketplace path migration that disrupts existing installs. Spec needs explicit resolutions: ship templates inside the package via `importlib.resources`, and commit to a marketplace source strategy.

3. **Phase 1's "shrink commands to wrappers" framing is too simple.** Three of the 8 subcommand candidates have a mix of conversational orchestration (interview, route confirmation, scheduler walkthrough) and deterministic file writes. The spec moves the file writes to CLI but elides where the orchestration lives — it cannot be in the wrapper template, since `!carrel <cmd>` is a shell invocation with no conditionals. The orchestration must live in skills AND the wrappers need to accept Claude-constructed args.

## Top 1 Effort Sizing Issue

**Phase 2 is underestimated.** The spec proposes +20 tests for Phase 2. Realistic estimate is +30-40:
- 3 builders × 5 tests each (manifest emission, skill emission, hook emission, agent translation, byte-diff against fixture) = 15
- 3 translators × 3 tests each (manifest, agent, hook) = 9
- Determinism + canonicalization tests = 4
- Backward-compat byte-diff against current CC plugin = 3
- New `tests/build/` infrastructure (fixtures, golden files) = 5

Plus, the templates path migration (if Spec adopts the `importlib.resources` fix) needs another 5-8 tests covering the new resource resolution. Total: ~40-45 new tests for Phase 2, not 20.

## Verdict

**Phase 1 + Phase 2 can be implemented as described, with three required spec amendments before delegated implementation**:

1. Replace the `PluginBuilder` ABC design with functional dispatch dict (matches every other carrel module).
2. Rename `host/` to `build/` (avoids lexical overload).
3. Explicitly commit on three under-spec'd items: where templates live after move (recommend: `src/carrel/templates/` via `importlib.resources`); how marketplace.json source path migrates (recommend: single dist target with path bump + migration note); how `commands/*.md` wrappers handle the orchestration prose from PARTIAL commands (recommend: absorb into skills; wrappers receive skill-constructed args).

Without these amendments, Phase 1 may still ship cleanly (the typer additions are mechanical) but Phase 2 will hit the templates/marketplace coupling at integration time and rework will be expensive. With the amendments, the spec is sound and the build sequence holds. Test target should be ~290 not 280, with explicit allocation for hook JS coverage (new infrastructure) and build determinism.

## Files Referenced

- `src/carrel/cli/main.py` (typer root, lines 5-22)
- `src/carrel/cli/setup_state.py` (group precedent, lines 63-145)
- `src/carrel/cli/vault.py` (largest group with 9 commands, lines 84-374)
- `src/carrel/cli/paper.py` (router invocation precedent, lines 50-117)
- `src/carrel/cli/trust.py` (gate CLI, lines 37-67)
- `src/carrel/policy/sensitivity.py` (functional dispatch precedent, lines 11-50)
- `src/carrel/env/install.py` (dict-based dispatch precedent, lines 6-62)
- `src/carrel/vault/templates.py` (templates path math, lines 86-92)
- `src/carrel/vault/scaffold.py` (template consumer)
- `src/carrel/convert/adapters/liteparse.py` (adapter-as-function precedent, lines 11-48)
- `commands/carrel-batch.md` (PARTIAL command, lines 98-116 for unattended mode)
- `commands/carrel-automate.md` (PARTIAL command, lines 96-103 for trust gate)
- `commands/carrel-setup.md` (uses setup-state advance, lines 24, 81, 98)
- `commands/carrel-migrate.md` (CLAUDE_PLUGIN_ROOT refs, lines 11, 21, 24, 25)
- `hooks/check-version.js` (CLAUDE_PLUGIN_ROOT fallback, line 18)
- `.claude-plugin/marketplace.json` (source path, line 14)
- `migrations/registry.json` (additive-only pattern)
- `tests/test_vault_cli.py`, `tests/test_env_validate.py`, `tests/test_cli_trust.py`, `tests/test_setup_state.py` (CLI test patterns)
