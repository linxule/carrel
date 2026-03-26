# 001: Core Library Extraction (v2)

_Revised based on reviews from Codex and Gemini. See `reviews/001-review-codex.md` and `reviews/001-review-gemini.md` for the full feedback. Changes marked with ⚡._

## Context

Carrel is an AI-augmented research environment for academics. It currently exists as a Claude Code plugin (skills, agents, hooks, commands) where most logic lives in markdown instructions that Claude follows. We're extracting the mechanical, deterministic parts into a Python core library that any transport (CLI, MCP server, Claude plugin, OpenAI agent, Kimi agent) can call.

### Architecture

```
Skills (markdown)     → human judgment layer, loaded by any AI
Core library (Python) → deterministic operations, no AI needed
Transports (thin)     → plugin, CLI, MCP, agent SDK apps
```

The core library NEVER asks questions or makes judgment calls. It takes explicit parameters and does work. If a required parameter is missing, it returns an actionable error — the AI/transport layer handles getting the answer from the human.

### Relationship to ItDepends

Carrel is the on-ramp to ItDepends (abductive research agent). They share:
- Python + uv toolchain
- Pydantic models, typer CLI, rich output
- Carrel modules may eventually become ItDepends components

See `/Users/xulelin/Documents/Apps/itdepends/pyproject.toml` for the target stack.

## Task

Build the `carrel` Python package — a core library with a typer CLI. Extract logic from existing JavaScript scripts and skill documentation into clean Python modules.

## Stack

- **Python 3.11+**, managed by `uv`
- **pydantic** — all data models (input options, results, profiles)
- **typer** — CLI framework
- **rich** — terminal output formatting
- **python-frontmatter** — YAML frontmatter in markdown files
- **pyyaml** — YAML parsing
- **httpx** — async HTTP for cloud APIs (mineru, groq)

Do NOT use: pip, conda, npm, click (use typer instead), argparse, requests (use httpx).

## Directory Structure

Create this in the carrel project root, alongside the existing plugin:

```
carrel/
├── src/carrel/
│   ├── __init__.py           # version, public API re-exports
│   ├── models.py             # shared pydantic models
│   ├── errors.py             # ⚡ structured error types
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py           # typer app, top-level commands
│   │   ├── paper.py          # carrel paper convert|list|search|notes
│   │   ├── transcript.py     # carrel transcript create|list|search
│   │   ├── vault.py          # carrel vault init|new|search|organize|status
│   │   ├── env.py            # carrel env setup|doctor|install|profile
│   │   └── output.py         # ⚡ format switching (human/json/quiet)
│   │
│   ├── env/
│   │   ├── __init__.py
│   │   ├── audit.py          # hardware & tool detection
│   │   ├── profile.py        # read/write .carrel/environment.json
│   │   └── install.py        # install a specific tool
│   │
│   ├── convert/
│   │   ├── __init__.py
│   │   ├── router.py         # select tool based on file type + options
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── liteparse.py  # subprocess: lit parse
│   │   │   ├── mineru.py     # httpx: mineru API
│   │   │   └── markdownify.py # subprocess: npx markdownify
│   │   ├── frontmatter.py    # generate YAML frontmatter for papers
│   │   └── filer.py          # naming conventions + vault placement
│   │
│   ├── transcribe/
│   │   ├── __init__.py
│   │   ├── router.py         # select tool based on source + options
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── coli.py       # subprocess: coli asr
│   │   │   ├── groq.py       # httpx: Groq Whisper API
│   │   │   └── gemini.py     # httpx: YouTube URL → Gemini API
│   │   └── filer.py          # naming + vault placement
│   │
│   └── vault/
│       ├── __init__.py
│       ├── scaffold.py       # create vault structure + .obsidian/
│       ├── templates.py      # render templates with data
│       └── organize.py       # file naming, inbox sorting, linking
│
├── templates/                 # vault templates (copy from skills/vault-ops/templates/)
│   ├── paper-notes.md
│   ├── meeting.md
│   ├── reflection.md
│   ├── daily.md
│   ├── vault-scaffold.json   # vault folder structure definition
│   └── obsidian-config.json  # .obsidian/ config
│
├── tests/
│   ├── test_convert_router.py    # ⚡ split by concern
│   ├── test_transcribe_router.py
│   ├── test_vault_scaffold.py
│   ├── test_env_audit.py
│   ├── test_filer.py             # ⚡ naming + idempotency
│   └── test_organize.py
│
└── pyproject.toml
```

