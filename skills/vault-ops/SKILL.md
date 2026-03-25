---
name: vault-ops
description: "This skill should be used when a researcher wants to create, search, organize, or manage notes in their Obsidian vault. Triggers on 'create a note', 'find my notes about', 'organize', 'search vault', 'link notes', 'use template', or any vault file operation."
---

# vault-ops

Read, write, search, and organize the researcher's Obsidian vault. Handles note creation from templates, cross-linking with wiki syntax, and vault-wide search.

## When to Use

- Researcher wants to create a new note (paper, meeting, reflection, daily)
- Researcher asks to find, search, or organize vault content
- Researcher wants to link notes or explore connections
- Any read/write operation on vault files

## Vault Structure

Standard Carrel vault layout:

```
vault/
├── inbox/          # Drop zone — unsorted incoming
├── papers/         # Converted papers (markdown with frontmatter)
├── notes/          # Research notes, meeting notes, ideas
├── transcripts/    # Audio transcriptions
├── drafts/         # Writing in progress
├── talks/          # Presentation prep
├── admin/          # Committee work, letters, admin tasks
├── _meta/          # Cheat sheet, reflections, friction log
└── _templates/     # Note templates (paper, meeting, reflection, daily)
```

## Creating Notes

When creating a new note, use the appropriate template from `_templates/`:

1. **Paper note** → `_templates/paper.md` → save to `papers/`
2. **Meeting note** → `_templates/meeting.md` → save to `notes/`
3. **Reflection** → `_templates/reflection.md` → save to `_meta/reflections/`
4. **Daily note** → `_templates/daily.md` → save to `notes/`
5. **Freeform note** → no template → save to `notes/` or `inbox/`

Replace `{{date}}` placeholders with today's date (YYYY-MM-DD format).

Name files descriptively: `corley-gioia-2004.md`, `meeting-kevin-2026-03-26.md`, `draft-introduction.md`.

## YAML Frontmatter

All notes should have YAML frontmatter for Obsidian's Properties feature:

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

## Cross-Linking

Use Obsidian wiki-link syntax to connect notes:

- `[[note name]]` — link to another note
- `[[note name|display text]]` — link with custom display text
- `[[note name#heading]]` — link to a specific section

When creating or editing notes, suggest relevant links:
"This paper discusses identity construction — you have notes on that in `[[notes/identity-theory-overview]]`."

## Searching

To search the vault:
1. Use Grep/Glob tools to find content across markdown files
2. Search within specific folders for targeted results
3. Search YAML frontmatter for metadata queries (tags, authors, status)

## Organizing

- Move files between folders when the researcher requests
- Suggest organization: "I notice 5 files in inbox/ — want me to sort them?"
- Maintain consistent naming conventions
- Update links when moving files (find and replace `[[old-name]]` → `[[new-name]]`)

## Guidelines

- Always preserve existing content — never overwrite without asking
- Add frontmatter to files that don't have it
- Use the researcher's vocabulary (from CLAUDE.md profile)
- Suggest connections proactively: "This reminds me of your note on..."
- Keep file paths relative within the vault for Obsidian compatibility

## Related

- **Skills**: `environment-setup` creates the initial vault structure
- **Skills**: `convert` adds converted documents to the vault
- **Commands**: All commands that output to the vault use vault-ops conventions
