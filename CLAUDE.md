# Carrel

Research environment toolkit for academics. Two layers: a Python core library (`carrel` CLI) and a Claude Code plugin (skills, agents, hooks, commands).

## Quick Commands

```bash
# Core library
uv run pytest                                    # 29 tests
uv run carrel env doctor                         # Hardware + tools audit
uv run carrel vault init /tmp/test               # Scaffold a vault
uv run carrel paper convert paper.pdf            # Convert PDF (liteparse default)
uv run carrel transcript create rec.m4a          # Transcribe audio (coli default)
uv run carrel capture url https://example.com    # Web capture (defuddle)
uv run carrel google export <google-docs-url>    # Google Docs export (gws)
```

## Architecture

```
Skills (markdown)     → human judgment, loaded by any AI
Core library (Python) → deterministic operations, no AI
Transports (thin)     → plugin, CLI, MCP, agent SDK apps
```

The core library NEVER asks questions or makes judgment calls. Skills handle that. If a required parameter is missing, the library returns an actionable error.

## Directory Structure

```
carrel/
├── src/carrel/           # Python core library
│   ├── cli/              # typer CLI (paper, transcript, vault, env commands)
│   ├── convert/          # PDF/doc conversion (router, adapters, filer)
│   ├── transcribe/       # Audio/video transcription (router, adapters, filer)
│   ├── vault/            # Vault scaffold, organize, templates
│   ├── env/              # Audit, profile, install commands
│   ├── models.py         # Pydantic models (options, results, enums)
│   └── errors.py         # CarrelError with actionable hints
├── tests/                # pytest suite
├── templates/            # Vault templates (loaded by vault/templates.py)
├── skills/               # Plugin skills (convert, transcribe, vault-ops, environment-setup, etc.)
├── agents/               # Plugin agents (setup-interviewer, research-partner)
├── hooks/                # Plugin hooks (session start/end)
├── commands/             # Plugin slash commands (/carrel-*)
├── planning/             # Specs, reviews, prompts, reports (multi-model review workflow)
├── bootstrap.sh          # Fresh Mac setup script
└── pyproject.toml        # pydantic + typer + rich + httpx + markitdown
```

## Tool Routing

### PDF conversion
`liteparse` (local default) > `mineru` (cloud, explicit `--tool mineru`) > `markitdown` (non-PDF only)

No markdownify fallback for PDFs. Missing liteparse → clear error with install command.

### Audio transcription
`coli` (local default) > `groq` (cloud, explicit `--tool groq`)

No markdownify fallback for audio. Missing coli → clear error.

### YouTube
`youtube_captions` (local default, fetches existing captions with timestamps) > `gemini` (cloud, explicit `--tool gemini` or cloud_consent)

### Web pages
`defuddle` (local default, smart content extraction) > `markitdown` (fallback if defuddle not installed)

## Key Design Rules

- **Cloud consent**: `--tool <cloud-tool>` IS consent. No separate `--cloud` flag. Profile `cloud_consent` controls auto-routing only.
- **Idempotency**: SHA-256 source hash in output frontmatter. Re-run = skip. `--force` to overwrite.
- **Filesystem**: Write only inside vault. Read from anywhere.
- **Subprocesses**: `asyncio.create_subprocess_exec` (never `shell=True`). Configurable timeouts.
- **No AI imports**: Core library is deterministic. AI lives in the transport/skill layer.

## Gotchas

- `markitdown` (Microsoft's library) is the actual converter — NOT the MCP tool names (`youtube-to-markdown` etc. don't exist as CLI commands)
- Install constants are centralized in `env/install.py` — don't duplicate
- coli install uses `bun add -g @marswave/coli` (not npm)
- `generate-cheatsheet.js` is still a Node.js script (not yet ported to Python CLI)

## Relationship to ItDepends

Carrel is the on-ramp to ItDepends (abductive research agent). Same Python + pydantic + typer + rich stack. Carrel modules may become ItDepends components (profile → Mneme, vault papers → Scholia).

## Spec & Review History

Multi-model review process: spec written, reviewed by Codex (adversarial) + Gemini (constructive) through 3 rounds. All in `planning/`.

| File | Purpose |
|------|---------|
| `planning/specs/001-core-library-extraction-v3.md` | Implementation spec (final) |
| `planning/reviews/003-implementation-review.md` | Post-implementation review |
| `planning/reports/003-report-codex.md` | Fix report |