## ⚡ Key Design Rules (resolves review contradictions)

### Rule 1: Local-first by default, cloud is opt-in

Cloud tools (mineru, groq, gemini) are NEVER auto-selected by the router. They are used only when:
- The user passes `--tool mineru|groq|gemini` explicitly, OR
- The researcher profile has `cloud_consent: true` AND sensitivity is LOW or MEDIUM

If sensitivity is HIGH or unset, the router MUST select a local tool. If no local tool is available, it returns an error with an actionable message ("Install liteparse for local PDF conversion: brew tap run-llama/liteparse && brew install llamaindex-liteparse"), never silently falls back to cloud.

### Rule 2: The core library handles local tools only; cloud adapters are opt-in extras

The core library ships with adapters for:
- **liteparse** (local PDF, subprocess)
- **coli** (local audio, subprocess)
- **markdownify** (local, subprocess — non-PDF formats only)

Cloud adapters (mineru, groq, gemini) are included in the package but only activated when explicitly called. They never run without an API key being passed or present in the environment.

⚡ **mlx-whisper is NOT in the core library.** It is an MCP-backed tool managed by the transport layer (Claude plugin, etc.). The core library's transcribe router does not return `mlx-whisper` — if a transport wants to offer it, it wraps the MCP call outside the core.

### Rule 3: Filesystem boundaries

- **Writing**: Only inside the vault path. No exceptions.
- **Reading**: Allowed anywhere — input files (PDFs, audio) will typically be outside the vault. System configs (Claude Desktop config, .mcp.json) are read for audit purposes only.
- All paths resolved early via `.expanduser().resolve()` in the CLI layer before passing to core functions.

### Rule 4: Deterministic metadata fallbacks

When metadata (title, authors, year) cannot be extracted from the document:

| Field | Extraction | Fallback |
|-------|-----------|----------|
| title | Parse from PDF metadata or first heading | Original filename without extension |
| authors | Parse from PDF metadata or content | `None` (omitted from frontmatter) |
| year | Parse from PDF metadata or content | `None` (omitted from frontmatter) |
| journal | Parse from content | `None` |
| doi | Parse from content | `None` |

Naming when fields are missing:
- Full metadata: `corley-gioia-2004/paper.md`
- Authors + title only: `corley-gioia-identity-construction/paper.md`
- Title only: `identity-construction-in-organizations/paper.md`
- Nothing extractable: `original-filename/paper.md`

The library NEVER guesses, hallucinates, or asks. It uses what it has and moves on.

### Rule 5: Vault path resolution

The vault path is resolved in this order:
1. Explicit `--vault` flag (highest priority)
2. `CARREL_VAULT` environment variable
3. Walk up from current working directory looking for `.carrel/` directory
4. Error with actionable message: "No vault found. Run: carrel vault init ~/Documents/Research"

This resolution happens in the CLI layer (`cli/main.py`), not in core functions. Core functions always receive an explicit `vault: Path`.

## Module Specifications

### models.py — Shared Types

