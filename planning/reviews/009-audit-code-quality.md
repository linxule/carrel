# 009: Holistic Code Quality Audit

**Date**: 2026-04-20
**Reviewer**: Internal `code-reviewer` agent (confidence-filtered: HIGH+MEDIUM only)
**Scope**: Whole repo at `/Users/xulelin/Documents/Apps/mcp/carrel/`. Excluded: documentation surfaces (separate audit at `009-audit-documentation.md`) and plugin-surface integrity (separate audit at `009-audit-plugin-surface.md`).

**One-line:** Subprocess and version-consistency hygiene are excellent; the real damage is in error-boundary discipline (raw `ValidationError` and `JSONDecodeError` escape ~6 CLI commands), one broken hook (`session-reflect.js` reads only the legacy nested profile shape), one true idempotency gap (date-stamped transcript filenames defeat the SHA hash), and a thick layer of dead code in `models.py`/`paper.py`/`transcript.py`.

**Verdict**: Ship-quality core, but the CLI's error contract is leaky in ways the v0.5.0→v0.5.3 sprint did not catch. Two HIGH findings should be fixed before any wider deployment beyond your own use.

---

## Critical (fix before deployment)

### C1. `read_profile()` raises `pydantic.ValidationError` / `json.JSONDecodeError` past CLI error guards

**Files**: `src/carrel/env/profile.py:13-19`; consumed by `src/carrel/cli/paper.py:60`, `src/carrel/cli/transcript.py:111`, `src/carrel/cli/google.py:35`, `src/carrel/cli/env.py:61`.

`read_profile()` does `ResearcherProfile.model_validate(json.loads(path.read_text(...)))` with no exception wrapping. The four CLI commands above only catch `CarrelError`. A corrupted or stale `.carrel/environment.json` (e.g. an old install whose schema drifted, or a partial write) crashes any of `carrel paper convert`, `carrel transcript create`, `carrel google export`, `carrel env profile` with a raw Python traceback.

The A7 fix (`vault cheatsheet`) wrapped its inline `model_validate_json` call (vault.py:156-162). The systemic fix is to wrap inside `read_profile()` itself: catch `(ValidationError, json.JSONDecodeError, OSError)`, raise a `CarrelError("Could not parse <path>", hint="Run /carrel-setup to regenerate it.")`.

Test gap: only `test_vault_cli.py` exercises the malformed-profile path. None of the four leaky commands has a malformed-profile test.

### C2. `session-reflect.js` is dead for every researcher on the canonical (flat) profile shape

**File**: `hooks/session-reflect.js:90-93`.

Code: `const researcher = env.interview?.researcher; if (!researcher) { process.exit(0); }`.

The current canonical profile shape, written by `carrel vault init` via the Python `ResearcherProfile`, is FLAT (`env.name`, `env.field`, etc.) — there is no `env.interview`. `check-environment.js:271-281` correctly handles both shapes. `session-reflect.js` checks only the legacy nested shape, so for every vault scaffolded post-v0.5.x, the SessionEnd hook silently exits with no goodbye, no stats, no reflection prompt. The remediation block, the "See you next time" message, the vault stats, and the `/carrel-reflect` nudge — all dead.

**Fix**: mirror the flat-OR-nested fallback used by check-environment.js (lines 283-287). Read `env.name || env.interview?.researcher?.name` and proceed if either is present.

---

## Important (HIGH-confidence)

### I1. Transcript idempotency breaks across day boundaries

**Files**: `src/carrel/transcribe/filer.py:31-37`, `src/carrel/cli/transcript.py:112-116`.

`file_transcript` builds `output_path` using `transcript_filename(source=..., date=date.today().isoformat(), ...)` — the destination filename embeds today's date. The SHA-256 source_hash check at line 51 only fires if the filename matches an existing file. Re-running the same audio at 23:59 vs 00:01 produces a different output path, so the hash check never runs and a duplicate transcript is written under tomorrow's date.

Compare `file_paper` (filer.py:25-30): destination dir is derived from author/year/title, stable across days, hash check works.

**Fix**: drop `date` from the filename or move the hash check ahead of the date-based path lookup (search by source-hash across the `transcripts/` glob).

### I2. `--speakers` is silently dropped

**File**: `src/carrel/cli/transcript.py:101, 108`.

