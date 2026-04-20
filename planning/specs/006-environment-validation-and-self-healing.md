# 006: Environment Validation and Self-Healing

**Status**: Spec (pre-review)
**Version target**: v0.6.0
**Date**: 2026-04-20

---

## Context

Carrel's vault state lives across multiple artifacts: `.carrel/environment.json` (structured), vault `CLAUDE.md` (narrative), `_meta/my-environment.md` (dashboard), `_meta/cheat_sheet.md` (reference card). Multiple writers touch them — Python CLI (`carrel vault init`), Claude (writes CLAUDE.md, edits dashboard mid-session), legacy Node scripts (now removed in v0.5.2), researcher hand-edits.

A 2026-04-20 audit found schema drift in two of three writers: hardcoded version, invalid Sensitivity enum values, undocumented `preferences.*` keys that turned out to be wired only because the Python scaffold reads them via `dict.get()` (silent default rather than explicit contract). The `create-vault.js` legacy writer would have produced an `environment.json` that fails Pydantic parsing — but no validator catches it because the file is read on a need-to-know basis with permissive `dict` access in the hook and explicit `Pydantic` parsing only inside CLI commands that don't always run.

The pattern will recur. As Carrel grows (knowledge wiki added in v0.5, collaborator handbook in v0.5.1, paused-setup state in v0.5.2), more keys land in more writers. Without a validator + auto-healing layer, drift accumulates silently and surfaces as user-reported bugs.

This spec defines three layers — validator, linter, doctor — that detect and (optionally) fix configuration drift.

## Philosophy: Deterministic Where Possible, Agent Where Necessary

Self-healing must NOT be a black box. The discipline:

1. **Validation is deterministic.** Pydantic + custom field validators define the truth. No fuzzy matching.
2. **Auto-fix is conservative.** Only apply fixes where the mapping is unambiguous (`'prefer_local'` → `'medium' + cloud_consent=False` is a known rename; an unknown enum value is NOT auto-fixed).
3. **Agent intervention is surface-only.** When ambiguous drift exists, surface the choice to the researcher; don't decide for them.
4. **All fixes are reversible.** `.bak` files for any auto-fix; logs for any agent-applied changes.
5. **Validation runs cheap.** The session-start hook MUST NOT slow down session boot perceptibly. Validation is opt-in surfacing, not always-block.

### Feature filter (per spec 004 convention)

- Replaces researcher judgment → reject
- Catches silent corruption → accept (this is the core motivation)
- Auto-fixes ambiguous cases → reject (surface to researcher instead)
- Adds friction at session start → reject (must be near-zero overhead)
- Logs every fix with revert instructions → accept

---

## The Three Layers

```
LAYER 1: Validator — deterministic, read-only
────────────────────────────────────────────
  CLI: `carrel env validate`
  - Loads .carrel/environment.json via Pydantic
  - Reports validation errors with field-level paths
  - Reports drift warnings (extra keys, deprecated values, version mismatch)
  - Reports CLAUDE.md / environment.json desync (sensitivity field, etc.)
  - Exit code: 0 valid, 1 invalid, 2 drift-warnings-only
  - Output: human-readable by default; `--format json` for tooling

LAYER 2: Linter — deterministic, auto-fixes safe drift
─────────────────────────────────────────────────────
  CLI: `carrel env fix --safe`
  - Auto-applies known renames and defaults:
      sensitivity 'prefer_local' / 'cautious' → 'medium' (+ cloud_consent=False)
      version-string drift → bump to current plugin version
      missing optional fields → add with safe defaults
      tools_configured boolean re-sync (compare to actual installs)
  - Refuses ambiguous cases (unknown enum values, conflicting fields):
      "Cannot safely fix sensitivity='external' — please run /carrel-fix or edit manually."
  - Writes .carrel/environment.json.bak before any change
  - Reports what was fixed; what was deferred
  - Exit code: 0 nothing-to-do, 0 fixes-applied, 2 ambiguous-cases-need-attention

LAYER 3: Doctor — agent, interactive resolution
───────────────────────────────────────────────
  Command: /carrel-fix
  Skill: env-doctor (new) at `skills/env-doctor/SKILL.md`
  - Runs Layer 1 validator
  - Runs Layer 2 linter (with researcher approval)
  - For ambiguous drift, asks the researcher in plain language:
      "Your sensitivity field is 'external', which isn't a known value.
       From your other settings (cloud_consent=False, IRB-protected data),
       this looks like HIGH. Apply that?"
  - Also catches cross-artifact desync:
      CLAUDE.md says "Sensitivity: HIGH" but JSON says LOW → ask which is right
      tools_configured says zotero=true but `carrel env doctor` shows no install
  - Logs every applied change to _meta/capability-log.md (revertible)
```