```python
from pydantic import BaseModel
from enum import Enum
from pathlib import Path


class Sensitivity(str, Enum):
    HIGH = "high"        # IRB data, participant recordings
    MEDIUM = "medium"    # unpublished drafts
    LOW = "low"          # published papers, public materials


class ConvertTool(str, Enum):
    LITEPARSE = "liteparse"
    MINERU = "mineru"
    MARKDOWNIFY = "markdownify"


class TranscribeTool(str, Enum):
    COLI = "coli"
    GROQ = "groq"
    GEMINI = "gemini"
    MARKDOWNIFY = "markdownify"
    # ⚡ mlx-whisper removed — transport-layer concern


class HardwareCapability(str, Enum):
    HIGH = "high"        # Apple Silicon, 16GB+
    MEDIUM = "medium"    # Apple Silicon, 8GB or Intel with 16GB+
    LOW = "low"          # Older Intel, limited RAM


# --- Tool availability (⚡ three-category model) ---

class BinaryInfo(BaseModel):
    installed: bool
    version: str | None = None
    path: str | None = None


class ApiKeyStatus(BaseModel):
    configured: bool
    env_var: str             # e.g., "MINERU_API_KEY"


class ToolAvailability(BaseModel):
    """Canonical availability model covering all tool types."""
    binaries: dict[str, BinaryInfo]     # git, node, lit, coli, ffmpeg, etc.
    api_keys: dict[str, ApiKeyStatus]   # MINERU_API_KEY, GROQ_API_KEY, GEMINI_API_KEY
    mcp_servers: list[str]              # markdownify, mlx-whisper, etc. (from .mcp.json)


# --- Convert ---

class ConvertOptions(BaseModel):
    file: Path
    vault: Path
    tool: ConvertTool | None = None       # auto-detect if omitted (local-first)
    sensitivity: Sensitivity | None = None # read from profile if omitted
    cloud_consent: bool = False            # ⚡ explicit cloud opt-in
    dry_run: bool = False


class ConvertResult(BaseModel):
    path: Path
    tool: ConvertTool
    pages: int | None = None
    duration_seconds: float
    skipped: bool = False
    metadata: dict  # extracted frontmatter fields


# --- Transcribe ---

class TranscribeOptions(BaseModel):
    source: str                              # file path or YouTube URL
    vault: Path
    tool: TranscribeTool | None = None
    sensitivity: Sensitivity | None = None
    cloud_consent: bool = False              # ⚡ explicit cloud opt-in
    speakers: int | None = None              # expected speaker count
    dry_run: bool = False


class TranscribeResult(BaseModel):
    path: Path
    tool: TranscribeTool
    duration_seconds: float
    source_duration: str | None = None       # length of audio/video
    skipped: bool = False
    metadata: dict


# --- File operations (⚡ proper result types) ---

class FileResult(BaseModel):
    """Result of filing a document in the vault."""
    path: Path
    action: str    # "created", "skipped", "updated"
    reason: str | None = None  # e.g., "already exists"


class ScaffoldResult(BaseModel):
    """Result of vault scaffolding."""
    vault: Path
    created: list[str]   # paths created
    skipped: list[str]   # paths that already existed


# --- Audit ---

class AuditResult(BaseModel):
    os: str
    arch: str
    os_version: str | None = None
    ram_gb: int | None = None
    disk_free: str | None = None
    hardware_capability: HardwareCapability
    tools: ToolAvailability  # ⚡ replaces flat dict


# --- Profile ---

class ResearcherProfile(BaseModel):
    name: str | None = None
    field: str | None = None
    sensitivity: Sensitivity = Sensitivity.MEDIUM
    cloud_consent: bool = False          # ⚡ explicit cloud permission
    comfort_level: str = "beginner"      # beginner, comfortable, technical
    tools_configured: dict[str, bool] = {}
    preferences: dict = {}
```

### ⚡ errors.py — Structured Errors

