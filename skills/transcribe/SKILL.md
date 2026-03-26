---
name: transcribe
description: "This skill should be used when a researcher has audio or video files to transcribe, or a YouTube URL to get a transcript from. Triggers on 'transcribe', 'convert this recording', 'audio to text', 'get the transcript', or when an audio/video file or YouTube URL is provided."
---

# transcribe

The `carrel` CLI handles all mechanical transcription work. This skill focuses on the human judgment AI brings: when to ask questions, which flags to suggest, and what to do with the output.

## When to Use

- Researcher provides an audio or video file (mp3, wav, m4a, ogg, flac, mp4, webm, mov)
- Researcher provides a YouTube URL
- Researcher says "transcribe this", "convert this recording", "get the transcript"

## Primary Command

```bash
carrel transcript create <source> [--vault PATH] [--tool coli|groq|gemini] \
  [--kind recording|interview|meeting|lecture] [--speakers N] \
  [--sensitivity high|medium|low] [--force] [--dry-run]
```

The CLI handles tool routing, filing (`transcripts/<kind>-<name>-<date>.md`), and idempotency. Don't re-implement those.

## Judgment Calls Before Running

### Tool selection

- **YouTube URL** → always suggest `--tool gemini`. If researcher has no Gemini key, the CLI will give a clear error — don't try workarounds.
- **Local audio, sensitive data** → default to `coli` (local). Warn before suggesting `--tool groq`: "This will send audio to Groq's servers — is that okay given the sensitivity?"
- **Local audio, non-sensitive, slow hardware** → `--tool groq` is faster and cheaper than waiting on a slow local model.
- **Default** → omit `--tool` and let the CLI decide (coli for local audio).

Speaker diarization is available via `local-stt-mcp` (transport layer, optional) — if the researcher needs clean speaker labels and has it configured, mention it as an option.

### Kind selection

Ask or infer `--kind` before running — it affects the filing name and downstream usefulness:
- One-on-one with a participant → `interview`
- Team or project discussion → `meeting`
- Talk or course recording → `lecture`
- Field recording, ambient, personal note → `recording` (default)

### Pre-transcription questions for interviews

Before running on a research interview, ask:
- "Should I use participant codes instead of names? (e.g., P001)"
- "How many speakers? (helps with `--speakers N`)"
- "Is this sensitive data? (affects whether cloud tools are appropriate)"

Skip these questions for meetings, lectures, or recordings unless the researcher raises them.

## After Transcription: Cleanup

The raw transcript from the CLI will have STT errors. This is where AI adds value — review and clean it up:

1. Fix obvious typos and garbled words
2. Add punctuation and paragraph breaks where missing
3. Format speaker labels consistently (e.g., `**P001:**` not `P001 :`)
4. Mark unclear passages as `[unclear]` or `[inaudible]`
5. Add timestamps at major topic transitions if the recording had them

Edit the file in place. Note what you changed (e.g., "cleaned punctuation, standardized speaker labels, marked 3 unclear passages").

## Quality Notes to Offer

- Suggest researcher review any transcript that will be quoted or published
- Note if audio quality was poor — errors will be higher
- Gemini transcription for YouTube uses audio+visual together — quality is typically good
- Long recordings (>1h) may have drift toward the end; suggest spot-checking

## Follow-up Offers

After saving and cleaning:
"The transcript is saved. Would you like me to:
- Summarize the key points?
- Extract action items or decisions?
- Connect it to related notes in your vault?"

## Related

- **Skills**: `vault-ops` for file placement questions
- **Commands**: `carrel transcript list` to review what's been transcribed
