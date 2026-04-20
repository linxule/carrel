# 008: Deployment Readiness — Triangulated Review Synthesis

**Date**: 2026-04-20
**Range reviewed**: commit `1788485` (v0.5.0) through `17ae1d2` (Kimi follow-up)
**Reviewers**:
- Kimi (read-only second-pair-of-eyes, 2 rounds via `kimi:kimi-review` skill)
- Codex (fresh adversarial diagnostic via `codex:codex-rescue` agent)
- Internal `code-reviewer` agent (Python/JS code quality, confidence-filtered)

**Verdict**: Concern. Two BLOCKERS for Imperial deployment, one architectural insight that ties multiple bugs together, and a tight fix list that Codex can execute autonomously.

---

## Triangulation Map

Where reviewers converge is where the highest-confidence fixes live.

| Issue | Codex | Kimi | Code-Reviewer | Severity |
|-------|:-----:|:----:|:-------------:|:--------:|
| State transitions are procedurally coupled (Claude edits JSON; no deterministic boundary) | ✓ #1 (HIGH rec) | ✓ (re-review #5) | ✓ #5 (4 hand-synced version sources) | **HIGH** |
| Hook input validation insufficient against malformed `setup-state.json` | ✓ HIGH | ✓ #7 | ✓ #2 | **HIGH** |
| `SetupState` model is too permissive (phases 0-3 valid; version unvalidated) | ✓ MEDIUM | ✓ (re-review #4) | ✓ #4 | **HIGH** |

Where reviewers diverge is where unique perspectives matter.

| Issue | Source | Severity |
|-------|--------|---------|
| Windows still Mac-coded at moment of use (`/carrel-setup` hands off `brew`) | Codex unique | **BLOCKER** |
| README oversells, contradicts CLAUDE.md gotcha | Codex unique | **BLOCKER** |
| `install.ps1` missing verification step | Code-reviewer unique | HIGH |
| `install.ps1` bun fallback missing `https://` (`irm bun.sh/install.ps1`) | Kimi unique | MEDIUM |
| `audit.py` omits `bun` from `TOOL_CHECKS` | Kimi unique | MEDIUM |
| Spec 007 `ToolAvailability` NAME COLLISION with existing model in `src/carrel/models.py` | Kimi unique | MEDIUM |
| `cli/vault.py:155` raises raw `ValidationError`, not `CarrelError` | Code-reviewer unique | HIGH |
| SKILL.md mode detection gap: phase==9 + `completed_at==null` falls through | Kimi unique | MEDIUM |
| Spec 006 `fix` docstring contradicts known-safe fixes table | Kimi unique | MEDIUM |
| `migrations/0.5.1-to-0.5.2.md` manual fallback uses Unix `date -u` | Codex unique | MEDIUM |
| Cheatsheet renderer too thin for documented role | Codex unique | MEDIUM |
| README command list out of date (says 9, ships 13) | Codex unique | MEDIUM |
| `check-environment.js` reads briefs dir twice in same function | Code-reviewer unique | LOW |

---

## Tiered Fix Plan (for Codex delegation)

Codex should execute Tier 0 → Tier 1 → Tier 2 → Tier 3 in order. Each tier should be a single commit unless noted.

### TIER 0 — Deployment Blockers (must fix before Imperial release)

#### B1. Reconcile Windows messaging across docs (DOC-only)

**Problem**: `README.md:49` says installer "handles everything else" but `CLAUDE.md:140` warns Windows users "hit walls during /carrel-setup". Imperial faculty cannot deploy with contradictory docs.

**Fix**: Choose one truth and propagate.

Recommended truth (until spec 007 implementation lands):
- README: change `49` to "macOS, Linux, or Windows — the install script handles everything else for the install itself; some downstream tools (PDF conversion via liteparse, Google Workspace via gws) are currently macOS-only and Windows users will hit those gaps during /carrel-setup. See spec 007."
- README: add a "Platform Support" section near the top with a clear matrix: tool × platform × status.
- CLAUDE.md gotcha can stay as-is.

**Files**:
- `README.md` (lines 49-51 + insert new "Platform Support" section)

#### B2. Fix the Mac-coded `/carrel-setup` flow (CODE)

**Problem**: `commands/carrel-setup.md:66` (Phase 6 human steps) tells the researcher "Install Obsidian (offer `brew install --cask obsidian` or download from obsidian.md)". Decision tree (`skills/environment-setup/references/decision-tree.md`) recommends `brew install` unconditionally throughout. `src/carrel/env/install.py` constants are entirely brew-prefixed.

**Fix (minimum viable for deployment, NOT the full spec 007 work)**:
1. `commands/carrel-setup.md:66`: replace the single-platform Obsidian line with a 3-line OS-branched recommendation (brew on macOS, winget on Windows, download AppImage on Linux). Also add a brief "If you're on Windows, some tools below may not be available" note before Phase 5.
2. `src/carrel/env/install.py`: add a stub helper `install_command_for(tool: str, platform: str) -> str | None` that returns the platform-correct command for `obsidian`, `ffmpeg`, `bun` at minimum. Other tools can keep returning the brew form for now (with a TODO comment) — full coverage is spec 007's job.
3. `skills/environment-setup/references/decision-tree.md`: at the top, add a one-paragraph "Platform note" that says: "Recommendations below are macOS-first. On Windows, prefer `winget install ...` for system tools and document.io for downloads. On Linux, use your distro package manager. Spec 007 will fully platform-branch this document; until then, Claude should adapt the brew commands to the researcher's platform when reading audit.platform."

This is a stopgap — full fix is spec 007. But the stopgap means a Windows researcher who runs `/carrel-setup` today gets coherent guidance instead of failing instructions.

**Files**:
- `commands/carrel-setup.md`
- `src/carrel/env/install.py`
- `skills/environment-setup/references/decision-tree.md`

---

### TIER 1 — Architectural / High-leverage (one commit each)

#### A1. Add `carrel setup-state` CLI (Codex #1 recommendation)

**Why this matters most**: it removes the procedural coupling that underlies B2, several Tier 2 bugs, and the version-sync sprawl. Once this lands, /carrel-setup, migration docs, and the hook all have a single boundary instead of "Claude edits JSON correctly, hopefully".

**Spec**:
- `carrel setup-state advance --phase N --vault PATH` — atomically updates `last_completed_phase` (validates phase ∈ {5, 6, 7, 8, 9} since phase 4 is the initial write from `vault init`)
- `carrel setup-state complete --vault PATH` — sets `last_completed_phase=9` AND `completed_at=$(today ISO)`. Idempotent.
- `carrel setup-state show --vault PATH` — pretty-print current state
- `carrel setup-state reset --vault PATH` — for recovery; logs to capability log
- All commands use `SetupState` Pydantic model for read AND write — so unparseable input fails loudly

**Files to create**:
- `src/carrel/cli/setup_state.py` (new, ~100 LOC)
- `src/carrel/cli/main.py` (register the new typer app)
- `tests/test_setup_state.py` (new — round-trip + reject-malformed tests)

**Files to update** (consumer side):
- `commands/carrel-setup.md`: replace prose "update setup-state.json" instructions with `carrel setup-state advance --phase N` calls; replace "set completed_at to today's ISO date" with `carrel setup-state complete`
- `migrations/0.5.1-to-0.5.2.md`: replace the Unix-shell manual fallback with `carrel setup-state complete` (cross-platform — solves Codex MEDIUM about `date -u`)

#### A2. Tighten `SetupState` Pydantic model

**Fixes**: code-reviewer #4 + Codex MEDIUM + Kimi re-review #4

```python
class SetupState(BaseModel):
    last_completed_phase: int = Field(ge=4, le=9)  # was ge=0; persistence begins at 4
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+].+)?$")
    completed_at: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",  # ISO date
    )
```

Also add a `model_validator(mode="after")` that asserts `last_completed_phase == 9` IFF `completed_at is not None` (mutual implication — phase 9 without completed_at means setup is mid-handoff, NOT complete; closes Kimi re-review SKILL.md gap by making the contradiction model-rejected instead of doc-clarified).

**Files**:
- `src/carrel/models.py`
- `tests/test_models.py` (new tests for the validators)

#### A3. Harden `hooks/check-environment.js` setup-state reading

**Fixes**: code-reviewer #2 + Kimi re-review #7 + Codex HIGH

```js
const phase = setupState?.last_completed_phase;
if (!Number.isInteger(phase) || phase < 4 || phase > 9) {
  // Malformed state — surface a one-line diagnostic, don't silently skip
  if (setupState != null) {
    console.log('Note: .carrel/setup-state.json is malformed — run `carrel setup-state show` to inspect.');
  }
} else if (phase < 9 || setupState.completed_at == null) {
  // existing resume logic, with the phase==9 + null completed_at case now covered
}
```

Also: surface a stderr warning when `setup-state.json` exists but `JSON.parse` fails (Kimi LOW).

**Files**:
- `hooks/check-environment.js`

#### A4. Enforce version-source-of-truth via test

**Fixes**: code-reviewer #5

Add `tests/test_version_consistency.py` that loads `pyproject.toml`, `src/carrel/__init__.py:__version__`, `.claude-plugin/plugin.json:version`, `.claude-plugin/marketplace.json:plugins[0].version` and asserts all four match. CI catches drift before deploy.

**Files**:
- `tests/test_version_consistency.py` (new)

#### A5. Fix install.ps1 verification step + bun URL

**Fixes**: code-reviewer #1 + Kimi #1

1. `install.ps1`: bump `$Total = 8`. Add Step 8 mirroring `install.sh:273-287` — `Get-Command` for git/node/bun/uv/gh/claude, surface `Missing: ...` warning and PATH-refresh hint.
2. `install.ps1:73`: change `irm bun.sh/install.ps1 | iex` → `irm https://bun.sh/install.ps1 | iex`.

**Files**:
- `install.ps1`

#### A6. Add `bun` to `audit.py` TOOL_CHECKS

**Fixes**: Kimi re-review #2

`src/carrel/env/audit.py:18-32` — add `"bun": ["bun", "--version"]` to the TOOL_CHECKS dict so `carrel env doctor` surfaces missing bun cleanly.

**Files**:
- `src/carrel/env/audit.py`

#### A7. Fix `cli/vault.py` raw ValidationError

**Fixes**: code-reviewer #3

Wrap `ResearcherProfile.model_validate_json(...)` at line 155 in try/except for `ValidationError` and `json.JSONDecodeError`; re-raise as `CarrelError` with an actionable hint.

```python
from pydantic import ValidationError
import json
...
try:
    profile = ResearcherProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))
except (ValidationError, json.JSONDecodeError) as exc:
    raise CarrelError(
        f"Could not parse {profile_path}",
        hint="The file may be hand-edited or corrupted. Run /carrel-setup to regenerate.",
    ) from exc
```

**Files**:
- `src/carrel/cli/vault.py` (~5 lines)

---

### TIER 2 — Spec corrections (no code; affects future implementation)

#### S1. Spec 007: rename `ToolAvailability` to avoid collision

**Fixes**: Kimi re-review #3

`src/carrel/models.py` already has a `ToolAvailability(BaseModel)` with fields `binaries`, `api_keys`, `mcp_servers`. Spec 007 deliverable A3 proposes a NEW class with the same name and shape `dict[str, dict[Platform, bool]]`. Implementation would overwrite. Rename to `PlatformToolMatrix` or `ToolPlatformMatrix` in the spec.

**Files**:
- `planning/specs/007-cross-platform-support.md`

#### S2. Spec 006: clarify fix command scope

**Fixes**: Kimi re-review #6

`planning/specs/006-environment-validation-and-self-healing.md` — the `fix` command docstring says "Auto-fix safe drift in `.carrel/environment.json`" but the known-safe fixes table includes `setup-state.json` version updates. Either expand the docstring scope to both files, or split into `carrel env fix` (environment.json) + the new `carrel setup-state` CLI handles its own drift.

Recommendation given A1 lands first: spec 006 narrows `carrel env fix` to ONLY `environment.json`; setup-state drift handled by `carrel setup-state` (which can grow a `--repair` flag if needed).

**Files**:
- `planning/specs/006-environment-validation-and-self-healing.md`

#### S3. Spec 007: clearer "Lock Blockers" status

**Fixes**: Codex HIGH (007 not lock-ready)

The "Open Question 6 marked Locked" message in spec 007 is misleading — sequencing is locked, but the spec itself still has unresolved blockers (liteparse Windows, gws Windows). Move "Lock Blockers" section to the very TOP of the spec so no one starts implementation thinking it's ready.

**Files**:
- `planning/specs/007-cross-platform-support.md`

---

### TIER 3 — Hygiene

#### H1. Update README command list

**Fixes**: Codex MEDIUM

`README.md:17, :27` — say 13 commands not 9; add `/carrel-automate`, `/carrel-batch`, `/carrel-mirror`, `/carrel-share` to the table.

#### H2. Beef up `render_cheat_sheet`

**Fixes**: Codex MEDIUM

`src/carrel/vault/templates.py` — current renderer emits vault path, sensitivity, audio flag, folder names. Phase 7 framing implies a "core handoff artifact". Add: configured tools matrix (from `tools_configured`), 3-5 example commands per configured tool, a "common workflows" section based on `preferences.*`. Probably 60-100 lines added.

#### H3. Dedup briefs directory listing

**Fixes**: code-reviewer #9

`hooks/check-environment.js` — lift `briefs` array to top of `checkAutomation`, reuse instead of listing twice.

---

## Execution Order for Codex

Codex should pick up at TIER 0 immediately. Suggested commit sequence:

1. Commit: B1 README/CLAUDE.md reconciliation (doc-only, fastest)
2. Commit: B2 stopgap Mac-coded /carrel-setup fix (touches 3 files)
3. Commit: A1 `carrel setup-state` CLI (largest single commit; new module + consumer updates)
4. Commit: A2 tighten SetupState model + tests
5. Commit: A3 harden hook
6. Commit: A4 + A5 + A6 + A7 (small fixes; can batch)
7. Commit: S1 + S2 + S3 spec corrections (single commit)
8. Commit: H1 + H2 + H3 hygiene

Verification at each stage:
- `uv run pytest` (49 tests + new ones — should grow with A1, A2, A4)
- `bash -n install.sh` syntax check
- Manual scaffold smoke test on `/tmp/`

After Tier 0+1: bump version 0.5.2 → 0.5.3 (additive features + bug fixes; backward compatible). Migration `0.5.2-to-0.5.3.md` documenting the new `carrel setup-state` CLI as the canonical phase-management surface.

After Tier 2 spec edits: no version bump needed (planning artifacts only).

---

## Out of Scope for This Cycle (deferred)

- Full spec 007 implementation (waiting on liteparse Windows + gws Windows research)
- Full spec 006 implementation (waiting on platform field from spec 007)
- ItDepends integration work
- Knowledge wiki improvements

These are tracked elsewhere and shouldn't block Imperial deployment readiness.
