---
name: automation
description: "This skill should be used when a researcher wants to configure, understand, or adjust overnight vault maintenance. Triggers on 'schedule', 'automate', 'overnight', 'background processing', 'morning brief', 'unattended', 'what did Carrel do', 'review automation settings', 'trust level', or '/carrel-automate'."
---

# automation

Configure and explain overnight vault maintenance. The overnight agent runs in a fresh session while the researcher is away — processing inbox files, surfacing connections, checking vault health. This skill defines the contract that makes unattended operation safe and predictable.

## When to Use

- Researcher wants to set up automated vault maintenance
- Researcher asks about scheduled tasks, overnight processing, or background work
- Researcher wants to understand or change their trust level
- Researcher asks about morning briefs, pending decisions, or automation status
- Running `/carrel-automate`

## Feature Filter

Before adding any automation capability, ask: does this amplify the researcher's judgment, or does it replace it?

- Replaces researcher judgment → reject
- Amplifies researcher judgment → accept
- Makes researcher patterns visible → accept (with opt-in granularity)
- Removes friction from mechanical work → accept
- Removes friction from intellectual work → examine carefully
- Delegates within agreed boundaries → accept (with explicit level opt-in)

Draft feedback defaults OFF. Gap analysis defaults OFF. Reflection synthesis defaults ON. The more intimate the task, the more opt-in it requires.

---

## How Scheduled Automation Works

The overnight agent is a Claude session that runs on a schedule, without the researcher present.

**Primary path: Desktop App local scheduled tasks**
- Uses the researcher's existing subscription — no API key required
- Full local filesystem access
- Persistent scheduling (survives restarts if Desktop App is running)
- GUI setup: Claude Desktop → Schedule tab → New local task

**Power-user fallback: `claude -p` + cron**
- Requires API key and terminal familiarity
- One-shot headless execution
- See `references/desktop-scheduling-guide.md` for both setup paths

The agent reads `_meta/automation-prompt.md` as its instructions. This prompt is generated per-researcher by `/carrel-automate` — not a static template.

---

## The Automation Contract

Automation preferences live in `.carrel/environment.json` under an `automation` key:

```json
{
  "automation": {
    "enabled": false,
    "inbox_processing": true,
    "vault_health": true,
    "cross_linking_suggestions": true,
    "gap_analysis": false,
    "draft_feedback": false,
    "reflection_synthesis": true,
    "trust_level": "advisory",
    "model": "sonnet",
    "schedule": "daily",
    "review_cadence": "quarterly",
    "last_reviewed": null
  }
}
```

**Capabilities:**
- `inbox_processing` — convert and file new inbox items
- `vault_health` — count papers/notes/drafts, detect orphans and broken links
- `cross_linking_suggestions` — find connections between notes using shared citations and concepts
- `gap_analysis` — identify frequently-cited authors whose work isn't in the vault
- `draft_feedback` — analytical feedback on recent drafts (defaults OFF — most intimate)
- `reflection_synthesis` — synthesize reflection entries into monthly mirror

**Schedule options:** `daily` / `weekdays` / `weekly`

**Review cadence:** `monthly` / `quarterly` / `biannual` — the session-start hook warns when automation preferences haven't been reviewed in this long.

The automation section must stay in sync with the vault's root `CLAUDE.md`. When preferences change, update both files.

---

## Graduated Trust Levels

The researcher chooses how much to delegate. Default is **Advisory**. Each level up requires explicit opt-in.

| Level | Name | What the agent does | What the researcher does |
|-------|------|--------------------|-----------------------|
| 1 | **Advisory** | Writes all suggestions to `_meta/suggestions/`. Never touches vault files. | Reads suggestions, acts manually. |
| 2 | **Consultative** | Writes suggestions AND proposed actions to `_meta/pending-approvals.md` in structured executable format. Never executes. | Approves specific items in next session. |
| 3 | **Delegated** *(experimental)* | Files NEW items following vault conventions. Never reorganizes existing. Logs every action + revert instructions in the morning brief. | Reviews action log. Can undo. |
| 4 | **Partnership** *(experimental)* | Can move/rename/reorganize existing files within the epistemology in `CLAUDE.md`. Logs every action + specific revert instructions. | Reviews brief. Reverts via session checkpoints. |

