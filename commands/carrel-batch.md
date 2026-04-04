---
description: Batch convert or transcribe a folder of files and file them to your vault
---

# /carrel-batch — Batch Processing

Process a folder of files sequentially — convert documents, transcribe audio, and file everything to the right vault folders.

## When to Use

- Researcher says "process all these files", "batch convert my inbox", "convert everything in this folder"
- Returning from a conference with a pile of PDFs and recordings
- Clearing out an inbox folder of mixed file types

## What Happens

### Step 1: Enumerate

Look for files to process. Default folder is `inbox/` inside the vault; accepts any path.

Recognized types:
- **Documents** → `carrel paper convert`: `.pdf`, `.docx`, `.doc`, `.pptx`, `.xlsx`
- **Audio/video** → `carrel transcript create`: `.m4a`, `.mp3`, `.wav`, `.mp4`, `.webm`
- **YouTube URL lists** → `carrel transcript create --tool youtube_captions`: `.txt` files containing YouTube URLs (one per line)

Anything else: note it in the summary, skip it.

### Step 2: Route

Before starting, confirm routing with the researcher:

"Found N files in `inbox/`:
- 12 PDFs → liteparse (local)
- 3 Word docs → markitdown
- 4 audio files → coli (local)
- 1 txt file with 2 YouTube URLs → youtube_captions

Any files you want handled differently? (e.g., use mineru for the complex PDFs, mark anything sensitive)

Ready to start?"

If a file looks like it may need special handling — scanned PDF, encrypted file, very large audio — flag it now rather than after failure.

### Step 3: Process sequentially

Run one file at a time. Do not parallelize.

For each file:
```
carrel paper convert <file>           # documents
carrel transcript create <file>       # audio/video
carrel transcript create <url>        # YouTube URL
```

After each file completes, note the result (converted, skipped, failed) before moving to the next.

**Idempotency**: The filer checks SHA-256 against existing vault files. Already-converted files return `action="skipped"` — no re-processing, no duplicates.

**Speed**: liteparse takes ~30s per PDF. 40 PDFs ≈ 20 minutes. Tell the researcher upfront if it's a long queue.

### Step 4: Flag judgment calls inline

Don't silently fail. If something needs a decision, pause and ask:

- Scanned/image-only PDF → "This looks scanned — want me to retry with mineru (cloud OCR)?"
- Transcription quality looks poor → "The coli output for `interview-3.m4a` looks garbled. Want to retry with groq?"
- Sensitive-looking filename (e.g., `patient-interview.m4a`) → "This filename suggests sensitive content. Confirm local-only processing?"
- YouTube URL file with mixed valid/invalid URLs → "2 of 4 URLs failed. Want me to show which ones?"

For non-blocking issues, batch the questions at the end rather than interrupting constantly. For blocking issues (ambiguous routing, suspected sensitive content), stop and ask immediately.

### Step 5: File to vault

After each successful conversion, the CLI files to the standard locations:
- Documents → `papers/<author-year>/paper.md`
- Transcripts → `transcripts/<kind>/`

If frontmatter is sparse (no author/year detectable), the CLI will use a fallback slug. Mention any files that landed in fallback locations so the researcher can rename them.

### Step 6: Summary

When the queue is done:

"Batch complete:
- **Converted**: 14 files
- **Skipped**: 3 (already in vault)
- **Failed**: 1 — `scan-ocr.pdf` (image-only, retry with --tool mineru?)
- **Need input**: 1 — `unnamed-audio.m4a` (what kind: interview/meeting/lecture?)

Everything is in your vault. Want me to open any of the new files?"

## Notes

- ~30s per PDF is normal — liteparse is local and thorough
- For purely cloud-dependent tools (mineru, groq), check network before starting a large batch
- If the researcher wants to abort mid-batch, existing completed files are already filed and safe

## Headless Mode (Unattended)

When the prompt contains "You are running in UNATTENDED mode" (set by the overnight automation agent), this command adapts:

**Skip Step 2 (routing confirmation)** — process all recognized files immediately with default routing. No "Ready to start?" prompt.

**Skip inline questions (Step 4)** — instead of pausing for judgment calls, write them to `_meta/pending-decisions.md`:

```markdown
- [ ] **YYYY-MM-DD inbox**: `filename` — reason this needs human input
```

Defer rather than block on: scanned PDFs that need OCR, sensitive-looking filenames, poor transcription quality, ambiguous file types.

**Continue processing** everything else. Idempotency (SHA-256 filer check) still applies — already-converted files are skipped silently.

**Step 6 summary** becomes the morning brief: counts of converted/skipped/failed plus a link to `_meta/pending-decisions.md` if any items were deferred.

The automation skill (`skills/automation/SKILL.md`) has the full contract for what the overnight agent schedules, what counts as "safe to process", and how to format the morning brief.

## Related

- **Skills**: `convert`, `transcribe` (judgment on routing, sensitivity, quality), `automation` (unattended scheduling and morning brief)
- **CLI**: `carrel paper convert`, `carrel transcript create`
- **Commands**: `/carrel-convert` (single file), `/carrel-transcribe` (single recording)