The flag is declared (`speakers: int | None = typer.Option(None, "--speakers")`) and immediately discarded (`_ = speakers`). The `coli` adapter (`transcribe/adapters/coli.py:10-16`) takes only `model` and `json_output`, never `speakers`. Yet `skills/transcribe/SKILL.md:35` documents it: *"For speaker diarization, pass `--speakers N` … coli uses this to improve speaker separation."* That promise is not delivered.

**Fix**: either thread `speakers` through `_transcribe → transcribe_with_coli → coli` CLI args, or remove the option and update the skill doc.

### I3. Dead `ConvertOptions` / `TranscribeOptions` / `update_profile`

**Files**: `src/carrel/models.py:71-99` (`ConvertOptions`, `TranscribeOptions`), `src/carrel/env/profile.py:31-37` (`update_profile`).

Zero importers anywhere in `src/`, `tests/`, `hooks/`, or skills. Originally specified in `planning/specs/001-*` as the request DTOs that the CLI would build, but the CLI evolved to pass arguments positionally and the models are vestigial. Their presence misleads anyone reading `models.py` for the data contract.

**Fix**: delete them (they are part of the public Python API surface, but nothing depends on that surface today). Or, if you want to keep them, refactor the CLI commands to actually construct them — currently both worlds exist.

### I4. `ensure_gws_authenticated` raises the wrong error type

**File**: `src/carrel/google/export.py:103-119`.

When `gws drive about get` returns non-zero, it raises `ToolNotInstalled("gws", "brew install googleworkspace-cli && gws auth login -s drive")`. But "not installed" already returned earlier via `_run_gws`'s `FileNotFoundError` branch. The non-zero-return case is actually "installed but not authenticated" or "auth expired". The hint conflates two recovery paths and tells installed users to reinstall.

**Fix**: raise `ConversionError("gws not authenticated", hint="Run: gws auth login -s drive")` instead.

### I5. Pure pass-through wrappers in `paper.py` and `transcript.py` add only type-erasure

**Files**: `src/carrel/cli/paper.py:27-44` (`_select_convert_tool_only`, `_run_convert_pipeline`), `src/carrel/cli/transcript.py:55-91` (`_run_transcribe_pipeline`, `_select_transcribe_tool_only`).

All four wrappers do nothing but `await` the underlying pipeline function with the same args, and they DROP type annotations on the way through (paper.py:30, paper.py:40, transcript.py:58, transcript.py:79 all type `profile` as bare untyped — the underlying `convert/pipeline.py` and `transcribe/router.py` use `ResearcherProfile | None`). The wrappers exist only because the caller renamed the imports with `_for_file` suffixes.

**Fix**: delete the wrappers, call `select_convert_tool_only` / `run_convert_pipeline` / `select_transcribe_tool` directly. The aliases in the import block (`select_convert_tool_only as select_convert_tool_only_for_file`) are also unused once wrappers go.

### I6. `_transcribe`'s unreachable error has the wrong message

**File**: `src/carrel/cli/transcript.py:33-52`.

The dispatch at lines 35-51 exhaustively handles all four `TranscribeTool` enum values. Line 52's fallback `raise ToolNotConfigured("gemini", "GEMINI_API_KEY (required for YouTube transcription)")` is unreachable today, but if a 5th tool is added without updating `_transcribe`, the user sees a misleading "gemini not configured" message. Should be a generic `CarrelError(f"Unknown transcribe tool: {tool}")`.

While here: timeout heuristic at line 34 lengthens (300s) for `{COLI, GEMINI}` but not `GROQ`. GROQ is a network call processing the same kind of audio file, often long lectures — the asymmetry seems unintentional.

### I7. Cloud HTTP adapters skip `raise_for_status()` and don't guard `response.json()`

**Files**: `src/carrel/convert/adapters/mineru.py:14-21`, `src/carrel/transcribe/adapters/groq.py:14-27`, `src/carrel/transcribe/adapters/gemini.py:24-43`.

All three check `if response.status_code >= 400`, then call `response.json()` unconditionally. A 200 OK with non-JSON body (rate-limit HTML page, captive portal, proxy interstitial) crashes with raw `json.JSONDecodeError`. Plus all three call `file.read_bytes()` synchronously before entering the `async with` block (mineru.py:12, groq.py:12), blocking the event loop on large PDFs/audio.

