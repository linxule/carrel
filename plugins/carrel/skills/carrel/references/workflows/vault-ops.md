# Vault Ops

Use this workflow for note creation, vault search, organization proposals,
Obsidian-facing formatting, analytical threads, and research database views.

## Contents

- Papers And Notes
- Notes
- Links And Hygiene
- Analytical Threads
- Obsidian Formatting
- Research Databases
- Template Provenance
- Capability Log

## Papers And Notes

Converted papers are source content filed under `papers/<slug>/paper.md`.
Never apply a note template to converted paper content.

Paper notes are the researcher's own thinking and belong in `notes/`, usually
from `assets/templates/paper-notes.md`, with a link back to the converted
paper.

## Notes

Choose templates by intent:

- paper notes: thinking about a specific source;
- meeting: synchronous conversation;
- reflection: sensemaking or retrospective;
- daily: short work log;
- freeform: open research note.

Use frontmatter for title, date, status, tags, and type-specific fields. Keep
paths relative to the vault and prefer stable filenames over later moves.

## Links And Hygiene

Use Obsidian wikilinks for durable relationships:

- `[[note name]]`
- `[[note name|display text]]`
- `[[note name#heading]]`

When moving or renaming files, propose the move first, then update links if the
researcher approves. Do not reorganize the vault opportunistically.

If `inbox/` accumulates several files, offer a sorting pass. Use trust checks
before moving files automatically.

## Analytical Threads

Use `notes/threads/<thread-name>/` when the researcher wants parallel
interpretations of the same corpus or competing theoretical lenses.

Each thread should have a `README.md` with lens, starting questions, source
material, and status: active, paused, completed, or abandoned. Abandoned threads
stay in the vault with a reason.

## Obsidian Formatting

Use callouts in reading notes and interview summaries, not in raw converted
papers or raw transcripts:

- quote for excerpts;
- question for unresolved points;
- important for findings;
- warning for sensitivity alerts.

Use embeds when a note needs to display a specific section of a source inline.
Use foldable callouts for long passages.

## Research Databases

The `.base` templates in `assets/templates/` are optional Obsidian views:

- `reading-progress.base`: always useful as a reading pipeline.
- `paper-tracker.base`: many papers or literature review work.
- `interview-tracker.base`: qualitative interview projects.
- `writing-tracker.base`: active writing projects.

Before creating a custom database, ask what the researcher wants to track and
which columns matter. Start with folder or tag filters and only add formulas
when needed. Custom local databases must not use Carrel template markers.

## Template Provenance

The four shipped root `.base` trackers carry
`# carrel-template: name v0.0.0` markers so upgrades can report drift without
clobbering customization. Current marker scanning does not cover ordinary
Markdown or JSON scaffold assets.

| | Plugin-shipped | Vault-local |
|---|---|---|
| **Has `carrel-template:` marker** | Yes | Never |
| **Created by** | `vault init` (scaffold) | Claude during sessions, or the researcher manually |
| **Overwritten on re-scaffold** | Never; report marker drift instead | Never |

The bundled scaffold writes selected `.base` trackers at the vault root and
skips every existing path. It reports outdated or unversioned shipped trackers
without replacing them and leaves legacy `_templates/*.base` copies untouched.
When hand-editing or regenerating a vault template, preserve the existing marker
line yourself, and never add a
`carrel-template:` marker to a vault-local or custom file; that namespace is
reserved for plugin-shipped content.

## Capability Log

When creating a custom tracker, callout pattern, canvas, or workflow, append to
`_meta/capability-log.md` with date, type, what was created, why, source
reference used, and whether it looks reusable.

Update `_meta/my-environment.md` when tools, cloud services, custom trackers,
or optional capabilities change.
