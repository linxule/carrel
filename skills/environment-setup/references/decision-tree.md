> **Platform source:** Read `audit.platform` from `carrel env doctor --format json` and treat it as the canonical OS signal for this entire document. Use that value for every install recommendation below. Do not infer the OS from narrative text or from `AuditResult.os`.

# Decision Tree

Maps interview answers + hardware audit → configuration plan.

## Prerequisites (Bootstrap)

The canonical installers are `install.sh` on macOS/Linux and `install.ps1` on Windows. If a researcher has not run the appropriate installer yet, check for missing tools during the hardware audit and install what's needed:

| Tool | Purpose | Install |
|------|---------|---------|
| Xcode CLI tools | git, compilers | `xcode-select --install` |
| Homebrew | package manager | Official installer |
| Node.js | runtime for some tools | `brew install node` |
| bun | fast JS runtime (required for coli, defuddle) | Use the platform table below |
| uv | Python tools | `brew install uv` |
| gh | GitHub | `brew install gh` |

See `references/toolchain-guide.md` for the full toolchain policy and `references/obsidian-setup.md` for the Obsidian handoff details after install.

### Installing Obsidian
| Platform | Command |
|----------|---------|
| macOS | `brew install --cask obsidian` |
| Windows | `winget install Obsidian.Obsidian` |
| Linux | Download AppImage from https://obsidian.md |

Claude should read `audit.platform` and use the matching row.

### Installing ffmpeg
| Platform | Command |
|----------|---------|
| macOS | `brew install ffmpeg` |
| Windows | `winget install Gyan.FFmpeg` |
| Linux | `apt install -y ffmpeg  # or dnf install ffmpeg on Fedora` |

Claude should read `audit.platform` and use the matching row.

### Installing Zotero
| Platform | Command |
|----------|---------|
| macOS | `brew install --cask zotero` |
| Windows | `winget install Zotero.Zotero` |
| Linux | Download from https://www.zotero.org/download/ |

Claude should read `audit.platform` and use the matching row.

### Installing bun
| Platform | Command |
|----------|---------|
| macOS | `curl -fsSL https://bun.sh/install | bash` |
| Windows | `powershell -c "irm https://bun.sh/install.ps1 | iex"` |
| Linux | `curl -fsSL https://bun.sh/install | bash` |

Claude should read `audit.platform` and use the matching row.

### Installing gws
| Platform | Command |
|----------|---------|
| macOS | `npm install -g @googleworkspace/cli` |
| Windows | `npm install -g @googleworkspace/cli` |
| Linux | `npm install -g @googleworkspace/cli` |

Claude should read `audit.platform` and use the matching row.

## Core (Always Install)

These are set up for every researcher regardless of answers:

| Component | Method | Notes |
|-----------|--------|-------|
| Vault folder structure | `carrel vault init` | Customized based on field |
| `.obsidian/` config | `carrel vault init` | Core plugins, templates; see `references/obsidian-setup.md` |
| `CLAUDE.md` | Generated | Researcher profile + guidelines |
| Cheat sheet | `carrel vault init` writes initial; `carrel vault cheatsheet --force` regenerates | Reference card in `_meta/` |
| liteparse | `bun add -g @llamaindex/liteparse` | Local PDF conversion — always install |
| markitdown | Auto-installed with carrel | Office docs (Word, PowerPoint, Excel), EPUB, Jupyter |

## Sensitivity Assessment

**Schema note**: `sensitivity` is the `Sensitivity` enum (`"high" | "medium" | "low"`) and `cloud_consent` is a `bool` on `ResearcherProfile`. Together they encode the policy. Do NOT write string values like `"local_only"` to `cloud_consent` — that's the legacy v0.2-era schema and Pydantic will reject it.