**Levels 3-4 are experimental in v0.4.** They rely on session checkpoint history for revert. Make this clear during setup — the researcher's choice of trust level is itself an act of judgment, not an abdication of it.

### Confidence rubric for suggestions (all levels)

Cross-linking suggestions are rated before writing:
- **High**: shared citation AND shared concept AND both notes are substantial → appears in morning brief
- **Medium**: shared citation OR shared concept → written to `_meta/suggestions/` only
- **Low**: loose thematic similarity only → written to `_meta/suggestions/` only, never in brief

Only high-confidence items surface in the morning brief to avoid suggestion fatigue.

---

## Headless Mode Behavior

The overnight agent's prompt encodes: "You are running in UNATTENDED mode."

This means:
- Never ask questions or wait for input
- When encountering items needing human judgment → write to `_meta/pending-decisions.md`, skip the item
- At trust levels 3-4: log every action with revert instructions in the morning brief
- When the brief is complete, stop

Items that require human judgment (write to pending-decisions.md, do not process):
- Scanned PDFs that need cloud OCR
- Audio files where speaker count or sensitivity is unclear
- Files with ambiguous type
- Any item where cloud processing consent is uncertain given the researcher's sensitivity level

---

## Prompt Generation Logic

The prompt is generated per-researcher by `/carrel-automate` and saved to `_meta/automation-prompt.md`. It is NOT a static file shipped with the plugin.

**Assembled from:**
- Researcher name and field (from `environment.json`)
- Enabled capabilities (`inbox_processing`, `vault_health`, etc.)
- Trust level
- Model preference
- Sensitivity level (affects what the agent reads unattended)
- Active tools (which converters/transcribers are installed)

