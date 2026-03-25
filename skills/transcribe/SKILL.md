---
name: transcribe
description: "This skill should be used when a researcher has audio or video files to transcribe. Triggers on 'transcribe', 'convert this recording', 'audio to text', or when an audio file is provided (mp3, wav, m4a, mp4, webm)."
---

# transcribe

Audio and video transcription pipeline: process recordings into markdown text with metadata, save to the vault's transcripts folder.

## When to Use

- Researcher provides an audio or video file
- Researcher says "transcribe this", "convert this recording"
- File extensions: mp3, wav, m4a, ogg, flac, mp4, webm, mov

## Transcription Flow

### Step 1: Check the file
Confirm the file exists and note its format and approximate size.

### Step 2: Check sensitivity
Read CLAUDE.md for sensitivity level.
- For research interviews (high sensitivity): confirm local processing
- markdownify-mcp processes audio locally — safe for sensitive data

### Step 3: Transcribe
Use markdownify-mcp's `audio-to-markdown` tool:

```
audio-to-markdown({
  filePath: "/path/to/recording.mp3"
})
```

If ffmpeg is not installed and needed, offer to install it:
"I need a tool called ffmpeg to process this audio format. I can install it now — it takes about a minute."

### Step 4: Add metadata frontmatter

```yaml
---
title: [descriptive name or ask researcher]
date: [recording date if known]
duration: [if available]
participants: [ask researcher — use codes for research interviews]
project: [if applicable]
source_file: [original filename]
transcribed: [today's date]
transcriber: markdownify
---
```

For research interviews, suggest participant codes:
"For research ethics, I'll use participant codes instead of names. P001 for the first participant?"

### Step 5: Save to vault
Save to `transcripts/` with descriptive filename:
- Research interviews: `P001-interview-2026-03-26.md`
- Meetings: `meeting-project-name-2026-03-26.md`
- Lectures: `lecture-topic-2026-03-26.md`

### Step 6: Offer follow-up
"The transcript is saved. Would you like me to:
- Summarize the key points?
- Extract action items?
- Add speaker labels if they're missing?
- Connect it to related notes in your vault?"

## Quality Notes

- AI transcription has errors — suggest the researcher review important transcripts
- Speaker diarization may be limited — offer to help add labels manually
- Mark unclear passages with [unclear] or [inaudible]
- Include timestamps for key passages when available

## Related

- **MCP**: markdownify (`audio-to-markdown` tool)
- **Skills**: `vault-ops` for file placement
- **Commands**: `/carrel-transcribe` triggers this skill
