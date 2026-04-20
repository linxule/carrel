---
description: Set up your AI research environment — interview, configure tools, scaffold Obsidian vault
---

# /carrel-setup — Research Environment Setup

Full onboarding for a new research environment. Interviews the researcher, audits the machine, configures tools, and scaffolds an Obsidian vault.

## When to Use

- First time opening a project with Carrel installed
- Researcher says "set up", "get started", "configure my environment"
- Project folder has no `.carrel/` directory

## Time Expectations

Set realistic expectations up front. Total elapsed time for a thorough setup is **15-20 minutes of conversation with you (Claude) plus 10-15 minutes of human steps** (installing Obsidian, signing into things). It is fine to **pause between phases** — the setup is resumable. Natural pause points: after Phase 4 (vault scaffolded) and after Phase 7 (cheat sheet & verification).

## State Tracking

The setup writes `.carrel/setup-state.json` to track progress so the session-start hook can offer to resume if the researcher stops mid-flow. The Python `carrel vault init` initializes it after Phase 4. You (Claude) update `last_completed_phase` after each subsequent phase by editing the file, and set `completed_at` to today's ISO date when Phase 9 wraps. If the researcher pauses, leave `completed_at: null`; the hook will detect it and surface a resume prompt next session.

## What Happens

### Phase 1: The Conversation (~10 min)

Deploy `@setup-interviewer` for a natural conversational interview, or follow the protocol in `skills/environment-setup/references/interview-protocol.md`.

Cover: research area, file types, data sensitivity, existing tools, comfort level with AI.

### Phase 2: Silent Audit (~30 sec)

Run `carrel env doctor --format json` to detect hardware, installed tools, and existing configurations. Summarize findings in plain language — never show raw output.

### Phase 3: The Plan (~2 min)

Consult `skills/environment-setup/references/decision-tree.md` to map answers + audit to a configuration plan. Present the plan conversationally and get researcher approval.

### Phase 4: Scaffold (~2 min)

Run `carrel vault init <path>` to create:
- Vault folder structure (inbox, papers, notes, transcripts, drafts, talks, admin)
- `.obsidian/` configuration
- `.carrel/environment.json` (writes a default `ResearcherProfile`; replace with the interview profile below)
- Note templates + research-database `.base` files (selected from `preferences.*`)
- `_meta/cheat_sheet.md`, `_meta/my-environment.md`, `_meta/capability-log.md`, `_meta/friction_log.md`

After scaffolding, overwrite `.carrel/environment.json` with the researcher's profile from the interview (Claude does this directly — write the full `ResearcherProfile` JSON).

Then generate `CLAUDE.md` at project root with researcher profile, tool inventory, and behavioral guidelines. This file auto-loads in all future sessions.

**Natural pause point.** Ask the researcher: *"Your vault is set up and Claude knows your profile. We can keep going to optional tools and automation, or you can pause here and pick this up later — the session-start hook will remember where we stopped. Want to keep going?"*

- If they want to pause: leave `setup-state.json` as-is (`last_completed_phase: 4`, `completed_at: null`) — the hook will surface a resume prompt next session.
- If they want to continue: proceed to Phase 5.

> Note: if you're on Windows, some downstream tools below may not be available — see Platform Support in README.

### Phase 5: Optional MCPs [skippable]

If the decision tree indicates mineru or zotero, add to project `.mcp.json` and guide through API key setup. This phase is **fully optional** — say so to the researcher: "These add specific tools (Zotero integration, cloud PDF processing). Skip if you're not sure — you can add any of them later."

After this phase (whether you configured anything or skipped), update `setup-state.json` `last_completed_phase` to 5.

### Phase 6: Human Steps (~10-15 min real time)

Tell the researcher what THEY need to do (Claude can't install GUI apps):
- Install Obsidian:
  macOS: `brew install --cask obsidian`  
  Windows: `winget install Obsidian.Obsidian`  
  Linux: Download AppImage from https://obsidian.md/download
- Open Obsidian → "Open folder as vault" → select this project folder
- Install Web Clipper for their browser

After confirming these steps, update `setup-state.json` `last_completed_phase` to 6.

### Phase 7: Cheat Sheet & Verification

The vault scaffold (Phase 4) wrote a starter `_meta/cheat_sheet.md`. Regenerate it to reflect the personalized profile and any tools configured in Phases 5-6:

```bash
carrel vault cheatsheet --vault <path> --force
```

Then read the cheat sheet and edit it directly to add researcher-specific touches (workflow examples, named projects, custom shortcuts).

Test one operation: "Drop a PDF or Word file and I'll convert it to show you how it works."

After verification, update `setup-state.json` `last_completed_phase` to 7.

**Natural pause point.** Ask the researcher: *"That's the core setup done — you've got Obsidian, your tools work, and there's a cheat sheet. The remaining phases are about overnight automation and final handoff. Want to wrap up now or pause and finish later?"*

### Phase 8: Overnight Maintenance [skippable]

Offer automation: "Carrel can maintain your vault between sessions — processing new files, checking health, surfacing connections. Costs about $3-8/month with Sonnet on top of your Claude subscription."

If interested → run `/carrel-automate` inline. If not → skip, mention they can always run `/carrel-automate` later.

After this phase (configured or skipped), update `setup-state.json` `last_completed_phase` to 8.

### Phase 9: Handoff

Point to the cheat sheet in Obsidian. Confirm everything is working. "Next time you open Claude Desktop with this folder, I'll remember everything."

Then offer next steps based on the researcher's profile (read from `.carrel/environment.json`):

- **Always**: "Run `/carrel-status` anytime to verify the setup."
- **If `claude_code_familiarity == "new"`**: "If you're new to Claude Code as a tool, run `/powerup` for a guided tour of the assistant itself — interactive lessons with animated demos, separate from Carrel."
- **If `collaborators == true`**: "When you're ready to bring a collaborator into this vault, run `/carrel-share` — it generates a vault-specific handbook tailored to whoever is joining."

Skip the conditional pointers when the corresponding fields are missing or don't match — don't guess.

After the handoff, update `setup-state.json`: set `last_completed_phase` to 9 AND set `completed_at` to today's ISO date (`YYYY-MM-DD`). This marks setup complete; the session-start hook will stop surfacing the resume prompt.

## Resuming a Paused Setup

If `.carrel/setup-state.json` shows `last_completed_phase < 9` and `completed_at: null`, the researcher paused. When they next say "let's keep going" or run `/carrel-setup`:

1. Read `setup-state.json` to see where they stopped
2. Skip phases 1-N (already completed) — confirm with one quick recap rather than re-interviewing
3. Resume at phase N+1
4. Update `last_completed_phase` as you complete each remaining phase
5. Mark complete (set `completed_at`) at Phase 9

## Related

- **Skill**: `environment-setup` (full orchestration logic)
- **Agent**: `@setup-interviewer` (conversational interview)
- **Commands**: `/carrel-status` (check setup health after initial setup)