**Critical**: The prompt does NOT embed an absolute vault path. It instructs the agent to detect the vault root by finding `.carrel/environment.json` (same pattern as the session-start hook's `findCarrelRoot`). This survives iCloud sync, folder renames, and vault moves.

**On regeneration**: the old prompt is saved as `_meta/automation-prompt.prev.md`. The researcher can diff the two files to see what changed.

See the full example generated prompt in `references/overnight-prompt-guide.md`.

### Example generated prompt

When generating the prompt for a researcher, produce something like this — adapted to their specific name, field, sensitivity, enabled capabilities, and trust level:

```markdown
You are the Carrel overnight agent for Sarah's research vault.
You are running in UNATTENDED mode.

## Setup
1. Load the Carrel plugin.
2. Find the vault root by locating .carrel/environment.json (walk up from cwd).
3. Read .carrel/environment.json for preferences.
4. Read the vault's root CLAUDE.md for the agreed research epistemology.

## Unattended mode rules
- NEVER ask questions or wait for input. You are running without a researcher present.
- When you encounter items needing human judgment, write to _meta/pending-decisions.md.
- When you take actions (trust level 3-4), log each action with revert instructions
  in the morning brief.

## Your role
You maintain the vault between interactive sessions. You work within
the agreed epistemology — organizational behavior research, sensitivity medium.

## What to do (in order)

### 1. Inbox processing [enabled]
- List files in inbox/ newer than the most recent _meta/briefs/ entry
  (or all files if no briefs exist)
- Convert PDFs using liteparse, docs using markitdown, audio using coli
- File converted output to appropriate vault folders
- If a file needs human judgment: write to _meta/pending-decisions.md,
  do NOT process it

### 2. Vault health [enabled]
- Count papers, notes, transcripts, drafts
- Detect orphan notes (no backlinks from other notes)
- Detect broken internal [[links]]
- Note stale drafts (untouched >30 days)

### 3. Cross-linking suggestions [enabled]
- Read notes modified in the last 7 days
- Identify connections between notes that cite common sources or related concepts
- Rate each: high/medium/low confidence
  - High: shared citation + shared concept + both notes are substantial
  - Medium: shared citation OR shared concept
  - Low: loose thematic similarity only
- Write to _meta/suggestions/[date].md
- Only high-confidence items appear in the morning brief

### 4. Gap analysis [disabled — skip]

### 5. Draft feedback [disabled — skip]

### 6. Reflection synthesis [enabled]
- Read _meta/reflections/ entries since last mirror
- Write synthesis to _meta/mirror/ only if 30+ days since last mirror

## Trust level: Advisory (level 1)
- Write all suggestions to _meta/suggestions/. Never act on vault files.
- Never write to _meta/pending-approvals.md — that is for Consultative level.

## Write the morning brief
Save to _meta/briefs/[YYYY-MM-DD].md using the standard brief format.
```

The trust level section is replaced entirely based on the researcher's chosen level (see trust level rules below for levels 2-4).

---

## Morning Brief Format

Save to `_meta/briefs/YYYY-MM-DD.md` after each overnight run:

```markdown
# Morning Brief — YYYY-MM-DD

## Inbox
- Processed: N files (list with destinations)
- Failed: N files (list with reasons)
- Pending decisions: N items (see pending-decisions.md)

## Vault Health
- Papers: N (+N since last brief)
- Notes: N
- Drafts: N (N stale >30 days)
- Orphan notes: N
- Broken links: N

## Suggestions
[High-confidence items only]
- **Cross-link**: "sensemaking" and "retrospective rationality" both cite Weick 1995 but aren't linked
- **Gap**: You cite Feldman 2000 in 4 notes but Pentland (frequent co-author) isn't in your vault

## Active Plans
- "Chapter 3 Methodology" — next step: write data collection section

## Actions Taken
[Only if trust level >= Delegated]
- Filed inbox/smith-2026.pdf → papers/smith-2026/paper.md
  Revert: `mv papers/smith-2026/paper.md inbox/smith-2026.pdf`
```

If trust level is Advisory or Consultative, omit the "Actions Taken" section entirely.

The session-start hook reads the most recent brief and surfaces a summary at the start of each interactive session: "Morning brief ready (YYYY-MM-DD) — inbox: 3 processed, 1 pending. 2 suggestions."

---

## Pending Decisions Workflow

Single file `_meta/pending-decisions.md`, initialized by `/carrel-automate`. The overnight agent appends to it; the researcher resolves items interactively.

```markdown
# Pending Decisions

Items deferred from automated processing. Resolve in an interactive session.

- [ ] **2026-04-04 inbox**: `interview-p7.m4a` — audio file, needs speaker count and sensitivity level before transcription
- [ ] **2026-04-04 inbox**: `scan-2026.pdf` — appears to be scanned, needs cloud OCR (mineru). Your sensitivity is set to medium — confirm cloud processing?
- [x] **2026-04-03 inbox**: `slides.pptx` — resolved: converted with markitdown _(marked resolved by researcher on 2026-04-03)_
```

When resolving in an interactive session: check off the item with `[x]` and add a resolution note. Periodically archive resolved items (nice to have).

---

## Pending Approvals (Consultative Level)

At trust level 2 (Consultative), proposed actions are written to `_meta/pending-approvals.md` in structured executable format. The researcher approves individual items in the next session.

```markdown
# Pending Approvals

Proposed actions from overnight processing. Approve individually or all at once.

- [ ] **2026-04-04 cross-link**: Link [[sensemaking]] ↔ [[retrospective-rationality]] (both cite Weick 1995)
- [ ] **2026-04-04 file**: Move inbox/smith-2026.pdf → papers/smith-2026/paper.md
- [ ] **2026-04-04 gap**: Consider adding Pentland (frequent Feldman co-author, cited in 4 notes but not in vault)
```

When the researcher approves an item in an interactive session, execute it and mark `[x]`.

---

## Setting Up a Desktop Scheduled Task

After generating the prompt (`_meta/automation-prompt.md`), guide the researcher through Desktop task setup:

1. Open **Claude Desktop**
2. Go to the **Schedule** tab (or equivalent scheduling UI)
3. Click **New local task**
4. Paste the contents of `_meta/automation-prompt.md` as the task prompt
5. Set the schedule: `daily` / `weekdays` / `weekly` at a time that works (overnight, e.g., 2am)
6. Model: **Sonnet** (default) or **Opus** if the researcher chose that
7. Save the task

The Desktop App must be running (or set to launch on login) for scheduled tasks to fire. If the machine is off when a task is scheduled, the app will run one catch-up when it next opens.

For the `claude -p` + cron fallback, see `references/desktop-scheduling-guide.md`.

---

## Cost Model

Mention during setup so the researcher can make an informed choice:

| Task | Approx cost per run (Sonnet) |
|------|------------------------------|
| Inbox processing (5 files) | $0.03-0.05 |
| Vault health scan | $0.02-0.03 |
| Cross-linking suggestions | $0.05-0.10 |
| Gap analysis | $0.03-0.07 |
| Draft feedback (1 draft) | $0.07-0.15 |
| Full overnight run | $0.10-0.25 |

**Daily full run with Sonnet: approximately $3-8/month.** Monthly mirror with Opus runs about $0.50-1.00 per synthesis.

---

## _meta/ Structure for Automation

These directories are created lazily — only when first needed:

```
_meta/
├── briefs/                  # Morning briefs (one per run)
│   └── YYYY-MM-DD.md
├── suggestions/             # Cross-linking, gap analysis (all confidence levels)
│   └── YYYY-MM-DD.md
├── mirror/                  # Monthly research self-portraits
│   └── YYYY-MM.md
├── feedback/                # Draft feedback (opt-in)
│   └── draft-name-YYYY-MM-DD.md
├── plans/                   # Persistent planning artifacts
│   └── plan-name.md
├── pending-decisions.md     # Single file, appended by overnight agent
├── pending-approvals.md     # Structured actions awaiting approval (trust level 2)
├── automation-prompt.md     # Generated overnight agent prompt
└── automation-prompt.prev.md # Previous prompt (for diff review)
```

`/carrel-automate` initializes `pending-decisions.md` and `pending-approvals.md` with headers. `briefs/`, `suggestions/`, `mirror/`, `feedback/`, and `plans/` are created on first use.

---

## /carrel-automate Workflow

When running `/carrel-automate`:

1. Check current automation state in `environment.json`
2. **First time**: conversational interview
   - What should run unattended? Walk through each capability and its default
   - Trust level for vault operations? Explain each level; note that 3-4 are experimental
   - Model preference? (Sonnet default, Opus for higher-quality synthesis)
   - Schedule? (daily / weekdays / weekly)
   - Review cadence? (how often to revisit automation settings)
3. **Returning**: show current config, ask what to change
4. Update `environment.json` `automation` section
5. Update vault `CLAUDE.md` automation preferences section (two-track sync)
6. Update `_meta/my-environment.md` to reflect automation status
7. Generate the prompt → save to `_meta/automation-prompt.md`
   (save old prompt to `_meta/automation-prompt.prev.md` if one exists)
8. Initialize `_meta/` automation directories and header files
9. Guide researcher through Desktop App scheduled task setup (steps above)
10. Mention cost estimate for their chosen configuration

**Step 9 in environment-setup**: after cheat sheet generation, offer: "Carrel can maintain your vault between sessions — processing new files, checking health, surfacing connections. This uses Claude Desktop's scheduled tasks and costs approximately $3-8/month with Sonnet. Want to set this up now? You can always run `/carrel-automate` later."

---

## Related

- **Commands**: `/carrel-automate` triggers this skill; `/carrel-batch` uses the headless mode contract for unattended batch processing; `/carrel-mirror` generates the research self-portrait
- **Skills**: `vault-ops` for vault structure conventions the overnight agent follows; `environment-setup` (Step 9) offers automation opt-in during initial setup
- **Hooks**: session-start hook (`hooks/check-environment.js`) surfaces morning briefs, active plans, and pending items at session start
- **References**: `references/overnight-prompt-guide.md` (detailed prompt generation patterns), `references/desktop-scheduling-guide.md` (Desktop App + cron setup)
