# Ingestion

Use runtime commands for deterministic writes.

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

Use `--dry-run` to preview a batch and `--force` only when the researcher
explicitly wants an existing artifact replaced. If a run aborts, resume by
rerunning the same command without force; idempotent source hashes skip already
converted items. Unattended runs should write blocked items to
`_meta/pending-decisions.md` instead of asking questions.

After a batch, report processed, skipped, failed, and pending-decision counts.
Name the destination folders and any files that need human review.

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

For folder sweeps:

```bash
python3 scripts/carrel.py batch transcribe <folder> --vault <vault> --unattended --kind interview --format json
```
