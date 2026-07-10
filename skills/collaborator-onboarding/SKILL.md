---
name: collaborator-onboarding
description: "This skill should be used when a researcher wants to share their Carrel vault with someone else — an RA, co-author, lab member, or advisor. Triggers on 'share with', 'onboard a collaborator', 'generate a handbook', 'lab handbook', 'help my RA get up to speed', or when the /carrel-share command is invoked. Distinct from /carrel-setup, which sets up a NEW vault for a NEW researcher; this skill assumes an existing vault with accumulated context."
---

# collaborator-onboarding

Synthesizes the accumulated context of an existing Carrel vault into a markdown handbook that a new collaborator can read to come up to speed on **how this researcher works in this vault**. Vault-specific, not Carrel-general.

## When to Use

- Researcher mentions sharing the vault with someone (RA, co-author, lab member, advisor)
- The `/carrel-share` command is invoked
- A new lab member is joining and will work in this vault
- Periodic refresh of a shared lab handbook
- After significant changes to the vault (new tools added, sensitivity changed, automation enabled)

## What This Skill Is Not

- **Not `/carrel-setup`.** Setup is for someone creating their own new Carrel environment from scratch. This skill assumes the vault already exists and has been used.
- **Not `/carrel-mirror`.** Mirror writes a self-portrait for the researcher's own awareness. This skill writes for someone else to read — different audience, different framing.
- **Not Claude Code's `/team-onboarding`.** That command generates generic Claude Code usage tips from your local session history. This skill produces a vault-specific handbook from vault content.

## Source Material

Read these in order. Skip any that don't exist or are empty — degrade gracefully.

| Source | Purpose |
|--------|---------|
| `.carrel/environment.json` | Researcher profile, sensitivity, configured tools, automation status, wiki status, collaborators field, team_context |
| `CLAUDE.md` (vault root) | Narrative profile, "how to work with [name]" guidance |
| `_meta/friction_log.md` | Recurring pain points the collaborator should know about |
| `_meta/capability-log.md` | Custom trackers, plugins, conventions added over time |
| `_meta/reflections/` | Recent ~5 entries — current preoccupations |
| `_meta/mirror/` | Most recent self-portrait — synthesized trajectory |
| `notes/threads/` | Active analytical threads (status: active only) |
| `wiki/SCHEMA.md` | Wiki conventions and tag taxonomy (only if wiki active) |
| `wiki/index.md` | List of wiki pages (only if wiki active) |
| Vault folder structure | Top-level folders that exist in this vault |
| `_meta/cheat_sheet.md` | Existing reference card — point the collaborator at it |

## Synthesis Approach

The handbook must answer four questions for the collaborator:

1. **What does this researcher actually study and do?** (substance — from CLAUDE.md, environment.json, recent reflections)
2. **What are the rules and habits I need to respect?** (sensitivity, naming, conventions — from CLAUDE.md, capability log, wiki schema)
3. **What's currently happening?** (active threads, recent work — from `notes/threads/`, latest reflection)
4. **What should I do first?** (concrete entry points — from configured tools, vault structure)

Use `references/handbook-template.md` for the markdown structure. Each section has a "skip if" rule for graceful degradation.

## Modes

The skill has two operating modes — choose based on how the researcher framed the request.

### Interactive behavior (canonical path)

A short brief exchange up front, then conversational refinement at the end. Use this when the researcher says "share with my RA" or "onboard Jane" without further detail.

