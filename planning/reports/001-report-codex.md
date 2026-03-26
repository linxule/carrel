# 001 Core Library Extraction Report

## Scope Delivered

Implemented the Carrel core package under `src/carrel/` with:

- Pydantic models and actionable error types
- Environment audit and profile read/write/update
- Vault scaffolding, bundled template copying, cheat-sheet generation, and organization helpers
- Deterministic convert/transcribe routers
- Idempotent paper/transcript filing with `source_hash` frontmatter
- Async subprocess/http adapters for local and cloud tools
- Typer CLI for `paper`, `transcript`, `vault`, and `env`
- Root `templates/` copied from the existing vault template sources
- Test suite covering routers, scaffold, audit, naming fallbacks, and filer idempotency

## Files Added

- `pyproject.toml`
- `src/carrel/...`
- `templates/...`
- `tests/...`

## Ported Sources

- `skills/environment-setup/scripts/check-environment.js` -> `src/carrel/env/audit.py`
- `skills/environment-setup/scripts/create-vault.js` -> `src/carrel/vault/scaffold.py`
- `skills/vault-ops/templates/` -> `templates/`
- `skills/environment-setup/scripts/generate-cheatsheet.js` -> `src/carrel/vault/templates.py`

## Verification

Executed:

```bash
uv run pytest
uv run carrel vault init "$(mktemp -d /tmp/carrel-vault.XXXXXX)" --format quiet
uv run carrel env doctor --format quiet
```

Results:

- `uv run pytest` -> 18 passed
- `uv run carrel vault init ... --format quiet` -> returned created vault path
- `uv run carrel env doctor --format quiet` -> exited with code 1, matching the quiet-mode contract when tools/keys are missing

## Notes

- I moved `pytest` and `pytest-asyncio` into main dependencies so the exact required command `uv run pytest` works without extra flags.
- External tool execution paths are implemented, but not exercised end-to-end because local binaries/API keys are not configured in this workspace.
- The implementation keeps cloud execution opt-in through explicit tool naming or profile `cloud_consent`, and all subprocesses use `asyncio.create_subprocess_exec`.
