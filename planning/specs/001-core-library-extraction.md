# 001: Core Library Extraction

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
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py           # typer app, top-level commands
│   │   ├── paper.py          # carrel paper convert|list|search|notes
│   │   ├── transcript.py     # carrel transcript create|list|search
│   │   ├── vault.py          # carrel vault init|new|search|organize|status
│   │   └── env.py            # carrel env setup|doctor|install|profile
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
│   │   │   └── gemini.py     # YouTube URL → Gemini API
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
│   ├── test_convert.py
│   ├── test_transcribe.py
│   ├── test_vault.py
│   └── test_env.py
│
└── pyproject.toml
```

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
    MLX_WHISPER = "mlx-whisper"
    GROQ = "groq"
    GEMINI = "gemini"
    MARKDOWNIFY = "markdownify"

class HardwareCapability(str, Enum):
    HIGH = "high"        # Apple Silicon, 16GB+
    MEDIUM = "medium"    # Apple Silicon, 8GB or Intel with 16GB+
    LOW = "low"          # Older Intel, limited RAM

class ConvertOptions(BaseModel):
    file: Path
    vault: Path
    tool: ConvertTool | None = None       # auto-detect if omitted
    sensitivity: Sensitivity | None = None # read from profile if omitted
    dry_run: bool = False

class ConvertResult(BaseModel):
    path: Path
    tool: ConvertTool
    pages: int | None = None
    duration_seconds: float
    skipped: bool = False
    metadata: dict  # extracted frontmatter fields

class TranscribeOptions(BaseModel):
    source: str                              # file path or YouTube URL
    vault: Path
    tool: TranscribeTool | None = None
    sensitivity: Sensitivity | None = None
    speakers: int | None = None              # expected speaker count
    dry_run: bool = False

class TranscribeResult(BaseModel):
    path: Path
    tool: TranscribeTool
    duration_seconds: float
    source_duration: str | None = None       # length of audio/video
    skipped: bool = False
    metadata: dict

class AuditResult(BaseModel):
    os: str
    arch: str
    os_version: str | None = None
    ram_gb: int | None = None
    disk_free: str | None = None
    hardware_capability: HardwareCapability
    tools: dict[str, ToolInfo]
    existing_mcps: dict[str, list[str]]

class ToolInfo(BaseModel):
    installed: bool
    version: str | None = None
    path: str | None = None

class ResearcherProfile(BaseModel):
    name: str | None = None
    field: str | None = None
    sensitivity: Sensitivity = Sensitivity.MEDIUM
    comfort_level: str = "beginner"  # beginner, comfortable, technical
    tools_configured: dict[str, bool] = {}
    preferences: dict = {}
```

### env/audit.py — Hardware & Tool Detection

Port from `skills/environment-setup/scripts/check-environment.js`. The existing JS script is the reference implementation.

```python
async def audit(project_path: Path | None = None) -> AuditResult:
    """Detect OS, hardware, installed tools, existing MCP configs."""
    ...
```

Key behaviors:
- Detect OS (macOS/Linux/Windows), arch, RAM, disk
- Check for installed tools: git, gh, node, python, uv, brew, lit (liteparse), coli, ffmpeg, pandoc
- Check for Obsidian and Zotero (macOS: mdfind, others: which)
- Read existing MCP configs (Claude Desktop + project .mcp.json)
- Classify hardware capability: Apple Silicon 16GB+ = HIGH, Apple Silicon 8GB or Intel 16GB+ = MEDIUM, else LOW
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
    available_tools: dict[str, bool],
) -> ConvertTool:
    """Pick the best conversion tool based on constraints."""
```

Routing logic (from `skills/convert/SKILL.md`):
1. If file is NOT a PDF → markdownify (it handles DOCX/PPTX/XLSX/images well)
2. If file IS a PDF:
   - sensitivity HIGH → liteparse (local, no cloud)
   - mineru available and sensitivity not HIGH → mineru (best quality)
   - liteparse available → liteparse (good local option)
   - fallback → markdownify (poor for PDFs but always available)

### convert/adapters/liteparse.py

```python
async def convert_with_liteparse(file: Path, output_dir: Path) -> str:
    """Run `lit parse <file>` and return the text content."""
```

- Shell out to `lit parse <file>` via `asyncio.create_subprocess_exec`
- Return the spatial text output
- Raise `ToolNotInstalled("liteparse")` if `lit` not found
- Raise `ConversionError` with actionable message on failure

### convert/adapters/mineru.py

```python
async def convert_with_mineru(file: Path, api_key: str) -> str:
    """Call MineRU API to convert PDF."""
```

- Use httpx to call mineru API
- model="vlm" for best quality
- Return markdown content
- Raise `ToolNotConfigured("mineru", "MINERU_API_KEY required")` if no key

### convert/filer.py — Naming & Placement

```python
def file_paper(content: str, metadata: dict, vault: Path) -> Path:
    """Save converted paper to vault with proper naming and structure."""
