# Optional Adapters

Carrel's portable runtime is stdlib-first. External adapters are optional.

## Setup Plan Rules

During onboarding or repair, present optional tools as capability choices, not
installation blockers.

- State the research use case first: scanned PDFs, local transcription, Google
  export, web cleanup, or model-teammate review.
- Check sensitivity and cloud consent before naming cloud routes.
- Keep volatile install click-paths, marketplace steps, and host-specific
  command names in adapter docs or upstream source links.
- Store durable choices in `.carrel/environment.json` under
  `tools_configured`, `preferences`, or `model_teammates`.
- Re-run `env doctor` after a local install and summarize only what changed.

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

- YouTube caption fetches: retrieving a transcript from YouTube by video id is
  network access, not local processing. The bundled stdlib runtime does **not**
  implement it — it only recognizes YouTube URLs to slug the artifact by video
  id. Caption/audio fetching belongs to the typed CLI or a host adapter; the
  portable runtime files the supplied transcript via `--content`. High
  sensitivity blocks any such network fetch.

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

Model teammate installation is adapter-specific. Portable Carrel should only
record which teammates are available, what they are trusted to review, and what
sensitivity levels block their use.
