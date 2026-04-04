# 004: Architecture Review — Scheduled Automation and Shared Agency

Architecture feasibility review of the v0.4 spec. 11 findings (3 critical, 5 important, 3 informational). Assessed against the implemented codebase, not the spec's aspirations.

## Critical Issues

### 1. Batch processing has no concurrency model — "background bash" is not a programmable API

The spec says `/carrel-batch` should "Launch conversions as background bash tasks (parallel, respecting concurrency)" (spec A1, step 4). This relies on Claude Code's background bash feature, which is a UI interaction, not a plugin API. The plugin has no mechanism to programmatically launch, monitor, or collect results from background tasks.

The CLI processes one file at a time. `convert_command` in `src/carrel/cli/paper.py` (line 49) takes `file: Path` with `exists=True, dir_okay=False`. `transcript create` in `src/carrel/cli/transcript.py` (line 98) takes a single `source: str`. There is no batch CLI command.

The async pipeline is per-file. `run_convert_pipeline` in `src/carrel/convert/pipeline.py` (lines 46-54) processes one file. Each adapter spawns one subprocess with a 30-second timeout. For 20 PDFs sequentially, that is 10+ minutes wall clock.

The spec says "no changes except `models.py`" (spec section E), but actual parallel batch processing requires either a new CLI command using `asyncio.gather` or a new pipeline function in the core library.

What will actually happen: Claude reads the `/carrel-batch` command markdown, enumerates files via shell, and runs `carrel paper convert` sequentially for each file. "Respecting concurrency" is undefined — there is no semaphore, no max-parallel setting, and no way for the command to specify one.

**Recommendation**: Either (a) add a `carrel paper batch <directory>` CLI command to `src/carrel/cli/paper.py` that uses `asyncio.gather` with a configurable semaphore, accepting that this is a core library change, or (b) explicitly scope `/carrel-batch` to sequential processing with a clear summary at the end. Option (b) is honest and ships faster. The batch CLI command can come in v0.4.1 when real usage data shows whether parallel processing matters.

### 2. The "suggest + confirm" reorganization level has no execution mechanism

The four reorganization levels are conceptually sound (spec C2). But the "Suggest + confirm" level says: "Says 'yes' in next session → agent executes." This requires:

- The morning brief to contain actionable suggestions with an "approve?" marker
- The interactive session Claude to find approved items and execute them
- A structured format for executable suggestions

None of this is specified. The brief format (spec D1) is natural language. There is no structured format for executable suggestions that the interactive Claude could parse and act on. The session-start hook surfaces "pending decisions" (items the overnight agent could NOT process) but does not surface "pending approvals" (items the overnight agent suggested and the researcher needs to confirm). These are different things.

**Recommendation**: Add a `_meta/pending-approvals.md` file (or a section in `pending-decisions.md`) with a structured format:

```markdown
- [ ] **2026-04-04 cross-link**: Link [[note-a]] to [[note-b]] (both cite Weick 1995)
- [ ] **2026-04-04 move**: Move `inbox/smith-2026.pdf` to `papers/smith-2026/paper.md`
```

### 3. The generated prompt template embeds an absolute vault path that breaks on move

The generated prompt includes the vault's absolute path (spec B2 example: "research vault at [path]"). If the vault moves (iCloud sync, external drive, folder rename — all common for researchers), the overnight agent will target a nonexistent path.

**Recommendation**: Make the prompt use relative references: "You are in a Carrel vault. Detect the vault root by finding `.carrel/environment.json`, then read it for preferences." The overnight agent running via Desktop App local tasks has filesystem access and can detect the vault root the same way the session-start hook does (`findCarrelRoot` in `hooks/check-environment.js`, lines 14-22).

## Important Issues

### 4. The session-start hook has no YAML parser and a 10-second timeout

The spec says the hook should parse YAML frontmatter in `_meta/plans/` files to find `status: active` (spec C4, item 2). The hook (`hooks/check-environment.js`) is pure Node.js with no dependencies — it uses `require('fs')` and `require('path')` only (lines 1-3). There is no YAML parser.

Parsing `---\n...\n---` blocks with regex is fragile but feasible for the simple case of extracting `status` and `title` from plan frontmatter. However, the hook has a 10-second timeout (`hooks/hooks.json`, line 10). Directory listing + file reading + regex parsing for an unknown number of plan files is risky within that budget.

**Recommendation**: (a) Add a simple regex-based frontmatter extractor as a utility function in the hook file. (b) Cap the plan listing at 3 active plans. (c) Budget the new checks strictly: if `_meta/briefs/` does not exist, skip all automation checks immediately (most vaults will not have automation configured). (d) Consider increasing the hook timeout to 15 seconds in `hooks.json`.

### 5. The hook needs a "last session" timestamp to detect new briefs

The spec says the hook should "check if [the most recent brief] is newer than last session" (spec C4, item 1). But the hook has no concept of "last session." It reads environment.json and outputs text — it persists nothing between sessions.