```python
class CarrelError(Exception):
    """Base error with actionable message."""
    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint  # the "correct invocation" shown to user/agent
        super().__init__(message)


class ToolNotInstalled(CarrelError):
    def __init__(self, tool: str, install_command: str):
        super().__init__(
            f"{tool} is not installed",
            hint=f"Install it: {install_command}"
        )


class ToolNotConfigured(CarrelError):
    def __init__(self, tool: str, missing: str):
        super().__init__(
            f"{tool} is not configured: {missing}",
            hint=f"Set {missing} in your environment or pass --tool to use a local alternative"
        )


class CloudConsentRequired(CarrelError):
    """⚡ Raised when router would select a cloud tool but cloud_consent is False."""
    def __init__(self, tool: str, local_alternative: str | None = None):
        hint = f"Pass --tool {tool} to explicitly opt in to cloud processing"
        if local_alternative:
            hint += f", or use --tool {local_alternative} for local processing"
        super().__init__(
            f"Cloud tool {tool} requires explicit consent",
            hint=hint
        )


class VaultNotFound(CarrelError):
    def __init__(self):
        super().__init__(
            "No vault found",
            hint="Run: carrel vault init ~/Documents/Research\n"
                 "Or set CARREL_VAULT environment variable\n"
                 "Or pass --vault /path/to/vault"
        )


class ConversionError(CarrelError):
    pass


class TranscriptionError(CarrelError):
    pass
```

### env/audit.py — Hardware & Tool Detection

Port from `skills/environment-setup/scripts/check-environment.js`.

```python
import os

TOOL_CHECKS = {
    # binary name → version command
    "git": "git --version",
    "gh": "gh --version",
    "node": "node --version",
    "python": "python3 --version",
    "uv": "uv --version",
    "brew": "brew --version",
    "lit": "lit --version",
    "coli": "coli --version",
    "ffmpeg": "ffmpeg -version",
    "pandoc": "pandoc --version",
}

API_KEY_CHECKS = {
    "mineru": "MINERU_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

async def audit(project_path: Path | None = None) -> AuditResult:
    """Detect OS, hardware, installed tools, API keys, existing MCP configs."""
    ...
```

Key behaviors:
- Detect OS (macOS/Linux/Windows), arch, RAM, disk
- Check all binaries in TOOL_CHECKS via `asyncio.create_subprocess_exec`
- ⚡ Check API keys via environment variables (present or not — never log the value)
- ⚡ Read .mcp.json to discover configured MCP servers
- Check for Obsidian and Zotero (macOS: mdfind, others: which)
- Classify hardware capability: Apple Silicon 16GB+ = HIGH, Apple Silicon 8GB or Intel 16GB+ = MEDIUM, else LOW
- ⚡ Subprocess timeout: 10 seconds per tool check. On timeout, mark as `installed: False`
- Return structured AuditResult, never print to stdout

Reference: `/Users/xulelin/Documents/Apps/mcp/carrel/skills/environment-setup/scripts/check-environment.js`

### env/profile.py — Profile Management

```python
def read_profile(vault: Path) -> ResearcherProfile | None:
    """Read .carrel/environment.json, return None if not found."""

def write_profile(vault: Path, profile: ResearcherProfile) -> Path:
    """Write profile to .carrel/environment.json. Creates .carrel/ if needed."""

def update_profile(vault: Path, **updates) -> ResearcherProfile:
    """Merge updates into existing profile."""
```

### convert/router.py — Tool Selection

```python
def select_convert_tool(
    file: Path,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,       # ⚡ uses canonical availability model
    cloud_consent: bool = False,   # ⚡ explicit cloud opt-in
    explicit_tool: ConvertTool | None = None,  # ⚡ --tool flag override
) -> ConvertTool:
    """Pick the best conversion tool based on constraints.

    Raises CloudConsentRequired if the best tool is cloud-based
    but cloud_consent is False and no local alternative exists.
    """
```

⚡ Routing logic (revised — local-first, cloud opt-in):
1. If `explicit_tool` is set → use it (user knows what they want). If it's a cloud tool, still requires the API key to be configured.
2. If file is NOT a PDF → `markdownify` (handles DOCX/PPTX/XLSX/images well)
3. If file IS a PDF:
   - `liteparse` available → `liteparse` (local, free, default for all PDFs)
   - `liteparse` NOT available + `cloud_consent` is True + `mineru` API key configured → `mineru`
   - `liteparse` NOT available + `cloud_consent` is False → raise `ToolNotInstalled("liteparse", "brew tap run-llama/liteparse && brew install llamaindex-liteparse")`
   - absolute fallback → `markdownify` (poor quality, but always available)

