# Spec 011: Profile Sync Architecture

**Status**: Pre-research / pre-implementation
**Origin**: 009 holistic audit, A3 (Codex §3 + §6 — "narrative shadow state"; Bug Class 3 prediction)
**Target version**: 0.6.x or 0.7.0 (depending on scope)

---

## Problem

Profile data is asked to live in **five surfaces** that must stay in sync:

1. `.carrel/environment.json` — structured truth (Pydantic model, written by `vault init` + `setup-state`)
2. Vault `CLAUDE.md` — narrative for Claude's judgment (written once by setup, hand-maintained thereafter)
3. `_meta/my-environment.md` — researcher-facing dashboard (written once by scaffold, hand-maintained thereafter)
4. `_meta/cheat_sheet.md` — quick-reference card (regenerable via `carrel vault cheatsheet`)
5. `_meta/automation-prompt.md` — overnight prompt (written by `/carrel-automate`, hand-maintained thereafter)

**Only #4 has a deterministic generator.** Surfaces 2, 3, and 5 are asked to be hand-maintained by Claude based on the SKILL contract. After a researcher changes a setting (sensitivity, cloud consent, automation toggle, wiki preference), the surfaces drift, and Claude behaves according to whichever document it read first.

Codex Bug Class 3 will surface in pilot: a researcher adds a key, changes sensitivity, or enables automation/wiki — one surface says the tool is active, another says deferred, and Claude's behavior depends on which it loaded.

This is the third "markdown control plane" problem after setup-state (closed in v0.5.3) and trust enforcement (spec 008). Pattern: take a flow currently expressed as "Claude does X, Y, Z to keep things in sync", and make it `carrel <flow> <verb>` with the Pydantic model as gatekeeper.

## Why Now

The cheatsheet beef-up in v0.5.3 + the doc audit's findings (interview-protocol vs automation/SKILL truncation, vault-ops diagram missing folders) showed how easily the surfaces drift even within a single sprint. With Imperial pilot accumulating multi-week sessions, the drift will compound.

## Goals

For each of the four mirror surfaces (excluding environment.json which is the source), decide:

**Generated** OR **Hand-maintained-with-drift-check**.

### Proposal

| Surface | Decision | Mechanism |
|---------|----------|-----------|
| `_meta/cheat_sheet.md` | **Generated** (already done) | `carrel vault cheatsheet --force` |
| `_meta/my-environment.md` | **Generated** | NEW `carrel vault dashboard --force` regenerator |
| `_meta/automation-prompt.md` | **Generated** | NEW `carrel vault automation-prompt --force` (called by `/carrel-automate`) |
| Vault `CLAUDE.md` | **Hand-maintained-with-drift-check** | NEW `carrel vault check-sync` reports diffs |

The vault `CLAUDE.md` is intentionally hand-maintained — it carries narrative context that no template can capture. But the structured fields it embeds (sensitivity, cloud consent, configured tools, automation status, wiki status) should be auditable against the source.

### Goals breakdown

1. **`carrel vault dashboard --force`** — regenerates `_meta/my-environment.md` from environment.json + audit data + activity stats. Idempotent. Same template-vs-source pattern as `carrel vault cheatsheet`.
2. **`carrel vault automation-prompt --force`** — regenerates `_meta/automation-prompt.md` from `AutomationConfig`. Replaces the prose "Claude generates this" instruction in `commands/carrel-automate.md`.
3. **`carrel vault check-sync`** — diffs the structured fields embedded in vault `CLAUDE.md` against environment.json. Reports drift. Can be called by the session-start hook to surface "your CLAUDE.md is out of sync with your settings" warnings.
4. **Skill integration**: `/carrel-setup`, `/carrel-automate`, `/carrel-share` all use the regenerators instead of asking Claude to hand-maintain.

## Open Questions

- **`my-environment.md` template scope**: is this the same content as the cheat sheet, or does it have unique sections (activity stats, recent friction-log entries, capability log highlights)? If unique, the renderer needs to read more than environment.json. Probably yes — it's a "living dashboard" per current docs.
- **Activity stats**: where do they come from? Counting files in `papers/`, `transcripts/`, `inbox/`? Reading `_meta/friction_log.md`? This becomes a richer data source than just the profile.
- **`check-sync` heuristic**: how does it know what's "structured fields embedded in CLAUDE.md"? Options:
  - Convention (specific markers like `<!-- carrel:sensitivity -->`)
  - Section heading matching (look for `## Sensitivity` header and parse value)
  - LLM-based (defeats the purpose)
  
  Leaning toward marker comments — explicit, machine-parseable, future-proof.
- **Backfill for existing vaults**: vaults written before this spec lands won't have markers in CLAUDE.md. Migration: skip drift-check on un-marked vaults; print one-time hint to add markers.
- **Hook integration**: when does check-sync run? Every session-start would be expensive; once-per-day with a `last_checked_at` stamp would be reasonable.

## Constraints

- **No code changes to environment.json schema**: this spec is about the SURFACES, not the source.
- **All regenerators must be additive**: never delete user-added content. If `_meta/my-environment.md` has hand-written notes outside the regenerated sections, preserve them.
- **`--force` vs default**: regenerators default to NO action if the file exists; require `--force` to overwrite. Same pattern as `carrel vault cheatsheet`.
- **Cross-platform**: regenerators must work on macOS, Linux, Windows. No shell scripting.

## Lock Blockers

- **Marker convention decision**: needs alignment with skill-writing conventions before lock. Currently no skill uses HTML-comment markers; this would be a new pattern.
- **Activity-stats data source**: depends on whether `friction_log.md` and `capability-log.md` get structured renderers (they're currently free-form markdown). Probably defer to spec 011.5 ("structured logs") if needed.

## Cross-Cutting

- **Spec 008 (trust enforcement)**: trust level is one of the fields the dashboard surfaces. The regenerator should pull from `AutomationConfig`, the dashboard should consume.
- **Spec 010 (policy module)**: the policy module's `--explain` rationale should be retrievable by the dashboard ("Last routing decision: X chose Y because Z").
- **Spec 006 (env validation)**: the doctor agent's lint should call `check-sync` and surface drift findings as a lint category.

## Adjacent Work (NOT in this spec)

- Vault export/import across machines (Codex §5) — separate spec
- Telemetry/observability (Codex §5) — separate spec
- Recovery/snapshot story for assistant-written markdown (Codex §5) — separate spec
- `.carrel/exports/` retention story (Codex §2) — small enough to not need a spec; could fold into v0.5.5
