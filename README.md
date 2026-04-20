# Carrel

*Your private desk in the library. Set up by AI, built for thinking.*

Carrel is a Claude Code plugin that onboards researchers into an AI-augmented research environment. It works by **interviewing the researcher**, **assessing their machine**, **configuring the right tools**, and **teaching itself how to work with this specific person**.

## Quick Start

1. Install the plugin (see Installation below)
2. Create a folder for your research (e.g., `~/Documents/Research`)
3. Open that folder as a project in Claude Desktop
4. Say: *"I'd like to set up my research environment"*
5. Carrel interviews you and configures everything

## Platform Support

Carrel's bootstrap install is cross-platform, but the setup flow is not yet fully cross-platform. Until spec 007 lands, the install scripts can get Carrel onto macOS, Linux, or Windows, while some downstream `/carrel-setup` recommendations remain macOS-only.

| Tool | macOS | Linux | Windows | Notes |
|------|:-----:|:-----:|:-------:|-------|
| Install script | ✅ Full | ✅ Full | ✅ Full | Bootstrap only; downstream setup guidance still has platform gaps |
| Obsidian | ✅ Full | ✅ Full | ✅ Full | Native app on all three platforms; install commands differ by OS |
| liteparse | ✅ Full | ❌ Not supported | ❌ Not supported | Current Carrel guidance is macOS-only; use `mineru` or manual fallback until spec 007 |
| coli | ✅ Full | ✅ Full | ✅ Full | Requires Bun and `ffmpeg` |
| defuddle | ✅ Full | ✅ Full | ✅ Full | Bun-based CLI |
| gws | ⚠️ Partial | ❌ Not supported | ❌ Not supported | macOS-only in current Carrel docs, plus Google Cloud/OAuth setup |
| mineru | ✅ Full | ✅ Full | ✅ Full | Cloud service; requires `MINERU_API_KEY` |
| markitdown | ✅ Full | ✅ Full | ✅ Full | Bundled with Carrel's Python environment |

## What's Included

- **13 commands** (`/carrel-*` for setup, conversion, automation, collaboration, reflection, migration)
- **2 agents** (@setup-interviewer for onboarding, @research-partner for thinking)
- **10 skills** (environment setup, vault operations, conversion, transcription, web capture, research partnership, automation, knowledge wiki, collaborator onboarding, self-improve)
- **2 hooks** (session start environment check, session end reflection prompt)
- **1 Python core library** (`carrel` CLI — convert, transcribe, vault, env commands)

## Commands

| Command | What it does |
|---------|-------------|
| `/carrel-automate` | Set up or update overnight vault maintenance and analytical tasks |
| `/carrel-batch` | Batch convert or transcribe a folder of files and file them to your vault |
| `/carrel-capture` | Save web content to your vault |
| `/carrel-cheatsheet` | Regenerate your reference card |
| `/carrel-setup` | Full onboarding: interview, audit, scaffold vault |
| `/carrel-status` | Check what's installed and working |
| `/carrel-convert` | Convert PDF/Word/slides to markdown in your vault |
| `/carrel-feedback` | Generate anonymized feedback digest for sharing |
| `/carrel-migrate` | Check for updates, show what's new, apply migrations |
| `/carrel-mirror` | Synthesize your research patterns from reflections and logs |
| `/carrel-reflect` | End-of-session reflection |
| `/carrel-share` | Generate a collaborator handbook for this vault |
| `/carrel-transcribe` | Transcribe audio to text in your vault |

## Design Philosophy

1. **The researcher never touches a terminal.** Everything is conversational.
2. **Interview first, install second.** Understand their work, then configure what they need.
3. **Obsidian is the shared workspace.** Researcher sees a GUI notebook. Claude sees markdown.
4. **Sensitivity-aware by default.** Local-first. Nothing leaves the machine unless explicitly chosen.
5. **The setup IS the pedagogy.** By choosing what they need, researchers learn what tools do.
6. **Reflection is built in.** Every session can end with structured feedback that improves the plugin.

## Prerequisites

