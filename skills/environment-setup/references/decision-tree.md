# Decision Tree

Maps interview answers + hardware audit → configuration plan.

## Prerequisites (Bootstrap)

The bootstrap script (`bootstrap.sh`) handles machine-level prerequisites before the plugin runs. If a researcher hasn't run it, check for missing tools during the hardware audit and install what's needed:

| Tool | Purpose | Install |
|------|---------|---------|
| Xcode CLI tools | git, compilers | `xcode-select --install` |
| Homebrew | package manager | Official installer |
| Node.js | MCP servers (npx) | `brew install node` |
| uv | Python tools | `brew install uv` |
| gh | GitHub CLI | `brew install gh` |

See `references/toolchain-guide.md` for the full toolchain policy (what to install, what to avoid).

## Core (Always Install)

These are set up for every researcher regardless of answers:

| Component | Method | Notes |
|-----------|--------|-------|
| Vault folder structure | `create-vault.js` | Customized based on field |
| `.obsidian/` config | `create-vault.js` | Core plugins, templates |
| `CLAUDE.md` | Generated | Researcher profile + guidelines |
| Cheat sheet | `generate-cheatsheet.js` | Reference card in `_meta/` |
| markdownify-mcp | Plugin `.mcp.json` | Already bundled — PDF, Word, web, audio |

## Sensitivity Assessment

```
Interview: "Do you work with sensitive data?"

→ HIGH (IRB data, interview transcripts, unpublished manuscripts):
  - Set cloud_comfort to "local_only" in environment.json
  - CLAUDE.md: "ALWAYS warn before using any cloud API"
  - Default to local conversion tools
  - Flag mineru-mcp as cloud-based if using API mode
  - Note: markdownify-mcp runs locally — safe for sensitive data

→ MEDIUM (unpublished drafts, but no IRB/participant data):
  - Set cloud_comfort to "prefer_local"
  - CLAUDE.md: "Prefer local tools. Ask before cloud processing."
  - Cloud tools available but not default

→ LOW (published papers, public materials, course content):
  - Set cloud_comfort to "comfortable_with_cloud"
  - CLAUDE.md: "Cloud and local tools both available"
  - Can use all tools freely
```

## Reference Manager

```
Interview: "Do you use a reference manager?"

→ ZOTERO:
  - Check if Zotero app is installed (hardware audit)
  - Add zotero-mcp to project .mcp.json
  - Need: ZOTERO_API_KEY, ZOTERO_LIBRARY_ID
  - Guide through API key setup (docs/api-keys-guide.md)
  - If they're not ready now: note as "available later" in environment.json

→ MENDELEY / ENDNOTE:
  - Note: "No direct integration yet. Papers can still be converted manually."
  - Future capability — skip for now

→ NONE:
  - Skip. The vault's papers/ folder serves as a lightweight library.
```

## Audio Transcription

```
Interview: "Do you record meetings or interviews?"

→ YES:
  Hardware audit: check Apple Silicon + RAM

  → SENSITIVE DATA (IRB interviews, participant recordings):
    - MUST use local transcription only
    - Capable hardware (Apple Silicon, 16GB+):
      Add mlx-whisper-mcp to project .mcp.json
    - Weak hardware:
      Note limitation — local transcription may be slow
      markdownify audio-to-markdown as fallback (basic quality)
    - Install ffmpeg if not present: brew install ffmpeg

  → NOT SENSITIVE + CAPABLE HARDWARE:
    - Add mlx-whisper-mcp (local, fast, free)
    - Note Groq Whisper as cloud option for large batches
    - Install ffmpeg if not present

  → NOT SENSITIVE + WEAK HARDWARE:
    - Configure Groq Whisper (cloud, $0.04/hr, fastest)
    - Needs GROQ_API_KEY — guide through setup
    - markdownify as fallback

  → YOUTUBE / VIDEO LECTURES:
    - If vox-mcp configured with Gemini: YouTube URLs go straight to Gemini
      (one-step, no download, multimodal — uses audio + visual cues)
    - If no vox: markdownify youtube-to-markdown (captions only)

→ NO:
  - Skip transcription setup
  - Note: available later if needed
```

## Post-Interview Tool Installation

After the interview, install additional tools based on what the researcher needs. Follow `references/toolchain-guide.md` strictly — never install conda, pyenv, npm alternatives, etc.

```
Interview results → Install silently:

→ Records audio (interviews, meetings):
  - brew install ffmpeg (if not present)

→ Needs vox-mcp (multi-model access):
  - uv is already installed via bootstrap
  - No additional Python setup needed

→ Works with LaTeX or EPUB:
  - brew install pandoc

→ Everything else:
  - Node.js + markdownify-mcp covers it (already installed)
```

Summarize installations in plain language: "I set up a tool to handle your audio files" — not "I installed ffmpeg via Homebrew."

## Complex PDF Handling

```
Interview: "What kinds of files do you work with most?"
+ Hardware audit: types of PDFs

→ COMPLEX PDFs (scanned, tables, multi-column, figures):
  - markdownify-mcp handles basic PDFs
  - Recommend adding mineru-mcp for complex cases
  - Need: MINERU_API_KEY from mineru.net
  - WARNING: MineRU API is cloud-based — flag if sensitivity is HIGH
  - Alternative: suggest manual Adobe/Google Docs conversion for sensitive docs

→ SIMPLE PDFs (text-based, single column):
  - markdownify-mcp is sufficient
  - No additional setup needed
```

## Cloud Storage

