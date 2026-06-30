# Ingestion

Use runtime commands for deterministic writes.

## Web Capture

```bash
python scripts/carrel.py capture url <url> --vault <vault>
```

The runtime tries optional capture adapters when available. Agents may pass
`--content` and `--title` when they have already extracted clean text.

## Document Conversion

```bash
python scripts/carrel.py convert file <path> --vault <vault>
```

For PDFs, prefer local `liteparse` when available. For non-PDFs, prefer
`markitdown` when available. Cloud `mineru` is optional and follows the routing
policy.

For folder sweeps:

```bash
python scripts/carrel.py batch convert <folder> --vault <vault> --unattended --format json
```

Unattended failures are written as pending decisions instead of deleting or
overwriting sources.

## Google Export

```bash
python scripts/carrel.py google export <docs.google.com URL> --vault <vault>
```

The runtime validates Google Docs, Sheets, and Slides URLs and exports through
optional `gws` when it is installed and authenticated. Agents may pass
`--content` when another connector already fetched the document body. High
sensitivity still blocks cloud conversion tools after export.

## Transcription

```bash
python scripts/carrel.py transcript create <source> --vault <vault>
```

For local media, prefer `coli`. For YouTube URLs, prefer existing captions when
available. Cloud adapters are optional and policy-gated.

For folder sweeps:

```bash
python scripts/carrel.py batch transcribe <folder> --vault <vault> --unattended --kind interview --format json
```