```
Interview: "Do you work with sensitive data?"

→ HIGH (IRB data, interview transcripts, unpublished manuscripts):
  - Set sensitivity: "high" and cloud_consent: false in environment.json
  - CLAUDE.md: "ALWAYS warn before using any cloud service"
  - Default to local conversion tools only
  - liteparse (PDF), coli (audio), markitdown (Office docs) are all local — safe
  - mineru (cloud PDF service) not available in this profile
  - groq (cloud transcription) not available in this profile

→ MEDIUM (unpublished drafts, but no IRB/participant data):
  - Set sensitivity: "medium" and cloud_consent: false in environment.json
  - CLAUDE.md: "Prefer local tools. Ask before cloud processing."
  - Cloud tools available but not default; researcher must confirm

→ LOW (published papers, public materials, course content):
  - Set sensitivity: "low" and cloud_consent: true in environment.json
  - CLAUDE.md: "Cloud and local tools both available"
  - Can use all tools freely
```

## Reference Manager

```
Interview: "Do you use a reference manager?"

→ ZOTERO:
  - Check if Zotero app is installed (hardware audit)
  - If not installed, use the "Installing Zotero" table above and choose the row from `audit.platform`
  - Add zotero to project configuration
  - Need: ZOTERO_API_KEY, ZOTERO_LIBRARY_ID
  - Guide through key setup (see API Key Storage section below)
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
    - Install coli (works on all Macs, local, free):
        bun add -g @marswave/coli
    - Install ffmpeg if not present: use the "Installing ffmpeg" table above and choose the row from `audit.platform`
    - Note: coli runs entirely on your machine — nothing leaves it

  → NOT SENSITIVE:
    - Install coli for local transcription (default):
        bun add -g @marswave/coli
        plus the matching ffmpeg command from the "Installing ffmpeg" table above
    - Offer groq as a cloud option for large batches or faster turnaround:
        "There's also a fast cloud service (Groq) — useful if you have a lot of
        recordings. It adds timestamps. Needs a free account."
        GROQ_API_KEY from console.groq.com (free tier available)
        Complexity: LOW friction

→ NO:
  - Skip transcription setup
  - Note: available later if needed
```

## YouTube Transcription

```
Interview: "Do you use YouTube lectures, talks, or video courses?"

→ YES:
  Two options — present both, let researcher choose:

  → LOCAL (default — captions with timestamps):
    - Uses youtube-transcript-api (auto-installed with carrel)
    - Works immediately, no account needed, free
    - Pulls available captions with timestamps
    - Best for: English-captioned lectures, conference talks
    - Limitation: quality depends on the video's captions

  → CLOUD (Gemini — AI-processed transcription):
    - Gemini reads the video directly — better for non-captioned videos,
      foreign language content, or when you need higher accuracy
    - Needs a free Gemini key from ai.google.dev
    - Complexity: LOW friction
    - Researcher uses: carrel transcript create <youtube-url> --tool gemini
    - "Using --tool gemini is how you tell it to use the cloud service.
      No separate setting needed."

→ NO:
  - Skip. youtube-transcript-api is already installed — available anytime.
```

## Web Capture

```
Interview: "Do you save articles or web pages to read later?"

→ YES:
  - Install defuddle (smart content extraction, strips navigation and ads):
      bun add -g defuddle
  - Complexity: ZERO friction — one command, works immediately
  - Researcher workflow: drop a URL into the chat, carrel saves it as clean text
  - "It pulls the article text and discards everything else — no ads, no menus."

→ NO:
  - Skip. defuddle is lightweight — install anyway if they're unsure.
```

## Post-Interview Tool Installation

After the interview, install additional tools based on what the researcher needs. Follow `references/toolchain-guide.md` strictly — never install conda, pyenv, npm, or pip directly.

```
Interview results → Install silently:

→ Works with PDFs (almost every researcher):
  - bun add -g @llamaindex/liteparse
  - Local, free, no account. Always install this.

→ Records audio (interviews, meetings):
  - Use the matching ffmpeg command from the "Installing ffmpeg" table above
  - bun add -g @marswave/coli (local transcription — works on all supported platforms)

→ Saves web pages or articles:
  - bun add -g defuddle

→ Works with Word, PowerPoint, Excel, EPUB, Jupyter notebooks:
  - markitdown is auto-installed with carrel — nothing extra needed

→ Needs multi-model access (Gemini, GPT, etc.):
  - uv is already installed via bootstrap — no additional setup
```

