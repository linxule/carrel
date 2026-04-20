# 008: Internal Code Review

**Date**: 2026-04-20
**Reviewer**: Internal `code-reviewer` agent (confidence-filtered: HIGH+MEDIUM only)
**Scope**: Python and JavaScript code changes since `1788485` (v0.5.0). Spec markdown excluded.

**Verdict**: 6 issues at HIGH+ confidence. Two install-script issues are most user-visible; two hook/CLI issues are robustness; one model-validator gap is invisible today but cascades once spec 006 lands.

---

## HIGH

### 1. `install.ps1` is missing the verification step entirely

**Files**: `install.ps1:21, :148` vs `install.sh:34, :273-287`

`install.sh` has 8 steps, ending with a "Verifying installation" pass. `install.ps1` declares `$Total = 7` and stops after "Carrel plugin" — no `Get-Command` verification block. This matters most for the new bun installation: on Windows, `irm bun.sh/install.ps1 | iex` modifies the User PATH, but the running PowerShell session won't see it without an explicit refresh. There's no cross-platform guarantee that the user is told what's missing.

**Fix**: bump `$Total = 8`. Add `Write-Step 8 $Total "Verifying installation"` mirroring `install.sh:273-287`. Iterate over `git, node, bun, uv, gh, claude` with `Get-Command -ErrorAction SilentlyContinue` and surface a `Missing: ...` warning.

### 2. `check-environment.js` — phase ≥10 in setup-state.json silently bypasses guard

**File**: `hooks/check-environment.js:246`

`SetupState` enforces `Field(ge=0, le=9)`, but the hook reads JSON without re-validating. Condition `setup_state.last_completed_phase < 9` accepts any number — negatives, NaN-after-coercion-fails, `Infinity`, fractional values like `9.5`. The `phaseLabel` lookup at lines 248-254 has hard-coded keys 4..8; phases 0-3 yield generic strings; 9.5 yields "Setup paused at phase 9.5".

**Fix**:
```js
const phase = setupState.last_completed_phase;
if (!Number.isInteger(phase) || phase < 0 || phase > 9) {
  // malformed — skip resume prompt entirely
} else if (phase < 9) {
  // existing resume logic
}
```

### 3. `cli/vault.py:155` — malformed `environment.json` raises raw `pydantic.ValidationError`

**File**: `src/carrel/cli/vault.py:155`

`ResearcherProfile.model_validate_json(...)` raises `pydantic.ValidationError` (or `json.JSONDecodeError` for corrupt files). The `try` block at line 147 only catches `CarrelError`, so a malformed file produces a Python traceback to stderr instead of an actionable hint.

**Fix**:
```python
from pydantic import ValidationError
try:
    profile = ResearcherProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))
except (ValidationError, json.JSONDecodeError) as exc:
    raise CarrelError(
        f"Could not parse {profile_path}",
        hint="The file may be hand-edited or corrupted. Run /carrel-setup to regenerate.",
    ) from exc
```

### 4. `models.py:159` — `SetupState.version` has no validator

**File**: `src/carrel/models.py:158-160`

Spec 006 explicitly relies on `SetupState.version` being comparable to the live plugin version. But the field is just `str` — empty string and "not-a-semver" both pass. Will silently corrupt the planned migration-detection logic.

**Fix**:
```python
version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+].+)?$")
completed_at: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
```

### 5. `scaffold.py:101` — `__version__` import creates module-load coupling and version-source sprawl

**File**: `src/carrel/vault/scaffold.py:6`

Not circular today, but `carrel.vault.scaffold` cannot be imported without fully initializing `carrel/__init__.py`. More importantly: the version captured here is the package's at scaffold time, but a developer who installs locally with `uv pip install -e .` and bumps `__init__.py` mid-development will write the dev-bumped version to setup-state. That's then compared against `plugin.json` (a different source of truth read by `check-version.js`). Four sources of "current version" (pyproject.toml, __init__.py, plugin.json, marketplace.json) hand-synced by CLAUDE.md instruction is a latent drift risk.

**Fix (lower-effort)**: add a test at `tests/test_version_consistency.py` that asserts all four files report the same version. CI catches drift before deploy.

---

## MEDIUM (worth raising in PR)

### 9. `check-environment.js` — briefs directory listing happens twice in same function

**File**: `hooks/check-environment.js:85-89, :185-189`

Both blocks do `fs.readdirSync(briefsDir).filter(...).sort().reverse()`. Same data, two reads. Acceptable on first session start (small dirs), but if the two reads disagree (concurrent writes), the state machine can produce contradictory output (e.g., "morning brief ready" + "no recent briefs" simultaneously).

**Fix**: lift `briefs` array to a `let` at the top of `checkAutomation` and reuse.

---

## Lowered Confidence (not reporting as high-priority)

- #6 `cheatsheet` `--vault` normalization: actually fine via `resolve_vault()`. Inconsistent style only.
- #7 brief regex parsing brittleness: try/catch fallback exists; misreporting is the bigger UX hazard than crashes — but probability low. Worth a polish pass later.
- #8 scaffold writes phase 4 even for standalone `vault init`: copy is correct ("Setup paused after the vault was scaffolded"); docstring meaning aligns with `commands/carrel-setup.md`. One-line code comment would help.
- #10 `curl ... | bash` and `irm ... | iex` unpinned: industry standard for first-run installers; consistent with existing `uv` and `claude` install patterns. Informational only.

---

## Summary

Six HIGH-confidence issues. Recommended order:
1. install.ps1 verification step (most user-visible for Windows)
2. cli/vault.py error wrapping (malformed file UX)
3. SetupState validators (cascades into spec 006)
4. Phase guard in hook
5. Version-consistency test
6. Briefs dedup

All addressed in the triangulated synthesis (`008-deployment-readiness-triangulated.md`) as Tier 1 fixes A2-A7.
