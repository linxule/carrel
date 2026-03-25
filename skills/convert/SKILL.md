---
name: convert
description: "This skill should be used when a researcher needs to convert a PDF, Word document, PowerPoint, spreadsheet, or image to markdown. Triggers on 'convert', 'import', 'add this paper', drops a file, or mentions PDF/DOCX/PPTX/XLSX conversion."
---

# convert

Document conversion pipeline: detect file type, choose the right tool, convert to markdown, add YAML frontmatter, and save to the appropriate vault folder.

## When to Use

- Researcher drops a file or gives a file path
- Researcher says "convert", "import", "add this paper to my vault"
- Any PDF, DOCX, PPTX, XLSX, or image file needs to become markdown

## Tool Selection

### markdownify-mcp (default — always available)

The bundled MCP. Handles most formats locally:

| Format | Tool | Notes |
|--------|------|-------|
| PDF | `pdf-to-markdown` | Good for text-based PDFs |
| DOCX | `docx-to-markdown` | Preserves structure well |
| PPTX | `pptx-to-markdown` | Extracts slide content |
| XLSX | `xlsx-to-markdown` | Converts to markdown tables |
| Image | `image-to-markdown` | OCR + metadata |
| Web URL | `webpage-to-markdown` | Strips navigation/ads |
| YouTube | `youtube-to-markdown` | Transcript if available |

### mineru-mcp (optional — for complex PDFs)

Use when markdownify produces poor results on PDFs with:
- Complex tables with merged cells or multi-column layouts
- Scanned documents needing high-accuracy OCR
- Mathematical formulas
- Dense figures/charts that need extraction

Check if available: read `.carrel/environment.json` → `tools_configured.mineru`

```
mineru_parse({
  url: "file:///path/to/paper.pdf",
  model: "vlm"    // 90%+ accuracy for complex layouts
})
```

**Sensitivity warning**: MineRU API sends the document to a cloud service. If the researcher's sensitivity is "high" or "local_only" (check CLAUDE.md), warn before using:
"This PDF has complex tables. My local converter might not handle them well. I can use a more accurate cloud service, but it means sending the document to an external server. Would you prefer that, or should I try the local conversion first?"

## Conversion Flow

### Step 1: Detect format
Read the file extension or ask the researcher what kind of file it is.

### Step 2: Check sensitivity
Read CLAUDE.md or `.carrel/environment.json` for sensitivity level.
- `local_only` or `high`: Use markdownify only. Warn before mineru.
- `prefer_local`: Try markdownify first. Offer mineru if results are poor.
- `comfortable_with_cloud`: Use best tool for the job.

### Step 3: Convert
Call the appropriate markdownify tool or mineru tool.

### Step 4: Add frontmatter
For papers, add YAML frontmatter:

```yaml
---
title: [extracted or ask researcher]
authors: [extracted or ask researcher]
year: [extracted or ask researcher]
journal: [extracted or ask researcher]
doi: [if found]
source_file: [original filename]
converted: [today's date]
converter: markdownify|mineru
tags: []
status: unread
---
```

For other documents, add minimal frontmatter:
```yaml
---
title: [filename or extracted]
source_file: [original filename]
converted: [today's date]
tags: []
---
```

### Step 5: Save to vault
- Papers → `papers/`
- Slides/presentations → `talks/` or `papers/` depending on context
- Spreadsheets → `notes/` or context-dependent
- Other → `inbox/` (let researcher organize later)

Name the file descriptively: `author-year-short-title.md` for papers, `filename.md` for others.

### Step 6: Confirm
Tell the researcher what was converted and where it was saved:
"I've converted your PDF to markdown and saved it as `papers/corley-gioia-2004-identity-construction.md`. The tables came through well. Want me to create a summary or highlight key sections?"

## Quality Check

After conversion, quickly scan the output for:
- Garbled text (OCR errors)
- Missing or broken tables
- Lost formatting (headers, lists)
- Missing figures (note where they were)

If quality is poor, offer alternatives:
- "The tables didn't convert well. Want me to try the cloud converter for better accuracy?"
- "Some text looks garbled — this might be a scanned PDF. Let me try a different approach."

## Batch Conversion

If the researcher has multiple files:
1. List all files to convert
2. Process each one
3. Report results: "Converted 5 papers. 4 came through cleanly. One had table issues — I'll flag it."

## Related

- **MCP**: markdownify (bundled), mineru (optional)
- **Skills**: `vault-ops` for file placement and frontmatter conventions
- **Commands**: `/carrel-convert` triggers this skill
