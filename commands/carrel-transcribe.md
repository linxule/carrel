---
description: Transcribe an audio recording and save the transcript to your vault
---

# /carrel-transcribe — Audio Transcription

Transcribe audio files to markdown text and save to the transcripts folder.

## When to Use

- Researcher has an audio file to transcribe
- Researcher says "transcribe this", "convert this recording"
- Audio file from interviews, meetings, lectures

## What Happens

Uses the `transcribe` skill:

1. Run `carrel transcript create <file> [--kind interview|meeting|lecture]`
2. The CLI routes to the right tool (coli local, groq cloud, gemini for YouTube)
3. After transcription, clean up the output (fix typos, format speaker labels, mark [unclear])
4. Offer: summarize key points, extract action items, or connect to vault notes

## Notes

- Default tool is coli (local, works on all Macs including Intel)
- For sensitive recordings, the default is local — no data leaves the machine
- For YouTube URLs, use `carrel transcript create <url> --tool gemini`
- For research interviews: suggest `--kind interview` and participant codes (P001, P002)

## Related

- **Skill**: `transcribe`
- **CLI**: `carrel transcript create`, `carrel transcript list`
