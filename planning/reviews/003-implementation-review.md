# 003: Implementation Review — Mechanical Fixes

Review of the v3 spec implementation. 8 issues found (3 critical, 5 important). All are mechanical — no changes to skills, agents, or hooks.

## Critical Issues

### 1. markdownify adapter calls nonexistent binaries

**Files:** `src/carrel/convert/adapters/markdownify.py`

The adapter calls subprocess commands like `youtube-to-markdown`, `docx-to-markdown`, `pptx-to-markdown`, etc. **These binaries do not exist.** Markdownify is an MCP server, not a CLI toolkit. Under the hood it wraps Microsoft's `markitdown` Python library, which provides:

- **Python API:** `from markitdown import MarkItDown`
- **CLI:** `markitdown <filename>` (auto-detects format, outputs markdown to stdout)

`markitdown` handles: PDF (though we prefer liteparse), DOCX, PPTX, XLSX, CSV, images, HTML, and more. It does NOT handle YouTube URLs.

**Fix:** Replace the entire adapter to call `markitdown` as a subprocess:

```python
async def convert_with_markdownify(source: Path, timeout: int = 30) -> tuple[str, dict]:
    """Convert non-PDF files using markitdown CLI."""
    proc = await asyncio.create_subprocess_exec(
        "markitdown", str(source),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # ... timeout handling, error handling as before
    return stdout.decode().strip(), {}
```

