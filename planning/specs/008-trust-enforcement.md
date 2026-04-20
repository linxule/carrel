# Spec 008: Trust Enforcement Code Guard

**Status**: Locked, ready for implementation
**Origin**: 009 holistic audit, A1 (Codex §4 — "trust is a prompt contract, not a runtime guard")
**Target version**: 0.6.0 (markdown control plane closure milestone)

---

## Problem

The trust system (`Advisory` / `Consultative` / `Delegated` / `Partnership`) is stored in `AutomationConfig.trust_level`, narrated in `skills/automation/SKILL.md` and `skills/knowledge-wiki/SKILL.md`, and surfaced in the session-start hook banner. It is **never enforced at a code boundary**.

Worst-case blast radius: a delegated/partnership configuration grants whatever-the-current-assistant-can-write, with no guard rail beyond Claude reading the SKILL correctly. A misconfigured profile + a chatty assistant session is enough to cause unintended vault mutations. Wiki activation, automation enablement, and pending-decision writes are all direct-edit recipes that no code path can reject.

This is the second "markdown control plane" problem the audit identified. v0.5.3 closed the first one (setup-state) by adding a deterministic CLI as the validation boundary. This spec applies the same shape to trust.

## Why Now

Imperial pilot will surface the worst-case scenario — a researcher with `trust_level=advisory` whose Claude session writes to `_meta/pending-approvals.md` (a Consultative-level surface) because the SKILL was misread. Currently no error path catches this; the file just gets written.

## Locked Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Granularity | **Hierarchical** (`namespace:verb`) | Fewer enum entries; new actions just add a verb under an existing namespace; mirrors common ACL patterns |
| Override path | **Trust-elevation only**, no `--force` | The whole point is "no backdoor"; if Claude can talk itself out of a check, the boundary is theatre. Researcher must run `/carrel-automate` to elevate. |
| Audit log | **Defer to v2** | Useful but adds I/O on every check; nail the gate first, observability second. Spec 011's hook integration can surface drift later. |
| Read-side gating | **Out of scope** | Writes are the blast-radius surface. Read-gating is a privacy concern, not a trust concern; defer. |

## Action Vocabulary (locked)

Hierarchical `namespace:verb` form. Trust level required to perform the action shown in the rightmost column.

| Action | Description | Required Trust |
|--------|-------------|----------------|
| `automation:propose` | Write a proposal to `_meta/pending-approvals.md` for researcher review | Consultative |
| `automation:execute` | Execute a previously approved automation step (move file, run command) | Delegated |
| `automation:write-prompt` | Write/update `_meta/automation-prompt.md` for overnight runs | Delegated |
| `wiki:propose` | Suggest enabling the knowledge wiki; write a proposal note | Consultative |
| `wiki:write` | Create/update wiki pages autonomously | Delegated |
| `vault:move-file` | Move a file from `inbox/` to a typed folder (papers, transcripts, notes) | Delegated |
| `vault:reorganize` | Move/rename files outside the inbox routing flow | Partnership |

Trust hierarchy: `Advisory < Consultative < Delegated < Partnership`. Higher trust includes all lower-trust permissions.

## Implementation Plan

### CLI surface

```
carrel trust check <action> [--vault PATH] [--format human|json|quiet]
carrel trust list [--vault PATH] [--format ...]              # show what current trust allows
carrel trust show [--vault PATH] [--format ...]              # current trust level + audit summary
```

- `check` exits `0` if allowed, exits with `CarrelError` (non-zero) if denied. The error message names the action, the current trust level, and the minimum trust level that would allow it.
- `list` prints all actions, marked allowed/denied at current trust level. Helps researchers understand what their setting unlocks.
- `show` prints current `trust_level` from `AutomationConfig`. Sets up future v2 audit log integration.

### Module shape

