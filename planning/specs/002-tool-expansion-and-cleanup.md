# 002: Tool Expansion and Reference Doc Cleanup

Adds defuddle (web capture), youtube-transcript-api (local YouTube), gws (Google Workspace export). Fixes gemini adapter. Updates all stale reference docs.

## Context

The v3 core library extracted mechanical operations into Python CLI commands. However:
- Web capture has no CLI command (skill calls markitdown on URLs, which dumps the whole page)
- YouTube transcription has no local option (gemini-only, requires cloud)
- Google Docs/Sheets have no integration path
- The gemini adapter uses a deprecated model and incorrect mime_type
- 16+ references in environment-setup still mention the removed markdownify-MCP

This spec adds three new tools, fixes the gemini adapter, and cleans up all stale references.

## New Tools

### 1. defuddle — Web page content extraction

**What**: Smart article extraction from web pages. Strips navigation, ads, sidebars. Returns clean markdown + rich metadata (title, author, date, schema.org).

**Install**: `bun add -g defuddle`

**CLI**: `defuddle parse <url> --json --markdown` → JSON with `title`, `author`, `published`, `contentMarkdown`, `schemaOrgData`, etc.

**Why not markitdown**: markitdown dumps the entire page including navigation/ads. defuddle uses multi-pass content scoring and site-specific extractors (GitHub, Reddit, YouTube pages, etc.).

**Integration**: New adapter `convert/adapters/defuddle.py`, new CLI command `carrel capture <url>`.

### 2. youtube-transcript-api — Local YouTube captions

**What**: Fetches existing YouTube captions/subtitles with timestamps. No AI, no API key, no download. Free.

**Install**: Already a Python package: `youtube-transcript-api`

**Python API**:
```python
from youtube_transcript_api import YouTubeTranscriptApi
snippets = YouTubeTranscriptApi.get("VIDEO_ID")
# Each snippet: {"text": "...", "start": 0.0, "duration": 1.54}
```

**Why add this**: Provides a local, free, fast YouTube transcript option. Gemini is better (processes actual audio, works without captions) but requires cloud + API key. This is the local fallback.

**Limitation**: Only works if the video has captions (most do). Auto-generated captions are lower quality than Gemini's AI transcription.

**Integration**: New adapter `transcribe/adapters/youtube_captions.py`, new `TranscribeTool.YOUTUBE_CAPTIONS` enum value.

### 3. gws — Google Workspace CLI

**What**: Rust CLI for all Google Workspace APIs (Drive, Docs, Sheets, Slides, Gmail, etc.). Auth-once, then CLI calls.

**Install**: `brew install googleworkspace-cli`

**CLI**:
```bash
gws auth login -s drive          # one-time auth
gws drive files export --params '{"fileId": "ID", "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}' -o doc.docx
```

**Integration**: New module `google/export.py` that extracts file ID from a Google Docs/Sheets URL, calls `gws drive files export`, then routes the exported file through the normal conversion pipeline (DOCX → markitdown, PDF → liteparse).

**Auth detection**: `carrel env doctor` checks if `gws` is on PATH and authenticated. The setup interview asks about Google Workspace usage.

## Changes to Existing Code

### Fix gemini adapter

**File**: `src/carrel/transcribe/adapters/gemini.py`

Two fixes:

1. **Drop `mime_type`** from YouTube URL file_data (line 19):
```python
# Before:
{"file_data": {"mime_type": "text/uri-list", "file_uri": youtube_url}}

# After:
{"file_data": {"file_uri": youtube_url}}
```

2. **Update model** from deprecated `gemini-2.0-flash` to `gemini-2.5-flash` (line 26):
```python
# Before:
"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# After:
"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
```

### Update transcribe router

**File**: `src/carrel/transcribe/router.py`

Add YouTube local fallback. New routing for YouTube URLs:

1. `explicit_tool` set → return it
2. YouTube URL + `cloud_consent` + `GEMINI_API_KEY` → `gemini` (best quality, AI-processed)
3. YouTube URL + no cloud → `youtube_captions` (local, captions only)
4. Audio file + `coli` installed → `coli`
5. Audio file + `cloud_consent` + `GROQ_API_KEY` → `groq`
6. Audio file + nothing → raise `ToolNotInstalled("coli", ...)`

This means YouTube no longer raises `ToolNotConfigured` when there's no Gemini key — it falls back to local captions.

### Update models.py

**File**: `src/carrel/models.py`

