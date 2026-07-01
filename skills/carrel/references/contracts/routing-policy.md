# Routing Policy

Carrel defaults to local processing. Cloud tools are optional and must be
selected only when policy allows.

## Sensitivity Levels

- `high`: block cloud tools even when explicitly requested.
- `medium`: use local tools by default; require an explicit cloud tool request.
  Claude Code additionally pauses for human confirmation before the cloud call
  via a PreToolUse hook; hosts without that hook have no equivalent pause and
  should treat the explicit request as needing its own confirmation step.
- `low`: use local tools by default. Two distinct cases:
  - No tool explicitly requested and no local tool available: the router
    checks for a cloud tool when cloud consent is enabled, but the bundled
    stdlib runtime never actually reports a cloud tool as available (see Tool
    Classes) — this fallback only fires through a host adapter that adds real
    cloud tool detection, or via `policy explain --available-tools` for
    diagnostics.
  - A specific local tool explicitly requested and unavailable: the runtime
    does not cascade to checking cloud alternatives at all, even with consent
    enabled — it reports "not available" immediately. This is narrower than
    the full plugin's cascading sensitivity matrix.

## Tool Classes

- Convert local: `liteparse`, `markdownify`
- Convert cloud: `mineru`, `mistral_ocr`
- Capture local: `defuddle`, `markitdown`
- Transcribe local: `coli`
- Transcribe cloud: `groq`, `gemini`

Use `python3 scripts/carrel.py policy explain ...` to make the deterministic
selection visible before a write.

`paddleocr` is tracked as a candidate local OCR adapter, but current runtimes do
not accept it as a `--tool` value.
