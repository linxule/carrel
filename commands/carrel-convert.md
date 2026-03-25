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

1. Detect file type
2. Check sensitivity level (from CLAUDE.md)
3. Convert using markdownify-mcp (or mineru-mcp for complex PDFs)
4. Add YAML frontmatter (title, authors, year, tags, source info)
5. Save to appropriate vault folder (papers/, notes/, etc.)
6. Confirm with researcher

## Examples

**Single paper:**
> "Convert this PDF and save it to my papers folder"
→ Converts, adds frontmatter, saves to papers/author-year-title.md

**Web article:**
> "Save this article to my vault: https://example.com/article"
→ Fetches, converts, saves to inbox/

**Batch:**
> "Convert all the PDFs in my Downloads folder"
→ Processes each, reports results

## Related

- **Skill**: `convert` (full conversion logic and tool selection)
- **MCP**: markdownify (bundled), mineru (optional for complex PDFs)
