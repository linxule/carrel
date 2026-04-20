---
description: Set up your AI research environment — interview, configure tools, scaffold Obsidian vault
---

# /carrel-setup — Research Environment Setup

Full onboarding for a new research environment. Interviews the researcher, audits the machine, configures tools, and scaffolds an Obsidian vault.

## When to Use

- First time opening a project with Carrel installed
- Researcher says "set up", "get started", "configure my environment"
- Project folder has no `.carrel/` directory

## What Happens

### Phase 1: The Conversation (~10 min)

Deploy `@setup-interviewer` for a natural conversational interview, or follow the protocol in `skills/environment-setup/references/interview-protocol.md`.

Cover: research area, file types, data sensitivity, existing tools, comfort level with AI.

### Phase 2: Silent Audit (~30 sec)

Run `skills/environment-setup/scripts/check-environment.js` to detect hardware, installed tools, and existing configurations. Summarize findings in plain language — never show raw output.

### Phase 3: The Plan (~2 min)

Consult `skills/environment-setup/references/decision-tree.md` to map answers + audit to a configuration plan. Present the plan conversationally and get researcher approval.

### Phase 4: Scaffold (~2 min)

Run `skills/environment-setup/scripts/create-vault.js` to create:
- Vault folder structure
- `.obsidian/` configuration
- `.carrel/environment.json`
- Note templates
- Friction log

Then generate `CLAUDE.md` at project root with researcher profile, tool inventory, and behavioral guidelines. This file auto-loads in all future sessions.

### Phase 5: Optional MCPs

If the decision tree indicates mineru or zotero, add to project `.mcp.json` and guide through API key setup.

### Phase 6: Human Steps

Tell the researcher what THEY need to do:
- Install Obsidian (offer `brew install obsidian` or download from obsidian.md)
- Open Obsidian → "Open folder as vault" → select this project folder
- Install Web Clipper for their browser

### Phase 7: Cheat Sheet & Verification

Run `skills/environment-setup/scripts/generate-cheatsheet.js` to create a customized reference card at `_meta/cheat_sheet.md`.

Test one operation: "Drop a PDF or Word file and I'll convert it to show you how it works."

### Phase 8: Overnight Maintenance (Optional)

Offer automation: "Carrel can maintain your vault between sessions — processing new files, checking health, surfacing connections. Costs about $3-8/month with Sonnet."

If interested → run `/carrel-automate` inline. If not → skip, mention they can always run `/carrel-automate` later.

### Phase 9: Handoff

Point to the cheat sheet in Obsidian. Confirm everything is working. "Next time you open Claude Desktop with this folder, I'll remember everything."

Then offer next steps based on the researcher's profile (read from `.carrel/environment.json`):

- **Always**: "Run `/carrel-status` anytime to verify the setup."
- **If `claude_code_familiarity == "new"`**: "If you're new to Claude Code as a tool, try `/powerup` (if your install has it) for a guided tour of the assistant itself — separate from Carrel."
- **If `collaborators == true`**: "When you're ready to bring a collaborator into this vault, run `/carrel-share` — it generates a vault-specific handbook tailored to whoever is joining."

Skip the conditional pointers when the corresponding fields are missing or don't match — don't guess.

## Related

- **Skill**: `environment-setup` (full orchestration logic)
- **Agent**: `@setup-interviewer` (conversational interview)
- **Commands**: `/carrel-status` (check setup health after initial setup)
