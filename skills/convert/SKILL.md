---
name: convert
description: "This skill should be used when a researcher wants to convert a PDF, Word document, PowerPoint, spreadsheet, or image to markdown. Triggers on 'convert', 'import', 'add this paper', a dropped file path, or any mention of PDF/DOCX/PPTX/XLSX conversion."
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

When the researcher points at a folder ("process my inbox", "convert everything in `~/Drop`"), shift into batch mode. The folder walk + per-file dispatch lives in the CLI; this skill owns the confirmation step and the routing summary.

### Pre-batch confirmation

Before the batch fires, enumerate what's there and report routing back to the researcher. Default folder is `inbox/` inside the vault; any path is accepted.

Recognized document types: `.pdf`, `.docx`, `.doc`, `.pptx`, `.xlsx`. Anything else: note it in the summary, skip it.

Show a short report and ask before starting:

> Found 16 files in `inbox/`:
> - 12 PDFs → liteparse (local)
> - 3 Word docs → markitdown
> - 1 unsupported (`notes.numbers`) — will skip
>
> Any files you want handled differently? (e.g., use mineru for the complex PDFs, mark anything sensitive)
>
> Ready to start?

If a file looks like it may need special handling — scanned PDF, encrypted file, very large doc — flag it now rather than after failure. Tell the researcher upfront if the queue is long: liteparse takes ~30s per PDF, so 40 PDFs ≈ 20 minutes.

### Calling pattern

Once the researcher confirms, hand off to the CLI:

```bash
carrel batch convert <folder> [--vault PATH]
```

The CLI walks the folder, dispatches per file, and respects idempotency (SHA-256 source-hash; already-converted files return `action="skipped"`).

### During the batch

Flag judgment calls inline rather than silently failing:
- Scanned/image-only PDF → "This looks scanned — want me to retry with mineru (cloud OCR)?"
- Sensitive-looking filename (e.g., `patient-records.pdf`) → "This filename suggests sensitive content. Confirm local-only processing?"
- Repeated tool failures → stop and ask, don't keep retrying

Batch non-blocking questions at the end. Stop and ask immediately for blocking ones (ambiguous routing, suspected sensitive content).

### Post-batch summary

When the queue is done, give a single readable summary:

> Batch complete:
> - **Converted**: 14 files
> - **Skipped**: 3 (already in vault)
> - **Failed**: 1 — `scan-ocr.pdf` (image-only, retry with `--tool mineru`?)
> - **Need input**: 1 — see questions above
>
> Everything is in your vault. Want me to open any of the new files?

Mention any files that landed in fallback filing slots (sparse frontmatter, no author/year) so the researcher can rename them.

### Unattended-mode batches

If the batch is scheduled (running without the researcher present), the contract is different: skip the confirmation, defer judgment calls to `_meta/pending-decisions.md`, never block. That contract lives in the `automation` skill — invoke it via `carrel batch convert <folder> --unattended` from a scheduled prompt, not from interactive use.

### Aborting mid-batch

If the researcher wants to stop mid-batch, files already processed are filed and safe — the CLI commits per-file. Resume by re-running the command; idempotency skips what's already done.

## CRITICAL: Papers Are Not Notes

A converted paper is raw paper content with YAML frontmatter — nothing else. Never apply a note template to a converted paper. If the researcher wants to write notes *about* a paper, that is a separate file in `notes/` created with the note-taking skill.

## Follow-Up Offers

After a successful conversion, offer:
- "Want me to create reading notes for this paper?"
- "Should I check if any papers already in your vault cite this one?"

## Related

- `carrel paper list` — see what's already converted
- **Skills**: `vault-ops` for file conventions and note creation
