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
    "wiki_maintenance": false,
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
- `wiki_maintenance` — update the knowledge wiki with new sources, run lint (defaults OFF — requires wiki activation via `knowledge-wiki` skill)

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

Before reorganizing existing files outside inbox routing, run:

```bash
carrel trust check vault:reorganize --vault .
```

If the check exits non-zero, surface the gate to the researcher: "I tried to vault:reorganize but your trust level (<current>) does not allow that. To enable, raise trust to <required> via /carrel-automate." Then stop. Do not proceed with the write.
If the check exits 0, proceed:

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
Before writing, run:

```bash
carrel trust check vault:move-file --vault .
```

If the check exits non-zero, surface the gate to the researcher: "I tried to vault:move-file but your trust level (<current>) does not allow that. To enable, raise trust to <required> via /carrel-automate." Then stop. Do not proceed with the write.
If the check exits 0, proceed:
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

### 7. Field map maintenance [include only if wiki_maintenance is true; otherwise omit entirely]
- Read wiki/SCHEMA.md for conventions and tag taxonomy
- Read wiki/index.md for existing pages
- Read last 30 lines of wiki/log.md for recent activity and reasoning
- Scan papers/, transcripts/, and inbox/ for files newer than last wiki log entry
- For each new source: ingest following the knowledge-wiki skill protocol
  (create/update entity and concept pages, cross-link, update index)
- Quick lint: verify new pages have 2+ outbound wikilinks, index is current
- Weekly full lint: check for orphans, broken links, stale pages, tag violations
  (run if last full lint in log.md is >7 days ago)
- At trust level >= Delegated: list every wiki file created/modified in the morning brief's
  Actions Taken section with revert instructions:
  - New pages: `rm wiki/entities/new-page.md` + remove from index
  - Edited pages: note what changed (section added/modified). Full revert of edits relies on
    git history or session checkpoints — the brief provides enough context to identify what to review.
- Add wiki status to morning brief

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

## Field Map
- Pages: N total (+N new, +N updated this run)
- Contradictions: N pending review
- Orphans: N (if any)
- Sources not yet ingested: N
- Last full lint: YYYY-MM-DD
- **Insight:** One sentence of synthesis — a pattern, convergence, or emerging theme the agent noticed during this run. Not just counts. Example: "Your sources increasingly converge on practice theory as the dominant lens for organizational routines — 7 of 12 concept pages now reference it."

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
- [ ] **2026-04-04 inbox**: `scan-2026.pdf` — appears to be scanned, needs cloud OCR (`mistral_ocr` or `mineru`). Your sensitivity is set to medium — confirm cloud processing?
- [x] **2026-04-03 inbox**: `slides.pptx` — resolved: converted with markitdown _(marked resolved by researcher on 2026-04-03)_
```

When resolving in an interactive session: check off the item with `[x]` and add a resolution note. Periodically archive resolved items (nice to have).

---

## Pending Approvals (Consultative Level)

Before writing, run:

```bash
carrel trust check automation:propose --vault .
```

If the check exits non-zero, surface the gate to the researcher: "I tried to automation:propose but your trust level (<current>) does not allow that. To enable, raise trust to <required> via /carrel-automate." Then stop. Do not proceed with the write.
If the check exits 0, proceed:

At trust level 2 (Consultative), proposed actions are written to `_meta/pending-approvals.md` in structured executable format. The researcher approves individual items in the next session.

```markdown
# Pending Approvals

Proposed actions from overnight processing. Approve individually or all at once.

- [ ] **2026-04-04 cross-link**: Link [[sensemaking]] ↔ [[retrospective-rationality]] (both cite Weick 1995)
- [ ] **2026-04-04 file**: Move inbox/smith-2026.pdf → papers/smith-2026/paper.md
- [ ] **2026-04-04 gap**: Consider adding Pentland (frequent Feldman co-author, cited in 4 notes but not in vault)
```

Before writing, run:

```bash
carrel trust check automation:execute --vault .
```

If the check exits non-zero, surface the gate to the researcher: "I tried to automation:execute but your trust level (<current>) does not allow that. To enable, raise trust to <required> via /carrel-automate." Then stop. Do not proceed with the write.
If the check exits 0, proceed:

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
| Field map maintenance (5-10 sources) | $0.15-0.40 |
| Full overnight run (without field map) | $0.10-0.25 |
| Full overnight run (with field map) | $0.25-0.65 |

**Daily full run with Sonnet: approximately $3-8/month** without field map, **$5-15/month** with field map maintenance (depends on vault size and new source volume). Monthly mirror with Opus runs about $0.50-1.00 per synthesis.

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

The skill conducts the interview; the CLI writes the files. Final hand-off is the **Calling Pattern** below — one invocation after the interview resolves.

### The 10-step flow

1. **Check current state.** Read `.carrel/environment.json` `automation` section. `enabled: false` (default) → first-time, go to step 2. `enabled: true` → returning, go to step 3.

2. **First-time interview.** Conversational, not a form. Cover in any natural order:
   - **What should run unattended?** Walk each capability with its default (see "The Automation Contract"). Re-check `wiki_enabled` — only offer the `wiki_maintenance` toggle ("Field map maintenance") if `wiki_enabled: true`. If `false`, skip the toggle and add a closing note: *"One capability not set up yet is a knowledge field map — I can synthesize your sources into topic and entity pages over time. Ask me about a 'field map' when you're ready."*
   - **Trust level?** Use the "Graduated Trust Levels" section above as the canonical explainer — don't duplicate that language here. Note that levels 3-4 are experimental.
   - **Model preference?** Sonnet (default, faster, cheaper) vs Opus (deeper, higher cost).
   - **Schedule?** Daily / weekdays / weekly. If weekly, ask which day.
   - **Review cadence?** Monthly / quarterly / biannual.

3. **Returning interview.** Show current config in a readable summary. If `wiki_enabled` flipped to `true` since last review but `wiki_maintenance` is still `false`, surface it: *"Since your last automation review, you've set up a knowledge field map. Would you like to include field map maintenance in overnight automation?"* Then ask "What would you like to change?" — apply only requested changes.

4. **Update environment.json.** The Calling Pattern does this — flags map to typed `AutomationConfig` fields; CLI sets `last_reviewed` to today.

5. **Update vault `CLAUDE.md` (two-track sync).** Append or update an `## Automation` section in plain language — this is Claude's behavioral guide, not a config file. Describe what's authorized, the trust level, what to log. CLI does the structured write; you do the narrative one.

