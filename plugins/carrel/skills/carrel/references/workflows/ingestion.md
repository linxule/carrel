# Ingestion

Use runtime commands for deterministic writes.

## Contents

- Batch Protocol
- Web Capture
- Document Conversion
- Google Export
- Transcription

## Batch Protocol

For interactive batch conversion or transcription, do not start with the
runtime sweep. First inventory the folder:

- count supported and unsupported file types;
- identify likely PDFs, scans, media, Google exports, and web captures;
- flag anything that may be high sensitivity;
- say which local tools are available from `env doctor`;
- summarize the proposed route and ask before processing.

Stop before cloud processing when sensitivity is high or uncertain. Explicit
tool requests count as consent only when sensitivity is low or medium; high
sensitivity still blocks cloud tools.

Claude Code hosts get an additional human-visible pause at medium sensitivity
via the `sensitivity-gate` PreToolUse hook, even when a tool request already
counts as policy consent. Hosts without that hook have no equivalent pause —
in those hosts, treat an explicit medium-sensitivity cloud request as needing
its own confirmation step from the researcher before running it.

Show a short report before starting, e.g.:

> Found 16 files in `inbox/`: 12 PDFs → liteparse (local), 3 Word docs →
> markitdown, 1 unsupported (skipped). Ready to start?

Use `--dry-run` to preview a batch and `--force` only when the researcher
explicitly wants an existing artifact replaced. If a run aborts, resume by
rerunning the same command without force; idempotent source hashes skip already
converted items. Unattended runs should write blocked items to
`_meta/pending-decisions.md` instead of asking questions.

After a batch, give a matching summary: converted/transcribed, skipped
(already in vault), failed (with the reason and a retry suggestion, e.g. a
scanned PDF failing liteparse), and need-input counts, plus the destination
folder. Flag judgment calls inline during the batch rather than silently
failing — don't keep retrying the same failure.

Converted papers are not notes. Conversion creates source artifacts under
`papers/` or transcripts under `transcripts/`. Analytical notes, literature
threads, and field-map pages require a separate agent workflow.

## Web Capture

```bash
python3 scripts/carrel.py capture url <url> --vault <vault>
```

The runtime tries optional capture adapters when available. Agents may pass
`--content` and `--title` when they have already extracted clean text.

## Document Conversion

```bash
python3 scripts/carrel.py convert file <path> --vault <vault>
```

For PDFs, prefer local `liteparse` when available. For non-PDFs, prefer
`markitdown` when available. Cloud `mineru` and `mistral_ocr` are policy-gated
and require a host adapter; the bundled stdlib runtime does not call provider
PDF APIs directly. `paddleocr` is tracked as a possible future local OCR
adapter, but current runtimes do not accept `--tool paddleocr`.

### Quality Judgment

Recommend `--tool mineru`/`--tool mistral_ocr` (via a host adapter) when the
document has tables, figures, formulas, a scanned/image-based layout, or
multi-column journal structure — liteparse handles straightforward text-heavy
papers well, so don't suggest cloud OCR unprompted for those. After
conversion, scan for garbled text, broken tables, or lost section structure;
if quality is poor, offer re-conversion with a cloud tool before assuming the
source itself is unusable.

For folder sweeps:

```bash
python3 scripts/carrel.py batch convert <folder> --vault <vault> --unattended --format json
```

Unattended failures are written as pending decisions instead of deleting or
overwriting sources.

## Google Export

```bash
python3 scripts/carrel.py google export <docs.google.com URL> --vault <vault>
```

The runtime validates Google Docs, Sheets, and Slides URLs and exports through
optional `gws` when it is installed and authenticated. It defaults to
`--export-format txt` because text is portable without a conversion adapter.
Agents may pass `--content` when another connector already fetched the document
body. High sensitivity still blocks cloud export unless content is supplied
from a trusted local path.

## Transcription

```bash
python3 scripts/carrel.py transcript create <source> --vault <vault>
```

For local media, prefer `coli`. For YouTube URLs, use host/connector caption
access and pass the transcript with `--content`. Caption fetches are network
access and are blocked for high sensitivity. Cloud adapters are policy-gated
and require a host adapter; the bundled stdlib runtime files supplied
transcript text or calls local `coli`.

### Tool And Kind Selection

For local audio, default to `coli`. Warn before suggesting `--tool groq`
("this sends audio to Groq's servers") unless sensitivity is low; groq is
faster, but Carrel's current adapter returns plain transcript text without
word-level timestamps. For YouTube, try local captions first and only offer
`--tool gemini` (via a host adapter) if caption quality is poor. Pick
`--kind interview|meeting|lecture|recording` before running — it drives
filing and downstream usefulness; ask when it is not obvious from context.

For folder sweeps:

```bash
python3 scripts/carrel.py batch transcribe <folder> --vault <vault> --unattended --kind interview --format json
```