---

## Deliverables

All ship in v0.6.0.

### A. New CLI commands

#### A1. `carrel env validate`

```python
@app.command("validate")
def validate_command(
    vault: Path | None = None,
    format: str = "human",  # "human" | "json"
) -> None:
    """Validate .carrel/environment.json against ResearcherProfile schema."""
```

**Behavior:**
1. Find vault root (current dir or `--vault` arg)
2. Load `.carrel/environment.json` raw
3. Try `ResearcherProfile.model_validate(...)` — capture validation errors
4. Load `.carrel/setup-state.json` if present and validate via `SetupState.model_validate(...)` (added in v0.5.2; the canonical schema for resume tracking)
5. Drift checks (separate from Pydantic):
   - Extra top-level keys in `environment.json` (not in `ResearcherProfile.model_fields`)
   - `setup-state.json` `version` field mismatch with current plugin (this is the only file that carries a version — `environment.json` does not)
   - Stale `automation.last_reviewed` against `automation.review_cadence` (per AutomationConfig, computed against today's date)
   - `tools_configured` booleans vs actual install state — delegated to a shared `PlatformToolMatrix` that audit.py also consumes (see Cross-Cutting below)
6. CLAUDE.md desync checks (text-grep based, not full parse):
   - Look for "Sensitivity:" line in CLAUDE.md
   - Compare against `profile.sensitivity`
   - Report mismatch
7. Output formatted report; set exit code

**Cross-cutting note (post-Kimi-review)**: `ResearcherProfile` does not carry a `version` field — only `setup-state.json` (via `SetupState.version`) does. The earlier draft of this spec proposed a "version-on-environment.json" check; that's a confusion between the two state files and would always misfire. Kept here as the single source of truth: validate `SetupState.version` against the live plugin version, leave `environment.json` versionless.

**Output format (human):**

```
Environment validation: /Users/researcher/research/

  ✓ Schema valid (ResearcherProfile)
  ⚠ Drift detected:
    - Field 'preferences.qualitative' is set but undocumented in JSON schema
    - tools_configured.zotero=true but `carrel env doctor` shows zotero not installed
  ⚠ CLAUDE.md desync:
    - environment.json sensitivity=medium, CLAUDE.md says "Sensitivity: HIGH"

Run `carrel env fix --safe` to auto-correct, or `/carrel-fix` for interactive review.
```

#### A2. `carrel env fix --safe`

```python
@app.command("fix")
def fix_command(
    vault: Path | None = None,
    safe: bool = True,
    dry_run: bool = False,
) -> None:
    """Auto-fix safe drift in .carrel/environment.json."""
```

Setup-state drift is handled by `carrel setup-state` (added v0.5.3) — see A1 in 008-review.

**Known-safe fixes:**

| Drift | Fix |
|-------|-----|
| `sensitivity` not in enum but matches known rename (`'prefer_local'`, `'cautious'`) | Map to canonical (`'medium'`) and set `cloud_consent=False` |
| Missing optional field with safe default | Add with default |
| `tools_configured` boolean wrong per `PlatformToolMatrix` (tool not actually installed on this platform) | Set to `false`, log change |

**Refuses to fix:**

- Unknown enum values not matching any known rename
- Required-field missing
- CLAUDE.md/JSON desync (delegated to Layer 3)

**Always:**

- Writes `.carrel/environment.json.bak` (one previous version retained)
- Outputs change log
- Refuses to run if a `.bak` already exists from <60 seconds ago (prevents auto-fix-loop)

#### A3. Custom Pydantic validators on ResearcherProfile

Add `field_validator` decorators that catch common drift:

```python
class ResearcherProfile(BaseModel):
    @field_validator("sensitivity", mode="before")
    @classmethod
    def normalize_sensitivity(cls, v):
        """Map known legacy values to canonical enum."""
        renames = {
            "prefer_local": "medium",
            "cautious": "medium",
            "open": "low",
            "strict": "high",
        }
        if isinstance(v, str) and v.lower() in renames:
            return renames[v.lower()]
        return v
```

**Note**: validators MAP known renames into the enum at parse time so existing files don't fail loading. They do NOT silently accept unknown values — Pydantic still raises on truly invalid input. The `validate` command surfaces what was renamed via diff against raw JSON.

### B. New skill

#### B1. `env-doctor` skill at `skills/env-doctor/SKILL.md`

**Triggers:** `/carrel-fix` command, or researcher mentions "config drift", "settings out of sync", "environment is broken"

**Behavior:**

1. Run `carrel env validate --format json` silently
2. Present drift summary in plain language ("Your settings have a couple of small issues")
3. For each safe-fixable issue, ask: "Apply this fix?" (one-shot batch approval option)
4. For each ambiguous issue, present 2-3 options with reasoning, let researcher choose
5. After all fixes, re-run `validate` to confirm
6. Log applied fixes to `_meta/capability-log.md` with timestamps and revert instructions

**Anti-patterns:**
- Don't fix without asking
- Don't enumerate every drift item — group similar issues
- Don't use technical language ("ValidationError", "field_validator", "enum")
- Don't silently apply fixes during regular sessions — only when explicitly invoked

### C. New command

#### C1. `/carrel-fix` (`commands/carrel-fix.md`)

```yaml
---
description: Detect and resolve configuration drift in your vault
---
```

**Workflow:**
1. Trigger `env-doctor` skill
2. Skill handles the rest

### D. Hook changes

#### D1. Lightweight validation in session-start hook

`hooks/check-environment.js` learns to:

1. After current checks, spawn `carrel env validate --format json` with 2s timeout
2. If exit code is non-zero (validation failed) OR exit code is 2 (drift warnings):
   - Surface ONE LINE: `Config drift detected — run /carrel-fix to review`
3. Never block session boot
4. Cache last validation result in `.carrel/.validation-cache.json` (invalidated when `environment.json` mtime changes); skip validation if cache is valid

**Hard constraint**: this MUST add ≤200ms to session start in the steady state. The cache makes the steady state a stat() call.

### E. Automation integration

#### E1. `vault_health` capability extension

The existing `AutomationConfig.vault_health` capability (introduced in v0.4) already runs vault checks during overnight automation. Extend its scope:

- Run `carrel env validate` weekly
- Apply `carrel env fix --safe` automatically (researcher has already opted into Delegated trust if running this)
- Log changes to morning brief with revert instructions

For Advisory/Consultative trust levels: write findings to `_meta/suggestions/` or `_meta/pending-approvals.md` per existing trust-level rules. Do NOT auto-apply.

---

## Acceptance Criteria

### Must Have

| # | Criterion |
|---|-----------|
| 1 | `carrel env validate` reports schema errors with field-level paths |
| 2 | `carrel env validate` reports drift warnings (extra keys, version mismatch) |
| 3 | `carrel env validate` reports CLAUDE.md/JSON desync for sensitivity field at minimum |
| 4 | `carrel env fix --safe` correctly applies the three known-safe fixes from table |
| 5 | `carrel env fix --safe` refuses to fix unknown enum values; emits clear message |
| 6 | All `fix` operations write a `.bak` and emit a change log |
| 7 | Field validators on ResearcherProfile rename known legacy values without raising |
| 8 | `/carrel-fix` command + env-doctor skill handle the interactive flow |
| 9 | Session-start hook surfaces drift in ≤1 line, ≤200ms steady-state overhead |
| 10 | Automation `vault_health` integrates validate+fix per trust level |

### Should Have

| # | Criterion |
|---|-----------|
| 1 | `carrel env validate --format json` for tooling/automation use |
| 2 | Validator detects tools_configured booleans that don't match audit |
| 3 | env-doctor skill explains drift in researcher-friendly language (no enum names) |
| 4 | Multiple desyncs grouped into single ask, not asked one at a time |
| 5 | capability-log.md entries follow the existing self-improve format |

### Nice to Have

| # | Criterion |
|---|-----------|
| 1 | Validator suggests probable fix for ambiguous cases ("looks like HIGH because...") |
| 2 | Cache invalidation handles plugin upgrades gracefully (auto-invalidate on version bump) |
| 3 | `carrel env validate --history` shows past validation runs from cache |

---

## Implementation Order

1. Custom field validators on `ResearcherProfile` (`src/carrel/models.py`)
2. `carrel env validate` CLI (`src/carrel/cli/env.py` + `src/carrel/env/validate.py`)
3. `carrel env fix --safe` CLI (`src/carrel/cli/env.py` + `src/carrel/env/fix.py`)
4. Tests for validators and fix logic
5. `env-doctor` skill (`skills/env-doctor/SKILL.md`)
6. `/carrel-fix` command (`commands/carrel-fix.md`)
7. Hook extension (`hooks/check-environment.js`)
8. Automation integration (`skills/automation/SKILL.md` updates)
9. Migration `0.5.x-to-0.6.0.md`
10. Version bump to 0.6.0

---

## Cross-Cutting With Spec 007

Spec 006 (validator) and spec 007 (cross-platform) both touch `carrel env doctor`. Kimi review (2026-04-20) flagged a sequencing risk: the validator's `tools_configured` drift check assumes a definition of "is this tool installed" that becomes platform-aware in spec 007. If 006 ships first, the validator will misfire on Windows/Linux when 007 lands.

**Resolution**: introduce a shared `PlatformToolMatrix` in `models.py` that BOTH `audit.py` (reporting) AND the 006 validator (drift detection) consume. The matrix is a `dict[str, dict[Platform, bool]]` populated from per-tool detection logic. Spec 007 owns its construction; spec 006 only reads it.

This means:
- Spec 007 ships first (introduces `Platform` enum, `AuditResult.platform`, and `PlatformToolMatrix`)
- Spec 006 ships second (consumes the matrix; no platform-specific logic of its own)
- The two specs share one source of truth for "tool X is available on platform Y"

## Open Questions

1. **Where do CLAUDE.md/JSON desync checks live?** Pydantic validators can't see CLAUDE.md. Options: (a) separate `validate_consistency()` function in `env/validate.py` that text-greps CLAUDE.md, (b) defer to a new `claude_md_parser` utility. Lean toward (a) — minimal scope.

2. **Should `/carrel-fix` be a top-level command or a flag on `/carrel-status`?** `/carrel-status` already exists for "what's installed and working" checks. Adding `--fix` flag keeps surface area small. But pure `/carrel-fix` is more discoverable. Lean toward separate command, document the link.

3. **Validation cache invalidation strategy?** `mtime` on `environment.json` is necessary but not sufficient — a plugin upgrade can change validators without changing the file. Suggest: cache key includes both `mtime` and plugin version.

4. **What about CLAUDE.md being the source of truth, not environment.json?** Some researchers may hand-edit CLAUDE.md believing it's authoritative. Per existing convention (`environment-setup/SKILL.md`): "environment.json is the structured truth, CLAUDE.md is the narrative truth." When they conflict, JSON wins. The doctor agent should surface this distinction explicitly when resolving desync.

5. **Custom-tracker drift?** Researchers add `.base` files mid-session. Should the validator track which were added by `carrel vault init` vs. by Claude vs. by hand? Defer to v0.6.1 — out of v0.6.0 scope.

6. **`tools_configured` re-sync behavior.** If the validator sees `zotero=true` but Zotero isn't actually installed, should it (a) flip to `false` automatically, (b) warn and require fix, (c) re-trigger configuration? Lean toward (b) for `--safe` mode; (a) is too presumptive.

---

## Out of Scope (deferred)

- Validating MCP server configurations against `.mcp.json` schema
- Validating Obsidian plugin configurations
- Custom-tracker provenance tracking
- Multi-vault validation (e.g., scanning all `.carrel/` directories on the system)
- Migration of inter-vault preferences

---

## Reviews

To be conducted post-spec, per existing pattern:

- Codex (deep adversarial): `planning/reviews/006-review-codex.md`
- Kimi (independent second-pair-of-eyes): `planning/reviews/006-review-kimi.md`
- Code architect (feasibility): `planning/reviews/006-review-architect.md`

Lock decisions after all three reviews complete; then implement.
