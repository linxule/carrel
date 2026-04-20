# 009: Holistic Audit — Triangulated Synthesis

**Date**: 2026-04-20
**Range reviewed**: whole repo at v0.5.3 (commit `ae44c83`)
**Reviewers**:
- Internal `code-reviewer` agent (whole-repo Python/JS code quality, confidence-filtered) → `009-audit-code-quality.md`
- Documentation coherence pass (Opus, 1M context) — README, CLAUDE.md, every command/skill/agent/migration → `009-audit-documentation.md`
- Plugin-surface integrity pass (Opus, 1M context) — wiring of every command/skill/agent/hook → `009-audit-plugin-surface.md`
- Codex fresh adversarial pass (12-month-on-call lens) — meta-question of architecture + trust + privacy → `009-audit-adversarial.md`

**Verdict**: v0.5.3 closed the deployment-readiness sprint cleanly, but a holistic pass surfaces a deeper class of risk than 008 was scoped for: **the markdown control plane**. Trust, sensitivity, and profile-sync flows still live as prose contracts that Claude is asked to honor, not code boundaries that the system enforces. That's fine for a careful facilitator running early Imperial pilots — but it defines a maintenance ceiling.

Two BLOCKERS for the next researcher to use the system (`/carrel-research` ships in every cheat sheet but doesn't exist; the SessionEnd hook is silently dead for every vault scaffolded post-v0.4). Four more deployment-time hardening items (sensitivity routing actually enforces the local-first promise; error contract leak in `read_profile()`; cross-platform skills propagation; trust-level code guard). Then a long backlog of documentation drift and code hygiene that doesn't gate deployment but does compound over 12 months of maintenance.

---

## Triangulation Map

Where reviewers converge is where the highest-confidence fixes live.

| Issue | Code-Q | Docs | Plugin | Codex | Severity |
|-------|:-:|:-:|:-:|:-:|:-:|
| `hooks/session-reflect.js` only handles legacy nested profile shape (silent no-op for every modern vault) | C2 | — | B1 | Bug Class 1 | **BLOCKER** |
| `render_cheat_sheet` writes `/carrel-research` (no such command) into every wiki-enabled cheat sheet | — | (fwd) | B2 | (impl. §3) | **BLOCKER** |
| `cheatsheet-template.md` is fictional Mustache template; renderer is hardcoded Python f-string with different shape | — | H4 | D2 | §3 | **HIGH** |
| Cross-platform v0.5.3 stopgap stopped at command files; `skills/environment-setup/references/*` and parent SKILL still recommend `brew install` | — | H1,H2,H3 | (impl) | (impl. §6) | **HIGH** |
| Profile data is asked to live in 5 places (`environment.json`, vault `CLAUDE.md`, `_meta/my-environment.md`, `_meta/cheat_sheet.md`, sometimes `_meta/automation-prompt.md`) — only one has a deterministic generator | — | (fwd) | (fwd) | §3,§6,Bug Class 3 | **HIGH** |
| `ConvertOptions`/`TranscribeOptions` exist but are never used; routers accept `sensitivity`/`hardware` and discard them | I3 | — | — | §1,§6 (parametric ghosts) | MEDIUM |
| Twin `templates/` directories already drifted (root vs `skills/vault-ops/templates/vault-scaffold.json`) | — | — | (Tier3 note) | §1,§6 (template twins) | MEDIUM |
| Deprecated `bootstrap.sh` still framed as canonical in `decision-tree.md`; no runtime banner | M8 | M1 | — | — | LOW |

Where reviewers diverge is where unique perspectives matter.

| Issue | Source | Severity |
|-------|--------|---------|
| **Trust enforcement gap**: trust_level stored, narrated, surfaced — never enforced in code. Worst-case blast radius: full vault mutation by an assistant with normal write perms in advisory mode | Codex §4 | **HIGH** |
| **Sensitivity routing gap**: routers accept `sensitivity` and discard it; effective cloud gate is `cloud_consent` alone. Contradicts README's "Sensitivity-aware by default" promise | Codex §2, Bug Class 2 | **HIGH** |
| `read_profile()` raises raw `ValidationError`/`json.JSONDecodeError` past CLI guards in 4 commands (paper convert, transcript create, google export, env profile) — A7's fix only patched `vault cheatsheet` | Code-Q C1 | **HIGH** |
| Transcript idempotency breaks across day boundaries (date-stamped filename defeats SHA hash) | Code-Q I1 | HIGH |
| `carrel vault new` path traversal (no slugification on `name`) | Codex §2 | HIGH |
| `hardware-audit.md` documents an `AuditResult` JSON schema that doesn't match the actual Pydantic model | Doc H5 | HIGH |
| No path-containment check on filers; symlinked vault subdir could route writes outside | Codex §2 (HYPOTHESIS) | MEDIUM |
| `--speakers` flag declared, immediately discarded; coli adapter never receives it; SKILL doc promises diarization | Code-Q I2 | MEDIUM |
| `cloud_consent` printed as raw `false`/`true` in hook banner (legacy strings were `prefer_local`/`local_only`/`comfortable_with_cloud`) | Plugin B3 | MEDIUM |
| `AutomationConfig.last_reviewed` + `wiki_proposal_deferred_until` accept any string (SetupState got `pattern=` in v0.5.3; these didn't) | Code-Q M5 | MEDIUM |
| `commands/carrel-migrate.md` writes `version` to plugin-state; CLAUDE.md + check-version.js use `plugin_version` (works via `||` fallback) | Plugin D1, Code-Q M3 | MEDIUM |
| `gws` adapter raises `ToolNotInstalled` on auth failure (should be auth error) | Code-Q I4 | MEDIUM |
| Cloud HTTP adapters skip `raise_for_status()` and `response.json()` guards | Code-Q I7 | MEDIUM |
| `.carrel/exports/` has no cleanup story (sensitive Google Doc raw exports linger) | Codex §2 | MEDIUM |
| `vault status --format quiet` returns nothing | Code-Q M7 | MEDIUM |
| `interview-protocol.md` JSON omits the eight per-capability AutomationConfig booleans shown elsewhere | Doc M2 | MEDIUM |
| `vault-ops/SKILL.md` vault diagram omits `_meta/local/` and `_meta/reflections/` | Doc M4 | MEDIUM |
| `toolchain-guide.md` references `environment.json.data_types` field that doesn't exist on `ResearcherProfile` | Codex §3 | MEDIUM |
| Phase/Step numbering off by one between `commands/carrel-setup.md` and `environment-setup/SKILL.md` | Doc M6 | LOW |
| Three different YouTube URL parsers in three modules | Code-Q M2 | LOW |
| Twin `_source_hash` helpers in convert/transcribe filers | Code-Q M10 | LOW |
| 12 empty `catch {}` in `check-environment.js` | Code-Q M9 | LOW |
| Pure pass-through wrappers in `paper.py`/`transcript.py` (drop type annotations) | Code-Q I5 | LOW |
| Dead doctest scaffolding in `env/install.py` | Code-Q I8 | LOW |
| `carrel-share` SKILL documents a `--quick` flag with no plumbing | Plugin D5 | LOW |
| `environment-setup/SKILL.md:222` lumps live `check-environment.js` hook in with removed legacy scripts | Plugin D4 | LOW |
| `obsidian-setup.md` is an orphan reference (no skill cites it) | Plugin D3 | LOW |
| Nag-spam: post-version-bump migration prompt fires every session until acknowledged | Code-Q M3 | LOW |

---

## The Headline Insight (Codex)

**The Markdown Control Plane is the load-bearing risk.** v0.5.3 added one deterministic boundary (`carrel setup-state`). The audit says we need 2-3 more before deployment is operationally safe.

Specifically, three policy-critical flows still live in prose:

1. **Trust enforcement** — `trust_level` is stored in `AutomationConfig`, narrated in `automation/SKILL.md`, displayed in the hook, but never code-gated. A delegated/partnership configuration grants whatever-the-current-assistant-can-write, with no guard rail beyond Claude reading the SKILL correctly. *No CLI says "this write is not allowed at advisory level."*
2. **Sensitivity routing** — `sensitivity` flows from the profile through CLI args into both routers, both of which discard it. The product promise "local-first when sensitive" is enforced by hope. A profile that drifts to `cloud_consent=true` for one workflow can later route a sensitive PDF to Mineru when a local binary is missing.
3. **Profile sync** — `environment.json` is the structured source, but four other surfaces (`CLAUDE.md`, `_meta/my-environment.md`, `_meta/cheat_sheet.md`, `_meta/automation-prompt.md`) are asked to mirror it. Only `_meta/cheat_sheet.md` has a deterministic generator. Predicted bug class: after a researcher changes a setting, surfaces disagree, and Claude behaves according to whichever doc it read first.

The fix shape is the same that worked for setup-state: take a flow currently expressed as "Claude does X, Y, Z to keep things in sync", and make it `carrel <flow> <verb>` with the Pydantic model as gatekeeper.

---

## Tiered Fix Plan

### TIER 0 — Imperial pilot blockers

#### B1. `render_cheat_sheet` writes broken `/carrel-research` slash command

`src/carrel/vault/templates.py:137`. Every wiki-enabled cheat sheet ships a dead command. Two-minute fix.

**Fix**: replace the line with natural-language framing or remove. There is no `/carrel-research` command. Suggested copy: `"- Knowledge wiki: ask Claude about your field map; pages live in wiki/."`

#### B2. `session-reflect.js` is silently dead for every modern vault

`hooks/session-reflect.js:90` only reads `env.interview?.researcher` (legacy nested shape). Modern `ResearcherProfile` is flat. Hook exits before printing reflection prompt, vault stats, capability log nudges.

**Fix**: mirror the flat-OR-nested fallback used by `check-environment.js:271-281`. `const researcher = env.name ? env : env.interview?.researcher;`

#### B3. `read_profile()` error contract leaks across 4 CLI commands

`src/carrel/env/profile.py:13-19`. A corrupted or stale `.carrel/environment.json` produces a raw Python traceback in `paper convert`, `transcript create`, `google export`, `env profile`. The A7 fix in v0.5.3 only patched `vault cheatsheet`.

**Fix**: wrap inside `read_profile()` itself. Catch `(ValidationError, json.JSONDecodeError, OSError)`, raise `CarrelError("Could not parse <path>", hint="Run /carrel-setup to regenerate it.")`. Then add a malformed-profile test for at least one of the four downstream commands.

#### B4. Sensitivity is mechanically meaningless

`src/carrel/convert/router.py:10-31` and `src/carrel/transcribe/router.py:18-47` accept `sensitivity` and discard it. Cloud routing is gated only by `cloud_consent`. Contradicts the README promise.

**Fix (minimum viable)**: in `consent.py:6-10`, change `is_cloud_consented(tool, profile)` to also require `profile.sensitivity != Sensitivity.HIGH` (or whatever the established high-sensitivity enum value is) before allowing cloud tools. This is a one-screen change with massive product-promise impact. The deeper fix (a `policy.py` module that owns the routing decision) is Tier 1 work.

#### B5. Cross-platform v0.5.3 stopgap didn't propagate to the skill files Claude actually loads

`skills/environment-setup/references/decision-tree.md:400-418` (Obsidian Setup section), `skills/environment-setup/SKILL.md:147-152` (Step 7 Human Steps), `skills/environment-setup/references/obsidian-setup.md` (mac-only throughout) — all still recommend `brew install obsidian` unconditionally. A Windows researcher whose Claude session reads the SKILL flow rather than re-reading the command will get failing instructions. Bonus: bare `brew install obsidian` is wrong even on macOS (it's a cask).

**Fix**: Mirror the OS-branched block from `commands/carrel-setup.md:81-84` into all three locations. Use `brew install --cask obsidian` everywhere on macOS.

---

### TIER 1 — Architectural / High-leverage

#### A1. Trust-level code guard

The 12-month maintenance risk. Right now `Advisory`/`Consultative`/`Delegated`/`Partnership` are documentation contracts; the runtime stores the enum but doesn't enforce it. A misconfigured profile + a chatty assistant session is enough to cause unintended vault mutations.

**Recommended shape**: a `carrel trust-check <action>` CLI that takes an action description (`"write _meta/pending-approvals.md"` / `"reorganize papers/"` / `"enable wiki"`) and a vault path, returns 0 if allowed at the current trust level and exits with `CarrelError` otherwise. Claude calls it before mutations. Spec-and-build before delegated/partnership are recommended to a researcher.

This is the "next setup-state" — converts a markdown control plane into a code boundary with the Pydantic model as gatekeeper.

#### A2. Sensitivity routing — second pass beyond B4 stopgap

Make `sensitivity` a load-bearing input to the router. Either:
- **Option A (additive)**: keep both `sensitivity` and `cloud_consent` as inputs to `policy.is_cloud_consented(tool, sensitivity, cloud_consent)`. Document the matrix.
- **Option B (subtractive)**: deprecate `cloud_consent` and let `sensitivity` (LOW=cloud-OK, MEDIUM=ask, HIGH=local-only) be the single gate.

Either way, propagate the new policy module through `convert/router.py` and `transcribe/router.py`, replace direct `is_cloud_consented` calls. Surface the routing decision in CLI output (`--explain` flag, like `apt-get`).

#### A3. Profile sync source-of-truth

Decide whether each of the four mirror surfaces (`CLAUDE.md`, `_meta/my-environment.md`, `_meta/cheat_sheet.md`, `_meta/automation-prompt.md`) is:
- Generated from `environment.json` deterministically, OR
- Hand-maintained by Claude, with an explicit "stale check" that warns when out of sync

For each generated surface, add a regenerator command (we already have `carrel vault cheatsheet`; we need equivalents for `my-environment.md` and `automation-prompt.md`). For each hand-maintained surface, add a `carrel vault check-sync` that diffs the surface against environment.json and surfaces drift.

Likely scope: 2 new CLI commands + 1 audit command. Significant work but solves Codex's predicted Bug Class 3.

#### A4. Path containment + slugification

`carrel vault new <name>` (`src/carrel/cli/vault.py:41-64`) needs `name` slugified before joining to the vault path. Filers (`convert/filer.py`, `transcribe/filer.py`, `vault/scaffold.py`) need a final `resolve()` + ancestor check before write. One small `safe_vault_join(vault, *parts)` helper solves both.

#### A5. Date validators + AutomationConfig consistency

`AutomationConfig.last_reviewed` and `ResearcherProfile.wiki_proposal_deferred_until` should get the same `pattern=r"^\d{4}-\d{2}-\d{2}$"` treatment SetupState got in v0.5.3. Three lines of model code, plus tests.

#### A6. Decide ConvertOptions/TranscribeOptions/`hardware`/`sensitivity` parameter fate

Two paths:
- **Delete**: `ConvertOptions`, `TranscribeOptions`, the `hardware` and `sensitivity` parameters on routers. They're parametric ghosts. Future contributors keep mistaking them for load-bearing.
- **Use**: make routers actually consume them (relates to A2 sensitivity routing).

Pick one, do it.

#### A7. Cheatsheet template source-of-truth

`skills/environment-setup/references/cheatsheet-template.md` documents a fictional Mustache renderer. Three options:
- **Delete the file** + add a one-line pointer in SKILL Step 8: "the cheat sheet renderer lives in `src/carrel/vault/templates.py:render_cheat_sheet()` — see source for the current sections"
- **Rewrite it** as a faithful description of what `render_cheat_sheet` actually emits in v0.5.3 (Setup, Folders, Configured tools, Common workflows, Next steps)
- **Implement it** — refactor `render_cheat_sheet` to load this file as a Jinja/Mustache template

Recommended: option 2 (rewrite).

#### A8. Hardware-audit reference doc rewrite

`skills/environment-setup/references/hardware-audit.md` documents a JSON schema that doesn't match the actual `AuditResult` Pydantic model. Run `carrel env doctor --format json` against any vault and copy the output as the canonical example.

---

### TIER 2 — Documentation Coherence

These are all doc-only; ~2 hours total per the doc audit's estimate.

- **S1**: `decision-tree.md:7-20` — replace `bootstrap.sh` framing with `install.sh`/`install.ps1`
- **S2**: `decision-tree.md:400-418`, `environment-setup/SKILL.md:147-152`, `obsidian-setup.md` — add OS-branched Obsidian install (covered also by B5 above; B5 is the user-impact framing, S2 is the surface-by-surface fix)
- **S3**: `interview-protocol.md:118-125` — show full eight AutomationConfig booleans OR add the "Pydantic backfills defaults" comment
- **S4**: `docs/self-setup-guide.md:80-90` — add Windows + Linux Obsidian rows
- **S5**: `vault-ops/SKILL.md:21-35` — add `_meta/local/` and `_meta/reflections/` to vault diagram
- **S6**: `agents/setup-interviewer.md:67` — note AutomationConfig truncation rationale
- **S7**: `commands/carrel-setup.md` Phase numbers vs `environment-setup/SKILL.md` Step numbers — pick one convention, align
- **S8**: `commands/carrel-migrate.md:39` — write `plugin_version` (not `version`); align with CLAUDE.md + check-version.js
- **S9**: `environment-setup/SKILL.md:222` — clarify which legacy scripts were removed (the `scripts/` ones, NOT the live `hooks/check-environment.js`)
- **S10**: `commands/carrel-share.md:81` — either implement `--quick` mode detection in the SKILL OR rename the section
- **S11**: `obsidian-setup.md` — delete (orphan) or fold into decision-tree.md
- **S12**: `toolchain-guide.md:35-42` — remove the stale `environment.json.data_types` reference

---

### TIER 3 — Code Hygiene

#### Behavioral fixes

- **H1**: Transcript idempotency — drop date from filename OR move hash check ahead of date-based path lookup (`transcribe/filer.py:31-37`)
- **H2**: `--speakers` — thread through `_transcribe → coli` adapter OR remove the option + update SKILL doc (`cli/transcript.py:101,108`, `transcribe/adapters/coli.py`)
- **H3**: `gws` adapter raises wrong error type for auth failure (`google/export.py:103-119`)
- **H4**: HTTP adapter response.json() guards + raise_for_status (mineru.py, groq.py, gemini.py)
- **H5**: `youtube_captions.py:53` — replace broad `except Exception` with typed `TranscriptsDisabled`/`NoTranscriptFound`/`VideoUnavailable` matching
- **H6**: `vault status --format quiet` — print something or remove the QUIET branch
- **H7**: Migration nag-spam debouncer — stamp `last_acknowledged` in plugin-state, show prompt at most once per N hours
- **H8**: Cloud_consent display in hook banner — render boolean as text (`'cloud OK'` / `'prefer local'`) rather than raw `true`/`false`
- **H9**: `consent.py:7` use enum values from `ConvertTool`/`TranscribeTool` instead of string literals; add `gws` to cloud set if it should be there
- **H10**: `_transcribe` unreachable-error message uses wrong tool name (`cli/transcript.py:33-52`)

#### Refactor / dedup

- **H11**: Single YouTube URL parser module (currently 3 implementations across router/organize/youtube_captions)
- **H12**: Single `source_hash` helper (currently twin definitions in convert/filer + transcribe/filer)
- **H13**: Twin `templates/` directories — confirm `skills/vault-ops/templates/` is a stale copy; delete it; verify code reads only the root `templates/` (current evidence: yes)
- **H14**: 12 empty `catch {}` in `check-environment.js` — log to stderr with `carrel-hook:` prefix; OR explicitly comment why each is acceptable
- **H15**: Pure pass-through wrappers in `paper.py`/`transcript.py` — delete and call underlying functions directly
- **H16**: Triple re-export of `resolve_cloud_consent`/`resolve_vault` in `cli/main.py` + `cli/__init__.py`
- **H17**: Dead doctest scaffolding in `env/install.py` — convert to real `tests/test_install.py` OR enable `--doctest-modules` globally
- **H18**: `install.sh` ↔ `install.ps1` step 1 alignment + `bootstrap.sh` runtime deprecation banner

#### Test coverage

- **H19**: Add tests for the 6 untested CLI commands (`vault new`, `vault search`, `vault status`, `vault organize`, `paper list`, `transcript list`)
- **H20**: Add malformed-profile tests for the 4 leaky CLI commands (covered by B3 fix verification)

---

### TIER 4 — Strategic considerations (Codex §5)

Not for this cycle, but worth a planning doc:

- **Telemetry/observability**: Imperial deployment will surface bugs that current ephemeral-stderr error handling can't help debug. Consider a structured failure log (`.carrel/telemetry.jsonl`) the researcher can opt into and that the doctor agent (spec 006) can inspect.
- **Offline mode**: no repo-level "air-gapped" control plane. Network-dependent paths are scattered. A `carrel env doctor --offline-check` would surface them.
- **Vault export/import**: no `carrel vault export` / `carrel vault import` for moving between Imperial-managed and personal devices. Real gap for academics.
- **Dashboard regenerator**: `_meta/my-environment.md` is presented as a "living dashboard" but only scaffolded once. Needs a `carrel vault dashboard --regenerate` (subset of A3).
- **Recovery/snapshot story for assistant-written markdown**: delegated/partnership trust authorizes vault mutations with no first-party undo beyond Obsidian's file-recovery plugin and per-prompt session checkpoints. Worth a planning doc.
- **`.carrel/exports/` retention story**: Google Doc raw exports are stored and never cleaned. Sensitive content lingers silently.

---

## Execution Order

For a Codex-delegable next sprint, suggested commit sequence:

1. Commit: B1 + B2 + B3 batched (Tier 0 quick fixes, ~30 min)
2. Commit: B4 stopgap (Tier 0, sensitivity = HIGH blocks cloud)
3. Commit: B5 (skill cross-platform propagation)
4. Commit: A4 path containment + slugification
5. Commit: A5 date validators
6. Commit: A6 + A7 + A8 (decisions on parametric ghosts + cheatsheet template + hardware-audit doc)
7. Commit: Tier 2 documentation batch (~2 hours, single commit)
8. Commit: Tier 3 hygiene batch 1 (behavioral fixes H1-H10)
9. Commit: Tier 3 hygiene batch 2 (refactor/dedup H11-H18)
10. Commit: Tier 3 test coverage H19-H20

Defer to spec work (NOT this sprint):
- A1 (trust enforcement) → spec 008-trust-enforcement.md
- A2 (sensitivity routing second pass) → spec 010-policy-module.md  
- A3 (profile sync) → spec 011-profile-sync-architecture.md
- Tier 4 → individual planning docs

After Tier 0+1: bump 0.5.3 → 0.5.4.
After Tier 2+3: bump to 0.5.5 (or fold into 0.6.0 if spec 007 implementation also lands).

---

## Cross-Audit Cross-Calibration Notes

- **Code-quality C1 (read_profile boundary) and Codex's "narrative shadow state"** point at the same root cause from different angles. The error contract leaks because Python doesn't own the read; the read happens in a place that CarrelError doesn't catch. Same mechanism that lets profile state drift across surfaces lets exceptions drift across boundaries.
- **Plugin B2 (`/carrel-research` doesn't exist) and Doc H4 (cheatsheet-template.md is fictional)** are the same drift in different layers: the renderer documents a future state; the template documents a fictional past state. They're both signs that `render_cheat_sheet`'s contract was never written down.
- **Codex's "trust enforcement gap" and the Sensitivity routing gap** are the same architectural pattern: a Pydantic field that's stored but ignored at the policy boundary. A `carrel/policy.py` module that owns both (read trust_level + sensitivity, return go/no-go) would close both with one abstraction.

---

## Out of Scope for This Cycle (deferred)

- Full spec 006 implementation (still upstream-research-blocked)
- Full spec 007 implementation (still upstream-research-blocked)
- ItDepends integration
- Knowledge wiki improvements
- Tier 4 strategic items (each gets own planning doc)

These don't gate Imperial deployment; the Tier 0-3 work in this audit does.
