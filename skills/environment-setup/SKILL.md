---
name: environment-setup
description: "This skill should be used when a researcher wants to set up their AI research environment, mentions 'setup', 'get started', 'configure', 'onboard', or when opening a project folder with no .carrel/ directory. Also triggers on 'what tools do I have', 'check my setup', 'add a new tool'."
---

# environment-setup

Orchestrates researcher onboarding: interview, hardware audit, tool configuration, Obsidian vault scaffolding, and cheat sheet generation. Detects whether this is a first-time setup, a returning user, or a troubleshooting request.

## When to Use

- User wants to set up a research environment from scratch
- Project folder has no `.carrel/` directory (first-time detection)
- User asks about their setup, wants to add tools, or troubleshoot
- User mentions "get started", "configure", "onboard", "set up"

## Mode Detection

Check for `.carrel/environment.json` in the project root:

- **Not found** → First-time setup (full interview + scaffold)
- **Found** → Returning user. Read the file and offer:
  - Status check (what's working, what's missing)
  - Add new capabilities (e.g., "I want to add Zotero")
  - Troubleshoot issues
  - Jump straight into work

## First-Time Setup Flow

### Step 1: Interview (conversational, ~10 min)

Deploy the `@setup-interviewer` agent for a conversational interview, or follow the protocol in `references/interview-protocol.md` directly. Both approaches produce the same output.

**Key principles:** Be warm and curious. Use plain language — never say "MCP", "CLI", or "API" unless the researcher does first. This is a conversation, NOT a form.

Cover these areas naturally:
- Research field and typical work
- File types they work with
- Sensitivity of data (IRB, unpublished work)
- Existing tools (Zotero, Google Drive, note-taking)
- Comfort level with AI and technology

Output: structured answers for environment.json.

### Step 2: Hardware & Tools Audit (silent, ~30 sec)

Run `carrel env doctor --format json` silently. Consult `references/hardware-audit.md` for output interpretation. It detects:
- OS, architecture, RAM, disk space
- Installed tools (node, python, pandoc, ffmpeg, obsidian)
- Existing tool configurations
- Hardware capability tier (high/medium/low)

Do NOT show raw output to the researcher. Translate findings into plain language:
"You're on a Mac with Apple Silicon and plenty of storage. I found Python and Node already installed."

### Step 3: Decision Tree (~2 min)

Consult `references/decision-tree.md` to map interview + audit → configuration plan.

Present the plan in plain language:
"Based on what you've told me, here's what I'd recommend setting up:
- Obsidian for your research vault (it's a note-taking app with a nice interface)
- A document converter so I can read your PDFs and Word files
- [If applicable] A connection to your Zotero library
- [If applicable] Audio transcription for your interview recordings

Does this sound right? Anything you'd add or skip?"

### Step 4: Scaffold Vault (~2 min)

Run `carrel vault init <path>` to create:
- Vault folder structure (inbox, papers, notes, transcripts, drafts, talks, admin)
- `.obsidian/` configuration (core plugins, templates setup)
- `.carrel/environment.json` (structured profile with defaults)
- `_templates/` (paper, meeting, reflection, daily note templates)
- `_meta/cheat_sheet.md` (customized reference card)

After scaffolding, update `.carrel/environment.json` with the researcher's profile from the interview.

### Step 5: Write Personalized CLAUDE.md

**This is critical.** Write a `CLAUDE.md` file in the vault root that encodes the researcher's preferences in natural language. Claude loads this file automatically every session — it's the bridge between the structured profile and Claude's judgment.

Write CLAUDE.md with these sections:

```markdown
# Research Environment — [Researcher Name]

## About This Researcher
[Field, role, what they're working on, what they care about — from the interview]

## Preferences
- Sensitivity: [HIGH/MEDIUM/LOW] — [what this means for this person]
- Cloud tools: [comfortable/prefer local/local only] — [specific guidance]
- [If cloud comfortable]: Preferred cloud tools: [gemini for YouTube, groq for audio, etc.]
- [If sensitive]: ALWAYS use local tools. Never send data to cloud APIs without explicit permission.

## Available Tools
[List what was installed and configured, in plain language]
- PDF conversion: liteparse (local) [+ mineru if configured]
- Audio: coli (local) [+ groq if configured]
- YouTube: [local captions / Gemini — based on what was set up]
- Web capture: defuddle
- [Zotero, vox, gws — if configured]

## How to Work With [Name]
[Comfort level, explanation preferences, proactiveness level — from interview]
- [beginner]: Explain what you're doing in plain language. Don't assume they know markdown or git.
- [advanced]: Be concise. They know the tools.

## Session Notes
[Leave empty — Claude can append notes here across sessions about what's working, what the researcher prefers, patterns noticed]
```

**Why Claude writes this, not a script:** You just did the interview. You know this person — their field, their concerns, their comfort level. A script can only template. You can write guidance that actually helps future-you work with this specific researcher.

**When to update CLAUDE.md:** Whenever the researcher's preferences change meaningfully (new tool added, sensitivity changed, new workflow discovered). Read `.carrel/environment.json` to verify CLAUDE.md is still in sync. If it's stale, update the relevant section.

### Step 6: Configure Optional Tools

If the decision tree indicates mineru, zotero, or gws:
- Add them to the project `.mcp.json` (for MCP-based tools like zotero/vox)
- Guide the researcher through API key setup (see API Key Storage section in `references/decision-tree.md`)
- For gws: see `references/gws-setup-guide.md` — this is a high-friction setup, set expectations
- Or note as "available later" if they're not ready

### Step 7: Human Steps

Tell the researcher what THEY need to do (Claude can't install GUI apps):
- Install Obsidian: "Download from obsidian.md, or I can try `brew install obsidian` if you'd like"
- Open Obsidian → "Open folder as vault" → select this project folder
- Install Web Clipper for their browser (Chrome/Firefox/Safari extension store)

### Step 8: Verify & Generate Cheat Sheet

Run `scripts/generate-cheatsheet.js` to create a customized reference card at `_meta/cheat_sheet.md`. The template is in `references/cheatsheet-template.md`.

Test one operation end-to-end:
- "Let's test the setup. Drop a PDF or Word file in here and I'll convert it to your vault."

### Step 9: Wrap Up

- Confirm what's installed and working
- Point to the cheat sheet in Obsidian
- "Next time you open Claude Desktop with this folder, I'll remember everything."

## Preference Changes (Mid-Session or Returning User)

When a researcher's preferences change:
1. Update `.carrel/environment.json` with the new values
2. Update the relevant section of `CLAUDE.md` to match
3. If tools changed: run `carrel env doctor` to verify availability

Examples:
- "I got a Gemini key" → update environment.json cloud_consent + tools_configured, update CLAUDE.md Available Tools section
- "My data is more sensitive now" → update sensitivity everywhere, update CLAUDE.md Preferences section to reflect local-only
- "I don't use transcription anymore" → note in CLAUDE.md, don't offer transcription proactively

The key principle: **environment.json is the structured truth, CLAUDE.md is the narrative truth.** Keep them in sync. When in doubt, read environment.json and verify CLAUDE.md matches.

## Scripts

### generate-cheatsheet.js
Creates customized cheat sheet from environment.json.

Reads `.carrel/environment.json`, writes `_meta/cheat_sheet.md`.

## Related

- **Commands**: `/carrel-setup` triggers this skill
- **Agents**: `@setup-interviewer` (optional) provides richer conversational interview; the protocol in references/ works directly without it
- **Skills**: `vault-ops` for ongoing vault operations after setup
- **Hooks**: SessionStart hook checks for `.carrel/` and surfaces researcher profile