`.carrel/plugin-state.json` already exists for version tracking (`hooks/check-version.js`, lines 27-34). It could hold a `last_session_start` timestamp.

**Recommendation**: Add a `last_session_start` ISO date field to `.carrel/plugin-state.json`. The hook reads it at the start, writes the current timestamp at the end (after all checks complete). Use a temp-file-then-rename pattern for safe writes.

### 6. The implementation order has a hidden dependency — /carrel-batch headless mode depends on the automation skill

The build sequence puts `/carrel-batch` at step 4 and the automation skill at step 7. But `/carrel-batch` in headless mode (overnight inbox processing) needs to write judgment calls to `_meta/pending-decisions.md` instead of asking the researcher. The automation skill (step 7) defines the pending decisions workflow and the headless detection mechanism.

**Recommendation**: Build `/carrel-batch` as interactive-only first (step 4). After the automation skill is built (step 7), add a step 8 to update `/carrel-batch` with headless mode support. The revised build sequence:

1. Models
2. Vault structure (including pending-decisions.md initial format)
3. Session-start hook
4. `/carrel-batch` (interactive mode only)
5. Vault-ops extension (analytical threads)
6. Research-partner extension
7. Automation skill (headless detection, pending decisions workflow)
8. Update `/carrel-batch` with headless mode
9. `/carrel-automate`
10. `/carrel-mirror`
11. Environment-setup extension
12. Migration + version bump

### 7. Pre-conversion idempotency checking is impossible for papers

The spec says batch step 3 should "Check idempotency (SHA-256 hash in existing output frontmatter → skip already-converted)" before launching conversions. But the output path for papers depends on `paper_dirname` in `src/carrel/vault/organize.py` (lines 58-73), which requires `authors` and `year` — metadata that is only available after conversion.

**Recommendation**: Accept that idempotency checking happens at the filer level (post-conversion), not pre-conversion. The filer already implements SHA-256 checking. The only waste is re-running the conversion tool on already-converted files before the filer catches the duplicate, but the tool execution is fast for small files.

### 8. AutomationConfig model design (informational)

Adding `AutomationConfig` as a nested `BaseModel` inside `ResearcherProfile` is clean. Pydantic v2 handles nested model serialization correctly. Backward compatible — `model_validate()` will instantiate `AutomationConfig` with defaults when the `automation` key is absent.

The `model` and `schedule` fields should use `Literal["sonnet", "opus"]` and `Literal["daily", "weekdays", "weekly"]` types for validation.

### 9. New automation skill is the correct pattern (informational)

Confirmed. Folding into environment-setup would push past 500 lines and mix concerns. Folding into vault-ops would conflate interactive and autonomous behavior. The proposed extensions to existing skills (B3, B4, B5) are appropriately scoped.

### 10. _meta/ directories are compatible (informational)

The vault scaffold creates `_meta/` during initial scaffold. The new subdirectories created lazily are compatible. One gap: `_meta/pending-decisions.md` needs to be initialized with a header when automation is configured (paralleling how `scaffold_vault` initializes `friction_log.md`).

### 11. Open question responses

**Q1 (Headless detection)**: The detection should be in the prompt itself: "You are running in unattended mode. When you encounter items needing human judgment, write to `_meta/pending-decisions.md` instead of asking." The skills do not need to detect headless mode programmatically; the overnight agent's prompt already encodes the behavior.

**Q2 (Thread scope)**: `notes/threads/` only. Correct.

**Q3 (Brief accumulation)**: Preserve. Correct.

**Q4 (Pending decisions)**: Single file. Add a convention for periodic archiving.

**Q5 (Multi-vault)**: No for v0.4. Correct.

## Summary

| # | Finding | Severity | Complexity |
|---|---------|----------|------------|
| 1 | Batch processing has no concurrency model | Critical | High |
| 2 | "Suggest + confirm" has no execution mechanism | Critical | Medium |
| 3 | Generated prompt embeds absolute path | Critical | Low |
| 4 | Hook has no YAML parser, 10-second timeout | Important | Medium |
| 5 | Hook needs "last session" timestamp | Important | Low |
| 6 | Build order hidden dependency | Important | Low |
| 7 | Pre-conversion idempotency impossible | Important | Low |
| 8 | AutomationConfig model design | Informational | Low |
| 9 | New automation skill is correct pattern | Informational | None |
| 10 | _meta/ directories compatible | Informational | Low |
| 11 | Open question responses | Informational | None |

## Constraints preserved correctly

- Core library is deterministic, no AI imports
- Skills handle judgment, commands are thin wrappers
- Vault-local namespace respected
- One-plugin policy maintained
- All subprocess calls: `asyncio.create_subprocess_exec` (never `shell=True`)

The spec's claim that "no Python core library changes except models.py" is aspirational. If batch processing with true parallelism is a requirement, the core library needs a batch pipeline function. If sequential processing is acceptable, the constraint holds.