Summarize installations in plain language: "I set up a tool to handle your audio files" — not "I installed coli via bun."

## PDF Handling

```
Interview: "What kinds of files do you work with most?"
+ Hardware audit + Sensitivity check

→ ALWAYS install liteparse (local, free, no account):
  bun add -g @llamaindex/liteparse
  Handles most academic papers well. Fast (~500 pages/2 sec). Sensitive-data safe.

→ COMPLEX PDFs (scanned, tables, multi-column, figures, formulas):
  + NOT SENSITIVE:
    - Offer mineru as a higher-quality cloud option for complex cases
    - "For papers with dense tables and figures, there's a cloud service that
      handles them much better. It requires a free account."
    - MINERU_API_KEY from mineru.net (free signup)
    - Complexity: MEDIUM friction (signup required)
    - Researcher uses: carrel paper convert paper.pdf --tool mineru
    - "Using --tool mineru is how you tell it to use the cloud service."
  + SENSITIVE (IRB data, confidential docs):
    - liteparse only — no cloud
    - "Everything stays on your machine."

→ markitdown handles Word, PowerPoint, Excel, EPUB, Jupyter — not PDF.
  Routing is automatic; researchers don't need to know which tool handles what.
```

## Google Workspace Documents

```
Interview: "Do you work in Google Docs or Google Sheets?"

→ YES:
  ⚠ HIGH FRICTION WARNING — present honestly, don't push:

  "There's a way to pull Google Docs and Sheets directly into your vault — it
  exports them as clean text automatically. The catch: it requires setting up
  a Google Cloud project and an authorization flow, which takes 15–30 minutes
  and involves a few technical steps. It's worth it if you live in Google Docs,
  but I'd suggest waiting until after we have everything else working."

  If researcher wants it now:
  - Install gws using the "Installing gws" table above and choose the row from `audit.platform`
  - Guide through: Google Cloud Console → create project → enable Drive API →
    OAuth consent screen → download credentials → gws auth login
  - Point to: references/gws-setup-guide.md for step-by-step

  Once configured:
  - gws exports Google Docs/Sheets as files → carrel converts normally
  - Google Docs → markitdown → Markdown
  - Google Sheets → markitdown → Markdown table

  If researcher wants it later:
  - Note as "available later" in environment.json
  - "You can add this anytime — just let me know."

→ NO:
  - Skip entirely.
```

## Cloud Storage

```
Interview: "Where do you store files?"

→ GOOGLE DRIVE:
  - Note in environment.json
  - Files accessible via local sync folder (Google Drive for Desktop)
  - Researcher can drag files into vault or share paths with Claude
  - For Google Docs/Sheets specifically: see Google Workspace section above

→ DROPBOX / ONEDRIVE:
  - Same approach — files accessible via local sync folders
  - No special setup needed

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
  - Mention Interpretive Orchestration plugin as optional (see Optional Plugins)

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

## Research Databases (Bases)

```
Assessed from interview context — don't ask directly about "databases."
Instead, infer from their workflow and paper volume.

→ WORKS WITH MANY PAPERS (10+ papers, systematic review, literature review):
  - Create paper-tracker.base in vault root during scaffold
  - Create reading-progress.base in vault root during scaffold
  - If early-stage (researcher says "just starting", "first year", "beginning"):
    → Prefer SMALL SCALE path. Offer paper-tracker when papers accumulate.
  - Present: "I set up a paper tracker — open it in Obsidian and you'll see
    a sortable table of all your papers, filterable by theme, method, or status."

→ QUALITATIVE RESEARCHER WITH INTERVIEWS:
  - Create interview-tracker.base in vault root during scaffold
  - Present: "There's an interview tracker that shows which transcripts
    are coded and which need follow-up. It updates automatically."

→ ACTIVELY WRITING (thesis, paper, dissertation):
  - Create writing-tracker.base in vault root during scaffold
  - Present: "I added a writing tracker — it shows your sections, word counts,
    and deadlines in one view."

