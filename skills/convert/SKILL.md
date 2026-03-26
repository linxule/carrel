---
name: convert
description: "Use when a researcher wants to convert a PDF, Word document, PowerPoint, spreadsheet, or image to markdown. Triggers on 'convert', 'import', 'add this paper', a dropped file path, or any mention of PDF/DOCX/PPTX/XLSX conversion."
---

# convert

The `carrel` CLI handles all mechanical conversion work. This skill provides the judgment layer: when to invoke which options, how to interpret results, and what to do next.

## When to Trigger

- Researcher drops a file path or says "convert", "import", "add this paper"
- Any PDF, DOCX, PPTX, XLSX, or image needs to become markdown in the vault

## Running a Conversion

```bash
carrel paper convert <file> [--vault PATH]
```

That's the default. The CLI picks the right tool automatically (liteparse for PDFs, markitdown for everything else) and handles frontmatter, filing, and idempotency.

## Judgment Calls

### When to suggest `--tool mineru`

Recommend mineru when the researcher describes or the filename suggests:
- Tables, figures, or formulas that need accurate extraction
- Scanned or image-based PDFs
- Multi-column journal layouts where structure matters

Say: "This looks like a complex PDF with tables. Want me to use the cloud converter for better accuracy? (`--tool mineru`)"

Do not suggest mineru unprompted for straightforward text-heavy papers — liteparse handles those well.

### When to warn about sensitivity

If the researcher has mentioned data sensitivity, IRB materials, unpublished manuscripts, or confidential content, note before running:
- `--tool mineru` sends the document to a cloud API — skip it for sensitive files
- The default (liteparse) is local and safe

### When to use `--force`

Use `--force` only when the researcher explicitly wants to re-convert something already in the vault, or when quality was poor on a previous run.

### Dry run

Offer `--dry-run` when the researcher is unsure what will happen or wants to preview before committing.

## Interpreting Results

**Success**: Tell the researcher where the file landed and give a one-line quality read:
"Converted to `papers/corley-gioia-2004/paper.md`. Tables came through cleanly."

**Skipped (already converted)**: Explain the idempotency behavior:
"This paper is already in your vault. Use `--force` if you want to re-convert it."

**Error**: The CLI error message includes a hint — relay it and offer a path forward.

## Quality Assessment

After conversion, scan the output for:
- Garbled text (OCR artifacts)
- Broken or missing tables
- Lost section structure

If quality is poor, offer re-conversion:
- "The tables didn't come through well — want to retry with `--tool mineru` for better accuracy?"
- "Looks like a scanned PDF. The cloud converter handles those better."

## Batch Workflow

For multiple files, run each with `carrel paper convert`, then summarize:
"Converted 5 papers. 4 came through cleanly. One had table issues — flagging `smith-2019` for re-conversion."

## CRITICAL: Papers Are Not Notes

A converted paper is raw paper content with YAML frontmatter — nothing else. Never apply a note template to a converted paper. If the researcher wants to write notes *about* a paper, that is a separate file in `notes/` created with the note-taking skill.

## Follow-Up Offers

After a successful conversion, offer:
- "Want me to create reading notes for this paper?"
- "Should I check if any papers already in your vault cite this one?"

## Related

- `carrel paper list` — see what's already converted
- **Skills**: `vault-ops` for file conventions, `reading-notes` for note creation