```
Interview: "Where do you store files?"

→ GOOGLE DRIVE:
  - Note in environment.json
  - Researcher can share files with Claude by providing paths or dropping files
  - Future: Google Drive MCP connector (not yet stable enough to recommend)

→ DROPBOX / ONEDRIVE:
  - Same approach — note for future integration
  - Files accessible via local sync folders

→ LOCAL ONLY:
  - Simplest case — everything in the vault
```

## Vault Customization

```
Interview: "What does a typical work week look like?"

→ QUALITATIVE RESEARCHER (interviews, fieldwork, coding):
  - Keep transcripts/ folder
  - Add notes/fieldwork/ subfolder
  - Templates: add interview-note template
  - Mention Interpretive Orchestration plugin as optional (see Optional Plugins below)

→ QUANTITATIVE RESEARCHER (data analysis, statistics):
  - Rename transcripts/ → data/
  - Add notes/analysis/ subfolder
  - Templates: adjust paper template for methods/results emphasis

→ MIXED METHODS:
  - Keep all default folders
  - Add notes/analysis/ subfolder

→ PRIMARILY WRITING (papers, talks, blog):
  - Emphasize drafts/ and talks/
  - Templates: add talk-outline template

→ PRIMARILY TEACHING + ADMIN:
  - Emphasize admin/ and notes/
  - Templates: add course-note template
  - De-emphasize papers/ and transcripts/
```

## Multi-Model Access (Vox)

```
Interview: "Would you find it useful to get perspectives from different AI models?"
(Or detected from: researcher mentions Gemini, GPT, wanting a second opinion, etc.)

→ YES — INTERESTED:
  - Explain: "I can connect you to other AI models — Gemini, GPT, Grok, and more.
    You'd ask me to 'check this with Gemini' or 'get GPT's take on this'. Useful for
    getting a different perspective or using models with special strengths."
  - Ask: "Do you already have API keys with any providers, or would you like
    the simplest option?"

  → HAS SPECIFIC KEYS (e.g., Gemini, OpenAI):
    - Add vox-mcp to project .mcp.json with their specific provider keys
    - Help save API keys securely (see API key storage below)

  → WANTS SIMPLEST OPTION:
    - Recommend OpenRouter: one key, access to many models, pay-per-use
    - Guide: create account at openrouter.ai, get API key
    - Add vox-mcp to project .mcp.json with OPENROUTER_API_KEY

  → WANTS FREE OPTION:
    - Recommend Google Gemini: free tier is generous (1M token context)
    - Guide: create key at aistudio.google.com
    - Add vox-mcp to project .mcp.json with GEMINI_API_KEY

→ NO — NOT INTERESTED:
  - Skip. Note as "available later" in environment.json.
  - Claude (the host model) handles everything by default.

→ MAYBE LATER:
  - Note in environment.json. Don't configure now.
  - Researcher can say "I'd like to add other AI models" at any time.
```

### API Key Storage

When configuring vox or other MCPs that need API keys, Claude should help the researcher store them securely. Choose the approach based on the user's context:

**For Claude Desktop users (GUI-only, recommended for researchers):**
1. Store the key directly in the project `.mcp.json` under the `env` field
2. This is the simplest approach — no terminal required, the key is private and local
3. Example:
   ```json
   "vox": {
     "command": "uv",
     "args": ["run", "--directory", "/path/to/vox-mcp", "python", "server.py"],
     "env": { "GEMINI_API_KEY": "the-actual-key-here" }
   }
   ```
4. Tell the researcher: "I'll save your API key in your project configuration. It stays on your computer and persists across sessions."

**For CLI / terminal-comfortable users:**
1. Store in shell profile for system-wide availability:
   - macOS: append `export GEMINI_API_KEY="..."` to `~/.zshrc`
   - Linux: append to `~/.bashrc`
2. Then reference in `.mcp.json`: `"env": { "GEMINI_API_KEY": "${GEMINI_API_KEY}" }`
3. This is more secure on shared machines since the key isn't in a project file

**On Windows:**
1. Desktop users: store directly in `.mcp.json` env values (simplest)
2. Advanced: use system environment variables via Settings → System → Environment Variables

**Security note:** API keys stored in `.mcp.json` are plaintext on the researcher's machine. This is acceptable for personal research environments — the file is local, private, and not shared. For shared machines, use shell profile env vars instead.

## Optional Plugins

These are Claude Code plugins the researcher might benefit from. Mention when relevant — don't push. Same approach as optional MCPs: note as "available later" if they're not ready.

```
→ QUALITATIVE METHODOLOGY (Gioia, grounded theory, interpretive work):
  - Recommend: Interpretive Orchestration plugin
  - "There's a plugin specifically for qualitative coding — Gioia method,
    grounded theory, that kind of thing. Want me to install it?"
  - Install: claude plugin marketplace add linxule/interpretive-orchestration

→ OTHER METHODOLOGIES:
  - No additional plugins currently. Carrel + research-partner handles general work.

→ NOT SURE / LATER:
  - Note in environment.json. Don't configure now.
```

## Obsidian Setup

```
Always:
  - Scaffold .obsidian/ with core plugins
  - Configure templates to point to _templates/
  - Set inbox/ as default new file location

Hardware audit: "Is Obsidian installed?"

→ YES:
  - Just need to "Open folder as vault" in Obsidian
  - Check for useful existing plugins

→ NO:
  - Offer: "brew install obsidian" (if brew available)
  - Or: "Download from obsidian.md"
  - This is a human step — Claude can't click through the installer
```

## Summary: Present the Plan

After running through the tree, summarize to the researcher:

"Here's what I'd recommend for your setup:

**I'll set up now:**
- [list of automated components]

**You'll need to do:**
- [list of human steps — install Obsidian, Web Clipper, etc.]

**Available later (when you're ready):**
- [list of optional components noted for future]

Does this sound right?"
