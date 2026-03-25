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

1. Detect audio format
2. Check sensitivity (warn if cloud processing needed for sensitive recordings)
3. Transcribe using markdownify-mcp's `audio-to-markdown` tool
4. Add metadata frontmatter (date, duration, participants if known)
5. Save to `transcripts/`
6. Offer: summarize key points, extract action items, or add speaker labels

## Notes

- markdownify handles audio transcription locally
- For best results: high-quality recordings, clear speech
- Speaker diarization may be limited — researcher can add labels manually
- For research interviews: suggest adding participant codes (P001, P002) not real names

## Related

- **Skill**: `transcribe`
- **MCP**: markdownify (`audio-to-markdown` tool)
