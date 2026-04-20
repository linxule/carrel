# 008: Kimi Review (2 rounds)

**Date**: 2026-04-20
**Reviewer**: Kimi (via `kimi:kimi-review` skill / `kimi review --base <ref>`)
**Mode**: read-only second-pair-of-eyes

---

## Round 1 (commit `9493148` baseline)

**Verdict**: concern (7 findings: 2 HIGH + 4 MEDIUM + 1 LOW)

### HIGH

1. **Stale schema documentation** (`skills/environment-setup/references/decision-tree.md:39-52`, `interview-protocol.md` JSON output) contradicts ResearcherProfile Pydantic model. Decision tree said `cloud_consent: "local_only"` (string) but model has `cloud_consent: bool`. Interview protocol output used nested `{interview: {...}}` format but model is flat. **Status: FIXED in `9251bd5`**.

2. **`setup-state.json` has no Pydantic model** — written as raw `json.dumps` in scaffold.py, parsed ad-hoc in JS hook. No SetupState BaseModel; spec 006's validator had nothing to validate against. **Status: FIXED in `9251bd5`** (added `SetupState(BaseModel)` with `Field(ge=0, le=9)`).

### MEDIUM

3. **Spec 006 inconsistency**: proposed `version` field check on environment.json that doesn't exist on ResearcherProfile (only setup-state.json has version). **Status: FIXED in `17ae1d2`** (Cross-cutting note added; version check moved to setup-state.json).

4. **Specs 006 + 007 cross-cutting risk**: validator (006) compares `tools_configured` to env doctor; doctor (007) becomes platform-aware. Without shared availability matrix, validator misfires on Windows/Linux. **Status: FIXED in `17ae1d2`** (added shared `ToolAvailability` matrix as deliverable A3 in spec 007; sequencing locked: 007 first, 006 second).

5. **Spec 007 `liteparse Windows TBD` is not lock-ready** — too soft for a locked spec. **Status: FIXED in `17ae1d2`** (added explicit "Lock Blockers" section + decision matrix).

6. **`install.sh` and `install.ps1` don't install bun** despite `coli` and `defuddle` requiring it. **Status: FIXED in `17ae1d2`** (bun added as Step 3 in both installers).

### LOW

7. **`migrations/registry.json` 0.5.0→0.5.1 summary** said `/team-onboarding` instead of `/carrel-share`. **Status: FIXED in `9251bd5`**.

---

## Round 2 — Re-review (commit `17ae1d2` baseline)

**Verdict**: concern (7 findings: 6 MEDIUM + 1 LOW)

Round 1 fixes verified as effective. New findings introduced by the round 1 fixes:

### MEDIUM

1. **`install.ps1:73` bun fallback URL missing `https://`** — `irm bun.sh/install.ps1 | iex` will fail; PowerShell's Invoke-RestMethod requires absolute URI.
   **Fix**: change to `irm https://bun.sh/install.ps1 | iex`.

2. **`audit.py` omits bun from TOOL_CHECKS** — `carrel env doctor` doesn't probe for bun even though installers now install it and downstream tools depend on it.
   **Fix**: add `"bun": ["bun", "--version"]` to TOOL_CHECKS at `src/carrel/env/audit.py:18-32`.

3. **Spec 007 `ToolAvailability` NAME COLLISION** — `src/carrel/models.py` already defines `ToolAvailability(BaseModel)` with fields `binaries`, `api_keys`, `mcp_servers`. Spec 007 deliverable A3 introduces a new class with the SAME name and shape `dict[str, dict[Platform, bool]]`. Implementation would overwrite the existing model and break `audit.py`, `env.py`, `AuditResult`.
   **Fix**: rename to `PlatformToolMatrix` or `ToolPlatformMatrix` in spec 007.

4. **SKILL.md mode detection gap** at `skills/environment-setup/SKILL.md:22-27` — handles "phase >= 9 + completed_at set" (returning user) and "phase < 9 + completed_at null" (paused), but NOT the case where Claude crashes after updating phase to 9 but before writing `completed_at`. That state falls through.
   **Fix**: add explicit branch for `phase==9 && completed_at==null` → treat as returning user with note to finalize handoff.

5. **`commands/carrel-setup.md:41-48` two-step profile write is fragile** — Phase 4 instructs Claude to (a) run `carrel vault init` (writes generic DEFAULT_PROFILE), then (b) overwrite environment.json with interview profile. If Claude crashes between, blank profile remains. `scaffold_vault()` already accepts a `profile` parameter.
   **Fix**: instruct Claude to pass the interview profile directly into the scaffold call so correct env.json is written atomically.

6. **Spec 006 `fix` command docstring contradicts known-safe fixes table** — docstring scopes to `.carrel/environment.json`, but table includes `setup-state.json` version updates.
   **Fix**: clarify scope OR split setup-state fixes to a separate subcommand (recommended given pending `carrel setup-state` CLI).

### LOW

7. **`hooks/check-environment.js` silently suppresses resume on malformed setup-state.json** — `readJsonFile()` catches all parse errors and returns null. A truncated/corrupted file silently skips the resume prompt with no diagnostic.
   **Fix**: surface a one-line stderr warning when setup-state.json exists but cannot be parsed.

---

## Summary

Both rounds verified the implementation matched the documented intent for each round 1 fix. Round 2 caught:
- Two correctness bugs from the round 1 fixes (bun URL scheme, audit.py omission)
- One spec-level naming collision that would cause implementation failure
- Two doc-vs-implementation gaps (SKILL mode detection, two-step profile write)
- Two consistency issues (spec 006 docstring, hook silent failure)

All round 2 findings are addressed in the triangulated synthesis (`008-deployment-readiness-triangulated.md`) as Tier 1/2 fixes.
