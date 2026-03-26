# Carrel

*Your private desk in the library. Set up by AI, built for thinking.*

Carrel is a Claude Code plugin that onboards researchers into an AI-augmented research environment. It works by **interviewing the researcher**, **assessing their machine**, **configuring the right tools**, and **teaching itself how to work with this specific person**.

## Quick Start

1. Install the plugin (see Installation below)
2. Create a folder for your research (e.g., `~/Documents/Research`)
3. Open that folder as a project in Claude Desktop
4. Say: *"I'd like to set up my research environment"*
5. Carrel interviews you and configures everything

## What's Included

- **8 commands** (`/carrel-*` for setup, conversion, transcription, reflection)
- **2 agents** (@setup-interviewer for onboarding, @research-partner for thinking)
- **6 skills** (environment setup, vault operations, conversion, transcription, web capture, research partnership)
- **2 hooks** (session start environment check, session end reflection prompt)
- **1 Python core library** (`carrel` CLI — convert, transcribe, vault, env commands)

## Commands

| Command | What it does |
|---------|-------------|
| `/carrel-setup` | Full onboarding: interview, audit, scaffold vault |
| `/carrel-status` | Check what's installed and working |
| `/carrel-convert` | Convert PDF/Word/slides to markdown in your vault |
| `/carrel-transcribe` | Transcribe audio to text in your vault |
| `/carrel-capture` | Save web content to your vault |
| `/carrel-reflect` | End-of-session reflection |
| `/carrel-cheatsheet` | Regenerate your reference card |
| `/carrel-feedback` | Generate anonymized feedback digest for sharing |

## Design Philosophy

1. **The researcher never touches a terminal.** Everything is conversational.
2. **Interview first, install second.** Understand their work, then configure what they need.
3. **Obsidian is the shared workspace.** Researcher sees a GUI notebook. Claude sees markdown.
4. **Sensitivity-aware by default.** Local-first. Nothing leaves the machine unless explicitly chosen.
5. **The setup IS the pedagogy.** By choosing what they need, researchers learn what tools do.
6. **Reflection is built in.** Every session can end with structured feedback that improves the plugin.

## Prerequisites

- **Claude Desktop** (download from [claude.ai](https://claude.ai)) with Claude Code enabled (Settings → Features)
- **macOS** — the bootstrap script handles everything else

New machine? Run the bootstrap script first (see Installation).

## Optional MCPs

During setup, Carrel may add project-level MCPs based on the interview:

| MCP | When | Requires |
|-----|------|----------|
| [vox-mcp](https://github.com/linxule/vox-mcp) | Researcher wants access to other AI models (Gemini, GPT, Grok, etc.) | At least one provider key (e.g., `OPENROUTER_API_KEY` or `GEMINI_API_KEY`) |
| mineru-mcp | Complex PDFs with tables/figures | `MINERU_API_KEY` |
| [zotero-mcp](https://github.com/54yyyu/zotero-mcp) | Researcher uses Zotero | `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID` |

See `docs/api-keys-guide.md` for setup instructions.

## Works With

Carrel handles the research environment. For qualitative methodology (Gioia coding, grounded theory), pair it with the [Interpretive Orchestration](https://github.com/linxule/interpretive-orchestration) plugin:

```
/plugin marketplace add linxule/interpretive-orchestration
/plugin install interpretive-orchestration
```

## Installation

### Step 1: Bootstrap the Machine

On a fresh Mac (or any Mac missing developer tools), open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/bootstrap.sh)"
```

This installs: Xcode CLI tools, Homebrew, Node.js, uv, GitHub CLI, and Claude Code CLI. It's idempotent — safe to run again if something fails. Takes ~10 minutes on a fresh machine.

**If you have the script locally** (e.g., via AirDrop):
```bash
bash bootstrap.sh
```

### Step 2: Start a Research Project

The bootstrap script installs the Carrel plugin automatically. Just:

1. Create a folder: `mkdir -p ~/Documents/Research`
2. Open **Claude Desktop** → **Code tab** → select that folder as your project
3. Type: `/carrel-setup`
4. Carrel interviews you and configures everything (~15 min)

**Requires:** GitHub access to `linxule/carrel`. The facilitator adds the researcher as a collaborator on the private repo. The bootstrap script handles GitHub sign-in.

If the plugin didn't install during bootstrap, tell Claude: *"Install the Carrel plugin from linxule/carrel"*

### Facilitator-Assisted Setup

When setting up a researcher's machine in person:

1. Run the bootstrap script on their machine
2. Help them sign in to GitHub during the `gh auth login` step
3. Open Claude Desktop and install the plugin
4. Sit with them through the onboarding interview
5. Help with human steps: install Obsidian (`brew install --cask obsidian`), Web Clipper
6. Test with a real PDF conversion
7. Walk through the cheat sheet together

### Verifying Installation

In any Claude Code session:
```
/carrel-status
```
If Carrel is active, it reports the environment state. If not installed, the command won't be recognized.

## Platform Support

Carrel targets the **Code tab** in Claude Desktop, which runs the full Claude Code engine.

| Feature | Desktop Code tab | CLI |
|---------|-----------------|-----|
| Skills (all 6) | Yes | Yes |
| Commands (/carrel-*) | Yes | Yes |
| Hooks | Yes | Yes |
| Agents (@setup-interviewer, @research-partner) | Yes | Yes |
| MCP servers | Yes | Yes |
| File read/write | Yes | Yes |
| Bash commands (brew install, etc.) | Yes | Yes |

**Recommended for researchers:** Use the **Code tab** in Claude Desktop. Full capabilities with a friendly GUI.

## License

MIT
