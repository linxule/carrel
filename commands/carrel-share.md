---
description: Generate a vault-specific onboarding handbook for a collaborator (RA, co-author, lab member)
---

# /carrel-share — Collaborator Handbook

Synthesizes your vault's accumulated context — friction log, capability log, reflections, configured tools, sensitivity rules, active threads — into a markdown handbook that brings a new collaborator up to speed on **how YOU work in this vault**, not on Carrel in general.

If they need to set up their own Carrel environment, that's `/carrel-setup`. This is for sharing the conventions and habits of an existing vault.

## When to Use

- Researcher says "share this with my RA / co-author / lab member"
- Researcher says "onboard a collaborator", "generate a handbook", "explain my setup to someone"
- A new lab member is joining and will work in this vault (or a similar one)
- Periodic refresh of a shared lab handbook

## What Happens

### Step 1: Brief

Ask the researcher about the collaborator (one short exchange — don't make it a form):

- Who are they? (name, role — RA, co-author, lab member, advisor)
- What do they need to do in this vault? (read papers? add transcripts? write drafts? review?)
- How experienced are they with research workflows? (new grad student, senior PhD, faculty)

If the researcher just says "generate it", make reasonable defaults: assume a new lab member with general access.

### Step 2: Read the Vault

- `.carrel/environment.json` — researcher profile (name, field, sensitivity, configured tools, automation status, wiki status)
- `CLAUDE.md` (vault root) — narrative profile and how-to-work-with guidance
- `_meta/friction_log.md` — pain points worth warning the collaborator about
- `_meta/capability-log.md` — custom trackers, plugins, conventions added over time
- `_meta/reflections/` — recent entries (last ~5) for in-flight context
- `_meta/mirror/` — most recent self-portrait if one exists
- `notes/threads/` — analytical threads with `status: active` (skip abandoned/dormant)
- `wiki/SCHEMA.md` (if it exists) — wiki conventions, tag taxonomy
- Vault structure — top-level folders that exist (`papers/`, `transcripts/`, `inbox/`, `notes/`, `drafts/`, `talks/`, `admin/`)

Degrade gracefully: if a source is missing or empty, skip the corresponding section. Never fabricate content.

### Step 3: Synthesize

Use the structure in `skills/collaborator-onboarding/references/handbook-template.md`. Sections (skip any that have no source material):

1. **About this vault** — researcher, field, what they study, current focus
2. **Vault layout** — what's where, what each folder is for
3. **Sensitivity & tool defaults** — what's local-only, what touches the cloud, what to never do
4. **Tools available** — converters, transcribers, MCPs configured
5. **How [researcher] works** — synthesized from reflections + capability log (workflows, habits, preferences)
6. **Conventions to know** — naming, frontmatter, custom trackers, wiki schema (if present)
7. **Active threads** — what's currently in flight (from `notes/threads/`, status=active only)
8. **Friction & workarounds** — recurring pain points, what's been tried, what works
9. **How to ask Claude for help** — the researcher's preferences, comfort level, the personalized CLAUDE.md context
10. **Where to start** — concrete first actions for the collaborator (drop a PDF, read X paper, read the cheat sheet)

Lead with substance, not boilerplate. One paragraph per section is plenty for most.

### Step 4: Save

Write to `_meta/handbook/[YYYY-MM-DD]-for-[name].md` (slug the name: lowercase, hyphens). Examples:
- `_meta/handbook/2026-04-20-for-jane.md`
- `_meta/handbook/2026-04-20-for-new-ra.md`

If `_meta/handbook/` doesn't exist, create it.

### Step 5: Show & Refine

Show the researcher the draft. Ask one focused question: "Anything missing, or anything that shouldn't go to [name]?" Apply edits. Save the final.

### Step 6: Optional Canonical Copy

Offer: "Want me to also save this as `_meta/lab-handbook.md` — your canonical 'latest version' that you can update over time?" If yes, copy the file. If no, the dated handbook stands alone.

## Modes

**Interactive** (default): brief exchange in Step 1, conversational refinement in Step 5.

**Quick** (`--quick`): skip the brief, use defaults (new lab member, general access), save the dated handbook, skip the canonical copy. Useful for refreshing periodically.

## Guidelines

- **Vault-specific, not Carrel-general.** Don't write a Carrel tutorial. Write the conventions of THIS vault: what THIS researcher does, what THIS lab cares about.
- **Honest about gaps.** If the friction log is empty, say "no friction recorded yet" rather than inventing pain points.
- **Respect sensitivity.** If the researcher is HIGH sensitivity and the collaborator's role is unclear, ask whether to redact specific projects or notes from the handbook. Default to including only project-level descriptions, not file lists.
- **Short over long.** A handbook the collaborator will actually read beats a comprehensive document they'll skim.
- **Update, don't accumulate.** Each handbook is a snapshot. The canonical `lab-handbook.md` is overwritten when refreshed; the dated handbooks accumulate as a record of how the vault evolved.

## Related

- **Skill**: `collaborator-onboarding` (full synthesis logic + section template)
- **Commands**: `/carrel-mirror` (researcher-facing self-portrait — same data, different audience)
- **Commands**: `/carrel-setup` (for collaborators who need their OWN vault)
- **Files**: `_meta/handbook/`, `_meta/lab-handbook.md` (optional canonical copy)