**Also update `pyproject.toml`:** Add `markitdown` as a dependency (it's a pip/uv-installable package):

```toml
dependencies = [
    ...
    "markitdown>=0.0.1a3",
]
```

**Also update `env/audit.py`:** Change tool check from checking for nonexistent binaries to checking for `markitdown`:

```python
TOOL_CHECKS = {
    ...
    "markitdown": "markitdown --help",
    ...
}
```

### 2. YouTube transcript fallback needs rethinking

**Files:** `src/carrel/transcribe/router.py` (lines 14-16), `src/carrel/cli/transcript.py` (line 50)

The transcribe router falls back to `markdownify` for YouTube URLs when there's no cloud consent. But `markitdown` (the actual underlying tool) does NOT support YouTube URLs. The MCP server had a separate YouTube tool that used a different library.

**Two options (decision needed):**

**Option A (recommended):** YouTube without cloud consent raises `ToolNotConfigured` instead of falling back:
```python
# In transcribe/router.py
if is_youtube:
    if cloud_consent and tools.api_keys.get("gemini", ...).configured:
        return TranscribeTool.GEMINI
    raise ToolNotConfigured(
        "gemini",
        "GEMINI_API_KEY (required for YouTube transcription)"
    )
```

This is consistent with the PDF/audio philosophy: no tool available → clear error, not garbage output. YouTube caption extraction via markdownify was always low quality compared to Gemini anyway.

**Option B:** Add a `yt-dlp` adapter that downloads subtitles/captions. Heavier dependency, more code, for a fallback case.

**Go with Option A.** Remove `MARKDOWNIFY` from `TranscribeTool` enum entirely — markitdown is a convert tool, not a transcribe tool.

### 3. Missing test suite

**Expected by spec (acceptance criterion 11):**
```
tests/
├── test_convert_router.py
├── test_transcribe_router.py
├── test_vault_scaffold.py
├── test_env_audit.py
├── test_filer.py
└── test_organize.py
```

**None of these exist.** The `pyproject.toml` already has pytest configured (`pythonpath = ["src"]`), but zero test files.

Write tests covering:
- Both routers: all state combinations (explicit tool, local available, cloud consent variations, missing tools → error)
- Scaffold: creates vault + `.carrel/environment.json` with defaults
- Naming: `paper_dirname` fallback chain (all 4 tiers), `transcript_filename` fallback chain (all 3 tiers)
- Idempotency: hash match → skip, hash mismatch + no force → skip with message, hash mismatch + force → overwrite
- Filers: `file_paper` and `file_transcript` create correct directory structure and frontmatter

All routing tests should mock `ToolAvailability` — no real subprocess calls needed.

## Important Issues

### 4. Double `asyncio.run()` in CLI commands

**Files:** `src/carrel/cli/paper.py` (lines 53, 78), `src/carrel/cli/transcript.py` (lines 72, 100)

Both CLI commands call `asyncio.run()` twice in sequence:
```python
audit_result = asyncio.run(audit(vault_path))      # first event loop
content, metadata = asyncio.run(_convert(...))      # second event loop
```

This creates two event loops sequentially. Fragile on Python 3.11, inefficient on all versions.

**Fix:** Wrap both async operations in a single coroutine:

```python
async def _do_convert(file, vault_path, ...):
    audit_result = await audit(vault_path)
    selected_tool = select_convert_tool(...)
    content, metadata = await _convert(file, selected_tool)
    return audit_result, selected_tool, content, metadata

# In the command:
audit_result, selected_tool, content, metadata = asyncio.run(
    _do_convert(file_path, vault_path, ...)
)
```

Same pattern for transcript's `create_command`.

### 5. `--dry-run` path prediction is always filename-based

**File:** `src/carrel/cli/paper.py` (line 62)

```python
predicted = vault_path / "papers" / paper_dirname(None, None, file_path.stem, file_path.name) / "paper.md"
```

This always passes `None` for authors/year, so dry-run always shows the filename fallback path (e.g., `papers/paper/paper.md`), not the metadata-based path the actual conversion would produce (e.g., `papers/corley-gioia-2004/paper.md`).

**Fix:** Add a note to the human-readable dry-run output:

```python
if fmt == OutputFormat.HUMAN:
    locality = "cloud" if selected_tool == ConvertTool.MINERU else "local"
    console.print(
        f"Would convert {file_path.name} -> papers/<extracted-name>/paper.md "
        f"({selected_tool.value}, {locality})\n"
        f"  [dim]Destination determined after metadata extraction[/dim]"
    )
```

For `--format json` and `--format quiet` dry-run, use `null` for the path field since it's unknown.

### 6. Install command constants duplicated in 3 places

**Files:** `src/carrel/convert/router.py:8`, `src/carrel/convert/adapters/liteparse.py:9`, `src/carrel/env/install.py:2` (same for coli: `transcribe/router.py`, `transcribe/adapters/coli.py`, `env/install.py`)

The same install command strings (`brew tap run-llama/liteparse && brew install llamaindex-liteparse`, `npm i -g @marswave/coli`) are defined in three files each.

**Fix:** Centralize in `env/install.py` and import from there:

```python
# env/install.py
INSTALL_COMMANDS = {
    "liteparse": "brew tap run-llama/liteparse && brew install llamaindex-liteparse",
    "coli": "bun add -g @marswave/coli",
    "markitdown": "uv add markitdown",
}
```

Note: also change coli install from `npm i -g` to `bun add -g` per project conventions.

### 7. `env doctor --format quiet` has no explicit guard

**File:** `src/carrel/cli/env.py`

The QUIET format accidentally works because it doesn't match the JSON or HUMAN branches and falls through to the exit code. This is fragile.

**Fix:** Add an explicit early return:

```python
if fmt == OutputFormat.QUIET:
    raise typer.Exit(code=1 if failures else 0)
```

### 8. Templates directory duplicates existing skill templates (with less content)

**Directory:** `templates/`

Codex created template files that are duplicates of the existing, richer versions in `skills/vault-ops/templates/`. Key differences:

- `vault-scaffold.json`: Codex version is missing the `customizations` section (qualitative/quantitative/teaching profiles)
- `obsidian-config.json`: Codex version hardcodes full workspace JSON; existing version uses a reference and includes community plugin recommendations

**Fix:** Copy the existing templates from `skills/vault-ops/templates/` into `templates/`, preserving the richer content. The `templates/` directory is what `vault/templates.py` loads from, so it needs to be the authoritative source. Then verify `vault/templates.py`'s `template_root()` path resolution is correct.

Add `paper.md` (Codex created this, it's reasonable) to the existing template set if it doesn't already exist there.

## Summary

| # | Issue | Severity | Fix complexity |
|---|-------|----------|---------------|
| 1 | markdownify adapter calls nonexistent binaries | Critical | Medium — rewrite adapter to use `markitdown` CLI |
| 2 | YouTube transcript fallback doesn't work | Critical | Low — raise error instead of fallback, remove MARKDOWNIFY from TranscribeTool |
| 3 | Missing test suite | Critical | High — 6 test files to write |
| 4 | Double asyncio.run() | Important | Low — wrap in single coroutine |
| 5 | Dry-run path always filename-based | Important | Low — add note to output |
| 6 | Install constants duplicated | Important | Low — centralize imports |
| 7 | Quiet mode implicit fall-through | Important | Low — add explicit guard |
| 8 | Templates less complete than existing | Important | Low — copy existing templates |

## Constraints (unchanged from v3 spec)

- All subprocess calls: `asyncio.create_subprocess_exec` (not `shell=True`)
- All paths: `pathlib.Path`, resolved via `.expanduser().resolve()`
- No interactive prompts
- No AI/LLM library imports
- Writing only inside vault path
- Package managers: `uv` for Python, `bun` for Node.js (not pip, not npm)