Add new enum values:
```python
class TranscribeTool(str, Enum):
    COLI = "coli"
    GROQ = "groq"
    GEMINI = "gemini"
    YOUTUBE_CAPTIONS = "youtube_captions"   # NEW

class ConvertTool(str, Enum):
    LITEPARSE = "liteparse"
    MINERU = "mineru"
    MARKDOWNIFY = "markdownify"
    DEFUDDLE = "defuddle"                   # NEW
```

### Add new CLI command: `carrel capture`

**File**: New `src/carrel/cli/capture.py`

```python
@app.command("url")
def capture_url(
    url: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
```

Flow:
1. Call `defuddle parse <url> --json --markdown` as subprocess
2. Parse JSON: extract `contentMarkdown`, `title`, `author`, `published`, `domain`
3. Add YAML frontmatter (title, source URL, author, published, captured date, domain)
4. Save to `inbox/<slugified-title>.md`
5. Return `FileResult` with path

Fallback: if defuddle not installed, fall back to `markitdown <url>` (basic but works).

Register in `cli/main.py` as `app.add_typer(capture.app, name="capture")`.

### Add new CLI command: `carrel google export`

**File**: New `src/carrel/cli/google.py`

```python
@app.command("export")
def export_command(
    url: str = typer.Argument(...),   # Google Docs/Sheets URL
    vault: Path | None = typer.Option(None, "--vault"),
    format: str = typer.Option("docx", "--export-format", help="docx|pdf|txt|html"),
    force: bool = typer.Option(False, "--force"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
```

Flow:
1. Extract file ID from Google Docs URL (`docs.google.com/document/d/{ID}/edit`)
2. Check `gws` is on PATH and authenticated (call `gws drive about get --params '{"fields": "user"}'`)
3. Export via `gws drive files export --params '{"fileId": "ID", "mimeType": "..."}' -o /tmp/export.docx`
4. Route exported file through `carrel paper convert` pipeline (DOCX → markitdown, PDF → liteparse)
5. Return result

If `gws` not installed or not authenticated → raise `ToolNotInstalled("gws", "brew install googleworkspace-cli && gws auth login -s drive")`.

Register in `cli/main.py` as `app.add_typer(google.app, name="google")`.

### Update env/audit.py

**File**: `src/carrel/env/audit.py`

Add new tool checks:
```python
TOOL_CHECKS = {
    ...
    "defuddle": ["defuddle", "--version"],
    "gws": ["gws", "--version"],
}
```

### Update env/install.py

**File**: `src/carrel/env/install.py`

```python
INSTALL_COMMANDS = {
    ...
    "defuddle": "bun add -g defuddle",
    "gws": "brew install googleworkspace-cli",
    "youtube-transcript-api": "uv add youtube-transcript-api",
}
```

### Update pyproject.toml

Add `youtube-transcript-api` as a dependency:
```toml
dependencies = [
    ...
    "youtube-transcript-api>=1.0",
]
```

## New Files

| File | Purpose |
|------|---------|
| `src/carrel/convert/adapters/defuddle.py` | Subprocess: `defuddle parse <url> --json --markdown` |
| `src/carrel/transcribe/adapters/youtube_captions.py` | Python API: `YouTubeTranscriptApi.get(video_id)` with timestamp preservation |
| `src/carrel/google/__init__.py` | Google Workspace integration module |
| `src/carrel/google/export.py` | Extract file ID, call gws, route to conversion pipeline |
| `src/carrel/cli/capture.py` | `carrel capture url <url>` command |
| `src/carrel/cli/google.py` | `carrel google export <url>` command |

## New Tests

| File | Tests |
|------|-------|
| `tests/test_capture.py` | defuddle subprocess mock, fallback to markitdown, JSON parsing, frontmatter generation |
| `tests/test_youtube_captions.py` | Video ID extraction from URLs, transcript formatting with timestamps |
| `tests/test_google_export.py` | URL parsing (Docs, Sheets, Slides), gws subprocess mock, file routing |
| `tests/test_transcribe_router.py` | UPDATE: add YouTube captions fallback state |

## Stale Reference Doc Updates

These files in `skills/environment-setup/` reference the removed markdownify-MCP. Update them to reflect the actual tool stack.

### references/decision-tree.md

