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
- **1 MCP** (markdownify — PDF, Word, audio, web conversion)

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

- **Claude Desktop** with Claude Code enabled (Settings → Features)
- **Node.js** — required for the bundled markdownify MCP. If not installed, Claude will detect this during setup and offer to install it (`brew install node` on macOS). Without Node.js, document conversion won't work.
- **Python + uv** — required only if adding vox-mcp (multi-model access)

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

### Option A: Kevin Pilot (Facilitator-Assisted, In Person)

**Pre-session prep (on Kevin's machine or your own):**

1. Clone the repo to Kevin's machine:
   ```bash
   git clone https://github.com/linxule/carrel.git ~/Documents/Apps/carrel
   ```
   (Or copy the `carrel/` directory from your machine via USB/AirDrop)

2. Open **Claude Desktop** app

3. Start a **Claude Code** session (Code tab)

4. In the Claude Code session, install the plugin from local path:
   ```
   /plugin install --local ~/Documents/Apps/carrel
   ```
   Or if that doesn't work, try from the terminal before opening Desktop:
   ```bash
   claude plugin install --local ~/Documents/Apps/carrel
   ```

5. Create the research project folder:
   ```bash
   mkdir -p ~/Documents/Research
   ```

6. Close and reopen Claude Desktop. Start a new session, selecting `~/Documents/Research` as the project folder.

7. Kevin should see the Carrel welcome message. Say: *"I'd like to set up my research environment"*

**During session:**
- Carrel interviews Kevin (~10 min)
- You help with human steps: install Obsidian (`brew install obsidian`), Web Clipper
- Test with a real PDF conversion
- Walk through the cheat sheet together

### Option B: Private GitHub Repo (Remote Researchers)

For researchers you've granted access to the private repo:

1. Open Claude Desktop → Code tab
2. Run:
   ```
   /plugin marketplace add linxule/carrel
   /plugin install carrel@linxule
   ```
3. Create a research folder and open it as a project
4. Follow the Quick Start above

Requires: researcher has GitHub access to `linxule/carrel` (add them as collaborator).

### Option C: Public Marketplace (Future)

When ready for wider distribution, submit to the Anthropic plugin marketplace. Researchers would install from the Discover tab in Claude Desktop — no terminal needed.

### Verifying Installation

After install, in any Claude Code session:
```
/carrel-status
```
If Carrel is active, it will report the environment state. If not installed, the command won't be recognized.

## Platform Support

The **Code tab** in Claude Desktop runs the full Claude Code engine — all features work.

| Feature | Desktop Code tab | CLI | Cowork |
|---------|-----------------|-----|--------|
| Skills (all 6) | Yes | Yes | TBD |
| Commands (/carrel-*) | Yes | Yes | TBD |
| Hooks | Yes | Yes | TBD |
| Agents (@setup-interviewer, @research-partner) | Yes | Yes | TBD |
| MCP servers | Yes | Yes | TBD |
| File read/write | Yes | Yes | TBD |
| Bash commands (brew install, etc.) | Yes | Yes | TBD |

**Recommended for researchers:** Use the **Code tab** in Claude Desktop. It provides full capabilities with a GUI — no terminal required.

**Cowork** is a separate product optimized for knowledge work. Plugin support is not yet documented by Anthropic — assume features may not be available there. Use the **Code tab** for full capabilities.

## License

MIT