**Brief (one short exchange — don't make it a form):**
- Who are they? (name, role — RA, co-author, lab member, advisor)
- What do they need to do in this vault? (read papers? add transcripts? write drafts? review?)
- How experienced are they with research workflows? (new grad student, senior PhD, faculty)

**Synthesis and refinement:** read the sources above, apply the selected sensitivity rules yourself, draft the handbook, and show it to the researcher. Ask one focused question: "Anything missing, or anything that shouldn't go to [name]?" Apply edits and obtain approval of the exact final body.

**Canonical copy (optional):** offer "Want me to also save this as `_meta/lab-handbook.md` — your canonical 'latest version' you can update over time?" If yes, copy the file. If no, the dated handbook stands alone.

### Quick mode

Skip the brief, use defaults (new lab member, general access), save the dated handbook, skip the canonical copy. Use this when the researcher says "just generate one", "quick handbook", "draft something I can edit", or otherwise signals they want a starting point rather than a conversation.

Quick mode is a behavioral shortcut and uses the CLI's deterministic fallback synthesis via `--mode quick`. It is not the canonical path for a polished handoff.

## Calling Pattern

For the interactive path, pipe the exact approved handbook body to the CLI:

```bash
printf '%s\n' "<approved handbook body>" | carrel vault share generate \
  --mode full \
  --for <collaborator-slug> \
  --sensitivity low|medium|high \
  --from-stdin [--canonical] [--vault PATH]
```

The CLI owns vault-safe path validation and exact persistence to the dated file and, only with `--canonical`, `_meta/lab-handbook.md`. On the stdin path it does not read vault sources, synthesize prose, or sanitize/redact the supplied body. This skill owns source reads, synthesis, sensitivity judgment, preview, refinement, and approval.

Use `--explain --from-stdin` with the same body to preview destinations and metadata without writing. For a quick starter only, omit stdin and call `--mode quick`; the deterministic fallback is backward-compatible but less context-rich.

## Output

Files land at `_meta/handbook/[YYYY-MM-DD]-for-[collaborator-slug].md`.

- `[YYYY-MM-DD]` = today's date
- `[collaborator-slug]` = lowercase, hyphenated. Examples: `jane`, `new-ra`, `co-author-cornell`. If the collaborator isn't named, use `lab-member`.

Optionally also save as `_meta/lab-handbook.md` — the canonical "latest" version. Researcher chooses (interactive mode only).

## Sensitivity Considerations

The `--sensitivity` flag records the selected policy tier. This skill must apply that tier while choosing sources and drafting the approved stdin body; do not claim the stdin persistence path sanitizes it.

**Default:** read the researcher's `sensitivity` from `.carrel/environment.json` and pass it through. Override only when the collaborator's access is narrower than the researcher's vault-wide setting (e.g., a HIGH-sensitivity vault but the new RA only needs the public-facing project — pass `--sensitivity medium` with the researcher's confirmation).

**Narration during synthesis (HIGH sensitivity):**
- Default to project-level descriptions, not file lists
- Don't include unpublished manuscript titles or transcript filenames in the handbook
- Ask whether specific projects, papers, or threads should be redacted before sharing
- Mention sensitivity rules prominently in the handbook itself (the collaborator needs to know what they can and can't do)

**Narration during synthesis (MEDIUM sensitivity):**
- File lists are fine; redact only files explicitly marked sensitive (e.g., filenames starting with `private-` or `irb-`)
- Mention sensitivity rules briefly so the collaborator knows the contract

**Narration during synthesis (LOW sensitivity):**
- Full vault visibility; no redaction beyond the researcher's explicit asks

If the collaborator's role is unclear, default to the more restrictive interpretation and tell the researcher you've done so: "I treated their access as HIGH-sensitivity since you didn't specify their role — let me know if I should loosen it."

## Anti-Patterns to Avoid

- **Don't write a Carrel tutorial.** The collaborator can read Carrel docs; this handbook is about THIS vault and THIS researcher.
- **Don't fabricate.** If the friction log is empty, write "no recurring friction recorded yet" rather than inventing pain points to fill the section.
- **Don't recite raw counts.** "14 papers in `papers/`" is not useful. "Mostly institutional theory, with a recent shift toward field-level change" is.
- **Don't accumulate.** Each handbook is a snapshot. Don't try to maintain a single growing document automatically — let the researcher refresh when they want to.
- **Don't pretend to know the collaborator.** If they haven't been described, write generic guidance and flag it: "Tailor the entry-point recommendations once you know more about [name]."

## Update Cadence

The handbook is a snapshot. Refresh whenever:
- A new collaborator joins (new dated handbook for them)
- The vault has changed substantially (new tools, sensitivity shift, automation enabled, wiki activated)
- The shared lab handbook is being passed around and someone notices it's stale (overwrite the canonical `lab-handbook.md`)

There is no automatic refresh. The researcher decides.

## Related

- **Command**: `/carrel-share` (entry point for this skill)
- **Skills**: `vault-ops` (vault structure conventions), `automation` (if vault has scheduled automation, surface that to the collaborator), `knowledge-wiki` (if wiki active, explain its conventions)
- **Commands**: `/carrel-mirror` (self-portrait — adjacent but different audience), `/carrel-setup` (for collaborators who need their own vault)
- **Files**: `_meta/handbook/`, `_meta/lab-handbook.md` (optional canonical copy)