| Line(s) | Current | Change to |
|---------|---------|-----------|
| 25-26 | `create-vault.js` | `carrel vault init` |
| 29 | `markdownify-mcp \| Plugin .mcp.json \| Already bundled` | Remove row. Tools are now CLI-managed, not MCP. |
| 41 | `markdownify-mcp runs locally` | `liteparse and markitdown run locally — safe for sensitive data` |
| 85, 92 | `mlx-whisper-mcp` | Replace with `coli` (the local ASR the CLI supports) |
| 88 | `markdownify audio-to-markdown as fallback` | Remove. No markdownify audio fallback. |
| 99 | `markdownify as fallback` | Remove. Audio uses coli (local) or groq (cloud). |
| 104 | `markdownify youtube-to-markdown (captions only)` | `youtube-transcript-api (local captions with timestamps)` |
| 124 | `npm i -g @marswave/coli` | `bun add -g @marswave/coli` |
| 134 | `Node.js + markdownify-mcp covers it` | `carrel CLI handles conversion routing (liteparse, markitdown, defuddle)` |
| 159-160 | `markdownify is for web pages, Word docs, slides, and audio only` | `markitdown handles Word docs, slides, spreadsheets. defuddle handles web pages. coli/groq handle audio.` |

Also add new sections for:
- **Google Workspace**: If researcher uses Google Docs → recommend `gws` setup
- **Web capture**: `defuddle` for saving articles, `carrel capture <url>`

### references/toolchain-guide.md

| Line(s) | Current | Change to |
|---------|---------|-----------|
| 27 | `npx -y mcp-markdownify-server` | Remove. No MCP server needed. |
| 42 | `Required by markdownify-mcp for audio-to-text` | `Required for audio processing. Used by coli for local transcription.` |
| 46 | `markdownify-mcp handles most cases` | `carrel CLI routes to the right tool automatically` |
| 76 | `"Installing node via Homebrew for the markdownify MCP server"` | `"Installing a local document converter"` |

Add new tool entries:
- `defuddle` — `bun add -g defuddle` (web capture)
- `gws` — `brew install googleworkspace-cli` (Google Workspace)

### references/cheatsheet-template.md

| Line | Current | Change to |
|------|---------|-----------|
| 24 | `Document conversion \| Active \| markdownify (local)` | `PDF conversion \| Active \| liteparse (local)` + new rows for other formats |

Add rows for: web capture (defuddle), YouTube (local captions + gemini), Google Docs (gws), audio (coli/groq).

### scripts/generate-cheatsheet.js

| Line | Current | Change to |
|------|---------|-----------|
| 48 | `const hasTranscripts = tools.markdownify` | `const hasTranscripts = tools.coli \|\| tools.groq` |
| 74 | `Document conversion \| ✅ \| markdownify (local)` | `PDF conversion \| ✅ \| liteparse (local)` |
| 76 | `tools.markdownify ? 'markdownify (local)'` | `tools.coli ? 'coli (local)' : tools.groq ? 'groq (cloud)' : 'Not available'` |

### scripts/create-vault.js

| Line | Current | Change to |
|------|---------|-----------|
| 143 | `templateNames = ['paper.md', 'meeting.md', 'reflection.md', 'daily.md']` | Add `'paper-notes.md'` to the array |
| 168 | `markdownify: true` in tools_configured | `{ liteparse: false, markitdown: true, coli: false, defuddle: false, gws: false }` |

### skills/convert/SKILL.md

| Line | Current | Change to |
|------|---------|-----------|
| 89 | `reading-notes` skill reference | `vault-ops` (reading-notes doesn't exist) |

## Acceptance Criteria

1. `uv run carrel capture url https://example.com` fetches and saves to vault with frontmatter
2. `uv run carrel capture url <url> --dry-run` shows destination
3. `carrel transcript create <youtube-url>` falls back to local captions when no Gemini key
4. `carrel transcript create <youtube-url> --tool gemini` uses Gemini (with fixed model and no mime_type)
5. `carrel google export <google-docs-url>` exports and converts (when gws is authenticated)
6. `carrel google export <url>` without gws gives clear install hint
7. `carrel env doctor` shows defuddle and gws status
8. `uv run pytest` passes all new and existing tests
9. No remaining references to `markdownify-mcp` as an MCP server in any non-planning file
10. No references to `npm` for coli install (should be `bun`)
11. No references to `mlx-whisper-mcp` in decision-tree (should be `coli`)
12. `create-vault.js` includes `paper-notes.md` in templateNames

## Constraints (unchanged)

- `asyncio.create_subprocess_exec` (not `shell=True`) for all subprocess calls
- `pathlib.Path` everywhere, resolved via `.expanduser().resolve()`
- No interactive prompts — all inputs via flags
- No AI/LLM library imports
- Write only inside vault path
- Package managers: `uv` for Python, `bun` for Node.js

Save your report to `planning/reports/002-report-codex.md`.
