# 014 Implementation Audit — Synthesis + Fixes Applied

**Date**: 2026-05-17
**Trigger**: pre-commit audit of v0.9.0 working tree
**Reviewers**: 4 parallel (plugin-validator, code-reviewer, kimi-review, codex-rescue)
**Baseline state**: 4-implementer parallel build complete; 275 tests passing; nothing committed
**Final state**: 279 tests passing; ready to commit

This is the consolidated audit trail. Individual reports for plugin-validator and codex are saved at `014-impl-review-plugin-validator.md` and `014-impl-review-codex.md`. Code-reviewer and kimi findings are captured in this synthesis (they returned findings inline rather than writing files).

---

## Verdict matrix

| Reviewer | Verdict | Severity peaks |
|---|---|---|
| plugin-validator | valid-with-warnings | 2 WARN, 3 INFO |
| code-reviewer | fix-first | 1 HIGH, 2 MED, 4 LOW |
| codex | fix-first | 1 HIGH, 4 MED |
| kimi | concern (fix-first) | 2 HIGH, 4 MED |

**Convergent issues** (≥2 reviewers): hook JSON shape (plugin-validator + code-reviewer with CC docs sources).
**Single-source HIGH issues**: kimi caught all 6 skill→CLI contract mismatches the other 3 missed (different lens — kimi reads the contract between markdown skills and Python CLI, which the others didn't).

---

## Fixes applied

### HIGH

**H1 — Hook JSON shape (plugin-validator + code-reviewer)**

`hooks/inject-context.js` and `hooks/sensitivity-gate.js` emitted decisions at top-level JSON. CC requires `hookSpecificOutput` nesting with `hookEventName`. Without the fix, both hooks would silently no-op — the per-turn context never injects, and the sensitivity gate never fires.

- `hooks/inject-context.js` — wrapped `additionalContext` in `{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext}}`
- `hooks/sensitivity-gate.js` — wrapped `permissionDecision` + `permissionDecisionReason` in `{hookSpecificOutput: {hookEventName: "PreToolUse", ...}}`

Both reviewers cited https://code.claude.com/docs/en/hooks and the Anthropic plugin-dev hook-development skill as sources.

**H2 — `automate configure` rejected 7 capability boolean flags (kimi)**

`skills/automation/SKILL.md`'s calling pattern documented `--inbox-processing`, `--vault-health`, `--cross-linking`, `--gap-analysis`, `--draft-feedback`, `--reflection-synthesis`, `--wiki-maintenance`. CLI only had `--enabled`, `--trust-level`, `--schedule`, `--review-cadence`, `--model`. Skill-constructed invocations would fail with Typer "no such option."

- `src/carrel/cli/automate.py` — added 7 `Optional[bool]` flags with `--flag/--no-flag` syntax. Default `None` means "preserve existing profile value." Lock-the-contract test added at `tests/test_automate_cli.py::test_automate_configure_accepts_capability_boolean_flags`.

**H3 — `feedback exporter` never read `_meta/reflections/` (kimi)**

`session-reflection` skill states "the CLI reads `_meta/reflections/` and `_meta/friction_log.md`." The CLI only walked `friction-log/` and `capability-log/`. Researchers expecting reflections in their feedback digest would get none.

- `src/carrel/feedback/exporter.py` — added `REFLECTIONS_DIR = "reflections"` to the directory sweep. Test fixture extended to seed a reflection file; assertion added that reflection content appears in digest.

### MED

**M1 — Hook output paths used `process.cwd()` instead of walking up (code-reviewer)**

`hooks/inject-context.js` read `.carrel/environment.json` from `process.cwd()` only. When CC opens in a vault subdirectory (e.g., `vault/papers/foo/`), the hook silently no-ops. Inconsistent with `check-environment.js` which has `findCarrelRoot()`.

- `hooks/inject-context.js` — copied `findCarrelRoot()` from `check-environment.js`; all path reads now anchor to the resolved vault root.

**M2 — Sensitivity-gate shell-truncation naive (codex)**

The truncation regex `/\s(&&|\|\||;|\|)\s/` required whitespace around operators and didn't handle quotes. A quoted path with ` && ` could pass through to the `--explain` subprocess and fail, leading to silent pass-through of the original cloud command.

- `hooks/sensitivity-gate.js` — replaced naive truncation with a stricter rule: if the carrel-invocation tail contains any of `; & | < > \` $`` `, the hook passes through silently. `execFileSync` already prevents shell-injection (no shell), but the reject path catches naive-split breakage. Researchers can append `# bypass-gate` for commands that legitimately need operators.

**M3 — Pending-decisions double-write on rerun (codex)**

`_append_pending_decision` always appended a new row. Re-running the same unattended batch would stack duplicate checklist rows.

- `src/carrel/cli/batch.py` — dedupe by exact row match (date + body). Test added at `tests/test_batch_cli.py::test_batch_convert_unattended_deduplicates_pending_decisions`.

**M4 — Migration doc didn't warn about skill-driven invocation (codex)**

The migration doc said the slash command surface was preserved but didn't explain that direct invocation (no skill orchestration) errors for several commands. `/carrel-mirror` is the concrete breakage: direct invocation hits a CLI requiring `--write --from-stdin`.

- `migrations/0.8.1-to-0.9.0.md` — added "How the 7 shrunk commands work now" section + "Debugging hooks" section with `CARREL_HOOK_DEBUG=1` instructions.

**M5 — Silent hook failures undiagnosable (codex)**

Both new hooks suppressed all errors with no stderr, file log, or debug flag. `check-environment.js` does log to stderr unconditionally — regression in diagnosability.

- Both `hooks/inject-context.js` and `hooks/sensitivity-gate.js` — added opt-in stderr logging via `CARREL_HOOK_DEBUG=1` env var. Logs prefixed `[carrel:<hook-name>] <reason>`.

**M6 — `reflect-log` path mismatch (kimi)**

Skill: `_meta/reflections/reflection-YYYY-MM-DD.md` from `_templates/reflection.md`. CLI: `_meta/reflect-log/<YYYY-MM-DD>.md` with hardcoded header. Mirror + feedback-export both expect to read reflections at the skill's path — without alignment, those files would never find them.

- `src/carrel/cli/vault.py` reflect-log — path corrected; seeds from vault's `_templates/reflection.md` on first write of day if present (else minimal header). Test path assertion updated.

**M7 — Mirror filename daily instead of monthly (kimi)**

Skill contract: `_meta/mirror/YYYY-MM.md` with same-month idempotency. CLI wrote `_meta/mirror/YYYY-MM-DD.md` daily — idempotency broken (re-run on different day creates new file). Spec text was also wrong here (had `YYYY-MM-DD`). Implementer A correctly noted following spec, but spec was the error vs legacy + skill convention.

- `src/carrel/cli/vault.py` mirror — date format changed to `%Y-%m`. Spec corrected at the same time. Test path assertion updated.

**M8 — Feedback-digest output path mismatch (kimi)**

Skill: `_meta/feedback-digest-YYYY-MM-DD.md` (flat file in `_meta/`). CLI: `_meta/feedback-export/<YYYY-MM-DD>.md` (in subdirectory). Researcher or automation prompt looking at the skill-documented path wouldn't find the file.

- `src/carrel/cli/vault.py` feedback-export — path corrected. Test path assertion updated.

**M9 — `batch transcribe` missing `--kind` + 3 audio extensions (kimi)**

Skill documents `--kind interview|meeting|lecture|recording` and lists `.mov .ogg .flac` among audio extensions. CLI lacked `--kind` (typer would reject) and `AUDIO_EXTENSIONS` was missing the three formats (silently skipped).

- `src/carrel/cli/batch.py` — added `--kind` Option, forwarded to each `carrel transcript create` subprocess. Extended `AUDIO_EXTENSIONS` to include the three formats. Lock-the-contract tests added: `test_batch_transcribe_forwards_kind_flag`, `test_batch_transcribe_recognizes_extended_audio_extensions`.

### Deferred / declined

**`PreToolUse "ask"` value uncertainty (plugin-validator)** — Validator flagged that only `"allow"`/`"deny"` are publicly documented, but `"ask"` is widely used in CC plugin ecosystem and matches the spec's intent for the MED-sensitivity case. Code-reviewer didn't flag this. Leaving as `"ask"`; if it proves to silent-no-op, switch to `"allow"` with a stderr warning prepended in a follow-up.

**SessionEnd 10s timeout (plugin-validator INFO)** — Low risk; existing hook, not in v0.9.0 scope.

**`marketplace.json` `keywords` == `tags` (plugin-validator INFO)** — Intentional; some marketplace UI variants honor one or the other.

**`/carrel-mirror` reaching research-partner agent (codex HIGH)** — Codex flagged `agents/research-partner.md` description doesn't mention mirror. But slash commands don't dispatch agents directly — they invoke skills via description triggers. `skills/research-partner/SKILL.md:3` already has `/carrel-mirror`, `mirror`, `self-portrait` in its trigger phrases. SKILL discoverability is the load-bearing path; agent file is for `@research-partner` invocation which is a different surface. Addressed via migration-doc note about skill-driven vs direct invocation rather than modifying the agent.

**`synthesizer.py` cosmetic `redactions_applied` entries (code-reviewer LOW)** — Touches a niche test path; existing test passes. Defer.

**`reflect-log` concurrency safety (code-reviewer LOW)** — Single-user CLI; not a real concern.

**`automate.py` atomic-write helper duplication (code-reviewer LOW)** — Could share with `env/profile.py:write_profile` in a future cleanup pass.

---

## Test outcomes

- Baseline before audit: 275 passing
- After fixes + new lock-the-contract tests: **279 passing** (added test_automate_configure_accepts_capability_boolean_flags, test_batch_convert_unattended_deduplicates_pending_decisions, test_batch_transcribe_forwards_kind_flag, test_batch_transcribe_recognizes_extended_audio_extensions)
- Hook smoke tests: silent on no-op paths; metacharacter rejection verified; `CARREL_HOOK_DEBUG=1` produces expected stderr.

---

## What the audit caught that the planning process didn't

1. **Spec→implementation skill contract drift**. The spec text for several deliverables was less prescriptive than the skill prose authored later in the same release. Parallel implementers each followed slightly different sources of truth. **Future**: in any release that ships skill + CLI changes for the same surface, add a spec section explicitly enumerating the file paths + flag set both must agree on, and a CI test that runs skill files through a grep-and-match against the CLI's `--help`.

2. **CC hook protocol details aren't in spec 014**. The `hookSpecificOutput` requirement isn't carrel-specific; it's standard CC contract. The spec assumed implementer familiarity. **Future**: link the CC hooks reference from any spec that adds new hook event handlers; perhaps a `references/cc-hook-output-schema.md` for the writing-team workflow.

3. **Adversarial-reviewer convergence is a quality signal**. The hook JSON issue surfaced in two reviewers independently with CC docs cited; that's strong signal compared to one-reviewer-only flags. Pattern worth replicating: dispatch ≥3 reviewers, give weight to convergent findings.

4. **Kimi's skill↔CLI contract lens is unique**. The other 3 reviewers focused on code quality, plugin structure, and adversarial attack surface. Kimi was the only one reading both skill markdown AND CLI surface and asking "do they agree?" Worth keeping kimi-review in any audit that touches both layers.

---

## Sign-off

All HIGH and MED findings addressed. 279 tests green. Hooks smoke-tested. Spec + migration doc updated to match the contracts the CLI now implements.

Ready to commit as v0.9.0.
