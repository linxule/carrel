---
description: Check what tools are installed and working in your research environment
---

# /carrel-status — Environment Health Check

Shows what's configured, what's working, and what capabilities are available or missing.

## When to Use

- Researcher asks "what's installed?", "check my setup", "what tools do I have?"
- Troubleshooting: something that used to work isn't working
- After adding a new tool or MCP

## What Happens

1. Read `.carrel/environment.json` for saved configuration
2. Run `skills/environment-setup/scripts/check-environment.js` for live audit
3. Compare saved config vs actual state
4. Report in plain language

## Output Format

Present results conversationally:

"Here's your current setup:

**Working:**
- Document conversion (markdownify) — converts PDFs, Word docs, web pages
- Obsidian vault at ~/Documents/Research — 23 notes, 8 papers
- Note templates ready

**Not configured (available if you want):**
- Complex PDF conversion (MineRU) — for papers with tricky tables
- Zotero connection — to search your reference library from here

**Issues:**
- [any detected problems]

Want me to set up any of the missing tools?"

## Related

- **Skill**: `environment-setup` (status mode)
- **Commands**: `/carrel-setup` (full setup if not configured yet)
