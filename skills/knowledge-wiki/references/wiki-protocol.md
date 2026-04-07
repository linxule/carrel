# Wiki Protocol

Adapted from [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) and [Hermes Agent's implementation](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md). This document defines the operations and conventions for maintaining the wiki inside a carrel vault.

When upstream improves, update this document. The carrel-specific adaptations (folder mapping, trust gating, log reasoning) live in the parent SKILL.md and trust-activation.md — they're stable across protocol updates.

---

## Architecture: Two Layers in One Vault

The upstream pattern defines three layers (raw/wiki/schema). In carrel, the raw layer IS the existing vault:

| Layer | Upstream | Carrel adaptation |
|-------|----------|-------------------|
| **Source (immutable)** | `raw/articles/`, `raw/papers/`, `raw/transcripts/` | `papers/`, `transcripts/`, `inbox/` — already exist |
| **Wiki (agent-owned)** | `entities/`, `concepts/`, `comparisons/`, `queries/` | `wiki/entities/`, `wiki/concepts/`, `wiki/comparisons/`, `wiki/queries/` |
| **Schema** | `SCHEMA.md`, `index.md`, `log.md` at root | `wiki/SCHEMA.md`, `wiki/index.md`, `wiki/log.md` |

The agent reads source folders but NEVER modifies them. The agent owns everything in `wiki/`.

---

## SCHEMA.md Template

Generated during wiki initialization, customized to the researcher's domain. The domain and tag taxonomy come from:
- `environment.json` → researcher field
- Existing paper frontmatter tags in `papers/`
- The researcher's own input during the consultative proposal

```markdown
# Wiki Schema

## Domain
[Generated from researcher profile — e.g., "Organizational behavior research, with focus on
identity, sensemaking, and institutional change"]

## Source Folders
The wiki synthesizes from these carrel vault folders (read-only):
- `papers/` — converted academic papers and web captures
- `transcripts/` — audio/video transcriptions
- `notes/` — researcher's own notes (reference but don't duplicate)

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `organizational-identity.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` for inter-wiki links (minimum 2 outbound links per page)
- Use `[[papers/author-year/paper]]` to reference source material
- When updating a page, always bump the `updated` date
- Every new page must be added to `wiki/index.md` under the correct section
- Every action must be appended to `wiki/log.md` with reasoning

## Frontmatter

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [from taxonomy below]
sources: [papers/author-year/paper, transcripts/name]
---
```

## Tag Taxonomy
[Generated from existing paper tags + researcher input. Start with 10-20 tags.]

Example for organizational behavior:
- Theories: identity, sensemaking, institutional-theory, practice-theory
- Methods: qualitative, quantitative, case-study, ethnography, grounded-theory
- Topics: organizational-change, leadership, culture, innovation
- People/Orgs: person, organization, research-group
- Meta: comparison, timeline, controversy, gap, methodology

Rule: every tag on a page must appear in this taxonomy. If a new tag is needed,
add it here first, then use it. This prevents tag sprawl.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions or things outside the domain
- **Split a page** when it exceeds ~200 lines — break into sub-topics with cross-links
- **Archive a page** when content is fully superseded — move to `wiki/_archive/`, remove from index

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for researcher review in the morning brief or _meta/pending-decisions.md
```

---

## index.md Template

The index is sectioned by type. Each entry is one line: wikilink + summary.

```markdown
# Field Map Index

> Content catalog. Every wiki page listed under its type with a one-line summary.
> Read this first to find relevant pages for any query.
> Last updated: YYYY-MM-DD | Total pages: N

## Entities
<!-- Alphabetical within section -->
- [[wiki/entities/weick]] — Karl Weick, sensemaking theorist, organizational studies
- [[wiki/entities/gioia]] — Dennis Gioia, identity and sensemaking researcher

## Concepts
- [[wiki/concepts/organizational-identity]] — How organizations define "who we are"
- [[wiki/concepts/sensemaking]] — Process of making sense of ambiguous situations

## Comparisons
- [[wiki/comparisons/identity-vs-image]] — Organizational identity vs. organizational image

## Queries
- [[wiki/queries/methods-for-studying-identity]] — Filed query: methodological approaches
```

**Scaling:** When any section exceeds 50 entries, split into sub-sections by first letter or sub-domain. When index exceeds 200 entries, create `wiki/_meta/topic-map.md` for thematic navigation.

---

## log.md Template

```markdown
# Wiki Log

> Chronological record of all wiki actions. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: create, ingest, update, query, lint, archive
> Each entry includes reasoning for non-trivial decisions.
> When this file exceeds 500 entries, rotate: rename to log-YYYY.md, start fresh.

## [YYYY-MM-DD] create | Wiki initialized
- Domain: [from researcher profile]
- Tag taxonomy: [N] initial tags from existing paper frontmatter
- Initial pages: [N] entities, [N] concepts from existing vault content
```

---

## Operations

### 1. Ingest

When the researcher adds a source or when automation detects new files:

**Step 1 — Identify new sources:**
- In interactive mode: researcher points to a specific file or says "I just added a paper"
- In automation mode: scan `papers/` and `transcripts/` for files with mtime newer than the last log entry

**Step 2 — Read the source:**
- Read the converted markdown from its location in the vault
- For large papers (100+ pages of markdown), focus on abstract, introduction, discussion, conclusion

**Step 3 — Discuss takeaways (interactive mode only):**
- "What stands out to you?" / "How does this relate to your current work?"
- In automation mode: skip this — proceed directly to synthesis

**Step 4 — Check what already exists:**
- Search `wiki/index.md` for mentioned entities and concepts
- Search across `wiki/**/*.md` for key terms from the source
- This prevents duplicates and ensures cross-referencing

**Step 5 — Write or update wiki pages:**
- **New entities/concepts:** Create only if they meet Page Thresholds in SCHEMA.md
- **Existing pages:** Add new information, update facts, bump `updated` date
- **Contradictions:** Follow the Update Policy — never silently overwrite
- **Cross-reference:** Every new/updated page must link to at least 2 other wiki pages via `[[wikilinks]]`
- **Tags:** Only use tags from the taxonomy in SCHEMA.md
- **Source references:** Link back to the source file: `sources: [papers/smith-2025/paper]`

**Step 6 — Update navigation:**
- Add new pages to `wiki/index.md` under correct section, alphabetically
- Update the "Total pages" count and "Last updated" date
- Append to `wiki/log.md` with reasoning for each create/update decision

**Step 7 — Report what changed:**
- In interactive mode: list every file created/updated with brief explanation
- In automation mode: add to morning brief

A single source can trigger updates across 5-15 wiki pages. This is the compounding effect.

### 2. Query

When the researcher asks about their domain:

**Step 1 — Find relevant pages:**
- Read `wiki/index.md` to identify relevant pages by title and summary
- For large wikis, also search `wiki/**/*.md` for key terms

**Step 2 — Read relevant pages:**
- Read the wiki pages, not the raw sources (the wiki IS the compiled knowledge)
- Only go to source papers when the wiki page doesn't have enough detail

**Step 3 — Synthesize answer:**
- Draw from compiled wiki knowledge
- Cite wiki pages: "Based on [[wiki/concepts/sensemaking]] and [[wiki/entities/weick]]..."
- When the wiki has contradictions noted, present both positions

**Step 4 — File if valuable:**
- If the answer is a substantial comparison, deep dive, or novel synthesis → save to `wiki/queries/` or `wiki/comparisons/`
- Don't file trivial lookups — only answers that would be painful to re-derive
- Update index.md if filed

**Step 5 — Log (only if filed):**
- If a query result was filed to `wiki/queries/` or `wiki/comparisons/`, append to log.md
- Trivial lookups do not require logging — keeps query mode lightweight

### 3. Lint

When the researcher asks for a health check, or during weekly automation:

**Quick lint (daily, during automation):**
- Verify pages created in this session have 2+ outbound wikilinks
- Verify new pages are in index.md
- Check log.md size (rotate if >500 entries)

**Full lint (weekly, or on request):**

Run these checks programmatically where possible:

1. **Orphan pages:** Wiki pages with no inbound `[[wikilinks]]` from other wiki pages
2. **Broken wikilinks:** `[[links]]` pointing to pages that don't exist
3. **Index completeness:** Every wiki page should appear in index.md
4. **Frontmatter validation:** Required fields present (title, created, updated, type, tags, sources). Tags in taxonomy.
5. **Stale content:** Pages whose `updated` date is >90 days older than the most recent source mentioning the same entities
6. **Contradictions:** Pages sharing tags/entities but stating different facts
7. **Page size:** Flag pages over 200 lines as split candidates
8. **Tag audit:** List tags in use, flag any not in SCHEMA.md taxonomy
9. **Source coverage:** Papers in `papers/` that have never been ingested (no wiki page references them)

**Report:** Group findings by severity (broken links > orphans > stale > style). Include specific file paths and suggested actions. Append summary to log.md.

---

## Bulk Ingest (Cold Start)

When the wiki is first activated with existing vault content:

1. Do NOT try to ingest everything at once
2. Scan `papers/` — identify the 5-10 most substantial or frequently-referenced papers
3. Read those papers, create initial entity and concept pages
4. Build the initial tag taxonomy from existing paper frontmatter tags
5. Let the researcher review the initial pages and schema
6. Subsequent ingestion is incremental — each new session picks up where the last left off

See `references/trust-activation.md` for the full cold-start procedure.

---

## Obsidian Integration

The wiki directory works as part of the Obsidian vault out of the box:
- `[[wikilinks]]` render as clickable links in Obsidian
- Graph View shows the knowledge network (filter to `path:wiki/` for wiki-only view)
- YAML frontmatter powers Dataview queries
- Researcher can browse, correct, and annotate wiki pages directly in Obsidian

Useful Dataview queries for wiki pages:
```
TABLE tags, updated, length(sources) as "Sources"
FROM "wiki/entities"
SORT updated DESC
```

```
TABLE type, tags
FROM "wiki"
WHERE contains(tags, "sensemaking")
```

---

## Pitfalls

- **Never modify files in papers/ or transcripts/** — sources are immutable
- **Always orient before writing** — read SCHEMA + index + recent log. Skipping causes duplicates.
- **Always update index.md and log.md** — these are the navigational backbone
- **Don't create pages for passing mentions** — follow Page Thresholds
- **Don't create pages without cross-references** — every page links to 2+ others
- **Frontmatter is required** — enables search, filtering, staleness detection
- **Tags must come from taxonomy** — add new tags to SCHEMA.md first
- **Include reasoning in log entries** — the next Claude instance needs to follow precedent
- **Ask before mass-updating** — if an ingest would touch 10+ existing pages, confirm scope (interactive mode) or note in brief (automation mode)
- **Handle contradictions explicitly** — note both claims with dates, mark in frontmatter, flag for review
