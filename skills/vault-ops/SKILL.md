---
name: vault-ops
description: "This skill should be used when a researcher wants to create, search, organize, or manage notes in their Obsidian vault. Triggers on 'create a note', 'find my notes about', 'organize', 'search vault', 'link notes', 'use template', 'vault status', 'check inbox', 'what's in my vault', or any vault file operation."
---

# vault-ops

Read, write, search, and organize the researcher's Obsidian vault. The CLI handles mechanical operations — this skill provides the judgment layer: which template, what links, when to reorganize.

## When to Use

- Researcher wants to create a new note (paper notes, meeting, reflection, daily)
- Researcher asks to find, search, or organize vault content
- Researcher wants to link notes or explore connections
- Any read/write operation on vault files

## Vault Structure

Standard Carrel vault layout (created via `carrel vault init <path>`):

```
vault/
├── inbox/          # Drop zone — unsorted incoming
├── papers/         # Converted papers — one FOLDER per paper
│   └── corley-gioia-2004/
│       ├── paper.md            # The converted paper content
│       └── images/             # Extracted figures/assets
├── notes/          # Research notes, meeting notes, ideas
├── transcripts/    # Audio transcriptions (filed via carrel transcript)
├── drafts/         # Writing in progress
├── talks/          # Presentation prep
├── admin/          # Committee work, letters, admin tasks
├── _meta/          # Cheat sheet, reflections, friction log
└── _templates/     # Note templates (meeting, reflection, daily, paper-notes)
```

## Papers vs Notes — Critical Distinction

**Converted papers** and **researcher notes** are different things:

- **Converted paper** = the actual paper content converted from PDF/DOCX → filed to `papers/<author-year>/paper.md` by `carrel paper convert`. NO note template. Just frontmatter + converted content.
- **Paper notes** = researcher's own thinking about a paper → saved to `notes/` using `_templates/paper-notes.md`. Links back with `[[papers/corley-gioia-2004/paper]]`.

NEVER apply a note template to a converted paper. The convert command handles papers; vault-ops handles notes about papers.

## Template Selection Judgment

Use `carrel vault new <template> <name>` to create from template, or apply manually:

1. **paper-notes** — researcher's thinking about a specific paper → `notes/`
2. **meeting** — any synchronous conversation → `notes/`
3. **reflection** — periodic sensemaking, project retrospectives → `_meta/reflections/`
4. **daily** — daily log, task tracking → `notes/`
5. **freeform** — no template, open-ended → `notes/` or `inbox/`

Replace `{{date}}` placeholders with today's date (YYYY-MM-DD). Name files descriptively: `meeting-kevin-2026-03-26.md`, `notes-on-corley-gioia-2004.md`.

## YAML Frontmatter

All notes should have YAML frontmatter for Obsidian's Properties:

```yaml
---
title: The Title
tags: [qualitative, identity, organizational-change]
date: 2026-03-26
status: draft
---
```

For paper notes, include: title, authors, year, journal, doi, tags, status.
For meeting notes: date, participants, project, type.

## Cross-Linking Intelligence

Use Obsidian wiki-link syntax to connect notes:

- `[[note name]]` — link to another note
- `[[note name|display text]]` — link with custom display text
- `[[note name#heading]]` — link to a specific section

When creating or editing notes, actively suggest relevant links based on vault content:
"This paper discusses identity construction — you have notes on that in `[[notes/identity-theory-overview]]`."

Use `carrel vault search <query>` to surface related content before suggesting links.

## Vault Hygiene

- Check `carrel vault status` to see accumulation before suggesting organization
- Use `carrel vault organize` to get sorting suggestions for inbox files
- If inbox has 5+ files, proactively flag: "You have N files in inbox/ — want me to sort them?"
- Update links when moving files: find and replace `[[old-name]]` → `[[new-name]]`
- Every file has a home — nothing stays in vault root

## Guidelines

- Always preserve existing content — never overwrite without asking
- Add frontmatter to files that lack it
- Use the researcher's vocabulary (from CLAUDE.md profile)
- Suggest connections proactively when context is recognizable
- Keep file paths relative within the vault for Obsidian compatibility

## Related

- **CLI**: `carrel vault init` creates vault structure; `carrel paper convert` files papers; `carrel transcript` files transcripts
- **Skills**: `convert` adds converted documents; `environment-setup` bootstraps the workspace
