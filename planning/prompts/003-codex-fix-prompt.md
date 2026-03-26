Fix 8 issues found in the v3 implementation review. The review is at `planning/reviews/003-implementation-review.md`. The original spec is at `planning/specs/001-core-library-extraction-v3.md`. Read both before starting.

## What to fix

### Critical (do these first)

1. **Rewrite `src/carrel/convert/adapters/markdownify.py`** — the current adapter calls nonexistent binaries (`youtube-to-markdown`, `docx-to-markdown`, etc.). Replace with a single `markitdown <filename>` subprocess call. `markitdown` is Microsoft's file converter — one command, auto-detects format. Also add `"markitdown>=0.0.1a3"` to `pyproject.toml` dependencies and update the tool check in `env/audit.py` to check for `markitdown` instead of the old binary names.

2. **Fix YouTube transcript fallback** — `markitdown` does NOT support YouTube URLs, so the markdownify fallback for YouTube in `transcribe/router.py` won't work. Remove `MARKDOWNIFY` from the `TranscribeTool` enum in `models.py`. In the transcribe router, YouTube without cloud consent should raise `ToolNotConfigured("gemini", "GEMINI_API_KEY (required for YouTube transcription)")` instead of falling back. Update `cli/transcript.py` to remove the markdownify import and dispatch branch for transcription.

3. **Write the test suite** — 6 files, all missing:
   - `tests/test_convert_router.py` — all state combinations for `select_convert_tool`: explicit tool, PDF + liteparse available, PDF + no liteparse + cloud consent, PDF + no liteparse + no cloud → error, non-PDF → markitdown
   - `tests/test_transcribe_router.py` — all states for `select_transcribe_tool`: explicit tool, YouTube + gemini, YouTube + no cloud → error, audio + coli, audio + no coli + cloud, audio + no coli + no cloud → error
   - `tests/test_vault_scaffold.py` — `scaffold_vault` creates dirs, `.carrel/environment.json` with default profile, templates, `.obsidian/`
   - `tests/test_env_audit.py` — mock subprocess calls, verify `AuditResult` structure, hardware classification logic
   - `tests/test_filer.py` — idempotency: new file → "created", same hash → "skipped", different hash + no force → "skipped" with message, different hash + force → "overwritten". Test both `file_paper` and `file_transcript`.
   - `tests/test_organize.py` — `paper_dirname` fallback chain (all 4 tiers: author+year, author+title, title only, filename). `transcript_filename` fallback chain (all 3 tiers).

   Mock `ToolAvailability` in router tests — no real subprocess calls. Use `tmp_path` fixture for filer and scaffold tests.

### Important (do after critical)

4. **Fix double `asyncio.run()`** in `cli/paper.py` and `cli/transcript.py`. Each command calls `asyncio.run()` twice in sequence (once for audit, once for convert/transcribe). Wrap both async operations in a single coroutine and call `asyncio.run()` once.

5. **Fix dry-run path prediction** in `cli/paper.py` line 62. Currently passes `None` for authors/year, so dry-run always shows filename-based path. For `--format human`, show `papers/<extracted-name>/paper.md` with a note: "Destination determined after metadata extraction". For `--format json`, use `null` for the path.

6. **Centralize install constants** — `LITEPARSE_INSTALL` and `COLI_INSTALL` are each defined in 3 files. Move to `env/install.py` and import from there. Also change coli install from `npm i -g @marswave/coli` to `bun add -g @marswave/coli`.

7. **Add explicit quiet guard** in `cli/env.py` doctor command. Currently QUIET works by accident (implicit fall-through). Add `if fmt == OutputFormat.QUIET: raise typer.Exit(code=1 if failures else 0)` before the JSON/HUMAN branches.

8. **Fix templates** — the `templates/` directory has less complete versions than the existing templates in `skills/vault-ops/templates/`. Copy `vault-scaffold.json` and `obsidian-config.json` from `skills/vault-ops/templates/` to `templates/`, preserving the richer content (customizations section, community plugin recommendations). Keep the `paper.md` template Codex added — it's a good addition.

## Constraints (unchanged)

- `asyncio.create_subprocess_exec` (not `shell=True`) for all subprocess calls
- `pathlib.Path` everywhere, resolved via `.expanduser().resolve()`
- No interactive prompts — all inputs via flags
- No AI/LLM library imports
- Write only inside vault path
- Package managers: `uv` for Python, `bun` for Node.js

## Verification

After all fixes, confirm:
- `uv run pytest` passes all tests
- `uv run carrel env doctor` works
- `uv run carrel paper convert --help` shows all flags
- No imports of nonexistent modules
- `TranscribeTool` enum no longer has `MARKDOWNIFY`

Save your report to `planning/reports/003-report-codex.md`.
