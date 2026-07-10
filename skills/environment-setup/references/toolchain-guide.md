# Toolchain Guide

When the environment setup needs to install developer tools, use these guidelines. Researchers don't know or care about toolchain choices — make them silently and correctly.

## Python

| Install | Never install | Why |
|---------|---------------|-----|
| **uv** | conda, pyenv, pip, pipenv, poetry | Single tool for packages + environments. No activation dance. Fast. |

```bash
brew install uv
uv run --directory /path/to/server python server.py   # run Python server
uv tool install package-name                           # global tool
```

If the researcher says "I use conda" for their own data science work, that's fine — leave their conda alone. But Carrel's tools always use uv. `markitdown` is a Python package that installs automatically with carrel — no manual step needed.

## JavaScript / Node.js

| Install | Never install | Why |
|---------|---------------|-----|
| **bun** | npm (globally), yarn, pnpm | bun handles global JS tool installs. All Carrel JS tools use `bun add -g`. |

```bash
brew install bun
bun add -g defuddle          # web content extraction
bun add -g @marswave/coli    # audio transcription (note: @marswave/coli, not just coli)
```

Node itself may already be installed by the bootstrap script — that's fine for running things. But new tool installs always use bun, not npm/npx.

## Audio Processing

Install only if researcher records interviews, meetings, or lectures:

```bash
brew install ffmpeg
bun add -g @marswave/coli
```

Both are required together — `coli` handles transcription, `ffmpeg` handles audio decoding. Install both when the interview or current profile says the researcher records interviews, meetings, or lectures.

## Document Tools

The carrel CLI handles conversion directly — no MCP servers needed. Tool selection depends on file type:

| File type | Tool | How it's installed |
|-----------|------|--------------------|
| PDF | `liteparse` | `npm install -g @llamaindex/liteparse` |
| DOCX, PPTX, XLSX, images, web | `markitdown` | Auto-installed with carrel (Python package) |
| Web pages (standalone extraction) | `defuddle` | `bun add -g defuddle` |

**liteparse notes:** handles PDFs well without extra deps. LibreOffice (~800MB) extends it to DOCX/PPTX/XLSX but carrel routes those to markitdown instead — don't install LibreOffice unless specifically requested.

**Google Workspace (gws):** high-friction setup requiring a Google Cloud project + OAuth configuration. Only install if researcher explicitly needs to pull from Google Drive/Docs. Command: `brew install googleworkspace-cli`. Warn the researcher this requires Google Cloud setup before it works.

## Version Control

Handled by the bootstrap script:
- **git** — included with Xcode Command Line Tools
- **gh** — GitHub CLI, installed via brew

The researcher does NOT need to learn git commands. Claude handles commits, pushes, and syncs. Explain git to interested researchers in terms of "save points" and "syncing to the cloud."

## GUI Applications

Claude can install CLI tools via brew, but GUI apps need the researcher's OK:

| App | Install | Or |
|-----|---------|-----|
| Obsidian | `brew install --cask obsidian` | Download from obsidian.md |
| Zotero | `brew install --cask zotero` | Download from zotero.org |

Always ask before running `brew install --cask` — it installs a visible application.

## General Principles

1. **Install silently.** Don't explain what brew/uv/bun are unless the researcher asks.
2. **Install lazily.** Only install what the interview results require. Don't pre-install "just in case."
3. **Summarize in plain language.** "I'm setting up a tool to convert your PDFs" not "Installing liteparse via Homebrew for PDF-to-Markdown conversion."
4. **Check first.** Always run the hardware audit to see what's already installed before installing anything.
5. **One tool per job.** Don't install alternatives. Pick the right one from this guide and use it.
