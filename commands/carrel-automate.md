---
description: Set up or update overnight vault maintenance and analytical tasks
---

# /carrel-automate — Overnight Vault Automation

Configure scheduled tasks that run while you sleep: inbox processing, gap analysis, cross-linking, draft feedback, and reflection synthesis.

## When to Use

- Researcher wants to set up overnight processing for the first time
- Returning to update automation preferences or schedule
- Phase 8 of `/carrel-setup` (automation opt-in)

## What Happens

### Step 1: Check Current State

Read `.carrel/environment.json`. Look for an `automation` section.

- **`automation.enabled` is `false`** (default): this is a first-time setup — proceed to the interview.
- **`automation.enabled` is `true`**: this is a returning researcher — show the current config and ask what they want to change.

### Step 2: Interview (First Time)

Have a short conversational interview. Cover:

**What should run unattended?** Let the researcher choose any combination:
- Inbox processing (convert and file new papers/notes)
- Vault health check (broken links, orphaned notes, filing gaps)
- Cross-linking (surface connections between notes and papers)
- Gap analysis (flag under-cited claims, missing literature)
- Draft feedback (light structural notes on in-progress writing)
- Reflection synthesis (weekly/monthly summary of what you've been reading and thinking)
- Field map maintenance (keep your knowledge field map current with new sources, run consistency checks) — only offer as a toggle if `wiki_enabled: true` in environment.json. If `wiki_enabled` is false, skip the toggle but add a brief closing note: "One capability not set up yet is a knowledge field map — I can synthesize your sources into topic and entity pages over time. Ask me about a 'field map' to start that when you're ready."

**Trust level?** Explain each briefly before asking:
- *Advisory* — suggestions only, nothing written without your approval
- *Consultative* — proposes specific actions in structured format, you approve before execution
- *Delegated (experimental)* — files NEW items following vault conventions, never reorganizes existing. Logs all actions + revert instructions.
- *Partnership (experimental)* — can reorganize existing files within the epistemology in CLAUDE.md. Logs all actions + revert instructions.

**Model preference?**
- Sonnet (default, faster and cheaper)
- Opus (deeper reasoning, higher cost)

**Schedule?**
- Daily (every night)
- Weekdays (Mon–Fri)
- Weekly (pick a day)

**Review cadence?** How often to revisit and update these settings:
- Monthly / Quarterly / Biannual

### Step 3: Interview (Returning)

Show the current configuration in a readable summary. Re-check `wiki_enabled` in environment.json — if it is now `true` but `wiki_maintenance` is `false`, surface this as a new option: "Since your last automation review, you've set up a knowledge field map. Would you like to include field map maintenance in overnight automation?"

Ask: "What would you like to change?" Apply only the requested changes.

### Step 4: Update environment.json

Write the `automation` section to `.carrel/environment.json`:

```json
"automation": {
  "enabled": true,
  "inbox_processing": true,
  "vault_health": true,
  "cross_linking_suggestions": true,
  "gap_analysis": false,
  "draft_feedback": false,
  "reflection_synthesis": true,
  "wiki_maintenance": false,
  "trust_level": "advisory",
  "model": "sonnet",
  "schedule": "daily",
  "review_cadence": "quarterly",
  "last_reviewed": "2026-04-04"
}
```

Set each boolean based on the researcher's choices. `last_reviewed` is today's date.

### Step 5: Update vault CLAUDE.md (Two-Track Sync)

Append or update an `## Automation` section in the vault's `CLAUDE.md`. Write it in plain language — this is Claude's behavioral guide, not a config file. Describe what tasks are authorized, what trust level applies, and what to log.

### Step 6: Update _meta/my-environment.md

If this file exists, update or add an automation status line so the researcher can see it at a glance in Obsidian.

### Step 7: Generate Automation Prompt

Create a personalized prompt template at `_meta/automation-prompt.md`. This is what gets pasted into the Desktop App scheduler.

If `_meta/automation-prompt.md` already exists, save the old version as `_meta/automation-prompt.prev.md` before writing the new one.

The prompt should:
- Reference the vault CLAUDE.md for behavioral guidelines
- List the authorized tasks
- State the trust level and what to do with outputs
Consult `skills/automation/SKILL.md` for prompt templates and phrasing that matches the trust level.

### Step 8: Initialize _meta/ Directories

Create these files if they don't exist:

- `_meta/pending-decisions.md` — header only: `# Pending Decisions`
- `_meta/pending-approvals.md` — header only: `# Pending Approvals`
Don't overwrite existing files.

### Step 9: Guide Through Desktop App Setup

Walk the researcher through scheduling:

1. "Open Claude Desktop → go to the **Schedule** tab → click **New local task**"
2. "Open `_meta/automation-prompt.md` in Obsidian and copy the entire prompt"
3. "Paste it into the task prompt field"
4. "Set the schedule to **[chosen schedule]** at a time when your computer is usually on (overnight works well)"
5. "Set the model to **[chosen model]**"
6. "Save the task"

If they're on weekdays or weekly, note which days or which day they chose.

### Step 10: Cost Heads-Up

Mention the rough cost estimate so there are no surprises:

- Daily Sonnet: ~$3–8/month depending on vault size and tasks
- Daily Opus: ~$15–40/month
- Weekly: roughly one-seventh the daily rate

Frame it as approximate — actual cost depends on vault size and which tasks run.

## Tone

Keep it practical and reassuring. Researchers may be cautious about AI acting on their files without supervision — acknowledge that and let the trust level choice reflect that caution. Advisory mode is a perfectly good starting point.

## Related

- **Skill**: `automation` (prompt templates, trust level definitions, task logic)
- **Commands**: `/carrel-setup` (Step 9 offers automation opt-in), `/carrel-status` (shows automation status)