**Fix**: `try: payload = response.json() except ValueError: raise ConversionError/TranscriptionError("Non-JSON response", hint=…)`. For the sync-IO concern: read bytes once, before the client open, into a local var (you already do that — but it blocks before you await). For Carrel's usage pattern (single-file CLI invocation) this is OK; for any future MCP server use it is not.

### I8. Dead doctest scaffolding in `env/install.py`

**File**: `src/carrel/env/install.py:60-71`.

`__test__ = {"install_command_for": """ >>> ... """}` is a Python doctest finder hook, but `pyproject.toml` has no `--doctest-modules` in `addopts` and no `conftest.py` enabling doctests. So this string is never executed. It looks like a test but is documentation that nobody runs.

**Fix**: either add `addopts = "--doctest-modules"` (and accept the cost of doctesting all modules), or delete `__test__` and convert the cases to a real `tests/test_install.py` (which doesn't exist yet — install.py has zero coverage for the platform-fallback logic).

---

## Medium

### M1. Six CLI commands have zero test coverage

`vault new`, `vault search`, `vault status`, `vault organize`, `paper list`, `transcript list` (vault.py:42-138, paper.py:117-131, transcript.py:171-185).

`paper convert` itself has no integration test (`tests/test_paper_cli.py` does not exist), only the underlying filer is tested.

Capture's `_capture_slug` / `_capture_path` derivations have no unit tests — only the CLI happy path and one fallback path are exercised.

### M2. Three different YouTube URL parsers in three modules

- `src/carrel/transcribe/router.py:10-15` (`_is_youtube_url`)
- `src/carrel/vault/organize.py:75-83` (`_youtube_slug`)
- `src/carrel/transcribe/adapters/youtube_captions.py:11-29` (`extract_youtube_video_id`)

All parse YouTube URLs, none share code, only `extract_youtube_video_id` handles `/embed/`, `/shorts/`, `/live/`. Consolidate into one module (`transcribe/youtube_url.py`) with `is_youtube_url`, `extract_video_id`, `slug_for_filename` and import everywhere.

### M3. JS hook nag spam after version bump

**File**: `hooks/check-environment.js:323-328` + `commands/carrel-migrate.md:36-43`.

`checkVersion` returns `needsMigration: true` and the hook prints "Carrel updated: X → Y. Run /carrel-migrate" every session until the user runs `/carrel-migrate`, which is the only thing that updates `plugin-state.json`. If the user ignores the prompt, every session-start prints it. Either stamp `plugin_version` in plugin-state from the hook with a `last_acknowledged` field, or accept the design but add a debouncer (don't show more than once per N hours).

Same file: `state.plugin_version || state.version` (check-version.js:33). `/carrel-migrate` writes `version`. Standardize on `plugin_version` (the field name CLAUDE.md documents).

### M4. `consent.py` uses string literals instead of enum values

**File**: `src/carrel/consent.py:7`.

`if tool and tool in {"mineru", "groq", "gemini"}:`. Caller passes `tool.value` from `ConvertTool` / `TranscribeTool` enums. If a new cloud tool enum value is added, this set silently misses it. Change to a single source of truth: `from carrel.models import ConvertTool, TranscribeTool; CLOUD_TOOLS = {ConvertTool.MINERU.value, TranscribeTool.GROQ.value, TranscribeTool.GEMINI.value}`. Note: `gws` (Google Workspace, a cloud API) is also not in this set — by design or by oversight?

### M5. `ResearcherProfile` and `AutomationConfig` accept any string for date fields

**File**: `src/carrel/models.py:179-186` (`wiki_proposal_deferred_until`), `src/carrel/models.py:146` (`AutomationConfig.last_reviewed`).

Both are `str | None`. `SetupState` got the `pattern=r"^\d{4}-\d{2}-\d{2}$"` treatment in v0.5.3; these did not. A user (or an LLM editing the JSON) can write "yesterday" or "2026-13-99" and it round-trips. The session-start hook then `new Date(automation.last_reviewed)` produces `Invalid Date` and the cadence comparison breaks silently (NaN comparisons).

**Fix**: add the same `pattern` on both fields, or a `field_validator` that parses with `datetime.date.fromisoformat`.

### M6. Unguarded `response.json()` in `youtube_captions.py:53` (broad `except Exception:`)

**File**: `src/carrel/transcribe/adapters/youtube_captions.py:49-57`.

Catches `Exception` (with a `# pragma: no cover` comment) and re-raises a `TranscriptionError` with a single hint. Hides distinct failure modes — network timeout, video unavailable, transcripts disabled, age-restricted. The youtube-transcript-api library exposes typed exceptions (`TranscriptsDisabled`, `NoTranscriptFound`, `VideoUnavailable`); pattern-match on those for actionable hints. The "library exception classes vary by version" pragma is not a justification — pin the version (already pinned `>=1.0` in pyproject.toml) and use the typed exceptions.

### M7. `vault status --format quiet` returns nothing

**File**: `src/carrel/cli/vault.py:97-109`.

`if fmt == OutputFormat.QUIET: return` after computing counts but never printing them. QUIET mode is documented (output.py:13-31) as printing one machine-parseable value, but here it prints nothing. Either print the vault path, the total file count, or remove the QUIET branch (and let the JSON branch do double duty).

### M8. install.sh ↔ install.ps1 step 1 drift

- install.sh step 1: "System prerequisites" — Xcode CLI tools+Homebrew on macOS, git+curl on Linux.
- install.ps1 step 1: "Git" only. No curl check. No winget version probe.
- Cosmetic: `Write-Step` shows `[1/8] Git` while bash shows `[1/8] System prerequisites`. Different mental model for users who run both. Either align step semantics or rename step 1 in install.ps1 to "System prerequisites" and ensure curl/winget too.
- Also: `bootstrap.sh` is documented-deprecated but has no runtime banner. A user piping `curl ... | bash` doesn't read the docstring. Add `info "DEPRECATED: use install.sh instead"` and `read -r ... continue?` early.

### M9. Empty `catch {}` blocks in `check-environment.js`

12 instances. Each silently swallows any error in a brief-reading or filesystem walk. The hook's contract is "never block the session" so a catch-all is defensible at the outermost level, but burying 12 individual catches inside a single `try` makes failure impossible to diagnose in production. At minimum, log to `process.stderr` with a recognizable prefix (`carrel-hook: <where>: <message>`) so users who see something missing can debug it.

### M10. Twin `_source_hash` definitions in convert/transcribe filers

- `src/carrel/convert/filer.py:12-13` hashes a file path's bytes.
- `src/carrel/transcribe/filer.py:13-19` hashes URL string OR file path's bytes.

Two identically-named private helpers, two slightly different signatures. Move both into a shared `carrel/source_hash.py` module: `def hash_source(source: str | Path) -> str:` that handles both cases, eliminate the duplication.

---

## Low / informational (mentioned for completeness)

- `audit.py:107-108` collapses non-arm64 to "x86_64" — drops 32-bit and ppc64le distinction. Edge case.
- `bun.sh` (install.sh) vs `bun.com` (env/install.py) — both work, drift is cosmetic.
- `pyproject.toml` lacks `[tool.pytest.ini_options] asyncio_mode = "auto"` — currently fine because tests use decorators, but pin it for future-proofing.
- `cli/main.py:23` re-exports `resolve_cloud_consent` and `resolve_vault` in `__all__` despite never using them; `cli/__init__.py:8` also re-exports `resolve_cloud_consent`. Triple re-export.
- `paper.py:126` and `transcript.py:180` use `print(...)` while sibling commands use `console.print(...)`. Stylistic.

---

## Summary

| Severity | Count | Theme |
|---|---|---|
| Critical | 2 | Error-boundary leak (C1); dead hook for canonical profile shape (C2) |
| Important | 8 | Idempotency gap, dropped flag, dead models, wrong error class, untyped wrappers, untested HTTP error paths, dead doctests, broad except |
| Medium | 10 | Test coverage holes, divergent patterns, nag-spam UX, missing field validators, install-script drift, duplicate helpers |
| Low | 5 | Stylistic / edge-case |

The two Critical findings are the kind that pass code review by experienced reviewers because the surface looks fine; you only see them when a researcher's environment.json is older or partially-corrupt (C1), or when you grep both hooks for the same parser (C2). Worth fixing before Imperial deployment.
