# Optional Adapters

Carrel's portable runtime is stdlib-first. External adapters are optional.

## Local Tool Adapters

- `liteparse`: PDF conversion through the `lit` executable.
- `markdownify`: non-PDF conversion and web fallback through the `markitdown`
  executable.
- `defuddle`: web article extraction.
- `coli`: local audio transcription.
- `gws`: Google Workspace export.

## Tracked Candidates

- `paddleocr`: evaluated local OCR/layout candidate for scanned or
  layout-heavy PDFs. Current Carrel runtimes do not accept `--tool paddleocr`.
  Do not make it a default or bundled dependency without a separate
  install/runtime decision; it is heavier than liteparse and may download models
  unless preseeded.

## Network Tool Adapters

- YouTube caption fetches: retrieve transcript metadata from YouTube by video
  ID. Treat this as network access, not local processing; high sensitivity
  blocks it.

## Cloud Tool Adapters

- `MINERU_API_KEY`: cloud PDF conversion.
- `MISTRAL_API_KEY`: cloud OCR for scanned or layout-heavy PDFs through
  Mistral OCR.
- `GROQ_API_KEY`: cloud audio transcription.
- `GEMINI_API_KEY`: cloud transcription and video understanding. YouTube URL
  transcription sends the URL to Google; it is not just local caption retrieval.

Cloud adapters must follow the routing policy. High sensitivity blocks cloud
processing even if credentials are present. The bundled stdlib runtime reports
cloud credentials in `env doctor`, but normal tool selection only auto-selects
local executable adapters. Provider API execution belongs in a host adapter
unless a bounded local command wrapper is added here deliberately.

## Host Adapters

Host adapters may add slash commands, lifecycle hooks, or generated memory
files. They must call or preserve the portable runtime contracts rather than
making host-specific files canonical.
