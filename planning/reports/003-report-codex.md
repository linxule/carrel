# 003 Fix Report

## Summary

Applied the 8 requested fixes from `planning/prompts/003-codex-fix-prompt.md` and verified the final implementation against the review and the v3 spec.

## Fixes Applied

1. Rewrote `src/carrel/convert/adapters/markdownify.py` to use a single `markitdown <file>` subprocess call.
2. Added `markitdown>=0.0.1a3` to `pyproject.toml` and updated `src/carrel/env/audit.py` to check `markitdown`.
3. Removed `MARKDOWNIFY` from `TranscribeTool` in `src/carrel/models.py`.
4. Changed YouTube routing in `src/carrel/transcribe/router.py` to raise `ToolNotConfigured("gemini", "GEMINI_API_KEY (required for YouTube transcription)")` when Gemini is unavailable.
5. Removed the markdownify fallback/import branch from `src/carrel/cli/transcript.py`.
6. Fixed double `asyncio.run()` in `src/carrel/cli/paper.py` and `src/carrel/cli/transcript.py` by using one coroutine pipeline per command path.
7. Fixed paper dry-run behavior in `src/carrel/cli/paper.py`:
   - human output now shows `papers/<extracted-name>/paper.md`
   - JSON/quiet dry-run now use `null` path via `ConvertResult.path: Path | None`
8. Centralized install command constants in `src/carrel/env/install.py` and switched coli install to `bun add -g @marswave/coli`.
9. Added the explicit quiet guard to `src/carrel/cli/env.py` doctor command.
10. Replaced `templates/vault-scaffold.json` and `templates/obsidian-config.json` with the richer versions from `skills/vault-ops/templates/`.
11. Updated the test suite to match the fixed contracts, including YouTube error behavior and `markitdown` audit coverage.

## Additional Runtime Fix

Verification exposed a packaging/runtime issue: `uv run carrel ...` could fail with `ModuleNotFoundError: No module named 'carrel'` because the project package was not being installed into the `uv run` environment consistently.

I fixed that by adding:

```toml
[tool.uv]
package = true
```

This was necessary for the requested verification command `uv run carrel env doctor` to work reliably.

## Verification

Executed successfully:

```bash
uv run pytest
uv run carrel env doctor
uv run carrel paper convert --help
uv run python - <<'PY'
import carrel.cli.main
import carrel.cli.paper
import carrel.cli.transcript
import carrel.convert.adapters.markdownify
import carrel.transcribe.router
print("imports-ok")
PY
uv run python - <<'PY'
from carrel.models import TranscribeTool
print([item.value for item in TranscribeTool])
PY
```

Results:

- `uv run pytest` -> 18 passed
- `uv run carrel env doctor` -> ran successfully and exited `1` because some tools/API keys are missing in this environment, which matches the command contract
- `uv run carrel paper convert --help` -> displayed the expected flags
- import smoke test -> `imports-ok`
- `TranscribeTool` values -> `['coli', 'groq', 'gemini']`

## Files Updated

- `pyproject.toml`
- `src/carrel/models.py`
- `src/carrel/env/audit.py`
- `src/carrel/env/install.py`
- `src/carrel/convert/adapters/markdownify.py`
- `src/carrel/convert/adapters/liteparse.py`
- `src/carrel/convert/router.py`
- `src/carrel/transcribe/router.py`
- `src/carrel/transcribe/adapters/coli.py`
- `src/carrel/cli/paper.py`
- `src/carrel/cli/transcript.py`
- `src/carrel/cli/env.py`
- `templates/vault-scaffold.json`
- `templates/obsidian-config.json`
- `tests/test_transcribe_router.py`
- `tests/test_env_audit.py`
