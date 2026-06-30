# Vault Ops

Use this workflow for note creation, vault search, organization proposals,
Obsidian-facing formatting, analytical threads, and research database views.

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

## Capability Log

When creating a custom tracker, callout pattern, canvas, or workflow, append to
`_meta/capability-log.md` with date, type, what was created, why, source
reference used, and whether it looks reusable.

Update `_meta/my-environment.md` when tools, cloud services, custom trackers,
or optional capabilities change.
