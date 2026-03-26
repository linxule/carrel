# Toolchain Guide

When the environment setup needs to install developer tools, use these guidelines. Researchers don't know or care about toolchain choices — make them silently and correctly.

## Python

| Install | Never install | Why |
|---------|---------------|-----|
| **uv** | conda, pyenv, pip, pipenv, poetry | Single tool for packages + environments. No activation dance. Fast. |

```bash
brew install uv
uv run --directory /path/to/server python server.py   # run MCP server
uv tool install package-name                           # global tool
```

If the researcher says "I use conda" for their own data science work, that's fine — leave their conda alone. But Carrel's tools always use uv.

## JavaScript / Node.js

| Install | Never install | Why |
|---------|---------------|-----|
| **node** (via brew) | bun, deno, nvm | MCP servers use npx, which ships with node. Widest compatibility. |

```bash
brew install node
npx -y mcp-markdownify-server   # run MCP server
```

Node is installed by the bootstrap script. No additional setup needed for most researchers.

Do NOT install global JS package managers (yarn, pnpm, bun) for researchers. npx handles all MCP use cases.

## Audio Processing

Install only if researcher records interviews, meetings, or lectures:

```bash
brew install ffmpeg
```

Required by markdownify-mcp for audio-to-text conversion. Check `environment.json` — if `data_types` includes audio, install this.

## Document Tools

Usually not needed — markdownify-mcp handles most cases. Install only if specific conversion issues arise:

| Tool | When | Command |
|------|------|---------|
| pandoc | Advanced format conversion (LaTeX, EPUB) | `brew install pandoc` |
| poppler | PDF text extraction fallback | `brew install poppler` |

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

1. **Install silently.** Don't explain what brew/uv/node are unless the researcher asks.
2. **Install lazily.** Only install what the interview results require. Don't pre-install "just in case."
3. **Summarize in plain language.** "I'm setting up a tool to convert your PDFs" not "Installing node via Homebrew for the markdownify MCP server."
4. **Check first.** Always run the hardware audit to see what's already installed before installing anything.
5. **One tool per job.** Don't install alternatives. Pick the right one from this guide and use it.