```

Convention (from `skills/vault-ops/SKILL.md`):
- Papers go in `papers/<author-year-short-title>/paper.md`
- Create images/ subfolder if there are extracted figures
- Add YAML frontmatter (title, authors, year, journal, doi, source_file, converted date, converter tool, tags, status)
- NEVER apply note templates to converted papers
- Return the path where the file was saved
- Idempotent: if the file already exists, return the existing path with `skipped=True`

### transcribe/router.py — Tool Selection

```python
def select_transcribe_tool(
    source: str,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    available_tools: dict[str, bool],
) -> TranscribeTool:
    """Pick the best transcription tool based on constraints."""
```

Routing logic (from `skills/transcribe/SKILL.md`):
1. If source is a YouTube URL → gemini (if available) else markdownify
2. If source is an audio/video file:
   - sensitivity HIGH + Apple Silicon → mlx-whisper (best local)
   - sensitivity HIGH + any hardware → coli (works on all Macs)
   - capable hardware → mlx-whisper (best quality)
   - weak hardware, not sensitive → groq (fastest cloud)
   - fallback → markdownify audio-to-markdown

### transcribe/adapters/coli.py

```python
async def transcribe_with_coli(
    file: Path,
    model: str = "sensevoice",
    json_output: bool = False,
) -> str:
    """Run `coli asr <file>` and return transcript text."""
```

- Shell out to `coli asr <file>` (optionally with `--json` and `--model`)
- First run may trigger model download (~155MB) — this is normal
- Requires ffmpeg for non-WAV files
- Raise `ToolNotInstalled("coli")` if not found
- Raise `ToolNotInstalled("ffmpeg")` if needed and not found

### vault/scaffold.py — Vault Creation

Port from `skills/environment-setup/scripts/create-vault.js`.

```python
def scaffold_vault(path: Path, profile: ResearcherProfile | None = None) -> list[str]:
    """Create vault folder structure, .obsidian/ config, templates. Returns list of created paths."""
```

Key behaviors:
- Create folders: inbox, papers, notes, transcripts, drafts, talks, admin, _meta, _templates
- Create .obsidian/ with core plugin config (from templates/obsidian-config.json)
- Copy templates to _templates/
- Create .carrel/ directory
- Idempotent: skip existing files/folders, never overwrite
- Return list of what was created vs skipped

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
def paper_filename(authors: str | None, year: str | None, title: str | None) -> str:
    """Generate a paper folder name: author-year-short-title"""

def transcript_filename(source: str, date: str, kind: str = "recording") -> str:
    """Generate a transcript filename: kind-topic-date.md"""

def sort_inbox(vault: Path) -> list[dict]:
    """Scan inbox/, suggest where each file should go. Returns suggestions, doesn't move."""
```

### cli/main.py — Typer App

```python
import typer
from rich.console import Console

app = typer.Typer(help="Carrel — research environment toolkit")
console = Console()

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
5. **Actionable errors.** Show the correct invocation on failure.
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
{"path":"papers/corley-gioia-2004/paper.md","tool":"liteparse","pages":24,"duration_seconds":1.2}

$ carrel paper convert paper.pdf --dry-run
Would convert paper.pdf → papers/corley-gioia-2004/paper.md (liteparse, local)

$ carrel paper convert paper.pdf --tool mineru
✓ papers/corley-gioia-2004/paper.md (24 pages, mineru, 8.3s)

$ carrel paper convert already-converted.pdf
→ skipped: papers/corley-gioia-2004/paper.md already exists

$ carrel transcript create recording.m4a
✓ transcripts/recording-2026-03-26.md (coli, 45.2s audio, 3.1s)

$ carrel transcript create https://youtube.com/watch?v=abc123
✓ transcripts/channel-name-topic-2026-03-26.md (gemini, 52min video)

$ carrel vault init ~/Documents/Research
✓ Created vault at ~/Documents/Research (7 folders, 5 templates, .obsidian/)

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
  mineru    ✗ not configured (MINERU_API_KEY missing)
  obsidian  ✓ installed
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

1. `uv run carrel env doctor` works and reports installed tools
2. `uv run carrel vault init /tmp/test-vault` creates a complete vault structure
3. `uv run carrel paper convert <any-pdf> --dry-run` shows what would happen
4. `uv run carrel paper convert <any-pdf>` converts using liteparse (if installed) and files correctly
5. `uv run carrel transcript create <audio-file> --dry-run` shows routing decision
6. All commands support `--format json` and `--format quiet`
7. All commands are idempotent
8. `pytest` passes with basic tests for routing logic and vault scaffold
9. No interactive prompts anywhere — all inputs via flags

## Constraints

- Do NOT install tools during library operations. `env/install.py` is the only module that installs things, and only when explicitly called.
- Do NOT make network calls unless the user explicitly chose a cloud tool (mineru, groq, gemini).
- Do NOT read or write files outside the vault path.
- Do NOT import any AI/LLM libraries. The core library is deterministic.
- All subprocess calls use `asyncio.create_subprocess_exec` (not `shell=True`).
- All file paths use `pathlib.Path`, never string concatenation.
