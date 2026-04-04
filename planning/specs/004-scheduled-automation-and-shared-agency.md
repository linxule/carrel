# 004: Scheduled Automation and Shared Agency

**Status**: Spec (post-review, decisions locked)
**Version target**: v0.4.0
**Date**: 2026-04-04
**Reviewed by**: Codex (adversarial), Code Architect (feasibility) — see `reviews/004-review-codex.md`, `reviews/004-review-architect.md`

---

## Context

Carrel v0.3 is session-based and conversational — every action passes through an interactive dialogue. v0.4 extends Carrel into **scheduled and autonomous operation**, where the agent maintains the vault, processes incoming materials, and surfaces insights between interactive sessions.

Prompted by comparing Carrel to [claude-howto](https://github.com/luongnv89/claude-howto) (a Claude Code tutorial with 5,900+ stars covering the full feature set). claude-howto is a curriculum; Carrel is a product. But its survey of platform capabilities — checkpoints, background tasks, headless mode, scheduled tasks — revealed features Carrel should leverage.

## Philosophy: Graduated Trust

v0.3 treats the researcher as the sole thinking agent. v0.4 revises this.

The researcher and agent share the research space. Both contribute. The relationship operates at the **trust level the researcher has chosen**:

| Level | Name | What the agent does | What the researcher does |
|-------|------|--------------------|-----------------------|
| 1 | **Advisory** | Observes and suggests. All action requires researcher initiative. | Reviews suggestions, acts on what's useful. |
| 2 | **Consultative** | Proposes specific actions in structured format. | Approves before execution. |
| 3 | **Delegated** *(experimental)* | Handles routine operations following vault conventions. Logs all actions + revert instructions. | Reviews morning brief. Can revert. |
| 4 | **Partnership** *(experimental)* | Reorganizes and restructures within agreed epistemology. Logs all actions + revert instructions. | Reviews morning brief. Can revert via checkpoints. |

The default is **Advisory**. Each level up requires explicit opt-in via `/carrel-automate`. The researcher can change levels at any time. The researcher's choice of trust level IS the exercise of judgment — choosing how much to delegate is itself an act of agency, not an abdication of it.

Levels 3-4 are labeled **experimental** in v0.4. They rely on Claude Code's platform checkpoints for undo (each scheduled run = new session with its own checkpoint history). The overnight brief at these levels MUST include revert instructions for every action taken.

### Feature filter

- Replaces researcher judgment → reject
- Amplifies researcher judgment → accept
- Makes researcher patterns visible → accept (with opt-in granularity)
- Removes friction from mechanical work → accept
- Removes friction from intellectual work → examine carefully
- Delegates within agreed boundaries → accept (with explicit level opt-in)

---

## Platform Capabilities (What Exists Today)

| Context | How it works | Access | Persistence | Best for |
|---------|-------------|--------|-------------|----------|
| **Background bash** | `Ctrl+B` or ask Claude | Local filesystem | Session-scoped | Batch conversion while chatting |
| **Session scheduling** | `CronCreate` / `/loop` | Local filesystem | Session (7-day max); `durable: true` survives restarts | Hourly vault health during work |
| **Headless CLI** | `claude -p "prompt"` | Local filesystem | One-shot | Power-user cron, CI integration |
| **Desktop local tasks** | Desktop App schedule UI | Local filesystem + MCP | Persistent, app must be open | **Primary automation for researchers** |
| **Cloud scheduled** | `/schedule` via RemoteTrigger | Fresh git clone only | Persistent, always-on | GitHub/Slack workflows (not local vaults) |

**Primary automation path**: Desktop App local scheduled tasks. Uses existing subscription (no API key), full local access, GUI setup, persistent. `claude -p` + cron is the power-user fallback.

---

## Deliverables

All of the following ship in v0.4.0. Grouped by layer but implemented together.

### A. New commands

#### A1. `/carrel-batch` — Batch process files

```yaml
---
description: Batch convert or transcribe a folder of files with background processing
---
```

**Workflow:**
1. Enumerate files in specified folder (or `inbox/` by default)
2. Determine routing per file: PDF → liteparse, docx → markitdown, audio → coli, video → coli, YouTube URLs in a text file → youtube_captions
3. Process files **sequentially** — run `carrel paper convert` or `carrel transcript create` per file, one at a time. No core library changes; parallelism deferred to v0.4.1 if usage shows need.
4. Idempotency is handled at the **filer level** (post-conversion SHA-256 check), not pre-conversion. The filer returns `action="skipped"` for already-converted files. Some redundant conversion work is accepted as the cost of simplicity.
5. Collect results after each file; file to vault following existing conventions (`papers/author-year/`, `transcripts/kind/`, etc.)
6. Generate summary: N converted, N skipped (idempotent), N failed (with reasons), N need human input
7. **Interactive mode**: flag items needing judgment inline ("This looks scanned — want cloud OCR via mineru?")
8. **Headless mode** (added after automation skill is built): write judgment calls to `_meta/pending-decisions.md` instead of asking

**Performance**: ~30s per PDF (liteparse), so 40 PDFs ≈ 20 min sequential. Fine for background/overnight. If researchers need faster batch, add `carrel paper batch <dir>` with `asyncio.gather` in v0.4.1.

**Skill dependency**: Extends `convert` and `transcribe` skills with batch orchestration logic. No new skill file — the command markdown describes the workflow; the existing skills provide the judgment.

**File**: `commands/carrel-batch.md`

#### A2. `/carrel-automate` — Configure scheduled automation

```yaml
---
description: Set up or update overnight vault maintenance and analytical tasks
---
```

**Workflow:**
1. Check current automation state in `environment.json`
2. If first time: conversational interview about automation preferences
   - What should run unattended? (inbox processing, vault health, cross-linking, gap analysis, draft feedback, reflection synthesis)
   - What trust level for vault reorganization? (Advisory / Consultative / Delegated [experimental] / Partnership [experimental])
   - Model preference for scheduled runs? (Sonnet default, Opus available)
   - How often? (daily / weekdays / weekly)
3. If returning: show current config, ask what to change
4. Update `environment.json` `automation` section
5. **Update vault CLAUDE.md** with automation preferences (preserving sync contract with environment.json — both must reflect the same truth)
6. **Update `_meta/my-environment.md`** to reflect automation status
7. **Generate a personalized prompt template** for the overnight agent (see B2)
8. Create `_meta/` automation directories if they don't exist. Initialize `_meta/pending-decisions.md` with header.
9. Guide researcher through Desktop App scheduled task creation:
   - "Open Claude Desktop → Schedule tab → New local task"
   - "Paste the prompt I've saved at `_meta/automation-prompt.md`"
   - "Set to [chosen schedule] at a time that works for you"
   - "Model: Sonnet (or Opus if you chose that)"

**Also accessible during `/carrel-setup`**: Step 9 of environment-setup skill offers: "Would you like to set up overnight vault maintenance? You can always do this later with `/carrel-automate`."

**File**: `commands/carrel-automate.md`

#### A3. `/carrel-mirror` — Research self-portrait

```yaml
---
description: Synthesize your research patterns from reflections, capability log, and friction log
---
```

**Workflow:**
1. Read `_meta/reflections/` (all entries, or since last mirror)
2. Read `_meta/capability-log.md` (what was created)
3. Read `_meta/friction_log.md` (what frustrated)
4. Read vault stats (paper count by field/year, note count, draft status)
5. Synthesize into a portrait:
   - What you've been reading (topics, fields, key authors)
   - What you've been creating (notes, canvases, custom trackers)
   - Recurring themes in reflections (keywords, sentiment shifts)
   - Friction patterns (what consistently frustrates)
   - Intellectual trajectory (shifting interests, emerging questions)
6. Interactive mode: present conversationally, discuss with researcher
7. Scheduled mode: write to `_meta/mirror/YYYY-MM.md`

**File**: `commands/carrel-mirror.md`

### B. New/modified skills

#### B1. Automation skill — `skills/automation/SKILL.md`

```yaml
---
name: automation
description: "Triggers on 'schedule', 'automate', 'overnight', 'background processing', 'morning brief', 'unattended'. Use when researcher wants to configure or discuss automated vault maintenance."
---
```

**Content:**
- How scheduled automation works (Desktop App local tasks)
- The automation contract (environment.json `automation` section)
- Reorganization levels (see C2)
- Headless skill behavior (how skills adapt when running unattended)
- Prompt template generation logic
- Morning brief format
- Pending decisions workflow
- How to guide researchers through Desktop task setup
- **References**: `references/overnight-prompt-guide.md` (template generation patterns), `references/desktop-scheduling-guide.md` (screenshots/steps for Desktop task setup)

#### B2. Generated prompt templates

Not shipped as static files. Generated per-researcher by `/carrel-automate`, saved to `_meta/automation-prompt.md` in the vault.

**Generation logic** (in the automation skill):

The prompt is assembled from:
- Researcher name and field (from environment.json)
- Enabled automation capabilities (from environment.json `automation` section)
- Trust level (from environment.json `automation.trust_level`)
- Model preference
- Sensitivity level (affects what the agent can read/process unattended)
- Active tools (what converters/transcribers are available)

**Note**: The prompt does NOT embed an absolute vault path. Instead it instructs the agent to detect the vault root by finding `.carrel/environment.json` (same pattern as `hooks/check-environment.js`'s `findCarrelRoot`). This survives vault moves (iCloud sync, folder renames).

**Example generated prompt** (saved to `_meta/automation-prompt.md`):

```markdown
You are the Carrel overnight agent for [name]'s research vault.
You are running in UNATTENDED mode.

## Setup
1. Load the Carrel plugin.
2. Find the vault root by locating .carrel/environment.json (walk up from cwd).
3. Read .carrel/environment.json for preferences.
4. Read the vault's root CLAUDE.md for the agreed research epistemology.

## Unattended mode rules
- NEVER ask questions or wait for input. You are running without a researcher present.
- When you encounter items needing human judgment, write to _meta/pending-decisions.md.
- When you take actions (trust level 3-4), log each action with revert instructions in the morning brief.

## Your role
You maintain the vault between interactive sessions. You work within
the agreed epistemology — [field] research, sensitivity [level].

## What to do (in order)

### 1. Inbox processing [if enabled]
- List files in inbox/ that are newer than the most recent _meta/briefs/ entry (or all files if no briefs exist)
- Convert PDFs using liteparse, docs using markitdown, audio using coli
- File converted output to appropriate vault folders
- If a file needs human judgment (scanned PDF, sensitive audio, ambiguous type):
  write to _meta/pending-decisions.md, do NOT process it

### 2. Vault health [if enabled]
- Count papers, notes, transcripts, drafts
- Detect orphan notes (no backlinks from other notes)
- Detect broken internal [[links]]
- Note stale drafts (untouched >30 days)

### 3. Cross-linking suggestions [if enabled]
- Read notes modified in the last 7 days
- Identify potential connections between notes that cite common sources
  or discuss related concepts
- Rate each suggestion: high/medium/low confidence
  - High: shared citation + shared concept + both notes are substantial
  - Medium: shared citation OR shared concept
  - Low: loose thematic similarity only
- Write to _meta/suggestions/[date].md. Only high-confidence items appear in the morning brief.

### 4. Gap analysis [if enabled]
- Scan paper-notes for cited authors/works
- Identify frequently-cited authors whose key works are not in the vault
- Write gap observations to _meta/suggestions/[date].md

### 5. Draft feedback [if enabled]
- Read any file in drafts/ modified in the last 7 days
- Prepare analytical feedback: argument structure, internal consistency,
  connection to literature in vault
- Write to _meta/feedback/[draft-name]-[date].md
- Never modify the draft itself

### 6. Reflection synthesis [if enabled]
- Read _meta/reflections/ entries since last mirror (check _meta/mirror/ for most recent)
- Identify recurring themes, shifting interests, emotional patterns
- Write synthesis to _meta/mirror/ only if it's been 30+ days since last mirror

## Trust level: [level name]
[Level-specific instructions — generated based on chosen level]

### Advisory (level 1)
- Write all suggestions to _meta/suggestions/. Never act on vault files.

### Consultative (level 2)
- Write suggestions to _meta/suggestions/.
- Write proposed actions to _meta/pending-approvals.md in structured format:
  `- [ ] **[date] [type]**: [action description]`
- Never execute actions. The researcher approves in the next interactive session.

### Delegated (level 3) [experimental]
- File NEW items following vault conventions (papers/author-year/, transcripts/kind/).
- Never reorganize, move, or rename EXISTING files.
- Log every action in the morning brief with revert instructions.
- Write suggestions for existing-file changes to _meta/pending-approvals.md.

### Partnership (level 4) [experimental]
- Can file new items AND reorganize existing files within the vault epistemology from CLAUDE.md.
- Log every action in the morning brief with specific revert instructions (commands to undo each change).
- The researcher can revert via the session's checkpoint history.

## Write the morning brief
Save to _meta/briefs/[date].md with:
- Inbox: processed / failed / pending decisions
- Vault stats (compare against previous brief if one exists for delta)
- High-confidence suggestions (if any)
- Active plans from _meta/plans/ (if any)
- Pending decisions summary
- Pending approvals (if trust level 2)
- Actions taken + revert instructions (if trust level 3-4)
```

**Why generated, not shipped**: each researcher's prompt reflects their specific field, sensitivity, enabled capabilities, and trust level. A shipped template with variables would be less natural and harder to maintain than a generated prompt that the researcher can read and edit.

**Update flow**: when the researcher changes preferences via `/carrel-automate`, the prompt is regenerated. The old prompt is kept as `_meta/automation-prompt.prev.md` for comparison.

#### B3. Extend `environment-setup` skill

Add Step 9 (after cheatsheet generation, before wrap-up):

> **Step 9: Overnight maintenance (optional)**
>
> "Carrel can maintain your vault between sessions — processing new files, checking health, surfacing connections. This uses Claude Desktop's scheduled tasks feature and costs approximately $3-6/month in API usage via Sonnet."
>
> If interested → run `/carrel-automate` inline or note for later.
> If not → skip, mention they can always run `/carrel-automate` later.

**File modified**: `skills/environment-setup/SKILL.md`

#### B4. Extend `vault-ops` skill

Add section on analytical threads:

> **Analytical Threads**
>
> When a researcher wants to explore material through different theoretical lenses:
> 1. Create `notes/threads/<thread-name>/` (e.g., `notes/threads/practice-theory/`)
> 2. Create a thread overview note: `notes/threads/<thread-name>/README.md` with:
>    - Theoretical lens description
>    - Starting questions
>    - Source material (links to papers/transcripts being analyzed)
>    - Status: active / paused / completed / abandoned (with reason)
> 3. Notes within the thread follow normal vault-ops conventions
> 4. No thread is "primary" — parallel threads are preserved intellectual experiments
> 5. "Abandoned" threads stay with a note explaining why (this IS data)

**File modified**: `skills/vault-ops/SKILL.md`

#### B5. Extend `research-partner` skill

Add awareness of:
- Active plans in `_meta/plans/` — reference them when relevant to discussion
- Analytical threads — offer to scaffold new threads, help switch between them
- Morning brief — if one exists from overnight, reference its suggestions in conversation
- Pending decisions — proactively surface unresolved items from `_meta/pending-decisions.md`

**File modified**: `skills/research-partner/SKILL.md`

### C. Architecture changes

#### C1. `environment.json` expansion

Add `automation` section to `ResearcherProfile`:

```python
# In src/carrel/models.py
from typing import Literal

class TrustLevel(str, Enum):
    ADVISORY = "advisory"               # Write suggestions, never act
    CONSULTATIVE = "consultative"       # Propose actions, researcher approves before execution
    DELEGATED = "delegated"             # Handle routine ops, researcher reviews via brief (experimental)
    PARTNERSHIP = "partnership"          # Reorganize within epistemology, researcher reviews (experimental)

class AutomationModel(str, Enum):
    SONNET = "sonnet"
    OPUS = "opus"

class AutomationSchedule(str, Enum):
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"

class AutomationConfig(BaseModel):
    enabled: bool = False
    inbox_processing: bool = True
    vault_health: bool = True
    cross_linking_suggestions: bool = True
    gap_analysis: bool = False
    draft_feedback: bool = False               # Defaults OFF (most intimate)
    reflection_synthesis: bool = True
    trust_level: TrustLevel = TrustLevel.ADVISORY
    model: AutomationModel = AutomationModel.SONNET
    schedule: AutomationSchedule = AutomationSchedule.DAILY
    review_cadence: Literal["monthly", "quarterly", "biannual"] = "quarterly"
    last_reviewed: str | None = None            # ISO date

class ResearcherProfile(BaseModel):
    name: str | None = None
    field: str | None = None
    sensitivity: Sensitivity = Sensitivity.MEDIUM
    cloud_consent: bool = False
    comfort_level: str = "beginner"
    tools_configured: dict[str, bool] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)  # NEW
```

**Migration**: existing environment.json files without `automation` key → `AutomationConfig()` defaults (enabled=false). No breaking change. Pydantic v2 `model_validate()` instantiates `AutomationConfig` with defaults when key is absent.

#### C2. Trust levels (graduated)

Four levels, chosen during `/carrel-automate`. Maps to the philosophy section's graduated trust model:

| Level | Name | What the agent does | What the researcher does |
|-------|------|--------------------|-----------------------|
| 1 | **Advisory** | Writes all suggestions to `_meta/suggestions/`. Never touches vault files. | Reads suggestions, acts on them manually. |
| 2 | **Consultative** | Writes suggestions AND proposed actions to `_meta/pending-approvals.md` in structured executable format. | Approves specific items in next session → agent executes. |
| 3 | **Delegated** *(experimental)* | Files NEW items following vault conventions. Never reorganizes existing. Logs actions + revert instructions in brief. | Reviews action log. Can undo via revert instructions. |
| 4 | **Partnership** *(experimental)* | Can move/rename/reorganize existing files within CLAUDE.md epistemology. Logs actions + revert instructions in brief. | Reviews brief. Can revert via session checkpoints. |

Default: **Advisory**. Each level up requires explicit opt-in. Levels 3-4 labeled experimental in the `/carrel-automate` interview. The prompt template encodes the chosen level's rules.

**Pending approvals format** (for Consultative level):
```markdown
# Pending Approvals

Proposed actions from overnight processing. Approve individually or all at once.

- [ ] **2026-04-04 cross-link**: Link [[sensemaking]] ↔ [[retrospective-rationality]] (both cite Weick 1995)
- [ ] **2026-04-04 file**: Move inbox/smith-2026.pdf → papers/smith-2026/paper.md
- [ ] **2026-04-04 gap**: Consider adding Pentland (frequent Feldman co-author, cited in 4 notes but not in vault)
```

#### C3. Vault structure expansion

```
_meta/
├── briefs/                  # Morning briefs (daily)
│   └── YYYY-MM-DD.md
├── suggestions/             # Cross-linking, gap analysis
│   └── YYYY-MM-DD.md
├── mirror/                  # Monthly research self-portraits
│   └── YYYY-MM.md
├── pending-decisions.md     # Single file, appended to by overnight agent
├── pending-approvals.md     # Structured executable actions awaiting approval (trust level 2)
├── feedback/                # Draft feedback (opt-in)
│   └── draft-name-YYYY-MM-DD.md
├── plans/                   # Persistent planning artifacts
│   └── plan-name.md
├── automation-prompt.md     # Generated overnight agent prompt
├── automation-prompt.prev.md # Previous prompt (for diff)
├── cheat_sheet.md           # (existing)
├── reflections/             # (existing)
├── capability-log.md        # (existing)
├── friction_log.md          # (existing)
└── my-environment.md        # (existing)
```

**Created lazily**: `briefs/`, `suggestions/`, `mirror/`, `feedback/`, `plans/` created only when first needed (either by `/carrel-automate` setup or first use of a feature like `/carrel-mirror`). `pending-decisions.md` and `pending-approvals.md` initialized with headers during `/carrel-automate`.

**State tracking**: `.carrel/plugin-state.json` gains a `last_session_start` ISO date field. The session-start hook reads this to determine which briefs are "new." Written by the hook at the END of its checks (after all output) using temp-file-then-rename for safe writes.

```json
{
  "plugin_version": "0.4.0",
  "last_migrated": "2026-04-04",
  "last_session_start": "2026-04-04T09:15:00Z"
}
```

**Plan file format**:
```markdown
---
title: Chapter 3 Methodology
created: 2026-04-04
updated: 2026-04-04
status: active
---
```
Status values: `active` | `paused` | `completed`. Frontmatter is intentionally simple for regex parsing by the hook (no nested YAML, no lists).

```markdown
## Goal
[What this plan is for]

## Steps
- [ ] Step 1
- [ ] Step 2

## Notes
[Evolving notes, decisions, open questions — updated by either party]
```

#### C4. Session-start hook expansion

Extend `hooks/check-environment.js`. All new checks are **gated on `_meta/briefs/` existence** — if the directory doesn't exist, skip all automation checks immediately (fast path for vaults without automation).

**Parsing strategy**: Simple regex-based frontmatter extraction for plan files. Pattern: `/^---\n([\s\S]*?)\n---/` then line-by-line key-value extraction. No YAML parser dependency. Cap plan listing at 3 active plans.

**Timeout**: Consider increasing from 10s to 15s in `hooks.json` to accommodate new checks on slow disks.

New checks:

1. **Read `last_session_start` from `.carrel/plugin-state.json`** (existing file, new field)

2. **Check for new morning briefs in `_meta/briefs/`**
   - Find most recent brief by filename (YYYY-MM-DD.md sort)
   - Compare against `last_session_start`
   - Output: "Morning brief ready (YYYY-MM-DD) — inbox: 3 processed, 1 pending. 2 suggestions."

3. **Check for active plans in `_meta/plans/`**
   - Read up to 5 plan files, regex-extract `status` and `title` from frontmatter
   - Output (max 3): "Active plan: 'Chapter 3 Methodology' (updated Apr 2)"

4. **Check for pending decisions in `_meta/pending-decisions.md`**
   - Count lines matching `^- \[ \]`
   - Output: "2 pending decisions from overnight processing"

5. **Check for pending approvals in `_meta/pending-approvals.md`**
   - Count lines matching `^- \[ \]`
   - Output: "3 pending approvals — review with /carrel-automate or approve inline"

6. **Check automation status**
   - If `automation.enabled` but no briefs in last 7 days: "Automation configured but no recent briefs — is the Desktop scheduled task running?"
   - If `automation.last_reviewed` is stale (compare against `review_cadence`): "Automation preferences last reviewed [date]. Run /carrel-automate to update."

7. **Write `last_session_start`** to plugin-state.json (temp-file-then-rename)

**File modified**: `hooks/check-environment.js`

### D. Templates

#### D1. Morning brief template

Not a vault template (no `carrel-template:` marker). This is a reference for the overnight agent's output format, embedded in the automation skill's prompt generation logic.

**Format**:
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
[Only if reorganization level >= act_convention]
- Filed new-paper.pdf → papers/smith-2026/paper.md
```

#### D2. Pending decisions format

Single file `_meta/pending-decisions.md`, appended to by overnight agent, resolved interactively:

```markdown
# Pending Decisions

Items deferred from automated processing. Resolve in an interactive session.

- [ ] **2026-04-04 inbox**: `interview-p7.m4a` — audio file, needs speaker count and sensitivity level before transcription
- [ ] **2026-04-04 inbox**: `scan-2026.pdf` — appears to be scanned, needs cloud OCR (mineru). Your sensitivity is set to medium — confirm cloud processing?
- [x] **2026-04-03 inbox**: `slides.pptx` — resolved: converted with markitdown _(marked resolved by researcher on 2026-04-03)_
```

### E. What does NOT change

- **Python core library** (`src/carrel/`) — no changes except `models.py` (adding `AutomationConfig`, `TrustLevel`, related enums). Batch processing is sequential via existing per-file CLI commands — no new pipeline functions. All automation logic lives in the skill/command/hook layer.
- **Existing command files** — all 9 current `.md` files in `commands/` unchanged. Note: the environment-setup, vault-ops, and research-partner SKILLS are extended (adding sections), which indirectly enriches `/carrel-setup`, `/carrel-status`, etc. This is skill-layer evolution, not command-layer breakage.
- **One-plugin policy** — no new dependencies or companion plugins. Hook stays stdlib-only (fs, path, regex).
- **Vault-local namespace** — automation operates within the trust level contract. Researcher-created files outside `_meta/` are never modified at Advisory/Consultative levels. At Delegated/Partnership levels (experimental), modifications are logged with revert instructions.

---

## Cost Model

Desktop App local scheduled tasks use the researcher's existing subscription. Costs are in API usage:

| Task | Estimated tokens per run | Approx cost (Sonnet) |
|------|-------------------------|---------------------|
| Inbox processing (5 new files) | ~15K | $0.03-0.05 |
| Vault health scan | ~10K | $0.02-0.03 |
| Cross-linking suggestions | ~30K | $0.05-0.10 |
| Gap analysis | ~20K | $0.03-0.07 |
| Draft feedback (1 draft) | ~40K | $0.07-0.15 |
| Full overnight run | ~80K | $0.10-0.25 |
| Monthly mirror (Opus) | ~100K | $0.50-1.00 |

**Daily full run with Sonnet: ~$3-8/month.** Mentioned during `/carrel-automate` setup so researcher can make an informed choice.

---

## Failure Modes and Mitigations

| Failure mode | Mitigation |
|---|---|
| **Suggestion fatigue** | Confidence scoring; only high-confidence in briefs; low-confidence accumulates silently in suggestions/ |
| **Uncanny overnight feedback** | Draft feedback defaults OFF; `_meta/feedback/` is clearly agent-namespaced |
| **Stale automation contract** | `review_cadence` in environment.json; session-start hook warns when >90 days since last review |
| **Machine off / app closed** | Desktop App does one catch-up run on wake; session-start hook covers gaps |
| **Token cost surprises** | Cost estimates during `/carrel-automate`; efficient diffing (SHA hashes, date-based scanning) |
| **Overnight agent modifies something it shouldn't** | Reorganization levels are explicit; default is suggest-only; researcher can always revert |
| **Prompt template drift** | `/carrel-automate` regenerates when preferences change; `.prev.md` enables diff review |
| **Multiple overnight runs stack up** | Morning brief uses date-based naming; duplicate runs are idempotent (SHA check on conversions) |

---

## Implementation Order

All ship in v0.4.0. Build in this sequence (revised per architect review to resolve hidden dependencies):

1. **Models** — `AutomationConfig` + `TrustLevel` + `AutomationModel` + `AutomationSchedule` in `models.py`
2. **Vault structure** — plan format, pending-decisions format, pending-approvals format, `_meta/` subdirectory conventions (lazy creation logic)
3. **Session-start hook** — extend with brief/plan/decision surfacing, `last_session_start` state, regex frontmatter parser
4. **`/carrel-batch`** — command (interactive mode only). Sequential processing, filer-level idempotency.
5. **Vault-ops extension** — analytical threads convention (`notes/threads/`)
6. **Research-partner extension** — awareness of plans, threads, briefs, pending decisions/approvals
7. **Automation skill** — new skill with prompt generation logic, trust level rules, headless mode contract, Desktop scheduling guide
8. **Update `/carrel-batch`** — add headless mode (pending-decisions.md instead of interactive questions), now that automation skill defines the contract
9. **`/carrel-automate`** — command wrapping automation skill. Generates prompt, updates environment.json + CLAUDE.md + my-environment.md.
10. **`/carrel-mirror`** — command for research self-portrait (interactive-only first; overnight scheduling uses same command via prompt template)
11. **Environment-setup extension** — Step 9 automation opt-in
12. **Migration** — `migrations/0.3.0-to-0.4.0.md` covering new capabilities
13. **Version bump** — plugin.json + marketplace.json → 0.4.0

---

## Acceptance Criteria

### Must have
- [ ] `ResearcherProfile` supports `automation` field (with `AutomationConfig`, `TrustLevel`, typed enums) with backward compatibility
- [ ] `/carrel-batch` converts a folder of mixed files sequentially with summary (interactive mode)
- [ ] `/carrel-batch` headless mode writes judgment calls to `_meta/pending-decisions.md`
- [ ] `/carrel-automate` interviews, updates environment.json + CLAUDE.md + my-environment.md, generates per-researcher prompt template
- [ ] Generated prompt uses vault detection (not absolute path), includes unattended mode instructions, reads CLAUDE.md
- [ ] Session-start hook surfaces morning briefs, active plans, pending decisions, and pending approvals
- [ ] `last_session_start` tracked in `.carrel/plugin-state.json` with safe write
- [ ] `_meta/plans/` convention with simple frontmatter (regex-parseable)
- [ ] `_meta/pending-decisions.md` format with checkbox resolution
- [ ] `_meta/pending-approvals.md` structured executable format (for Consultative trust level)
- [ ] Analytical threads convention in vault-ops skill (`notes/threads/`)
- [ ] `/carrel-mirror` synthesizes reflections + capability log + friction log (interactive mode)
- [ ] Four trust levels documented and encoded in prompt generation (Advisory, Consultative, Delegated [experimental], Partnership [experimental])
- [ ] All new `_meta/` directories created lazily

### Should have
- [ ] Research-partner aware of plans, threads, briefs, pending decisions/approvals
- [ ] Environment-setup Step 9 offers automation opt-in
- [ ] `/carrel-automate` accessible both standalone and during setup
- [ ] Cost estimates presented during automation setup
- [ ] Automation review cadence warning in session-start hook
- [ ] Trust levels 3-4 briefs include specific revert instructions for every action taken
- [ ] Confidence rubric for cross-linking suggestions (high/medium/low defined)

### Nice to have
- [ ] `_meta/automation-prompt.prev.md` for diff comparison on regeneration
- [ ] Vault health delta tracking (stats compared to last brief)
- [ ] Periodic archiving of resolved items from pending-decisions.md

---

## Resolved Questions (from review)

1. **Headless detection**: Encoded in the prompt text itself ("You are running in UNATTENDED mode"). Skills do not need to detect headless mode programmatically — the overnight agent's prompt encodes the behavioral rules. *(Both reviewers agreed)*

2. **Analytical thread scope**: `notes/threads/` only. Threads are analytical perspectives, not filing categories. *(Both reviewers agreed)*

3. **Brief accumulation**: Preserve indefinitely. Lightweight, serves as research log. *(Both reviewers agreed)*

4. **Pending decisions**: Single file `pending-decisions.md`. Add periodic archiving of resolved items (nice to have). *(Both reviewers agreed)*

5. **Multi-vault**: No for v0.4. Each vault self-contained. Cross-vault synthesis is v0.5+. *(Both reviewers agreed)*

6. **Batch processing model**: Sequential (no core library changes). Parallel batch deferred to v0.4.1 if needed. *(Architect recommendation, accepted)*

7. **Philosophy framing**: Graduated trust model with four named levels. Resolves the "never a fait accompli" contradiction by honestly describing levels 3-4 as delegation within agreed boundaries. *(Codex flagged the contradiction; graduated trust resolves it)*

8. **Prompt absolute path**: Use vault detection pattern (find `.carrel/`) instead of embedded path. Survives iCloud sync, folder renames. *(Architect critical finding, accepted)*

9. **Hook parsing**: Regex-based frontmatter extraction, no YAML dependency. Gate automation checks on `_meta/briefs/` existence. Consider 15s timeout. *(Architect recommendation, accepted)*

10. **CLAUDE.md sync**: `/carrel-automate` must update root CLAUDE.md and `_meta/my-environment.md` alongside environment.json. Preserves the existing two-track truth model. *(Codex finding, accepted)*

---

## References

- [claude-howto](https://github.com/luongnv89/claude-howto) — Claude Code tutorial that prompted this exploration
- Carrel v0.3 CLAUDE.md — current architecture and design principles
- Claude Code docs: [scheduled tasks](https://docs.anthropic.com/en/docs/claude-code/scheduled-tasks), [headless mode](https://docs.anthropic.com/en/docs/claude-code/cli-reference), Desktop App
- Planning vision conversation (2026-04-04) — Lotus Wisdom contemplation on shared agency, three temporalities, desk metaphor
