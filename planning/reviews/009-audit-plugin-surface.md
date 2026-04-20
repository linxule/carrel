# Plugin Surface Integrity Audit — v0.5.3

**Date:** 2026-04-20
**Auditor:** Opus (1M context)
**Scope:** Walk every declared command/skill/agent/hook in `.claude-plugin/` and verify it works end-to-end against the current `src/carrel/` CLI surface and Pydantic models.

---

## Verdict

**Mostly aligned, with two runtime bugs and one user-visible regression.**

The plugin manifest is intentionally minimal (auto-discovery from `commands/`, `agents/`, `skills/`, `hooks/`), so there are no orphaned declarations. Counts in README (13 commands, 10 skills, 2 agents, 2 hooks) match what's on disk. References between commands and skills resolve. CLI invocations in skills match the `carrel` typer surface. Pydantic shapes line up with the canonical `interview-protocol.md` template.

But three issues will degrade or break the researcher experience right now:

1. **`hooks/session-reflect.js` is broken on every modern vault** — only reads the legacy nested `env.interview?.researcher` shape and silently `process.exit(0)` for any flat `ResearcherProfile`. The SessionEnd hook fires but produces no output, no reflection prompt, no session stats.
2. **`render_cheat_sheet()` references `/carrel-research`, a command that does not exist.** Every regenerated cheat sheet ships a broken slash command to the researcher.
3. **`hooks/check-environment.js` displays `cloud_consent` as raw boolean** (`Cloud preference: false`) instead of human-readable text, and falls back to legacy string `'prefer_local'` that the model would now reject.

Everything else is cosmetic or documentary drift. Tier-1 fixes are 30 minutes of work.

---

## Tier 1 — Runtime bugs (would break or silently degrade the experience)

### B1. `hooks/session-reflect.js:90` — only handles legacy nested profile shape

```js
const researcher = env.interview?.researcher;
if (!researcher) {
  process.exit(0);
}
```

