# Ingestion

Use runtime commands for deterministic writes.

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
PDF APIs directly. Treat `paddleocr` as an explicit local OCR candidate only
after the host has installed its Python/runtime dependencies.

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
