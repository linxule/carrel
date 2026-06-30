# Field Map

Use this workflow when a researcher asks for a field map, knowledge map,
literature synthesis, cross-source memory, contradiction tracking, or a durable
knowledge base inside the vault.

## Contents

- Activation
- Vault Layout
- Read Mode
- Write Mode
- Ingest And Lint
- Logging
- Automation

## Activation

Call it a field map in conversation. Use "wiki" only for file paths or
technical discussion.

Propose a field map when the researcher has many sources, repeatedly asks
cross-source questions, requests a knowledge base, or wants contradictions and
concepts tracked over time. Do not activate it for a small vault unless the
researcher asks.

Before creating or modifying field-map pages, check:

```bash
python3 scripts/carrel.py trust check wiki:propose --vault <vault>
```

Explicit researcher opt-in grants consultative field-map behavior even if the
global automation trust level is advisory. Higher automation trust levels allow
more autonomous field-map maintenance only within the same sensitivity policy.

## Vault Layout

Use `wiki/` as the synthesis layer:

- `wiki/SCHEMA.md`: conventions, taxonomy, page thresholds, and tags.
- `wiki/index.md`: sectioned catalog of pages.
- `wiki/log.md`: chronological decisions with reasons.
- `wiki/entities/`: people, organizations, cases, methods, tools.
- `wiki/concepts/`: theories, constructs, debates, methods.
- `wiki/comparisons/`: side-by-side syntheses.
- `wiki/queries/`: saved answers worth keeping.

`papers/` and `transcripts/` are source layers. `notes/` is the researcher's
own thinking. Do not overwrite those layers during field-map maintenance.

## Read Mode

For domain questions, read `wiki/index.md`, then only the relevant field-map
pages. For large maps, search within `wiki/` before loading pages.

Cite field-map pages with vault links so the researcher can trace the answer.
If an answer is worth keeping, propose saving it to `wiki/queries/` at
consultative trust; at delegated or partnership trust, file it and update the
index and log.

Do not log trivial lookups.

## Write Mode

Before writes, run:

```bash
python3 scripts/carrel.py trust check wiki:write --vault <vault>
```

Then orient by reading `wiki/SCHEMA.md`, `wiki/index.md`, and recent
`wiki/log.md`. Write only after approval unless the configured trust level
allows the action.

## Ingest And Lint

For new converted sources, read the source markdown and create or update field
map pages only when the source adds durable concepts, entities, comparisons, or
contradictions. Keep short one-off observations in notes instead.

Lint field-map pages for broken links, orphan pages, missing index entries,
tag drift, and contradiction pages without review status.

For every substantial write, update `wiki/index.md` and append a log entry.

## Logging

`wiki/log.md` must explain why a non-trivial decision was made:

- created page because multiple sources distinguish a concept;
- merged or split pages with rationale;
- contradiction flagged and source pages linked;
- query filed because it will likely be reused.

Reasoning is required because future agents need continuity.

## Automation

When `automation.wiki_maintenance` is true, unattended runs may scan new
sources after inbox processing, ingest approved source classes, run quick lint,
and add field-map status to the morning brief. Uncertain source interpretation
or sensitivity conflicts go to `_meta/pending-decisions.md`.
