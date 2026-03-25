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

Run `scripts/check-environment.js` silently. Consult `references/hardware-audit.md` for detailed audit commands and output formatting. It detects:
- OS, architecture, RAM, disk space
- Installed tools (node, python, pandoc, ffmpeg, obsidian)
- Existing MCP configurations
- Available MCP connections

Do NOT show raw output to the researcher. Summarize findings in plain language:
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

Run `scripts/create-vault.js` to create:
- Vault folder structure (inbox, papers, notes, transcripts, drafts, talks, admin)
- `.obsidian/` configuration (core plugins, templates setup)
- `.carrel/environment.json` (structured profile)
- `CLAUDE.md` (auto-loaded every session)
- `_templates/` (paper, meeting, reflection, daily note templates)
- `_meta/cheat_sheet.md` (customized reference card)

Consult `references/obsidian-setup.md` for .obsidian/ config details.
Consult `skills/vault-ops/templates/` for template contents.

### Step 5: Configure Optional MCPs

If the decision tree indicates mineru or zotero:
- Add them to the project `.mcp.json`
- Guide the researcher through API key setup (see `docs/api-keys-guide.md`)
- Or note as "available later" if they're not ready

### Step 6: Human Steps

Tell the researcher what THEY need to do (Claude can't install GUI apps):
- Install Obsidian: "Download from obsidian.md, or I can try `brew install obsidian` if you'd like"
- Open Obsidian → "Open folder as vault" → select this project folder
- Install Web Clipper for their browser (Chrome/Firefox/Safari extension store)

### Step 7: Verify & Generate Cheat Sheet

Run `scripts/generate-cheatsheet.js` to create a customized reference card at `_meta/cheat_sheet.md`. The template is in `references/cheatsheet-template.md`.

Test one operation end-to-end:
- "Let's test the setup. Drop a PDF or Word file in here and I'll convert it to your vault."

### Step 8: Wrap Up

- Confirm what's installed and working
- Point to the cheat sheet in Obsidian
- "Next time you open Claude Desktop with this folder, I'll remember everything."

## Scripts

### create-vault.js
Scaffolds the complete vault structure.

```bash
node "${CLAUDE_PLUGIN_ROOT}/skills/environment-setup/scripts/create-vault.js" \
  --project-path /path/to/project
```

Returns JSON with created/skipped files. Never overwrites existing content.
Researcher profile and sensitivity are written to `.carrel/environment.json` by Claude after the interview, not via script args.

### check-environment.js
Audits hardware and installed tools.

```bash
node "${CLAUDE_PLUGIN_ROOT}/skills/environment-setup/scripts/check-environment.js" \
  --project-path /path/to/project
```

Returns JSON with OS, arch, RAM, disk, installed tools, MCP status.

### generate-cheatsheet.js
Creates customized cheat sheet from environment.json.

```bash
node "${CLAUDE_PLUGIN_ROOT}/skills/environment-setup/scripts/generate-cheatsheet.js" \
  --project-path /path/to/project
```

Reads `.carrel/environment.json`, writes `_meta/cheat_sheet.md`.

## Related

- **Commands**: `/carrel-setup` triggers this skill
- **Agents**: `@setup-interviewer` (optional) provides richer conversational interview; the protocol in references/ works directly without it
- **Skills**: `vault-ops` for ongoing vault operations after setup
- **Hooks**: `check-environment.js` (SessionStart) uses the audit script
