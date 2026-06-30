# Optional Adapters

Carrel's portable runtime is stdlib-first. External adapters are optional.

## Local Tool Adapters

- `lit`: PDF conversion through liteparse.
- `markitdown`: non-PDF conversion and web fallback.
- `defuddle`: web article extraction.
- `coli`: local audio transcription.
- `gws`: Google Workspace export.

## Cloud Tool Adapters

- `MINERU_API_KEY`: cloud PDF conversion.
- `GROQ_API_KEY`: cloud audio transcription.
- `GEMINI_API_KEY`: cloud transcription.

Cloud adapters must follow the routing policy. High sensitivity blocks cloud
processing even if credentials are present. The bundled stdlib runtime reports
cloud credentials in `env doctor`, but normal tool selection only auto-selects
local executable adapters. Provider API execution belongs in a host adapter
unless a bounded local command wrapper is added here deliberately.

## Host Adapters

Host adapters may add slash commands, lifecycle hooks, or generated memory
files. They must call or preserve the portable runtime contracts rather than
making host-specific files canonical.
