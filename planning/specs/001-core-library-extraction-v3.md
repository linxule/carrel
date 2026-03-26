# 001: Core Library Extraction (v3 — Final)

_v3 resolves 6 contract issues from Codex round 2 and 1 from Gemini round 2. See `reviews/002-review-codex.md` and `reviews/002-review-gemini.md`. Changes marked with 🔧. This is the implementation spec._

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

```
carrel/
├── src/carrel/
│   ├── __init__.py
│   ├── models.py
│   ├── errors.py
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── paper.py
│   │   ├── transcript.py
│   │   ├── vault.py
│   │   ├── env.py
│   │   └── output.py
│   │
│   ├── env/
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   ├── profile.py
│   │   └── install.py
│   │
│   ├── convert/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── liteparse.py
│   │   │   ├── mineru.py
│   │   │   └── markdownify.py
│   │   ├── frontmatter.py
│   │   └── filer.py
│   │
│   ├── transcribe/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── coli.py
│   │   │   ├── groq.py
│   │   │   └── gemini.py
│   │   └── filer.py
│   │
│   └── vault/
│       ├── __init__.py
│       ├── scaffold.py
│       ├── templates.py
│       └── organize.py
│
├── templates/
│   ├── paper-notes.md
│   ├── meeting.md
│   ├── reflection.md
│   ├── daily.md
│   ├── vault-scaffold.json
│   └── obsidian-config.json
│
├── tests/
│   ├── test_convert_router.py
│   ├── test_transcribe_router.py
│   ├── test_vault_scaffold.py
│   ├── test_env_audit.py
│   ├── test_filer.py
│   └── test_organize.py
│
└── pyproject.toml
```

## Key Design Rules

### 🔧 Rule 1: Cloud consent — ONE rule, no ambiguity

Passing `--tool <cloud-tool>` IS consent. No additional `--cloud` flag needed. The mental model:

| Scenario | Cloud tool runs? | Why |
|----------|-----------------|-----|
| `carrel paper convert file.pdf` | No | Auto-routing always picks local |
| `carrel paper convert file.pdf --tool mineru` | **Yes** | User explicitly named a cloud tool — that's consent |
| `carrel transcript create file.m4a --tool groq` | **Yes** | Same — explicit tool selection is consent |
| Auto-route + profile `cloud_consent: true` + sensitivity LOW/MEDIUM | **Yes** | Profile pre-authorized cloud for non-sensitive work |
| Auto-route + profile `cloud_consent: false` (or unset) | No | Stays local; errors if no local tool available |

**There is no `--cloud` flag.** Cloud consent comes from either (a) explicitly naming a cloud tool via `--tool`, or (b) the profile's `cloud_consent` field. This eliminates the three-rule contradiction from v2.

The router NEVER auto-selects a cloud tool unless the profile explicitly permits it. When the profile doesn't permit cloud and no local tool is available, the router raises `ToolNotInstalled` with an install command — it never falls through to cloud silently.

### Rule 2: Core library scope

The core library ships adapters for:
- **liteparse** (local PDF, subprocess)
- **coli** (local audio, subprocess)
- **markdownify** (local, subprocess — non-PDF formats only)
- **mineru** (cloud PDF, httpx — only runs when explicitly selected)
- **groq** (cloud audio, httpx — only runs when explicitly selected)
- **gemini** (cloud YouTube, httpx — only runs when explicitly selected)

**mlx-whisper is NOT in the core library.** It is MCP-backed and managed by the transport layer.

### Rule 3: Filesystem boundaries

- **Writing**: Only inside the vault path. No exceptions.
- **Reading**: Allowed anywhere — input files, system configs, .mcp.json.
- All paths resolved via `.expanduser().resolve()` in the CLI layer before passing to core functions.

### Rule 4: Deterministic metadata fallbacks (papers)

| Field | Extraction | Fallback |
|-------|-----------|----------|
| title | PDF metadata or first heading | Filename without extension |
| authors | PDF metadata or content | `None` (omitted) |
| year | PDF metadata or content | `None` (omitted) |
| journal | Content | `None` |
| doi | Content | `None` |

Paper directory naming:
- Full metadata: `corley-gioia-2004/paper.md`
- Authors + title: `corley-gioia-identity-construction/paper.md`
- Title only: `identity-construction-in-organizations/paper.md`
- Nothing extractable: `original-filename/paper.md`

### 🔧 Rule 4b: Deterministic metadata fallbacks (transcripts)

