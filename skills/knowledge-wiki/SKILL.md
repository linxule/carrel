---
name: knowledge-wiki
description: "This skill should be used when a researcher wants to build, query, or maintain a synthesized knowledge base across their sources. Triggers on 'field map', 'knowledge map', 'what do my sources say about', 'synthesize across papers', 'literature review', 'systematic review', 'wiki', 'track contradictions', 'knowledge base', 'I keep losing track', 'lint wiki', 'wiki health', or when the agent observes repeated cross-source questions in a vault with 15+ papers."
---

# knowledge-wiki

Maintain a persistent field map as interlinked Markdown pages inside a Carrel vault. This is a curated adaptation of [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) and [Hermes Agent llm-wiki 2.1](https://github.com/NousResearch/hermes-agent/blob/8e3f9537db21b49ebe796f7b5a6ff489028fe1fb/skills/research/llm-wiki/SKILL.md).

The researcher curates sources and directs analysis. The agent synthesizes, cross-references, preserves provenance, and maintains navigation. Call it a “field map” in researcher-facing conversation; reserve “wiki” for paths and technical explanation.

## Activation

Use an active wiki when `wiki/SCHEMA.md` exists. Consider proposing one when the researcher explicitly asks, repeatedly asks cross-source questions, or has 15+ substantial sources and needs durable synthesis. Do not propose when `wiki_preference` is `researcher-managed` or a deferral date has not passed.

Before presenting a proposed schema or write batch, run:

```bash
carrel trust check wiki:propose --vault .
```

A direct request does not bypass the trust boundary. If the check fails, explain the required level and help the researcher raise trust through `/carrel-automate`; do not write.

## Trust-Gated Actions

| Action | Minimum trust | Meaning |
|--------|---------------|---------|
| `wiki:propose` | Consultative | Inspect sources and present an exact proposed batch without changing wiki files. |
| `wiki:apply-approved` | Consultative | Apply only the exact batch the researcher just approved. |
| `wiki:write` | Delegated | Perform autonomous or unattended wiki maintenance. |

At Consultative trust, use this sequence:

1. Orient and draft the exact file additions/edits.
2. Show the batch, including every path and material change.
3. Receive explicit approval for that batch.
4. Run `carrel trust check wiki:apply-approved --vault .`.
5. Apply only the approved batch; re-propose any expansion.

At Delegated or Partnership trust, run `carrel trust check wiki:write --vault .` before autonomous writes. Enabling the wiki does not silently raise global trust.

## Vault Mapping

Carrel does not import Hermes' separate `raw/` layer or `WIKI_PATH` environment variable. Existing vault folders remain the source layer:

```text
papers/          converted source papers; read only during wiki work
transcripts/     converted transcripts; read only during wiki work
inbox/           sources awaiting normal Carrel routing
notes/           researcher's voice; never wiki-managed
wiki/            agent-maintained synthesis
  SCHEMA.md
  index.md
  log.md
  entities/
  concepts/
  comparisons/
  queries/
drafts/          researcher writing; never wiki-managed
```

The wiki skill reads already-converted Markdown. Use `convert`, `transcribe`, or `web-capture` before ingestion when needed.

## Read Mode

1. Read `wiki/index.md` and search `wiki/` for relevant terms.
2. Read only the relevant pages; use source files when the compiled page lacks needed detail.
3. Cite field-map pages with wikilinks and expose contradictions rather than flattening them.
4. Propose filing a durable answer at Consultative trust. Apply it only through the approved-batch sequence. At Delegated+ trust, autonomous filing uses `wiki:write`.
5. Log only queries that become wiki pages.

## Write Mode

Before drafting a write batch, read `wiki/SCHEMA.md`, `wiki/index.md`, the last 30 lines of `wiki/log.md`, relevant researcher callouts, and related existing pages. Then follow `references/wiki-protocol.md`.

Every page uses required frontmatter plus optional quality signals:

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [taxonomy-tag]
sources: [papers/author-year/paper.md]
source_digests:
  papers/author-year/paper.md: <sha256-of-markdown-body>
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

`confidence`, `contested`, and `contradictions` are optional. Existing pages without quality fields or `source_digests` remain valid; backfill them only when editing that page or applying an approved repair.

Compute each `source_digests` value over the source Markdown body after its closing frontmatter delimiter. This wiki-level map is distinct from Carrel's source-file `source_hash` idempotency field. On pages synthesizing three or more sources, append a marker such as `^[papers/author-year/paper.md]` to paragraphs whose claims depend on a particular source.

## Lint

Quick lint new or changed pages for outbound links, index membership, required fields, valid taxonomy tags, and current source digests. Full lint additionally reports:

- orphan pages and broken wikilinks;
- stale, oversized, and unindexed pages;
- low-confidence pages;
- pages with `contested: true`;
- contradiction links needing review;
- single-source pages without `confidence`;
- source digest drift.

Report counts and exact paths. Drift is a review signal, not permission to rewrite a page or source automatically.

## Automation

When `automation.wiki_maintenance` is true, autonomous maintenance requires Delegated trust and a successful `wiki:write` check. Run wiki work after inbox processing, then include these counts in the morning brief: pages new/updated, low confidence, contested, contradictions, missing single-source confidence, source drift, orphans, and un-ingested sources. Include one synthesis insight and every changed path with revert guidance.

## Durable Handoff

Append reasoning—not just actions—to `wiki/log.md`. Never remove `> [!researcher]` callouts. Update `index.md` for every created, archived, or renamed page. Ask before a batch touching 10 or more existing pages even when interactive trust permits it.

## Related

- `references/wiki-protocol.md`: schemas, ingest/query/lint details, and provenance rules.
- `references/trust-activation.md`: proposal, initialization, and trust-graduation flow.
- `automation`: unattended scheduling and morning-brief behavior.
