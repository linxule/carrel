---
name: knowledge-wiki
description: "This skill should be used when a researcher wants to build, query, or maintain a synthesized knowledge base across their sources. Triggers on 'field map', 'knowledge map', 'what do my sources say about', 'synthesize across papers', 'literature review', 'systematic review', 'wiki', 'track contradictions', 'knowledge base', 'I keep losing track', 'lint wiki', 'wiki health', or when the agent observes repeated cross-source questions in a vault with 15+ papers."
---

# knowledge-wiki

Maintain a persistent, compounding knowledge base as interlinked markdown pages inside the researcher's vault. Based on [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), adapted for carrel's vault structure and trust model. Upstream reference: [Hermes Agent implementation](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md).

Unlike traditional RAG (which rediscovers knowledge per query), the wiki compiles knowledge once and keeps it current. Cross-references already exist. Contradictions have already been flagged. Synthesis reflects everything ingested.

**Division of labor:** The researcher curates sources and directs analysis. The agent summarizes, cross-references, files, and maintains consistency.

## When to Use

**Active wiki exists** (wiki/ folder with SCHEMA.md):
- Researcher asks a question about their domain → query operation
- Researcher adds new source material → ingest operation
- Researcher asks about wiki health or consistency → lint operation
- Running in overnight automation with `wiki_maintenance` enabled

**No wiki yet — consider proposing** (see `references/trust-activation.md`):
- Researcher has 15+ papers and asks cross-source questions
- Researcher re-asks questions they've asked before (knowledge slipping)
- Researcher explicitly asks for a "knowledge base", "field map", "literature review", or "wiki"
- Trust level is consultative or higher
- Agent observes repeated cross-source questions in a vault with 15+ papers

**Do NOT activate:**
- Researcher has fewer than 15 sources and hasn't asked
- Trust level is advisory and researcher hasn't explicitly requested
- Researcher has expressed preference for managing their own synthesis (`wiki_preference: "researcher-managed"` in environment.json)

## Trust-Gated Behavior

The wiki follows carrel's graduated trust model. The same `trust_level` in `automation.trust_level` governs wiki behavior:

| Trust | Wiki behavior | Agent writes to wiki/ |
|-------|--------------|----------------------|
| **Advisory** | No wiki. Research-partner suggests themes. | Never |
| **Consultative** | Agent proposes wiki, drafts SCHEMA.md, creates pages WITH approval. | Only after researcher approves each batch |
| **Delegated** | Agent maintains wiki autonomously for new sources. Logs every action with reasoning. | Yes — new pages, updates, index maintenance |
| **Partnership** | Agent reorganizes structure, splits/merges pages, identifies research gaps. | Yes — including structural changes |

**Explicit opt-in overrides trust gating.** If a researcher says "set up a knowledge wiki" at any trust level, proceed. Their request IS the trust grant for wiki operations.

## Vault Integration — Folder Mapping

The wiki lives INSIDE the carrel vault. Carrel's existing folders ARE the raw source layer — no separate `raw/` tree:

```
vault/
├── papers/          ← Source layer (immutable, created by carrel paper convert)
├── transcripts/     ← Source layer (immutable, created by carrel transcript create)
├── notes/           ← Researcher's own notes (NOT wiki-managed)
├── inbox/           ← Unsorted incoming (processed by automation)
├── wiki/            ← Synthesis layer (agent-maintained)
│   ├── SCHEMA.md    ← Conventions, domain, tag taxonomy
│   ├── index.md     ← Sectioned content catalog
│   ├── log.md       ← Chronological action log with reasoning
│   ├── entities/    ← People, organizations, models, tools
│   ├── concepts/    ← Topics, theories, methods, debates
│   ├── comparisons/ ← Side-by-side analyses
│   └── queries/     ← Filed query results worth keeping
├── drafts/          ← Researcher's writing (reads from wiki, not managed by it)
└── _meta/           ← Briefs, suggestions, automation state
```

**Critical distinctions:**
- `papers/` and `transcripts/` = source material. The wiki READS these. Never writes to them.
- `notes/` = researcher's own thinking. Separate from wiki pages. The researcher may link to wiki pages from their notes, but wiki never overwrites notes.
- `wiki/` = agent-maintained synthesis. The agent owns these files. The researcher reviews and corrects.
- `drafts/` = researcher's writing. May reference wiki pages but is never wiki-managed.

## Source Ingestion Pipeline

When new sources arrive, the conversion pipeline feeds the wiki:

| Source type | Carrel command | Lands in | Wiki reads from |
|-------------|---------------|----------|-----------------|
| PDF paper | `carrel paper convert` | `papers/<author-year>/paper.md` | `papers/` |
| Audio/video | `carrel transcript create` | `transcripts/<name>.md` | `transcripts/` |
| Web page | `carrel capture url` | `papers/<slug>.md` or `inbox/` | `papers/` or `inbox/` |
| Google Doc | `carrel google export` | `papers/` or `notes/` | wherever it lands |

The wiki skill does NOT run conversion — that's the convert/transcribe/web-capture skills. The wiki reads already-converted markdown.

## Two Operating Modes

### Read mode (query)
Lightweight. For answering questions about the researcher's domain.

1. Read `wiki/index.md` to find relevant pages
2. For large wikis (50+ pages), also search across `wiki/**/*.md` for key terms
3. Read relevant wiki pages
4. Synthesize answer, citing wiki pages: "Based on [[wiki/concepts/sensemaking]] and [[wiki/entities/weick]]..."
5. If the answer is a substantial synthesis worth keeping → file to `wiki/queries/` or `wiki/comparisons/`, update index.md, and append to log.md

**Logging:** Only log queries that result in a filed wiki page. Trivial lookups do NOT require logging — this keeps read mode lightweight.

**Context cost:** index.md + 2-5 relevant pages. No full orientation needed. Only load log.md if filing a query result.

### Write mode (ingest, lint)
Full orientation required before writing.

1. Read `wiki/SCHEMA.md` — conventions, domain, tag taxonomy
2. Read `wiki/index.md` — what pages exist
3. Read last 30 lines of `wiki/log.md` — recent activity and reasoning
4. Then proceed with ingest or lint operations (see `references/wiki-protocol.md`)

**Context cost:** schema + index + recent log + source material + relevant existing pages. Budget for this.

## Context Management

**Session-start:** Do NOT auto-load the wiki. The session-start hook surfaces a one-liner:
`Wiki: 47 pages, last updated 2026-04-07, 1 contradiction pending review`

**On-demand:** Full orientation only when the researcher asks a wiki question or when running in automation mode.

**Large wikis (100+ pages):** Read index.md to identify the relevant SECTION, then search within wiki/ for specific terms. Don't read the entire index into context.

## Automation Integration

When `wiki_maintenance` is enabled in `environment.json → automation`:

The overnight prompt includes wiki operations AFTER inbox processing (so newly converted papers are available):

1. Orient: read SCHEMA.md, index.md, recent log.md
2. Scan `papers/` and `transcripts/` for files newer than last wiki log entry
3. For each new source: run ingest protocol (see `references/wiki-protocol.md`)
4. Quick lint: verify new pages have 2+ outbound links, index is current
5. Add wiki status to morning brief:
   - Pages: N total (+N new, +N updated)
   - Contradictions: N pending review
   - Orphans: N (if any)
6. Full lint: run weekly (check log.md for last full lint date)

## Log Format — Reasoning for Handoff

Because each Claude session is stateless, log.md entries include WHY, not just WHAT. This lets the next Claude instance follow precedent:

```markdown
## [2026-04-07] ingest | Smith & Jones 2025
- Created: entities/organizational-ambidexterity.md
  (split from 'organizational-adaptation' — 3 sources define it differently, warrants own page)
- Updated: concepts/sensemaking.md
  (added crisis subsection rather than separate page — only 1 source so far, below page threshold)
- Updated: entities/weick.md (added new publication reference)
- Cross-linked: [[organizational-ambidexterity]] ↔ [[dynamic-capabilities]]
- Index updated: +1 entity, 2 entities updated
```

One line of reasoning per non-trivial decision. This is how consistency is maintained across ephemeral agent instances.

## Researcher-Facing Language

Call it a "field map" in conversation, not a "knowledge wiki":

> "I could maintain a field map for you — topic pages that synthesize what your sources say, track key researchers and concepts, and flag where sources disagree. You'd review what I write. Think of it as a living summary of your field that gets smarter with every paper you add."

Use "wiki" only in technical contexts (file paths, skill name, protocol references).

## Related

- **Protocol**: `references/wiki-protocol.md` — full ingest/query/lint operations, templates, conventions
- **Trust**: `references/trust-activation.md` — graduation signals, proposal script, cold-start procedure
- **Skills**: `vault-ops` for note templates and vault hygiene; `automation` for overnight scheduling; `convert`/`transcribe`/`web-capture` for source conversion
- **Upstream**: [Karpathy's gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), [Hermes Agent skill](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