| Source type | Name extraction | Fallback |
|-------------|----------------|----------|
| YouTube URL | Video title from Gemini response or URL slug | `youtube-<url-slug>-<date>.md` |
| Audio file with known context | Kind + topic from filename | `<kind>-<topic>-<date>.md` |
| Audio file, no context | Filename stripped of extension | `recording-<filename>-<date>.md` |

The `kind` parameter controls the prefix: `interview`, `meeting`, `lecture`, `recording` (default).

Examples:
- `carrel transcript create interview-P001.m4a` → `transcripts/interview-P001-2026-03-26.md`
- `carrel transcript create meeting.m4a --kind meeting` → `transcripts/meeting-2026-03-26.md`
- `carrel transcript create random.wav` → `transcripts/recording-random-2026-03-26.md`
- YouTube: `transcripts/video-title-slug-2026-03-26.md`

### Rule 5: Vault path resolution

Resolution order:
1. Explicit `--vault` flag
2. `CARREL_VAULT` environment variable
3. Walk up from cwd looking for `.carrel/` directory
4. Raise `VaultNotFound` with actionable hint

This happens in the CLI layer only. Core functions always receive explicit `vault: Path`.

### 🔧 Rule 6: `vault init` creates the profile

`vault init` creates `.carrel/environment.json` with default values:
```json
{
  "sensitivity": "medium",
  "cloud_consent": false,
  "comfort_level": "beginner",
  "tools_configured": {},
  "preferences": {}
}
```

Human-specific fields (`name`, `field`) start as `null` and are filled later by the AI interview layer via `update_profile()`. This ensures the profile file exists for all downstream operations immediately after `vault init`.

### 🔧 Rule 7: `--format quiet` contract per command

| Command | `--format quiet` returns |
|---------|-------------------------|
| `paper convert` | Output file path |
| `paper list` | One path per line |
| `transcript create` | Output file path |
| `transcript list` | One path per line |
| `vault init` | Vault root path |
| `vault new` | Created file path |
| `vault search` | One path per line |
| `vault status` | Suppressed (exit 0, no output) |
| `vault organize` | One suggestion per line |
| `env doctor` | Suppressed (exit code only: 0 = all ok, 1 = missing tools) |
| `env profile` | Profile file path |

## Module Specifications

### models.py

```python
from pydantic import BaseModel
from enum import Enum
from pathlib import Path


class Sensitivity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConvertTool(str, Enum):
    LITEPARSE = "liteparse"
    MINERU = "mineru"
    MARKDOWNIFY = "markdownify"


class TranscribeTool(str, Enum):
    COLI = "coli"
    GROQ = "groq"
    GEMINI = "gemini"
    MARKDOWNIFY = "markdownify"


class HardwareCapability(str, Enum):
    HIGH = "high"       # Apple Silicon, 16GB+
    MEDIUM = "medium"   # Apple Silicon 8GB or Intel 16GB+
    LOW = "low"         # Older Intel, limited RAM


# --- Tool availability ---

class BinaryInfo(BaseModel):
    installed: bool
    version: str | None = None
    path: str | None = None

class ApiKeyStatus(BaseModel):
    configured: bool
    env_var: str

class ToolAvailability(BaseModel):
    binaries: dict[str, BinaryInfo]
    api_keys: dict[str, ApiKeyStatus]
    mcp_servers: list[str]


# --- Convert ---

class ConvertOptions(BaseModel):
    file: Path
    vault: Path
    tool: ConvertTool | None = None
    sensitivity: Sensitivity | None = None
    force: bool = False              # 🔧 overwrite existing output
    dry_run: bool = False

class ConvertResult(BaseModel):
    path: Path
    tool: ConvertTool
    pages: int | None = None
    duration_seconds: float
    skipped: bool = False
    metadata: dict


# --- Transcribe ---

class TranscribeOptions(BaseModel):
    source: str                       # file path or YouTube URL
    vault: Path
    tool: TranscribeTool | None = None
    sensitivity: Sensitivity | None = None
    kind: str = "recording"           # 🔧 interview, meeting, lecture, recording
    speakers: int | None = None
    force: bool = False               # 🔧 overwrite existing output
    dry_run: bool = False
    timeout: int | None = None        # 🔧 Gemini review: override default timeout

class TranscribeResult(BaseModel):
    path: Path
    tool: TranscribeTool
    duration_seconds: float
    source_duration: str | None = None
    skipped: bool = False
    metadata: dict


# --- File operations ---

class FileResult(BaseModel):
    path: Path
    action: str       # "created", "skipped", "overwritten"
    reason: str | None = None

class ScaffoldResult(BaseModel):
    vault: Path
    profile_path: Path    # 🔧 .carrel/environment.json — always created
    created: list[str]
    skipped: list[str]


# --- Audit ---

class AuditResult(BaseModel):
    os: str
    arch: str
    os_version: str | None = None
    ram_gb: int | None = None
    disk_free: str | None = None
    hardware_capability: HardwareCapability
    tools: ToolAvailability


# --- Profile ---

class ResearcherProfile(BaseModel):
    name: str | None = None
    field: str | None = None
    sensitivity: Sensitivity = Sensitivity.MEDIUM
    cloud_consent: bool = False
    comfort_level: str = "beginner"
    tools_configured: dict[str, bool] = {}
    preferences: dict = {}
```