**Note:** LiteParse is the default for ALL PDFs regardless of sensitivity. MineRU is only used when explicitly requested or when liteparse is missing and the user has opted into cloud.

### convert/adapters/liteparse.py

```python
async def convert_with_liteparse(
    file: Path,
    output_dir: Path,
    timeout: int = 30,  # ⚡ configurable timeout in seconds
) -> str:
    """Run `lit parse <file>` and return the text content."""
```

- Shell out to `lit parse <file>` via `asyncio.create_subprocess_exec`
- ⚡ Apply timeout (default 30s, ~500 pages fits easily)
- Return the spatial text output
- Raise `ToolNotInstalled("liteparse", "brew tap run-llama/liteparse && brew install llamaindex-liteparse")` if `lit` not found
- Raise `ConversionError` with stderr content on failure

### convert/adapters/mineru.py

```python
async def convert_with_mineru(
    file: Path,
    api_key: str,
    timeout: int = 120,  # ⚡ cloud calls get longer timeout
) -> str:
    """Call MineRU API to convert PDF."""
```

- Use httpx to call mineru API with `model="vlm"`
- ⚡ Require `api_key` parameter — never read from environment directly (the CLI layer resolves this)
- Return markdown content
- Raise `ToolNotConfigured("mineru", "MINERU_API_KEY")` if api_key is empty

### convert/filer.py — Naming & Placement

⚡ Returns `FileResult` instead of bare `Path`:

```python
def file_paper(
    content: str,
    metadata: dict,
    vault: Path,
    source_file: Path,
) -> FileResult:
    """Save converted paper to vault with proper naming and structure.

    Returns FileResult with action="created" or action="skipped".
    """
```

Convention (from `skills/vault-ops/SKILL.md`):
- Papers go in `papers/<author-year-short-title>/paper.md`
- Create images/ subfolder if there are extracted figures
- Add YAML frontmatter (title, authors, year, journal, doi, source_file, converted date, converter tool, tags, status)
- NEVER apply note templates to converted papers
- ⚡ Idempotency check: if `papers/<name>/paper.md` already exists AND the source file hash matches, return `FileResult(action="skipped", reason="already exists")`. If hash differs, return `FileResult(action="skipped", reason="already exists with different content — use --force to overwrite")`
- ⚡ Naming follows Rule 4 (deterministic fallbacks)

### transcribe/router.py — Tool Selection

```python
def select_transcribe_tool(
    source: str,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,        # ⚡ canonical availability model
    cloud_consent: bool = False,    # ⚡ explicit cloud opt-in
    explicit_tool: TranscribeTool | None = None,
) -> TranscribeTool:
    """Pick the best transcription tool based on constraints."""
```

⚡ Routing logic (revised — local-first, cloud opt-in):
1. If `explicit_tool` is set → use it
2. If source is a YouTube URL:
   - `cloud_consent` True + `gemini` API key configured → `gemini`
   - `cloud_consent` False → `markdownify` youtube-to-markdown (captions only, lower quality)
3. If source is an audio/video file:
   - `coli` available → `coli` (local, works on all hardware)
   - `coli` NOT available + `cloud_consent` True + `groq` API key configured → `groq`
   - `coli` NOT available + `cloud_consent` False → raise `ToolNotInstalled("coli", "npm i -g @marswave/coli")`
   - absolute fallback → `markdownify` audio-to-markdown

**Note:** coli is the default for ALL audio. Cloud (groq) only when explicitly requested or coli is unavailable with cloud consent.

### transcribe/adapters/coli.py

```python
async def transcribe_with_coli(
    file: Path,
    model: str = "sensevoice",
    json_output: bool = False,
    timeout: int = 300,  # ⚡ audio can be long — 5 min default
) -> str:
    """Run `coli asr <file>` and return transcript text."""
```

