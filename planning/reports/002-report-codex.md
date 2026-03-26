# 002 Tool Expansion And Cleanup Report

## Scope Delivered

Implemented the tool-expansion spec across the CLI, adapters, routing, environment metadata, tests, and stale reference material.

Delivered:

- `defuddle` web capture via new `carrel capture url <url>` flow
- local YouTube captions via `youtube-transcript-api`
- Google Workspace export via `carrel google export <google-docs-url>`
- Gemini adapter fix: `gemini-2.5-flash` and no `mime_type` on YouTube URL `file_data`
- YouTube router fallback from Gemini to local captions
- new env/install metadata for `defuddle`, `gws`, and `youtube-transcript-api`
- stale environment-setup doc/script cleanup
- packaging fix so `uv run carrel ...` works from a fresh `.venv`

## Files Added

- `src/carrel/cli/capture.py`
- `src/carrel/cli/google.py`
- `src/carrel/convert/adapters/defuddle.py`
- `src/carrel/convert/pipeline.py`
- `src/carrel/google/__init__.py`
- `src/carrel/google/export.py`
- `src/carrel/transcribe/adapters/youtube_captions.py`
- `tests/test_capture.py`
- `tests/test_google_export.py`
- `tests/test_transcript_cli.py`
- `tests/test_youtube_captions.py`

## Key Updates

- `src/carrel/models.py`
  - Added `ConvertTool.DEFUDDLE`
  - Added `TranscribeTool.YOUTUBE_CAPTIONS`
- `src/carrel/transcribe/router.py`
  - YouTube now routes to Gemini only when cloud is allowed and configured
  - Otherwise it falls back to `youtube_captions`
- `src/carrel/transcribe/adapters/gemini.py`
  - Removed `mime_type` from `file_data`
  - Switched model to `gemini-2.5-flash`
- `src/carrel/env/audit.py`
  - Added doctor checks for `defuddle` and `gws`
- `src/carrel/env/install.py`
  - Added install hints for `defuddle`, `gws`, and `youtube-transcript-api`
- `src/carrel/cli/main.py`
  - Registered `capture` and `google` Typer apps
- `pyproject.toml`
  - Added `youtube-transcript-api`
  - Switched to `setuptools` `src/` packaging
  - Added `tool.uv.config-settings = { editable_mode = "compat" }` to keep `uv run carrel ...` working from a clean env
- `skills/environment-setup/...`
  - Updated stale references away from removed MCP/server paths
  - Updated cheatsheet generator and vault scaffold JS
  - Added `paper-notes.md` to the JS vault scaffold template list

## Acceptance Criteria

1. Pass: `uv run carrel capture url https://example.com ...` dry-run path verified; file-writing path covered by `tests/test_capture.py`
2. Pass: `--dry-run` shows destination
3. Pass: YouTube falls back to local captions when Gemini is unavailable
4. Pass: `--tool gemini` path uses the fixed Gemini adapter
5. Pass: Google export CLI exports then routes through normal conversion/fileing flow in tests
6. Pass: missing `gws` returns a clear install/auth hint
7. Pass: `carrel env doctor` reports `defuddle` and `gws`
8. Pass: `uv run pytest` passes
9. Pass: no remaining `markdownify-mcp` server references in non-planning files
10. Pass: no `npm` install references for `coli`
11. Pass: no `mlx-whisper-mcp` references remain in `decision-tree.md`
12. Pass: `create-vault.js` now includes `paper-notes.md`

## Verification

Executed:

```bash
uv run pytest
uv run python -c "import carrel; import carrel.cli.main; print(carrel.__file__)"
uv run carrel capture url https://example.com/posts/test --vault "$(mktemp -d /tmp/carrel-capture.XXXXXX)" --dry-run
uv run carrel env doctor --project-path .
rg -n 'markdownify-mcp|mlx-whisper-mcp|npx -y mcp-markdownify-server|npm i -g @marswave/coli' . -g '!planning/**'
```

Results:

- `uv run pytest` -> `29 passed`
- `uv run python ...` -> imported `carrel` from `src/carrel/__init__.py`
- `uv run carrel capture ... --dry-run` -> printed the predicted inbox destination
- `uv run carrel env doctor --project-path .` -> ran successfully and showed `defuddle` and `gws`; exited `1` because some tools/API keys are still missing in this machine state
- stale-reference grep -> no matches

## Notes

- I reused the existing paper conversion/fileing flow for Google Workspace exports by adding a shared convert pipeline module instead of duplicating converter selection logic.
- The repository already had unrelated worktree changes outside this task. I did not revert them.
