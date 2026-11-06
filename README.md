# Carrel

Your private desk in the library, set up by AI and built for thinking.

Carrel sets up an AI-assisted research environment for academics. It interviews you about your work, checks your computer, installs the tools you need and learns how you like to work. It then helps you convert papers, transcribe interviews, capture web pages and keep an Obsidian vault in order.

Carrel works fully in Claude Code. A smaller, portable version also works in GitHub Copilot, Codex, Kimi Code and other AI apps.

## Install Carrel in Claude Desktop without a terminal

Most researchers should use this route. You need [Claude Desktop](https://claude.ai/download) on macOS, Windows or Linux.

1. Open Claude Desktop and select the **Code** tab. If you do not see it, turn on Claude Code in **Settings** > **Features**.
2. Select **+** next to the plugin tabs, then **Add marketplace**.
3. Enter `linxule/carrel` and select **Sync**.
4. Find Carrel in the plugin list and turn it on.
5. Create a folder for your research, such as `Documents/Research`, and open it as your project.
6. Type `Install the Carrel CLI for me`. Claude installs the command-line tools that Carrel runs on and asks your permission before each step.
7. Type `/carrel-setup` to start the setup interview.

## Install Carrel with a terminal

Use this route on a new computer, or if the first route did not work. The script installs Git, Node.js, uv, the GitHub command-line tool and Claude Code, then the Carrel plugin and its command-line tools. It takes about 10 minutes and is safe to run again.

On macOS or Linux, open Terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
```

On Windows, open PowerShell as an administrator and run:

```powershell
irm https://raw.githubusercontent.com/linxule/carrel/main/install.ps1 | iex
```

Then open Claude Desktop, select the **Code** tab, open your research folder and type `/carrel-setup`.

If you already have Claude Code and uv, you can install the 2 parts yourself:

```bash
claude plugin marketplace add linxule/carrel
```

```bash
claude plugin install carrel@carrel --scope user
```

```bash
uv tool install git+https://github.com/linxule/carrel.git
```

## Use Carrel in other AI apps

Other apps get Carrel's portable workflows: vault setup, paper conversion, transcription, web capture, environment repair, reflection and collaborator handbooks. They do not get the Claude Code slash commands, hooks or agents. Your computer needs Python 3.10 or newer.

| App | Without a terminal | With a terminal |
|-----|--------------------|-----------------|
| GitHub Copilot app | Follow [the Copilot app steps](#install-carrel-in-the-github-copilot-app) | Not needed |
| GitHub Copilot in VS Code | In the Chat panel, open **Customize**, add `linxule/carrel` as a plugin marketplace, then install Carrel | Not needed |
| GitHub Copilot CLI | Not available | `copilot plugin marketplace add linxule/carrel`, then `copilot plugin install carrel@carrel` |
| Codex | Not available | `codex plugin marketplace add linxule/carrel`, then install Carrel from `/plugins` |
| Kimi Code | Not available | In Kimi Code, run `/plugins install https://github.com/linxule/carrel` |
| Claude (web or desktop app) | Download [carrel.zip](https://github.com/linxule/carrel/releases/download/skill-latest/carrel.zip). In Claude, go to **Customize** > **Skills**, select **+** > **Create skill** > **Upload a skill**, and choose the file | Not needed |
| Cursor, OpenCode, Gemini CLI and other skill apps | Not available | `npx skills add linxule/carrel-skill` |

Use `linxule/carrel-skill`, not `linxule/carrel`, with `npx skills`. This repository also holds skills that only work inside Claude Code.

For Claude, turn on code execution first in **Settings** > **Capabilities**. Do not upload GitHub's "Download ZIP" of a repository: Claude rejects it because the folder name does not match the skill name.

Skills are not signed. Read the short, standard-library-only scripts in `skills/carrel/scripts/` before you install.

### Install Carrel in the GitHub Copilot app

You need to add the Carrel marketplace before you can install Carrel. The **Install plugin** box cannot find Carrel until you do.

1. Select **Customize** in the sidebar.
2. Select the marketplace settings control next to the marketplace dropdown.
3. Add `linxule/carrel` as a GitHub repository.
4. Choose the `carrel` marketplace in the dropdown.
5. Search for Carrel on **Browse** and select **Install**.

If you use the **Install plugin** box instead, enter `carrel@carrel` after step 3. The part after `@` is the marketplace name, which is `carrel`, not `linxule`.

The same rule applies in VS Code and the Copilot CLI: add the marketplace first, then install `carrel@carrel`.

## Check that Carrel works

In Claude Code, type `/carrel-status`. Carrel reports what is installed and working. If Claude does not recognize the command, the plugin is not installed.

## Fix installation problems

- "Failed to add marketplace": check your internet connection, then try again.
- "Plugin not found in marketplace": use `carrel@carrel`. The marketplace is called `carrel`, not `linxule`.
- "Carrel CLI not found" when a session starts: ask Claude to install the Carrel CLI, or run the `uv tool install` command above.
- The plugin installed but no commands appear: restart Claude Desktop.

If none of these help, open a terminal, run `claude`, and ask: "Install the Carrel plugin from linxule/carrel and fix whatever is wrong."

## Set up Carrel for someone else

If you are helping a researcher in person:

1. Run the install script on their computer.
2. Open Claude Desktop with them and run `/carrel-setup`.
3. Stay with them through the setup interview.
4. Help them install Obsidian and the Obsidian Web Clipper.
5. Convert one of their real PDFs together.
6. Go through the cheat sheet that Carrel creates.

## Instructions for AI assistants

If you are an AI assistant installing Carrel for a user:

1. Check what is installed: `node --version`, `uv --version` and `claude --version`.
2. If anything is missing, run `install.sh` or `install.ps1`, or install it with the system package manager.
3. Run `claude plugin marketplace add linxule/carrel`.
4. Run `claude plugin install carrel@carrel --scope user`.
5. Run `uv tool install git+https://github.com/linxule/carrel.git`. The plugin's hooks and commands need it.
6. Check that `claude plugin list` shows `carrel@carrel` and `carrel --version` works.

The repository is public. GitHub sign-in is optional, but it avoids API rate limits.

## What Carrel includes

The Claude Code plugin includes:

- 15 slash commands, listed below
- 2 agents: `@setup-interviewer` for onboarding and `@research-partner` for thinking through your work
- workflow skills for setup, ingestion, vault work, research partnership, automation, collaboration, field maps and maintenance
- 4 hooks that check your environment, prompt a reflection at the end of a session, add vault context to each message and ask before sending data to a cloud tool
- the `carrel` command-line tool, which does all file work in a predictable, testable way

| Command | What it does |
|---------|--------------|
| `/carrel-setup` | Interview you, check your computer and create your vault |
| `/carrel-status` | Show what is installed and working |
| `/carrel-fix` | Find environment problems and guide the repair |
| `/carrel-convert` | Convert a PDF, Word file or slides to Markdown in your vault |
| `/carrel-transcribe` | Transcribe audio into your vault |
| `/carrel-capture` | Save a web page to your vault |
| `/carrel-batch` | Convert or transcribe a whole folder |
| `/carrel-cheatsheet` | Rebuild your reference card |
| `/carrel-reflect` | Write an end-of-session reflection |
| `/carrel-mirror` | Summarize your research patterns from reflections and logs |
| `/carrel-feedback` | Create an anonymized feedback digest you can share |
| `/carrel-share` | Write a handbook for a collaborator joining your vault |
| `/carrel-automate` | Set up overnight vault maintenance |
| `/carrel-teammates` | Add or review other AI models as teammates (Codex, Gemini, Kimi) |
| `/carrel-migrate` | Check for updates and apply them |

## How Carrel works

Carrel follows 6 principles:

1. You never need to use a terminal. Everything happens in conversation.
2. Carrel interviews you first, then installs only what you need.
3. Obsidian is the shared workspace. You see a notebook. Claude sees Markdown files.
4. Your data stays on your computer unless you choose a cloud tool.
5. Choosing your tools teaches you what each tool does.
6. Each session can end with a reflection that improves Carrel.

Carrel uses 4 trust levels for automation: advisory, consultative, delegated and partnership. The `carrel` tool checks the trust level before any action that needs it. To see what your vault allows, run `carrel trust list --vault .`.

Carrel keeps judgment and file work apart. Skills hold the judgment, such as interviews and synthesis. The `carrel` tool does the file work. Slash commands are thin wrappers. Read [the v0.9.0 architecture spec](planning/specs/014-cc-plugin-v090.md) and [the command conventions](commands/CONVENTIONS.md) for details. To see why a hook did or did not act, set `CARREL_HOOK_DEBUG=1`.

## Platform support

The install scripts and setup flow work on macOS, Linux and Windows.

| Tool | What it does | Notes |
|------|--------------|-------|
| Obsidian | Notebook app for your vault | Install command differs by system |
| liteparse | Converts PDFs on your computer | `npm install -g @llamaindex/liteparse` |
| coli | Transcribes audio on your computer | `npm install -g @marswave/coli`; some formats need `ffmpeg` |
| defuddle | Captures web pages | `npm install -g defuddle` |
| markitdown | Converts Word, slides and spreadsheets | Included with Carrel |
| gws | Exports Google Docs | `npm install -g @googleworkspace/cli`; Windows sign-in needs a workaround |
| mineru | Converts complex PDFs in the cloud | Needs `MINERU_API_KEY` |
| mistral_ocr | Reads scanned PDFs in the cloud | Needs `MISTRAL_API_KEY` |
| paddleocr | Reads scanned PDFs on your computer | Optional, large install |

## Optional MCP servers

Depending on your interview answers, setup may add these servers to your project:

| Server | When Carrel adds it | What you need |
|--------|---------------------|---------------|
| [vox-mcp](https://github.com/linxule/vox-mcp) | You want to use other AI models, such as Gemini or GPT | At least one provider key, such as `OPENROUTER_API_KEY` |
| mineru-mcp | You work with complex PDFs that have tables and figures | `MINERU_API_KEY` |
| Mistral OCR | You have scanned PDFs and accept cloud processing | `MISTRAL_API_KEY` |
| [zotero-mcp](https://github.com/54yyyu/zotero-mcp) | You use Zotero | `ZOTERO_API_KEY` and `ZOTERO_LIBRARY_ID` |

Read [the API keys guide](docs/api-keys-guide.md) to set these up.

## Use Carrel with qualitative methods

For Gioia coding, grounded theory and other qualitative methods, add [the Interpretive Orchestration plugin](https://github.com/linxule/interpretive-orchestration):

```bash
claude plugin marketplace add linxule/interpretive-orchestration
```

```bash
claude plugin install interpretive-orchestration@interpretive-orchestration --scope user
```

## For contributors

`skills/carrel/` is the source of the portable skill. `plugins/carrel/` is generated from it. After you edit the skill, run `python scripts/sync-agent-plugin.py`. Read [the cross-host parity assessment](planning/reports/015-cross-host-feature-parity-assessment.md) to see which features each app supports.

## License

MIT