- Shell out to `coli asr <file>` (optionally with `--json` and `--model`)
- First run may trigger model download (~155MB) — this is normal, do not timeout during download
- Requires ffmpeg for non-WAV files
- Raise `ToolNotInstalled("coli", "npm i -g @marswave/coli")` if not found
- Raise `ToolNotInstalled("ffmpeg", "brew install ffmpeg")` if needed and not found

### transcribe/adapters/groq.py

```python
async def transcribe_with_groq(
    file: Path,
    api_key: str,
    timeout: int = 120,
) -> str:
    """Call Groq Whisper API to transcribe audio."""
```

- Use httpx to call Groq API
- ⚡ Require `api_key` parameter
- 25MB file size limit — raise actionable error if exceeded
- Return transcript text

### transcribe/adapters/gemini.py

```python
async def transcribe_with_gemini(
    youtube_url: str,
    api_key: str,
    prompt: str = "Transcribe this video with timestamps and speaker labels.",
    timeout: int = 300,
) -> str:
    """Pass YouTube URL to Gemini API for transcription."""
```

- Use httpx to call Gemini API with `file_data` containing the YouTube URL
- ⚡ Require `api_key` parameter
- Public videos only — raise error on private/unavailable videos
- Return formatted transcript

### vault/scaffold.py — Vault Creation

Port from `skills/environment-setup/scripts/create-vault.js`.

⚡ Returns `ScaffoldResult` instead of `list[str]`:

```python
def scaffold_vault(
    path: Path,
    profile: ResearcherProfile | None = None,
) -> ScaffoldResult:
    """Create vault folder structure, .obsidian/ config, templates.

    Returns ScaffoldResult with created/skipped lists.
    """
```

Key behaviors:
- Create folders: inbox, papers, notes, transcripts, drafts, talks, admin, _meta, _templates
- Create .obsidian/ with core plugin config (from templates/obsidian-config.json)
- Copy templates to _templates/
- Create .carrel/ directory
- Idempotent: skip existing files/folders, never overwrite
- ⚡ Return ScaffoldResult with separate `created` and `skipped` lists

Reference: `/Users/xulelin/Documents/Apps/mcp/carrel/skills/environment-setup/scripts/create-vault.js`

### vault/templates.py — Template Rendering

```python
def render_template(template_name: str, data: dict) -> str:
    """Load a template from templates/ and fill in placeholders."""

def list_templates() -> list[str]:
    """List available template names."""
```

### vault/organize.py — Naming & Conventions

```python
def paper_dirname(
    authors: str | None,
    year: str | None,
    title: str | None,
    source_filename: str | None = None,  # ⚡ fallback when no metadata
) -> str:
    """Generate a paper folder name. See Rule 4 for fallback chain."""

def transcript_filename(
    source: str,
    date: str,
    kind: str = "recording",
) -> str:
    """Generate a transcript filename: kind-topic-date.md"""

def sort_inbox(vault: Path) -> list[dict]:
    """Scan inbox/, suggest where each file should go. Returns suggestions, doesn't move."""
```

### ⚡ cli/output.py — Format Switching

```python
from enum import Enum

class OutputFormat(str, Enum):
    HUMAN = "human"
    JSON = "json"
    QUIET = "quiet"

def print_result(result: BaseModel, format: OutputFormat) -> None:
    """Print any pydantic result in the requested format."""
    # human → rich formatted
    # json → result.model_dump_json()
    # quiet → just the path field if present
```

### cli/main.py — Typer App

```python
import typer
from rich.console import Console

app = typer.Typer(help="Carrel — research environment toolkit")
console = Console()

# ⚡ Vault path resolution (Rule 5)
def resolve_vault(vault: Path | None = None) -> Path:
    """Resolve vault path from flag, env var, or parent walk."""
    if vault:
        return vault.expanduser().resolve()
    env_vault = os.environ.get("CARREL_VAULT")
    if env_vault:
        return Path(env_vault).expanduser().resolve()
    # Walk up from cwd
    current = Path.cwd()
    while current != current.parent:
        if (current / ".carrel").is_dir():
            return current
        current = current.parent
    raise VaultNotFound()

# Register subcommands
app.add_typer(paper_app, name="paper")
app.add_typer(transcript_app, name="transcript")
app.add_typer(vault_app, name="vault")
app.add_typer(env_app, name="env")
```