### errors.py

```python
class CarrelError(Exception):
    """Base error with actionable hint."""
    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint
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

🔧 `CloudConsentRequired` removed. The router either selects a local tool or raises `ToolNotInstalled` with an install command. If the user passes `--tool <cloud-tool>`, that IS consent — no separate error needed. If auto-routing with `cloud_consent: true` selects a cloud tool and the API key is missing, `ToolNotConfigured` is raised.

### env/audit.py

```python
TOOL_CHECKS = {
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
    """Detect OS, hardware, installed tools, API keys, MCP configs."""
```

- Subprocess timeout: 10s per tool. On timeout → `installed: False`
- API keys: check `os.environ` for presence (never log values)
- MCP servers: read .mcp.json if it exists at project_path
- macOS apps: mdfind for Obsidian, Zotero
- Hardware classification: Apple Silicon 16GB+ = HIGH, Apple Silicon 8GB or Intel 16GB+ = MEDIUM, else LOW

Reference: `skills/environment-setup/scripts/check-environment.js`

### env/profile.py

```python
def read_profile(vault: Path) -> ResearcherProfile | None:
    """Read .carrel/environment.json. Returns None if not found."""

def write_profile(vault: Path, profile: ResearcherProfile) -> Path:
    """Write profile. Creates .carrel/ if needed."""

def update_profile(vault: Path, **updates) -> ResearcherProfile:
    """Merge updates into existing profile."""
```

### convert/router.py

```python
def select_convert_tool(
    file: Path,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,
    cloud_consent: bool = False,
    explicit_tool: ConvertTool | None = None,
) -> ConvertTool:
```

🔧 Routing logic — ONE deterministic outcome per state, no dead branches:

1. `explicit_tool` set → return it (API key checked by the adapter, not the router)
2. File is NOT a PDF → return `markdownify`
3. File IS a PDF:
   - `lit` binary installed → return `liteparse`
   - `lit` NOT installed + `cloud_consent` True + `MINERU_API_KEY` configured → return `mineru`
   - `lit` NOT installed + `cloud_consent` False → raise `ToolNotInstalled("liteparse", "brew tap run-llama/liteparse && brew install llamaindex-liteparse")`

**No markdownify fallback for PDFs.** If the user has neither liteparse nor cloud access, they get a clear error with install instructions. This prevents silently producing garbage PDF conversions.

### convert/filer.py

```python
def file_paper(
    content: str,
    metadata: dict,
    vault: Path,
    source_file: Path,
    tool: ConvertTool,
    force: bool = False,          # 🔧 explicit force parameter
) -> FileResult:
```

🔧 Idempotency implementation:
- Compute SHA-256 of source file content
- Store hash in output frontmatter as `source_hash: <hex>`
- On re-run: read existing output's frontmatter, compare `source_hash`
  - Same hash → `FileResult(action="skipped", reason="already converted")`
  - Different hash + `force=False` → `FileResult(action="skipped", reason="source changed — pass --force to re-convert")`
  - Different hash + `force=True` → overwrite, `FileResult(action="overwritten")`
  - No existing output → create, `FileResult(action="created")`

### transcribe/router.py

```python
def select_transcribe_tool(
    source: str,
    sensitivity: Sensitivity,
    hardware: HardwareCapability,
    tools: ToolAvailability,
    cloud_consent: bool = False,
    explicit_tool: TranscribeTool | None = None,
) -> TranscribeTool:
```

🔧 Routing logic — ONE outcome per state:

1. `explicit_tool` set → return it
2. Source is YouTube URL:
   - `cloud_consent` True + `GEMINI_API_KEY` configured → return `gemini`
   - else → return `markdownify` (youtube-to-markdown, captions only)
3. Source is audio/video file:
   - `coli` binary installed → return `coli`
   - `coli` NOT installed + `cloud_consent` True + `GROQ_API_KEY` configured → return `groq`
   - `coli` NOT installed + `cloud_consent` False → raise `ToolNotInstalled("coli", "npm i -g @marswave/coli")`

**No markdownify fallback for audio files.** Same rationale as PDFs — clear error > garbage output.

**YouTube is the exception:** `markdownify` youtube-to-markdown (caption extraction) is an acceptable fallback because it produces usable output, unlike its PDF/audio conversion.

### transcribe/filer.py

🔧 New module (split from organize.py for clarity):

```python
def file_transcript(
    content: str,
    metadata: dict,
    vault: Path,
    source: str,
    tool: TranscribeTool,
    kind: str = "recording",
    force: bool = False,
) -> FileResult:
```

Same idempotency pattern as `file_paper`: SHA-256 hash in frontmatter, skip/force logic.

Naming uses Rule 4b fallback chain. The `kind` parameter is passed from `TranscribeOptions.kind`.

### transcribe/adapters/coli.py

```python
async def transcribe_with_coli(
    file: Path,
    model: str = "sensevoice",
    json_output: bool = False,
    timeout: int = 300,
) -> str:
```

### transcribe/adapters/groq.py

```python
async def transcribe_with_groq(file: Path, api_key: str, timeout: int = 120) -> str:
```

### transcribe/adapters/gemini.py

```python
async def transcribe_with_gemini(
    youtube_url: str,
    api_key: str,
    prompt: str = "Transcribe this video with timestamps and speaker labels.",
    timeout: int = 300,
) -> str:
```

🔧 Gemini review: all adapters accept `timeout` override. CLI passes `--timeout` to the options model, which passes to the adapter.

### vault/scaffold.py

```python
def scaffold_vault(path: Path, profile: ResearcherProfile | None = None) -> ScaffoldResult:
```

🔧 Now also creates `.carrel/environment.json` with default profile (Rule 6). Returns `ScaffoldResult` with `profile_path` field.

### vault/organize.py

```python
def paper_dirname(
    authors: str | None,
    year: str | None,
    title: str | None,
    source_filename: str | None = None,
) -> str:

def transcript_filename(
    source: str,
    date: str,
    kind: str = "recording",
    title: str | None = None,       # 🔧 extracted video/recording title
) -> str:

def sort_inbox(vault: Path) -> list[dict]:
```

### cli/output.py

```python
class OutputFormat(str, Enum):
    HUMAN = "human"
    JSON = "json"
    QUIET = "quiet"

def print_result(result: BaseModel, fmt: OutputFormat, quiet_field: str = "path") -> None:
    """Print result in requested format.

    human → rich formatted table/panel
    json  → result.model_dump_json()
    quiet → value of quiet_field from result, or empty string if absent
    """
```

🔧 The `quiet_field` parameter lets each CLI command specify what quiet mode emits. Commands that have no meaningful single value (vault status, env doctor) pass `quiet_field=""` and the function prints nothing — the exit code carries the signal.

### cli/main.py

```python
import typer

app = typer.Typer(help="Carrel — research environment toolkit")

def resolve_vault(vault: Path | None = None) -> Path:
    """Flag → CARREL_VAULT env → parent walk → VaultNotFound."""
    ...

def resolve_cloud_consent(tool: str | None, profile: ResearcherProfile | None) -> bool:
    """🔧 Explicit tool selection = consent. Otherwise check profile."""
    if tool and tool in ("mineru", "groq", "gemini"):
        return True  # naming a cloud tool IS consent
    if profile and profile.cloud_consent:
        return True
    return False
```

## CLI Design Principles

1. **Non-interactive.** Every input is a flag. No prompts.
2. **Progressive help.** Examples in every `--help`.
3. **Flags + stdin.** Pipelines work.
4. **Actionable errors.** `CarrelError.hint` shows the fix.
5. **Idempotent.** Re-run = skip.
6. **--dry-run** for writes.
7. **--format** human|json|quiet.
8. **--force** to overwrite existing output.
9. **Predictable.** `carrel <resource> <verb>` everywhere.
10. **Return data.** Path, tool, duration.

## CLI Examples

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
→ skipped: papers/corley-gioia-2004/paper.md (already converted)

$ carrel paper convert changed-source.pdf
→ skipped: papers/changed-source/paper.md (source changed — pass --force to re-convert)

$ carrel paper convert changed-source.pdf --force
✓ papers/changed-source/paper.md (24 pages, liteparse, 1.1s) [overwritten]

$ carrel transcript create recording.m4a
✓ transcripts/recording-recording-2026-03-26.md (coli, 45.2s audio, 3.1s)

$ carrel transcript create interview-P001.m4a --kind interview
✓ transcripts/interview-P001-2026-03-26.md (coli, 32min audio, 4.7s)

$ carrel transcript create https://youtube.com/watch?v=abc --tool gemini
✓ transcripts/video-title-2026-03-26.md (gemini, 52min video)

$ carrel transcript create long-lecture.mp4 --tool gemini --timeout 600
✓ transcripts/lecture-long-lecture-2026-03-26.md (gemini, 2h12m video, 45s)

$ carrel vault init ~/Documents/Research
✓ Created vault at ~/Documents/Research
  profile: ~/Documents/Research/.carrel/environment.json
  created: 7 folders, 5 templates, .obsidian/, .carrel/
  skipped: 0

$ carrel vault status
Vault: ~/Documents/Research
  papers/     12 files
  notes/       3 files
  transcripts/  2 files
  inbox/        5 files (unsorted)

$ carrel vault status --format quiet
[exit 0, no output]

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

$ carrel env doctor --format quiet
[exit 1 — mineru/groq/gemini missing]

$ carrel paper convert no-liteparse.pdf
Error: liteparse is not installed
  Install it: brew tap run-llama/liteparse && brew install llamaindex-liteparse
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

1. `skills/environment-setup/scripts/check-environment.js` → `env/audit.py`
2. `skills/environment-setup/scripts/create-vault.js` → `vault/scaffold.py`
3. `skills/environment-setup/scripts/generate-cheatsheet.js` → `vault/templates.py`

## Existing Skills as Logic Documentation

1. `skills/convert/SKILL.md` → `convert/router.py`
2. `skills/transcribe/SKILL.md` → `transcribe/router.py`
3. `skills/vault-ops/SKILL.md` → `vault/organize.py`
4. `skills/environment-setup/references/decision-tree.md` → routing constraints
5. `skills/environment-setup/references/toolchain-guide.md` → install commands

## Acceptance Criteria

1. `uv run carrel env doctor` reports binaries, API keys, and MCP servers
2. `uv run carrel vault init /tmp/test-vault` creates vault + `.carrel/environment.json`
3. `uv run carrel paper convert <pdf> --dry-run` shows tool + destination
4. `uv run carrel paper convert <pdf>` converts with liteparse and files in `papers/<name>/paper.md`
5. `uv run carrel paper convert <pdf>` re-run skips with "already converted"
6. `uv run carrel paper convert <pdf> --force` overwrites
7. `uv run carrel paper convert <pdf> --tool mineru` uses mineru (no extra consent flag needed)
8. `uv run carrel transcript create <audio> --dry-run` shows routing
9. `uv run carrel transcript create <audio> --kind interview` names correctly
10. All commands support `--format human|json|quiet` per Rule 7
11. `uv run pytest` passes: routing (both routers, all states), scaffold, naming (paper + transcript fallbacks), idempotency (hash, skip, force)
12. No interactive prompts. All inputs via flags.
13. All errors include `hint` field.

## Constraints

- Do NOT install tools during library operations. Only `env/install.py` installs, and only when explicitly called.
- Do NOT make network calls unless the user explicitly named a cloud tool via `--tool` or the profile has `cloud_consent: true` and sensitivity permits.
- Do NOT write files outside the vault path. Reading from anywhere is allowed.
- Do NOT import AI/LLM libraries.
- All subprocess calls: `asyncio.create_subprocess_exec` (not `shell=True`).
- All paths: `pathlib.Path`, resolved via `.expanduser().resolve()`.
- All subprocesses: configurable timeout (10s checks, 30s convert, 300s transcribe, overridable via `--timeout`).

## 🔧 Changelog from v2

| Issue | Source | Resolution |
|-------|--------|------------|
| Three different cloud-consent rules | Codex R2 #1 | ONE rule: `--tool <cloud>` = consent. Removed `--cloud` flag. Profile `cloud_consent` controls auto-routing only. |
| Router fallback chains have dead branches | Codex R2 #2 | Removed markdownify fallback for PDFs and audio. No local tool → error with install command. YouTube keeps markdownify fallback (usable quality). |
| `--force` in examples but not in API | Codex R2 #3 | Added `force: bool` to ConvertOptions, TranscribeOptions, and both filers. Hash stored in frontmatter as `source_hash`. |
| Transcript naming not deterministic | Codex R2 #4 | Added Rule 4b with fallback table. Added `kind` and `title` params to transcript_filename(). |
| `vault init` doesn't create profile | Codex R2 #5 | `vault init` now creates `.carrel/environment.json` with defaults. ScaffoldResult includes `profile_path`. |
| `--format quiet` undefined for non-path commands | Codex R2 #6 | Added Rule 7: quiet contract per command. Doctor → exit code. Status → suppressed. |
| Long video timeout | Gemini R2 | Added `timeout` to TranscribeOptions. CLI passes `--timeout` to override defaults. |