→ SMALL SCALE / UNSURE:
  - Create reading-progress.base only (lightweight, always useful)
  - Skip paper-tracker and interview-tracker unless they accumulate files later
  - The session-start hook or vault-ops skill can suggest adding trackers
    when file counts grow

Note: Bases require structured frontmatter in notes (status, tags, etc.).
The convert, transcribe, and vault-ops skills already add this frontmatter.

Note: carrel vault init copies .base files automatically based on the profile's
preferences dict. Set preferences.qualitative, preferences.many_papers, or
preferences.writing to true before running scaffold. reading-progress.base is
always included regardless of profile.
```

## Multi-Model Access (Vox)

```
Interview: "Would you find it useful to get perspectives from different AI models?"
(Or detected from: researcher mentions Gemini, GPT, wanting a second opinion, etc.)

→ YES — INTERESTED:
  - Explain: "I can connect you to other AI models — Gemini, GPT, Grok, and more.
    You'd ask me to 'check this with Gemini' or 'get GPT's take on this'. Useful for
    getting a different perspective or using models with special strengths."
  - Ask: "Do you already have accounts with any providers, or would you like
    the simplest option?"

  → HAS SPECIFIC KEYS (e.g., Gemini, OpenAI):
    - Configure with their specific provider keys
    - Help save keys securely (see Key Storage below)

  → WANTS SIMPLEST OPTION:
    - Recommend OpenRouter: one key, access to many models, pay-per-use
    - Guide: create account at openrouter.ai, get key
    - Add OPENROUTER_API_KEY to configuration

  → WANTS FREE OPTION:
    - Recommend Google Gemini: free tier is generous (1M token context)
    - Guide: create key at ai.google.dev
    - Add GEMINI_API_KEY to configuration

→ NO — NOT INTERESTED:
  - Skip. Note as "available later" in environment.json.

→ MAYBE LATER:
  - Note in environment.json. Don't configure now.
  - Researcher can say "I'd like to add other AI models" at any time.
```

### Key Storage

When configuring tools that need keys, Claude should help the researcher store them securely. Choose the approach based on the user's context:

**For Claude Desktop users (recommended for researchers):**
1. Store the key directly in the project configuration under the `env` field
2. Simplest approach — no terminal required, the key is private and stays on their machine
3. Tell the researcher: "I'll save your key in your project configuration. It stays on your computer and persists across sessions."

**For terminal-comfortable users:**
1. Store in shell profile for system-wide availability:
   - macOS: append `export GEMINI_API_KEY="..."` to `~/.zshrc`
2. Reference in project configuration: `"GEMINI_API_KEY": "${GEMINI_API_KEY}"`
3. More secure on shared machines since the key isn't in a project file

**Security note:** Keys stored in project configuration are plaintext on the researcher's machine. Acceptable for personal research environments — the file is local and not shared. For shared machines, use shell profile variables instead.

## Optional Plugins

These are plugins the researcher might benefit from. Mention when relevant — don't push.

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
  - Offer the matching command from the "Installing Obsidian" table above
  - This is a human step — Claude can't click through the installer
```

## Summary: Present the Plan

After running through the tree, summarize to the researcher:

"Here's what I'd recommend for your setup:

**I'll set up now:**
- [list of automated components]

**You'll need to do:**
- [list of human steps — install Obsidian, create accounts, etc.]

**Available later (when you're ready):**
- [list of optional components noted for future — e.g., Google Workspace, Zotero, multi-model access]

Does this sound right?"

---

## Tool Complexity Reference

Quick reference for when to push vs. when to offer:

| Tool | Friction | When to recommend |
|------|----------|------------------|
| liteparse | Zero | Always install |
| markitdown | Zero | Auto-installed with carrel |
| coli | Zero | Whenever audio is involved |
| defuddle | Zero | Whenever web is involved |
| youtube-transcript-api | Zero | Auto-installed with carrel |
| Gemini key | Low | YouTube cloud, complex PDFs (non-sensitive) |
| Groq key | Low | Audio cloud, large batches |
| mineru key | Medium | Complex PDFs only, non-sensitive |
| Google Workspace (gws) | HIGH | Only if they live in Google Docs; warn about setup time |