- New file: `src/carrel/cli/trust.py` — typer sub-app, ~80 LOC
- New file: `src/carrel/trust.py` — pure-Python policy module:
  ```python
  ACTIONS: dict[str, TrustLevel] = {
      "automation:propose": TrustLevel.CONSULTATIVE,
      "automation:execute": TrustLevel.DELEGATED,
      ...
  }

  def is_allowed(action: str, trust_level: TrustLevel) -> bool: ...
  def required_trust(action: str) -> TrustLevel: ...
  def list_actions() -> dict[str, tuple[TrustLevel, bool]]: ...  # for CLI list
  ```
- Updated: `src/carrel/cli/main.py` — register the new sub-app
- Updated: `src/carrel/models.py` — add `TrustLevel` enum if not already canonical (it currently lives as a string Literal in AutomationConfig — promote to proper enum)

### Skill integration (writes are the boundary)

For each gated write site in skills/commands/agents, add a `carrel trust check <action> --vault .` call before the write:

| Skill / Command | Write site | Action |
|-----------------|------------|--------|
| `skills/automation/SKILL.md` (Consultative section) | Writes to `_meta/pending-approvals.md` | `automation:propose` |
| `skills/automation/SKILL.md` (Delegated section) | Executes from `_meta/pending-approvals.md`; writes to `_meta/automation-prompt.md` | `automation:execute`, `automation:write-prompt` |
| `commands/carrel-automate.md` Phase 9 | Writes `_meta/automation-prompt.md` | `automation:write-prompt` |
| `skills/knowledge-wiki/SKILL.md` activation flow | Writes wiki structure | `wiki:write` (or `wiki:propose` for Consultative) |
| `skills/knowledge-wiki/references/trust-activation.md` | Writes `wiki_enabled` true + initial wiki structure | `wiki:write` |
| `skills/automation/SKILL.md` (Partnership section) | Reorganizes vault | `vault:reorganize` |
| `skills/automation/SKILL.md` (Delegated inbox routing) | Moves file from `inbox/` | `vault:move-file` |

If `check` returns non-zero, skill instructions tell Claude to surface the gate to the researcher: "I tried to <action> but your trust level (<current>) doesn't allow that. To enable, raise trust to <required> via `/carrel-automate`."

### Tests

`tests/test_trust.py` — at minimum:
- Each action × each trust level (matrix test, parametrized)
- Unknown action → CarrelError
- Missing environment.json → CarrelError with hint
- Round-trip: write profile with `trust_level=delegated`, check `automation:execute` returns 0, check `vault:reorganize` exits non-zero

`tests/test_cli_trust.py` — CLI invocation:
- `carrel trust check automation:propose` exits 0 at consultative
- `carrel trust list --format json` returns the action matrix

## Constraints (locked)

- **Cannot break v0.5.4 vaults**: existing `AutomationConfig.trust_level` values must continue to work. The check is additive — no existing skill is REQUIRED to call it (yet); the spec adds the call sites in skill markdown.
- **Must run sub-100ms**: trust check is called before every gated write; it cannot become a perceptible delay. (Pure Python enum comparison + one file read; should be ~10ms.)
- **Single source of truth**: trust level lives in `.carrel/environment.json`. The check reads from there. No caching that could go stale.
- **Pure Python, no I/O for the check itself**: just enum comparison + read of the profile.

## Cross-Cutting

- **Spec 010 (policy module)**: same architectural pattern. Spec 010's sensitivity routing decision uses the same "single Python decision boundary that downstream code consumes" shape. Could share infrastructure for `--explain` flag plumbing in the future.
- **Spec 011 (profile sync)**: trust level is one of the fields the dashboard surfaces. The deterministic generator for `_meta/automation-prompt.md` (spec 011) should consume the trust level from environment.json via `carrel trust show --format json`.

## Adjacent Work (NOT in this spec)

- Trust-level read gating (writes are the blast-radius surface)
- Trust-level downgrades during a session (e.g., "if too many failed checks, auto-downgrade to advisory") — defer
- Per-skill trust overrides — defer
- Audit log (`_meta/trust-log.jsonl`) — defer to v2
- Hook surface for "writes blocked in prior session" — defer (depends on audit log)