**Problem:** Canonical `ResearcherProfile` (per `models.py`, `interview-protocol.md`, and `check-environment.js`'s own detection logic) is **flat**: `env.name`, `env.field`, etc. — no `env.interview` wrapper. Every modern vault hits this guard and the hook exits before printing the reflection prompt, vault stats, or capability log entries. The IO-plugin remediation block also never fires.

**Impact:** SessionEnd hook is a no-op for every researcher onboarded after v0.4. The "If you have a moment, run /carrel-reflect" nudge that the README and `/carrel-reflect` skill assume happens, doesn't.

**Fix:** Mirror the `isFlat || isNested` detection from `check-environment.js:271`. Read `env.name || env.interview?.researcher?.name`.

### B2. `src/carrel/vault/templates.py:137` — references nonexistent `/carrel-research`

```python
if profile.wiki_enabled:
    workflows.append("- Knowledge wiki: query via `/carrel-research` and keep field-map pages current.")
```

**Problem:** No `commands/carrel-research.md` exists. Every wiki-enabled researcher gets a broken command pointer in their regenerated `_meta/cheat_sheet.md`.

**Impact:** User-visible. The cheat sheet is positioned as the core handoff artifact (per migration 0.5.2-to-0.5.3); shipping a dead slash command in it is the kind of paper cut that erodes trust on day 1.

**Fix:** Either remove the line, or change to natural-language ("Knowledge wiki: ask Claude about your field map; pages live in `wiki/`"). The wiki has no dedicated slash command — query is invoked via natural language per `knowledge-wiki/SKILL.md`.

### B3. `hooks/check-environment.js:286` — wrong fallback type for `cloud_consent`

```js
const cloudConsent = env.cloud_consent ?? env.interview?.preferences?.cloud_comfort ?? 'prefer_local';
```

**Problem 1:** Default `'prefer_local'` is a string, but `ResearcherProfile.cloud_consent: bool`. If `env.cloud_consent` is genuinely missing, the hook prints `Cloud preference: prefer_local` — a value Pydantic would reject if written back.

**Problem 2:** When `cloud_consent` IS present (the common case), the hook prints `Cloud preference: false` or `Cloud preference: true` — accurate but ugly. The legacy string values were `local_only | prefer_local | comfortable_with_cloud`, much more legible.

**Impact:** Every session-start banner shows a raw bool. Doesn't break anything, but contradicts the "warm welcome" framing.

**Fix:** Render booleans as text:
```js
const cloudLabel = typeof env.cloud_consent === 'boolean'
  ? (env.cloud_consent ? 'cloud OK' : 'prefer local')
  : (env.cloud_consent ?? 'prefer local');
```

---

## Tier 2 — Documentary drift (not runtime-broken, but confusing)

### D1. `commands/carrel-migrate.md:39` — schema mismatch with check-version.js and CLAUDE.md

`carrel-migrate.md` writes `{ "version": "..." }` to `.carrel/plugin-state.json`. CLAUDE.md (line 145) and `check-version.js:32` say the canonical key is `plugin_version`. `check-version.js` reads either via `state.plugin_version || state.version`, so this works in practice — but the documented schema in the migrate command will create files that drift away from the documented canonical name. New migrations and tooling will key off whichever name the author saw first.

**Fix:** Pick one. CLAUDE.md says `plugin_version`. Update `carrel-migrate.md` to match.

### D2. `skills/environment-setup/references/cheatsheet-template.md` is an orphan

This file describes a Handlebars-style template (`{{researcher.name}}`, `{{#if defuddle_available}}`) that nothing renders. The actual cheat sheet renderer is `src/carrel/vault/templates.py:render_cheat_sheet`, which hard-codes a different (less rich) format. The skills layer never reads the .md template.

**Impact:** Anyone reading the references thinks they understand the cheat sheet output. They don't — what `carrel vault cheatsheet` actually writes looks nothing like this template.

**Fix:** Either delete the orphan file or repurpose it as a "what the renderer aspires to" planning doc with a header noting it's not live.

### D3. `skills/environment-setup/references/obsidian-setup.md` is an orphan

No skill or command references this file (verified via grep — the only matches are inside templates/obsidian-config.json and skills/vault-ops/templates/obsidian-config.json, which are different files). Likely a hold-over from the old JS-based scaffolder era — `.obsidian/` is now scaffolded by `vault/scaffold.py` reading `templates/obsidian-config.json`.

**Fix:** Delete or fold into `decision-tree.md` Obsidian section.

### D4. `skills/environment-setup/SKILL.md:222` — claims removed scripts existed in `scripts/`

```
The legacy Node scripts (`check-environment.js`, `create-vault.js`, `generate-cheatsheet.js`)
were removed in v0.5.2 — they were superseded by the Python CLI in v0.3 and had drifted
to write invalid Pydantic data.
```

`check-environment.js` is not a "legacy removed" script — it's the current SessionStart hook at `hooks/check-environment.js`. The other two (`create-vault.js`, `generate-cheatsheet.js`) were genuinely removed. The wording conflates them.

**Fix:** Remove `check-environment.js` from the list, or qualify: "...the legacy `skills/environment-setup/scripts/{check-environment,create-vault,generate-cheatsheet}.js` were removed..."

### D5. `commands/carrel-share.md:81` — undocumented `--quick` flag

Skill mode says: `**Quick** ('--quick'): skip the brief, use defaults...`. There is no slash-command argument plumbing for this — the skill is markdown, not a CLI. Researchers reading "quick mode" will type `/carrel-share --quick` and get nothing different from the default flow. The flag is a documentation artifact from the agent-team spec that didn't ship.

**Fix:** Either implement actual mode detection in the skill (Claude reads the user's message for "quick" / "refresh"), or rename the section to "Quick mode (when researcher says 'just generate one')".

---

## Tier 3 — Minor / verified clean

### Verified working

- **All 13 commands** have valid frontmatter and reference skills/CLI commands that exist.
- **All 10 skills** have valid frontmatter; every `references/<file>.md` mentioned resolves to a real file (checked: handbook-template.md, concept-mapping.md, desktop-scheduling-guide.md, overnight-prompt-guide.md, obsidian-formatting.md, research-databases.md, capability-registry.md, trust-activation.md, wiki-protocol.md, interview-protocol.md, hardware-audit.md, decision-tree.md, gws-setup-guide.md, toolchain-guide.md).
- **No skill references a `scripts/` directory.** The v0.5.2 cleanup of `environment-setup/scripts/` is complete.
- **CLI commands referenced in skills/commands all exist:** `carrel vault init`, `carrel vault cheatsheet`, `carrel vault status`, `carrel vault search`, `carrel vault organize`, `carrel vault new`, `carrel paper convert`, `carrel paper list`, `carrel transcript create`, `carrel transcript list`, `carrel capture url`, `carrel google export`, `carrel env doctor`, `carrel env profile`, `carrel setup-state advance|complete|show|reset`.
- **README counts match implementation:** 13 commands, 10 skills, 2 agents, 2 hooks (excluding `check-version.js` which is a helper module imported by `check-environment.js`, not a separately-registered hook).
- **Versions aligned:** `pyproject.toml`, `src/carrel/__init__.py`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` all report `0.5.3`.
- **`hooks.json` registers both event types** (SessionStart, SessionEnd) with valid command paths using `${CLAUDE_PLUGIN_ROOT}`.
- **`SetupState` model boundaries are honored** by the hook's input validation (`check-environment.js:248-265`).
- **Pydantic shapes match the documented interview output schema** (`interview-protocol.md` matches `models.py:172-186` exactly).
- **Agents (`setup-interviewer`, `research-partner`) reference fields that exist** in `ResearcherProfile`. Setup-interviewer's documented output (line 67) points readers to `interview-protocol.md` which has the canonical schema with `cloud_consent: bool`, sensitivity enum, etc.

### Manifest integrity

- `.claude-plugin/plugin.json` and `marketplace.json` declare only metadata (name, version, description, author, source). They don't list components — Claude Code auto-discovers from `commands/`, `agents/`, `skills/`, `hooks/`. So no "declared but missing" or "missing but declared" issues.
- No `output-styles/`, `mcps/`, or other plugin extras at `.claude-plugin/` root. Clean.

### `templates/` directory consistency

- `templates/` and `skills/vault-ops/templates/` overlap intentionally — the `vault-ops/templates/` copy looks like a dev-time artifact (only the `.md` files, no `.base` files). Not currently broken (`scaffold.py` reads from `templates/` via `template_root()`), but worth noting that the duplicate exists. Most likely safe to delete `skills/vault-ops/templates/` — nothing in the source tree imports from it. Verified via grep: only references are `templates/*.base` strings in skill docs, which point to the canonical top-level `templates/`.

### Minor cosmetic

- `automation` skill (line 188) reads `env.automation` (correct shape per Pydantic model). All other field reads (`env.wiki_enabled`, `env.tools_configured`, `env.preferences`) match the model.
- `check-environment.js:200` reads `automation.last_reviewed` as ISO string and compares via `new Date()`. Matches `AutomationConfig.last_reviewed: str | None`.
- Setup-state pause detection (`check-environment.js:244-265`) matches the `SetupState` model's invariant (phase 9 ⟺ completed_at).

---

## Recommended fix order

1. **B1** (session-reflect dead) — 5 minutes, high impact
2. **B2** (`/carrel-research` doesn't exist) — 2 minutes, user-visible
3. **B3** (cloud_consent display) — 5 minutes, user-visible
4. **D1, D4** (doc-vs-code drift) — 10 minutes, prevents future confusion
5. **D2, D3, D5** (orphan files / undocumented flag) — 15 minutes, hygiene

Total: ~40 minutes to close all findings.

---

## What's NOT in this audit

- **Code quality inside `src/carrel/`** — out of scope per audit brief.
- **Documentation contradictions in README/CLAUDE.md** — separate doc audit.
- **Whether the surfaces are *good* or *useful*** — only whether the wiring resolves at runtime.
- **Cross-platform behavior** — covered by spec 007.
