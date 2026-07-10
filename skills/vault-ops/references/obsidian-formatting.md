# Obsidian Formatting Reference

<!-- Source: kepano/obsidian-skills/skills/obsidian-markdown @ a1dc48e68138490d522c04cbf5822214c6eb1202 (reviewed 2026-07-10) -->
<!-- Curated for Carrel research context -->
<!-- Review cadence: quarterly (next: 2026-10-10) -->

Research-relevant Obsidian syntax beyond basic markdown. Use these to make vault content more readable and navigable in Obsidian's GUI.

## Callouts

Block-level highlights. Use in reading notes, interview summaries, and paper annotations.

```markdown
> [!note] Optional Title
> Content inside the callout.

> [!quote] Gioia et al., 2013, p. 22
> "We offer what we believe is a systematic approach..."

> [!question] Follow-up
> How does this relate to the identity work literature?

> [!important]
> Key methodological insight worth returning to.

> [!example] Case: Hospital Merger
> Participants described identity threat through metaphors of loss.

> [!warning]
> Sensitivity: contains participant quotes. Do not share outside vault.
```

**Research callout types** (use these; skip decorative ones):

| Type | Use for |
|------|---------|
| `[!note]` | General annotations, marginalia |
| `[!quote]` | Direct quotes with attribution |
| `[!question]` | Open questions, things to follow up |
| `[!important]` | Key findings, critical insights |
| `[!example]` | Case illustrations, evidence |
| `[!warning]` | Sensitivity alerts, caveats |
| `[!summary]` | Section or paper summaries |
| `[!abstract]` | Paper abstracts |

Callouts are **foldable** — add `-` to collapse by default:

```markdown
> [!quote]- Full passage (click to expand)
> Long quote that would take too much space...
```

## Embeds

Pull content from other vault files inline. Critical for cross-referencing papers and notes.

```markdown
![[note-name]]                     Embed entire note
![[note-name#Heading]]             Embed specific section
![[note-name#^block-id]]           Embed specific paragraph
![[image.png]]                     Embed image (full width)
![[image.png|400]]                 Embed image (400px wide)
![[document.pdf#page=5]]           Embed PDF page
![[paper-tracker.base]]            Embed the default Obsidian Base view
![[paper-tracker.base#Needs Notes]] Embed a named Base view
```

Use embeds in reading notes to pull in key passages from converted papers:
```markdown
## Key Methodology
![[papers/corley-gioia-2004/paper#Data Collection]]
```

## Properties (YAML Frontmatter)

Obsidian reads YAML frontmatter as structured metadata. Bases and search use these.

```yaml
---
title: "Identity Construction in Organizational Change"
authors: [Corley, Gioia]
year: 2004
tags: [identity, organizational-change, qualitative]
status: noted
aliases: [Corley & Gioia 2004, corley-gioia]
cssclasses: [research-note]
---
```

**Key Obsidian-specific properties:**

| Property | Purpose |
|----------|---------|
| `tags` | Array of tags (also used by Bases filters) |
| `aliases` | Alternative names — makes wikilinks flexible (e.g., `[Corley & Gioia 2004]`) |

Tags can be inline too: `#identity` `#method/qualitative` (nested tags use `/`).

## Wikilinks

```markdown
[[note-name]]                      Basic link
[[note-name|display text]]         Link with custom display
[[note-name#Heading]]              Link to heading
[[note-name#^block-id]]            Link to specific block
[[papers/corley-gioia-2004/paper|Corley & Gioia (2004)]]   Link with citation display
```

When creating notes, actively link to related vault content. Obsidian's graph view and backlinks panel surface these connections.
