# Spec 008: Trust Enforcement Code Guard

**Status**: Pre-research / pre-implementation
**Origin**: 009 holistic audit, A1 (Codex §4 — "trust is a prompt contract, not a runtime guard")
**Target version**: 0.6.x

---

## Problem

The trust system (`Advisory` / `Consultative` / `Delegated` / `Partnership`) is stored in `AutomationConfig.trust_level`, narrated in `skills/automation/SKILL.md` and `skills/knowledge-wiki/SKILL.md`, and surfaced in the session-start hook banner. It is **never enforced at a code boundary**.

Worst-case blast radius: a delegated/partnership configuration grants whatever-the-current-assistant-can-write, with no guard rail beyond Claude reading the SKILL correctly. A misconfigured profile + a chatty assistant session is enough to cause unintended vault mutations. Wiki activation, automation enablement, and pending-decision writes are all direct-edit recipes that no code path can reject.

This is the second "markdown control plane" problem the audit identified. v0.5.3 closed the first one (setup-state) by adding a deterministic CLI as the validation boundary. This spec proposes the same shape for trust.

## Why Now

Imperial pilot will surface the worst-case scenario — a researcher with `trust_level=advisory` whose Claude session writes to `_meta/pending-approvals.md` (a Consultative-level surface) because the SKILL was misread. Currently no error path catches this; the file just gets written.

## Goals

1. **A `carrel trust check <action>` CLI** that takes an action description and a vault path, returns `0` if the action is allowed at the current trust level, exits with `CarrelError` and a clear message otherwise.
2. **Action vocabulary**: enumerate the kinds of writes that need trust gating. Initial set:
   - `write-pending-approval` (Consultative+)
   - `write-overnight-prompt` (Delegated+)
   - `enable-wiki` (Consultative+ for proposal; Delegated for autonomous)
   - `reorganize-vault` (Partnership only)
   - `move-files` (Delegated+ for inbox routing; Partnership for arbitrary moves)
3. **Skill integration**: every skill that performs a trust-gated write calls `carrel trust check <action> --vault .` before the write. If non-zero exit, surface the gate failure to the researcher.
4. **No backdoor**: the check must consult `.carrel/environment.json` (the canonical AutomationConfig source), not be talked out of it by the assistant.

## Open Questions

- **Granularity**: enumerate per-action or use a hierarchical pattern (`automation:write`, `automation:execute`, `wiki:propose`, `wiki:write`)? Leaning hierarchical for fewer enum entries.
- **Override path**: should there be a `--force` flag, or must the researcher elevate trust level via `/carrel-automate` first? Leaning latter (no force) — the override path IS the trust elevation flow.
- **Audit log**: should every check (pass or fail) write to `_meta/trust-log.jsonl`? Useful for debugging; might be noisy. Spec 4 deferred for v1.
- **Hook integration**: should the session-start hook surface "writes blocked by trust level" if any happened in the prior session? Useful but requires the audit log.
- **What about reads?** This spec is write-gated only. Read-side trust (e.g., "can Claude SEE pending automation proposals at advisory level?") is out of scope.

## Constraints

- **Cannot break v0.5.4 vaults**: existing `AutomationConfig.trust_level` values must continue to work. The check is additive.
- **Must run sub-100ms**: trust check is called before every gated write; it cannot become a perceptible delay.
- **Single source of truth**: trust level lives in `.carrel/environment.json`. The check reads from there. No caching that could go stale.
- **Pure Python, no I/O for the check itself**: just enum comparison + read of one file.

## Lock Blockers

None known. This is internal architecture — no upstream dependencies. Ready for review when written.

## Cross-Cutting

- **Spec 010 (policy module)**: shares the "decision boundary" pattern with sensitivity routing. Consider whether trust + sensitivity should share a `policy.py` module.
- **Spec 011 (profile sync)**: trust level is one of the fields whose sync across surfaces matters. The deterministic generator for `_meta/automation-prompt.md` (spec 011) should consume the trust level from environment.json, not from a hand-edited mirror.

## Adjacent Work (NOT in this spec)

- Trust-level read gating (spec adds write gates only)
- Trust-level downgrades during a session (e.g., "if too many failed checks, auto-downgrade to advisory") — defer
- Per-skill trust overrides — defer
