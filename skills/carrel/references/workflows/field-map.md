# Field Map

Use this workflow for a durable cross-source synthesis, contradiction tracker,
literature map, or knowledge base inside the vault. Call it a field map in
conversation; use “wiki” only for paths and technical details.

## Activation and Trust

Propose a field map when the researcher asks, repeatedly asks cross-source
questions, or has enough sources that synthesis is slipping. Respect
`wiki_preference: researcher-managed` and active proposal deferrals.

The three actions are intentionally distinct:

```bash
python3 scripts/carrel.py trust check wiki:propose --vault <vault>
python3 scripts/carrel.py trust check wiki:apply-approved --vault <vault>
python3 scripts/carrel.py trust check wiki:write --vault <vault>
```

- `wiki:propose` (Consultative): inspect and present an exact batch.
- `wiki:apply-approved` (Consultative): apply only the batch the researcher just
  approved.
- `wiki:write` (Delegated): autonomous or unattended wiki maintenance.

A direct request does not bypass these gates. At Consultative trust, show every
path and material edit, obtain approval, check `wiki:apply-approved`, and apply
only that batch. Re-propose any expansion.

## Vault Layout

Use `wiki/` as the synthesis layer with `SCHEMA.md`, `index.md`, `log.md`, and
`entities/`, `concepts/`, `comparisons/`, and `queries/` directories. Do not add
Hermes' `raw/` layer or use `WIKI_PATH`. Carrel's `papers/`, `transcripts/`, and
`inbox/` are source layers; `notes/` remains the researcher's voice.

## Read and Write Modes

For queries, read `wiki/index.md`, search within `wiki/`, and load only relevant
pages. Cite pages with vault links and show both sides of contradictions. Do not
log trivial lookups.

Before drafting writes, read `wiki/SCHEMA.md`, `wiki/index.md`, recent
`wiki/log.md`, relevant pages, and researcher callouts. Every substantial write
updates the index and appends reasoning to the log.

Page frontmatter requires title, created/updated dates, type, tags, and sources.
It may also include:

```yaml
source_digests:
  papers/author-year/paper.md: <sha256-of-markdown-body>
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
```

Compute digests over the source Markdown body after frontmatter. This is
separate from Carrel's source-file `source_hash`. Existing pages without
digests or optional quality fields remain valid; backfill only when that page
is edited or through an approved repair. On pages synthesizing at least three
sources, mark source-dependent paragraphs with a relative marker such as
`^[papers/author-year/paper.md]`.

## Lint and Automation

Lint for broken links, orphans, missing index entries, tag drift, oversized
pages, low confidence, contested pages, contradiction links, single-source
pages without confidence, missing digests, and source drift. Findings are
review signals, not permission to repair.

When `automation.wiki_maintenance` is true, autonomous maintenance still
requires Delegated trust and `wiki:write`. Run after inbox processing. Add
counts for new/updated pages, low confidence, contested, contradictions,
single-source confidence gaps, source drift, orphans, and un-ingested sources
to the morning brief, along with one synthesis insight and changed paths.
