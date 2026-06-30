# Routing Policy

Carrel defaults to local processing. Cloud tools are optional and must be
selected only when policy allows.

## Sensitivity Levels

- `high`: block cloud tools even when explicitly requested.
- `medium`: use local tools by default; require an explicit cloud tool request.
- `low`: use local tools by default; allow cloud fallback when cloud consent is
  enabled.

## Tool Classes

- Convert local: `liteparse`, `markdownify`
- Convert cloud: `mineru`
- Capture local: `defuddle`, `markitdown`
- Transcribe local: `coli`, `youtube_captions`
- Transcribe cloud: `groq`, `gemini`

Use `python3 scripts/carrel.py policy explain ...` to make the deterministic
selection visible before a write.
