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

The setup writes `.carrel/setup-state.json` to track progress so the session-start hook can offer to resume if the researcher stops mid-flow. The Python `carrel vault init` initializes it after Phase 4. From then on, use the CLI rather than hand-editing JSON:

```bash
carrel setup-state show --vault <path>
carrel setup-state advance --phase 5 --vault <path>
carrel setup-state complete --vault <path>
```

If the researcher pauses, do nothing — leave the existing state in place and the hook will surface a resume prompt next session.

## What Happens

### Phase 1: The Conversation (~10 min)

Deploy `@setup-interviewer` for a natural conversational interview, or follow the protocol in `skills/environment-setup/references/interview-protocol.md`.

Cover: research area, file types, data sensitivity, existing tools, comfort level with AI.

### Phase 2: Silent Audit (~30 sec)

Run `carrel env doctor --format json` to detect hardware, installed tools, and existing configurations. Extract `audit.platform` from the JSON and remember it for Phases 5 and 6. Summarize findings in plain language — never show raw output.

### Phase 3: The Plan (~2 min)

Consult `skills/environment-setup/references/decision-tree.md` to map answers + audit to a configuration plan. Present the plan conversationally and get researcher approval.

### Phase 4: Scaffold (~2 min)

Run `carrel vault init <path>` to create:
- Vault folder structure (inbox, papers, notes, transcripts, drafts, talks, admin)
- `.obsidian/` configuration
- `.carrel/environment.json` (writes a default `ResearcherProfile`; replace with the interview profile below)
- `CLAUDE.md` starter with profile-sync HTML markers
- Note templates + research-database `.base` files (selected from `preferences.*`)
- `_meta/cheat_sheet.md`, `_meta/my-environment.md`, `_meta/capability-log.md`, `_meta/friction_log.md`

After scaffolding, overwrite `.carrel/environment.json` with the researcher's profile from the interview (Claude does this directly — write the full `ResearcherProfile` JSON).

Then update or regenerate the root `CLAUDE.md` so its HTML markers match the interview profile. If you rewrote `.carrel/environment.json` after `carrel vault init`, run:

```bash
carrel vault add-markers --vault <path>
```

Keep the narrative guidance in `CLAUDE.md`, but preserve the marker block so `carrel vault check-sync` can detect drift in future sessions.

**Natural pause point.** Ask the researcher: *"Your vault is set up and Claude knows your profile. We can keep going to optional tools and automation, or you can pause here and pick this up later — the session-start hook will remember where we stopped. Want to keep going?"*

- If they want to pause: leave `setup-state.json` as-is (`last_completed_phase: 4`, `completed_at: null`) — the hook will surface a resume prompt next session.
- If they want to continue: proceed to Phase 5.

> Note: if you're on Windows, some downstream tools below may not be available — see Platform Support in README.

### Phase 5: Optional MCPs [skippable]

If the decision tree indicates mineru or zotero, add to project `.mcp.json` and guide through API key setup. Tool recommendations in this phase are platform-gated: use the install row that matches the `audit.platform` value you extracted in Phase 2. This phase is **fully optional** — say so to the researcher: "These add specific tools (Zotero integration, cloud PDF processing). Skip if you're not sure — you can add any of them later."

After this phase (whether you configured anything or skipped), run:

```bash
carrel setup-state advance --phase 5 --vault <path>
```

### Phase 6: Human Steps (~10-15 min real time)

Tell the researcher what THEY need to do (Claude can't install GUI apps). Use the OS-aware tables in `skills/environment-setup/references/decision-tree.md` and match them to the `audit.platform` value from Phase 2:
- Install Obsidian with the matching platform command
- Open Obsidian → "Open folder as vault" → select this project folder
- Install Web Clipper for their browser

After confirming these steps, run:

```bash
carrel setup-state advance --phase 6 --vault <path>
```

### Phase 7: Cheat Sheet & Verification

The vault scaffold (Phase 4) wrote a starter `_meta/cheat_sheet.md`. Regenerate it to reflect the personalized profile and any tools configured in Phases 5-6:

```bash
carrel vault cheatsheet --vault <path> --force
```

Then read the cheat sheet and edit it directly to add researcher-specific touches (workflow examples, named projects, custom shortcuts).

Test one operation: "Drop a PDF or Word file and I'll convert it to show you how it works."

After verification, run:

```bash
carrel setup-state advance --phase 7 --vault <path>
```

**Natural pause point.** Ask the researcher: *"That's the core setup done — you've got Obsidian, your tools work, and there's a cheat sheet. The remaining phases are about overnight automation and final handoff. Want to wrap up now or pause and finish later?"*

### Phase 8: Overnight Maintenance [skippable]

Offer automation: "Carrel can maintain your vault between sessions — processing new files, checking health, surfacing connections. Costs about $3-8/month with Sonnet on top of your Claude subscription."

If interested → run `/carrel-automate` inline. If not → skip, mention they can always run `/carrel-automate` later.

After this phase (configured or skipped), run:

```bash
carrel setup-state advance --phase 8 --vault <path>
```

### Phase 9: Handoff

Point to the cheat sheet in Obsidian. Confirm everything is working. "Next time you open Claude Desktop with this folder, I'll remember everything."

Then offer next steps based on the researcher's profile (read from `.carrel/environment.json`):

- **Always**: "Run `/carrel-status` anytime to verify the setup."
- **If `claude_code_familiarity == "new"`**: "If you're new to Claude Code as a tool, run `/powerup` for a guided tour of the assistant itself — interactive lessons with animated demos, separate from Carrel."
- **If `collaborators == true`**: "When you're ready to bring a collaborator into this vault, run `/carrel-share` — it generates a vault-specific handbook tailored to whoever is joining."

Skip the conditional pointers when the corresponding fields are missing or don't match — don't guess.

After the handoff, run:

```bash
carrel setup-state complete --vault <path>
```

This marks setup complete; the session-start hook will stop surfacing the resume prompt.

## Resuming a Paused Setup

If `carrel setup-state show --vault <path>` shows `last_completed_phase < 9` and `completed_at: null`, the researcher paused. When they next say "let's keep going" or run `/carrel-setup`:

1. Run `carrel setup-state show --vault <path>` to see where they stopped
2. Skip phases 1-N (already completed) — confirm with one quick recap rather than re-interviewing
3. Resume at phase N+1
4. Run `carrel setup-state advance --phase N --vault <path>` as you complete each remaining phase
5. Run `carrel setup-state complete --vault <path>` at Phase 9

## Related

- **Skill**: `environment-setup` (full orchestration logic)
- **Agent**: `@setup-interviewer` (conversational interview)
- **Commands**: `/carrel-status` (check setup health after initial setup)