6. **Update `_meta/my-environment.md`.** Update or add an automation status line for at-a-glance visibility in Obsidian. Regenerable via `carrel vault dashboard --force`.

7. **Generate the automation prompt.** The Calling Pattern handles this — CLI runs `carrel trust check automation:write-prompt --vault .` internally, assembles a per-researcher prompt from name, field, enabled capabilities, trust level, model, sensitivity, active tools, then writes `_meta/automation-prompt.md` (preserving any existing one as `automation-prompt.prev.md`).

8. **Initialize `_meta/` directories.** CLI creates `_meta/pending-decisions.md` and `_meta/pending-approvals.md` with headers if absent. Doesn't overwrite. Other directories (`briefs/`, `suggestions/`, etc.) are lazy.

9. **Walk through Desktop App setup.** Point the researcher at "Setting Up a Desktop Scheduled Task" above; confirm the task got saved.

10. **Cost heads-up.** Frame as approximate: *"Daily Sonnet runs about $3-8/month depending on vault size and tasks. Daily Opus is $15-40/month. Weekly is roughly one-seventh."* For per-task detail, point at "Cost Model" above.

### Calling pattern

Hand off to the CLI in one invocation once the interview resolves:

```bash
carrel automate configure --enabled true --trust-level advisory \
  --model sonnet --schedule daily --review-cadence quarterly \
  --inbox-processing true --vault-health true --cross-linking true \
  --gap-analysis false --draft-feedback false --reflection-synthesis true \
  --wiki-maintenance false --vault .
```

CLI owns: writing `AutomationConfig` to `environment.json`, running `policy.trust.is_allowed()` as the internal gate, generating `_meta/automation-prompt.md`, initializing pending-decisions/approvals files. Skill owns: the interview, the trust-level conversation, the vault `CLAUDE.md` narrative update, and the Desktop App walkthrough. Pass only flags the interview resolved — CLI preserves untouched fields on the returning-researcher path.

**Step 9 in environment-setup**: after cheat sheet generation, offer: *"Carrel can maintain your vault between sessions — processing new files, checking health, surfacing connections. Claude Desktop's scheduled tasks cost approximately $3-8/month with Sonnet. Set this up now? You can always run `/carrel-automate` later."*

---

## Unattended-Mode Contract for Batch Operations

When the overnight agent runs `carrel batch convert <folder> --unattended` or `carrel batch transcribe <folder> --unattended`, the batch contract changes — the `convert` and `transcribe` skills' interactive flows don't apply. This skill owns that contract.

**Adaptation rules** (apply to both convert and transcribe batches):

- **Skip the pre-batch confirmation.** Process all recognized files immediately with default routing. No "Ready to start?" prompt.
- **Skip inline questions.** Instead of pausing for judgment calls, write them to `_meta/pending-decisions.md`:
  ```markdown
  - [ ] **YYYY-MM-DD inbox**: `filename` — reason this needs human input
  ```
- **Defer rather than block** on: scanned PDFs needing cloud OCR, sensitive-looking filenames, poor transcription quality, ambiguous file types, files where cloud-processing consent is uncertain given the researcher's sensitivity.
- **Continue processing everything else.** Idempotency (SHA-256 source-hash) still applies — already-processed files are skipped silently.
- **Morning brief replaces the post-batch summary.** Counts of converted/skipped/failed plus a link to `_meta/pending-decisions.md` if items were deferred. Folds into the standard morning brief format above.

The `--unattended` flag is the **only** way the CLI knows to apply this contract. Never set it from interactive use — it suppresses confirmations the researcher would want to see.

The scheduled-prompt template (see "Example generated prompt" above) embeds the `--unattended` flag automatically for any batch invocations it schedules.

---

## Related

- **Commands**: `/carrel-automate` triggers this skill; `/carrel-batch` uses the headless mode contract for unattended batch processing; `/carrel-mirror` generates the research self-portrait
- **Skills**: `vault-ops` for vault structure conventions the overnight agent follows; `environment-setup` (Step 9) offers automation opt-in during initial setup
- **Hooks**: session-start hook (`hooks/check-environment.js`) surfaces morning briefs, active plans, and pending items at session start
- **References**: `references/overnight-prompt-guide.md` (detailed prompt generation patterns), `references/desktop-scheduling-guide.md` (Desktop App + cron setup)
