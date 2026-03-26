---
description: Convert a PDF, Word, or other document to markdown and add it to your vault
---

# /carrel-convert — Document Conversion

Convert files to markdown and save them to the appropriate vault folder with proper frontmatter.

## When to Use

- Researcher drops a file or gives a file path
- Researcher says "convert this", "import this paper", "add this to my vault"
- Any PDF, DOCX, PPTX, XLSX, or image needs conversion

## What Happens

Uses the `convert` skill:

1. Run `carrel paper convert <file> [--tool mineru] [--force] [--dry-run]`
2. The CLI picks the right tool (liteparse for PDFs, markitdown for everything else)
3. Adds YAML frontmatter (title, authors, year, tags, source info)
4. Files to `papers/<author-year>/paper.md` with folder-per-paper structure
5. Assess quality, offer re-conversion with `--tool mineru` if needed

## Examples

**Single paper:**
> "Convert this PDF and save it to my papers folder"
> Runs `carrel paper convert paper.pdf`, saves to `papers/corley-gioia-2004/paper.md`

**Complex PDF with tables:**
> "This has a lot of tables, use the cloud converter"
> Runs `carrel paper convert paper.pdf --tool mineru`

**Batch:**
> "Convert all the PDFs in my Downloads folder"
> Processes each with `carrel paper convert`, reports results

## Related

- **Skill**: `convert` (judgment calls — when to use which flags)
- **CLI**: `carrel paper convert`, `carrel paper list`
