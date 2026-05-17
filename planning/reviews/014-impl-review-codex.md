FIX-FIRST - v0.9.0 has useful CLI extraction, but `/carrel-mirror` can strand its rehomed prose and both new hooks fail closed only by disappearing, which is too opaque for a release.

## Q1 - Hook Attack Surface

Severity: MED. No direct shell-injection path found in the hook re-execution: `hooks/sensitivity-gate.js:60-64` uses `execFileSync('carrel', args, ...)`, not a shell, so `$()`, backticks, `;`, `&&`, and redirection are passed as argv text rather than executed. But the truncation is not sufficient as a gate parser: `hooks/sensitivity-gate.js:52-55` claims "unquoted" terminators while using `/\s(&&|\|\||;|\|)\s/` plus `tail.split(/\s+/)`, which ignores quotes and misses operators without surrounding spaces. A quoted path containing ` && ` can make the hook's `--explain` subprocess fail, then `hooks/sensitivity-gate.js:65-66` silently passes the original cloud command. Fix: parse shell syntax with a real tokenizer or reject ambiguous shell metacharacters instead of best-effort splitting.

## Q2 - Prose Homes

Severity: HIGH. `/carrel-feedback` is probably reachable because `skills/session-reflection/SKILL.md:2-3` explicitly names `/carrel-feedback`, and the wrapper is only `!carrel vault feedback ${ARGS}` at `commands/carrel-feedback.md:1-5`. Mirror is not reliably activated in the file the task identified: `agents/research-partner.md:3-4` triggers on generic thinking phrases only, with no `/carrel-mirror`, "mirror", or "self-portrait". The wrapper itself is just `!carrel vault mirror ${ARGS}` (`commands/carrel-mirror.md:1-5`), while the CLI errors unless `--write --from-stdin` is supplied (`src/carrel/cli/vault.py:440-468`). There is mirror prose in `skills/research-partner/SKILL.md:116-123`, but not in the agent. Fix: add mirror trigger/prose to the agent or make `/carrel-mirror` explicitly route to the skill before shelling out.

## Q3 - `migrate apply --plugin-root`

CLEAR - outside Claude Code, missing `$CLAUDE_PLUGIN_ROOT` raises `CarrelError("Plugin root not specified")` with the hint to pass `--plugin-root` or set the env var (`src/carrel/cli/migrate.py:19-28`), and the test covers that path (`tests/test_migrate_cli.py:85-95`).

## Q4 - `automate configure` Trust Gate

CLEAR - advisory denial is tested at `tests/test_automate_cli.py:66-93`; implementation gates on `automation:propose` (`src/carrel/cli/automate.py:27-31,77-90`) and emits an actionable "Raise trust to consultative" hint. The tests assert denial, current/required trust, unchanged profile, and action name, though not the exact hint text.

## Q5 - Batch Pending-Decisions Contract

Severity: MED. In unattended mode, only failures/timeouts and empty URL lists are written to `_meta/pending-decisions.md` (`src/carrel/cli/batch.py:130-144,166-178,188-208`); successful subprocesses are marked converted/transcribed and never recorded (`src/carrel/cli/batch.py:136-139,198-201`). That contract is coherent, but idempotency for pending decisions is absent: `_append_pending_decision` always appends a new checklist row (`src/carrel/cli/batch.py:89-96`), and tests only assert creation/content, not no duplicate on rerun (`tests/test_batch_cli.py:57-84,120-144`). Fix: dedupe by file/source plus reason, or include stable IDs and update existing open rows.

## Q6 - Silent Failure Modes

Severity: MED. Both new hooks suppress all internal errors with no stderr, file log, or debug flag. `inject-context` returns on missing/malformed env and swallows top-level exceptions (`hooks/inject-context.js:16-24,59-63`). `sensitivity-gate` ignores malformed payloads, suppresses `carrel --explain` stderr via `stdio: ['ignore','pipe','ignore']`, and returns on subprocess failure (`hooks/sensitivity-gate.js:31-66,93-97`). Existing hooks do log to stderr (`hooks/check-environment.js:73-75`), so this is a regression in diagnosability. Fix: add opt-in debug logging, e.g. `CARREL_HOOK_DEBUG=1`, and log hook/subprocess failures to stderr.

## Q7 - `additionalContext`

CLEAR - unverified in Claude Code consumption, but the hook sends JSON with `additionalContext` containing `Carrel vault context:`, sensitivity/cloud consent/trust from `.carrel/environment.json`, and optionally the newest brief title from `_meta/briefs/` (`hooks/inject-context.js:26-35,38-55`).

## Q8 - Migration Doc Gaps

Severity: MED. The migration doc says the slash command surface is preserved (`migrations/0.8.1-to-0.9.0.md:47-51`) and lists prose rehomes (`migrations/0.8.1-to-0.9.0.md:68-76`), but it does not warn that several preserved commands now require skill-built `${ARGS}`, stdin, or redact-list setup. `/carrel-mirror` is the concrete breakage: direct invocation reaches a CLI that requires `--write --from-stdin` (`src/carrel/cli/vault.py:460-468`). Fix: add an upgrade note distinguishing natural-language/skill-driven use from raw slash-command invocation, plus a short debugging note for silent hook failures.