- **Claude Desktop** (download from [claude.ai](https://claude.ai)) with Claude Code enabled (Settings → Features)
- **macOS, Linux, or Windows** — the install scripts handle the bootstrap install itself, but `/carrel-setup` still has macOS-only gaps for `liteparse` (PDF conversion) and `gws` (Google Workspace). Windows users will hit those gaps during setup until spec 007 lands.

New machine? Run the install script first (see Installation).

## Installation

There are two paths. **Path A is recommended** — it's more reliable because Claude Code in the terminal can diagnose and fix issues autonomously.

### Path A: One-Line Install (Recommended)

Best for fresh machines or when a facilitator is helping set up.

**macOS / Linux** — open Terminal and run:
```bash
curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
```

**Windows** — open PowerShell as Administrator and run:
```powershell
irm https://raw.githubusercontent.com/linxule/carrel/main/install.ps1 | iex
```

This installs all prerequisites (git, Node.js, uv, GitHub CLI, Claude Code), signs you in to GitHub, and installs the Carrel plugin. Idempotent — safe to run again. Takes ~10 minutes on a fresh machine.

If you have the script locally (e.g., via AirDrop):
```bash
bash install.sh          # macOS/Linux
.\install.ps1            # Windows PowerShell
```

**If the plugin didn't install** (the script will tell you), open a new terminal and run:
```bash
claude --dangerously-skip-permissions
```
Then tell Claude: *"Install the Carrel plugin from linxule/carrel"* — it will diagnose and fix whatever went wrong.

**Start using Carrel:**

1. Open **Claude Desktop** → **Code tab**
2. Select your research folder as the project
3. Type `/carrel-setup` to begin onboarding

### Path B: Claude Desktop Marketplace UI

For users who already have Claude Code and GitHub CLI set up.

1. Open **Claude Desktop** → **Code tab** → click **+** next to the plugin tabs
2. Click **Add marketplace**
3. Enter: `linxule/carrel`
4. Click **Sync**
5. Find Carrel in the plugin list → toggle it on

**Requires:** GitHub CLI (`gh`) authenticated with access to this repo. If you haven't set this up:
```bash
brew install gh
gh auth login
```

### For AI Assistants Helping With Setup

If you are an AI assistant (Claude, etc.) helping a user install Carrel, here is the reliable sequence:

1. **Check prerequisites**: `node --version`, `uv --version`, `gh auth status`, `claude --version`
2. **If anything is missing**: Run `install.sh` or install individually (brew on macOS, apt/dnf on Linux)
3. **GitHub auth is required** (private repo): `gh auth login` if not authenticated
4. **Add marketplace**: `claude plugin marketplace add linxule/carrel`
5. **Install plugin**: `claude plugin install carrel@carrel --scope user`
6. **Verify**: `claude plugin list` should show `carrel@carrel`

Common issues:
- `"Failed to add marketplace"` → GitHub auth not set up. Run `gh auth login` first.
- `"Plugin not found in marketplace"` → Use `carrel@carrel` (not `carrel@linxule`). The marketplace name is `carrel`.
- Plugin installs but no commands/skills appear → Restart Claude Desktop. Components auto-discover from `commands/`, `agents/`, `skills/` directories.

### Facilitator-Assisted Setup

When setting up a researcher's machine in person:

1. Run the bootstrap script on their machine
2. Help them sign in to GitHub during the `gh auth login` step
3. Install the plugin via terminal Claude Code (Path A, Step 2)
4. Open Claude Desktop and run `/carrel-setup`
5. Sit with them through the onboarding interview
6. Help with human steps: install Obsidian (`brew install --cask obsidian`), Web Clipper
7. Test with a real PDF conversion
8. Walk through the cheat sheet together

### Verifying Installation

In any Claude Code session:
```
/carrel-status
```
If Carrel is active, it reports the environment state. If not installed, the command won't be recognized.

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
claude plugin marketplace add linxule/interpretive-orchestration
claude plugin install interpretive-orchestration@interpretive-orchestration --scope user
```

## Supported Surfaces

Carrel targets the **Code tab** in Claude Desktop, which runs the full Claude Code engine.

| Feature | Desktop Code tab | CLI |
|---------|-----------------|-----|
| Skills (all 10) | Yes | Yes |
| Commands (/carrel-*) | Yes | Yes |
| Hooks | Yes | Yes |
| Agents (@setup-interviewer, @research-partner) | Yes | Yes |
| MCP servers | Yes | Yes |
| File read/write | Yes | Yes |
| Bash commands (brew install, etc.) | Yes | Yes |

**Recommended for researchers:** Use the **Code tab** in Claude Desktop. Full capabilities with a friendly GUI.

## License

MIT