### CLI Design Principles

Follow these strictly (from "Building CLIs for agents"):

1. **Non-interactive by default.** Every input is a flag. No interactive prompts.
2. **Progressive help.** `carrel --help` shows subcommands. `carrel paper convert --help` shows details + examples.
3. **Examples in every --help.** Pattern-matchable.
4. **Flags + stdin.** Support pipelines: `cat files.txt | carrel paper convert --stdin`
5. **Actionable errors.** Show the correct invocation on failure. Use `CarrelError.hint`.
6. **Idempotent.** Re-running the same command = no-op with a message.
7. **--dry-run** for anything that writes files.
8. **--format** flag: `human` (default, rich output), `json` (structured), `quiet` (just the path).
9. **Predictable structure.** `carrel <resource> <verb>` everywhere.
10. **Return data.** Show the path, tool used, duration. Not just "done".

### CLI Examples (for --help output)

```
$ carrel paper convert paper.pdf
✓ papers/corley-gioia-2004/paper.md (24 pages, liteparse, 1.2s)

$ carrel paper convert paper.pdf --format json
{"path":"papers/corley-gioia-2004/paper.md","tool":"liteparse","pages":24,"duration_seconds":1.2,"skipped":false}

$ carrel paper convert paper.pdf --dry-run
Would convert paper.pdf → papers/corley-gioia-2004/paper.md (liteparse, local)

$ carrel paper convert paper.pdf --tool mineru
✓ papers/corley-gioia-2004/paper.md (24 pages, mineru, 8.3s)

$ carrel paper convert already-converted.pdf
→ skipped: papers/corley-gioia-2004/paper.md (already exists)

$ carrel paper convert already-converted.pdf --force
✓ papers/corley-gioia-2004/paper.md (24 pages, liteparse, 1.1s) [overwritten]

$ carrel transcript create recording.m4a
✓ transcripts/recording-2026-03-26.md (coli, 45.2s audio, 3.1s)

$ carrel transcript create https://youtube.com/watch?v=abc123 --tool gemini
✓ transcripts/channel-name-topic-2026-03-26.md (gemini, 52min video)

$ carrel vault init ~/Documents/Research
✓ Created vault at ~/Documents/Research
  created: 7 folders, 5 templates, .obsidian/
  skipped: 0

$ carrel vault status
Vault: ~/Documents/Research
  papers/     12 files
  notes/       3 files
  transcripts/  2 files
  inbox/        5 files (unsorted)

$ carrel env doctor
  git       ✓ 2.44.0
  node      ✓ 22.1.0
  uv        ✓ 0.6.3
  lit       ✓ 1.3.0
  coli      ✓ 0.0.13
  ffmpeg    ✓ 7.1
  mineru    ✗ MINERU_API_KEY not set
  groq      ✗ GROQ_API_KEY not set
  gemini    ✗ GEMINI_API_KEY not set
  obsidian  ✓ installed

$ carrel paper convert sensitive-data.pdf
✓ papers/sensitive-data/paper.md (liteparse, local — no data left your machine)

$ carrel transcript create interview.m4a --tool groq
Error: Cloud tool groq requires explicit consent.
  Pass --cloud to opt in, or use --tool coli for local processing.
```

## pyproject.toml

```toml
[project]
name = "carrel"
version = "0.1.0"
description = "Research environment toolkit — convert, transcribe, organize"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "typer>=0.9",
    "rich>=13.0",
    "python-frontmatter>=1.1",
    "pyyaml>=6.0",
    "httpx>=0.24",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "ruff>=0.1",
]

[project.scripts]
carrel = "carrel.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/carrel"]

[tool.ruff]
line-length = 100
```

## Existing Code to Port

These files contain the reference implementation. Port the logic to Python, don't copy the Node.js patterns:

1. `skills/environment-setup/scripts/check-environment.js` → `env/audit.py`
2. `skills/environment-setup/scripts/create-vault.js` → `vault/scaffold.py`
3. `skills/environment-setup/scripts/generate-cheatsheet.js` → `vault/templates.py`

## Existing Skills as Logic Documentation

These skills document the routing logic, naming conventions, and behaviors. They are NOT code to port — they're specifications for what the code should do:

1. `skills/convert/SKILL.md` → routing logic for `convert/router.py`
2. `skills/transcribe/SKILL.md` → routing logic for `transcribe/router.py`
3. `skills/vault-ops/SKILL.md` → conventions for `vault/organize.py`
4. `skills/environment-setup/references/decision-tree.md` → routing constraints
5. `skills/environment-setup/references/toolchain-guide.md` → install commands

## Acceptance Criteria

1. `uv run carrel env doctor` works and reports installed binaries, API keys, and MCP servers
2. `uv run carrel vault init /tmp/test-vault` creates a complete vault structure, returns ScaffoldResult
3. `uv run carrel paper convert <any-pdf> --dry-run` shows what would happen (tool, destination)
4. `uv run carrel paper convert <any-pdf>` converts using liteparse (default local tool) and files correctly
5. `uv run carrel transcript create <audio-file> --dry-run` shows routing decision
6. All commands support `--format json` and `--format quiet`
7. All commands are idempotent (re-run = skip with message)
8. `uv run carrel paper convert <pdf> --tool mineru` raises `CloudConsentRequired` unless `--cloud` is also passed
9. `uv run pytest` passes with tests for: routing logic (both routers), vault scaffold, file naming (with fallbacks), idempotency
10. No interactive prompts anywhere — all inputs via flags
11. ⚡ All errors include actionable `hint` field with correct invocation

## Constraints

- Do NOT install tools during library operations. `env/install.py` is the only module that installs things, and only when explicitly called.
- ⚡ Do NOT make network calls unless: (a) the user explicitly passed `--tool <cloud-tool>`, AND (b) `--cloud` flag is set or profile has `cloud_consent: true`.
- ⚡ Do NOT write files outside the vault path. Reading input files and system configs from anywhere is allowed.
- Do NOT import any AI/LLM libraries. The core library is deterministic.
- All subprocess calls use `asyncio.create_subprocess_exec` (not `shell=True`).
- All file paths use `pathlib.Path`, never string concatenation.
- ⚡ All subprocess calls have configurable timeouts (default: 10s for tool checks, 30s for conversion, 300s for transcription).
- ⚡ All paths resolved via `.expanduser().resolve()` before use.

## ⚡ Changelog from v1

| Issue | Source | Resolution |
|-------|--------|------------|
| Cloud routing contradicts privacy constraint | Codex #1 | Added Rule 1: local-first, cloud opt-in via `cloud_consent` + `--cloud` flag |
| mlx-whisper in router but no adapter | Codex #2 | Removed from core. Transport-layer concern (Rule 2) |
| Filesystem constraint too broad | Codex #3 | Narrowed: write inside vault only, read anywhere (Rule 3) |
| Acceptance criteria vs router on default tool | Codex #4 | LiteParse is default for all PDFs. MineRU only when explicit (Rule 1) |
| Function signatures don't match behavior | Codex #5 | Added FileResult, ScaffoldResult models |
| Metadata fallbacks undefined | Codex #6 | Added Rule 4 with deterministic fallback table |
| Tool availability underspecified | Codex #7 | Added ToolAvailability with binaries, api_keys, mcp_servers |
| Vault path resolution | Gemini | Added Rule 5: flag → env var → parent walk → error |
| Subprocess timeouts | Gemini | Added configurable timeouts to all adapters |
| Path resolution | Gemini | Added .expanduser().resolve() requirement |
| Idempotency hashing | Gemini | Added source file hash check in filer.py |
