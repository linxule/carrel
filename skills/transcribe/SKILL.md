---
name: transcribe
description: "This skill should be used when a researcher has audio or video files to transcribe, or a YouTube URL to get a transcript from. Triggers on 'transcribe', 'convert this recording', 'audio to text', 'get the transcript', or when an audio/video file or YouTube URL is provided."
---

# transcribe

Transcription router: detects input type, picks the best tool based on hardware capability and sensitivity, converts to markdown, saves to vault.

## When to Use

- Researcher provides an audio or video file (mp3, wav, m4a, ogg, flac, mp4, webm, mov)
- Researcher provides a YouTube URL
- Researcher says "transcribe this", "convert this recording", "get the transcript"

## Tool Selection

Pick the right tool based on input type, hardware, and sensitivity:

### YouTube URLs → Gemini via vox (one-step)

If vox-mcp is configured with a Gemini key, pass the YouTube URL directly:

```
# Via vox chat tool — Gemini processes the video natively, no download needed
vox chat: "Transcribe this video with timestamps and speaker labels: https://www.youtube.com/watch?v=VIDEO_ID"
```

Gemini processes raw audio+video (not YouTube auto-captions). Works for videos up to ~1h at default quality, ~3h at low resolution. Public videos only.

If vox is not configured, fall back to markdownify's `youtube-to-markdown` (extracts captions only, lower quality).

### Audio files → route by hardware + sensitivity

Check `.carrel/environment.json` for hardware capability and sensitivity:

| Condition | Tool | Why |
|-----------|------|-----|
| Sensitive data + Apple Silicon 16GB+ | **mlx-whisper-mcp** (local) | Best quality, data stays on machine. |
| Sensitive data + any Mac (including older) | **coli** (local) | SenseVoice model works on all hardware including Intel Macs. |
| Capable hardware (Apple Silicon, 16GB+) | **mlx-whisper-mcp** (local) | Best quality, fast, free. |
| Older/weaker hardware, not sensitive | **Groq Whisper API** (cloud) | 299x real-time, cheapest cloud ($0.04/hr). |
| Nothing else available | **markdownify** audio-to-markdown | Always bundled. Basic quality. |

Check what's available:
- `mlx-whisper-mcp`: read `.mcp.json` or environment.json → `tools_configured.mlx_whisper`
- `coli`: check if `coli` command exists (`which coli`). Installed via `npm i -g @marswave/coli`
- `Groq`: needs `GROQ_API_KEY` — check environment.json
- `markdownify`: always available (bundled with plugin)

**coli usage** (local, works on all Macs):
```bash
coli asr recording.m4a                    # transcribe file
coli asr recording.m4a --json             # with language, emotion, timestamps
coli asr recording.m4a --model sensevoice # SenseVoice (default, multilingual)
coli asr recording.m4a --model whisper    # Whisper tiny.en (English only, lighter)
```
First run downloads the model (~155MB) to `~/.coli/models/`. Requires ffmpeg for non-WAV files.

**Sensitivity warning for cloud tools**: If sensitivity is "high" or "local_only", warn before using Groq or any cloud API:
"This recording contains sensitive data. I'll transcribe it locally on your machine so nothing is sent to external servers."

### Speaker diarization

If the researcher needs speaker labels (interviews, meetings with multiple participants):
- `local-stt-mcp` supports speaker diarization via pyannote (local, Apple Silicon)
- If not available, transcribe first, then offer to add speaker labels manually

## Transcription Flow

### Step 1: Detect input type
- YouTube URL → use Gemini/vox path
- Audio/video file → check file exists, note format and size
- If ffmpeg is not installed and needed: "I need a tool to process this audio format. I can install it now — takes about a minute." (`brew install ffmpeg`)

### Step 2: Select tool
Follow the routing table above. Check hardware audit results and sensitivity.

### Step 3: Transcribe
Call the selected tool. For long files (>30 min), let the researcher know it may take a moment.

### Step 4: Clean up the output
After raw transcription, review and improve before saving:
- Fix obvious typos and garbled words
- Add punctuation and paragraph breaks
- Format speaker labels consistently (if present)
- Mark unclear passages with [unclear] or [inaudible]
- Add timestamps at key transitions

This cleanup step is what makes the output useful — raw STT output is messy.

### Step 5: Add metadata frontmatter

```yaml
---
title: [descriptive name or ask researcher]
date: [recording date if known]
duration: [if available]
participants: [ask researcher — use codes for research interviews]
project: [if applicable]
source_file: [original filename or YouTube URL]
transcribed: [today's date]
transcriber: [mlx-whisper | groq | gemini | markdownify]
---
```

For research interviews, suggest participant codes:
"For research ethics, I'll use participant codes instead of names. P001 for the first participant?"

### Step 6: Save to vault
Save to `transcripts/` with descriptive filename:
- Research interviews: `P001-interview-2026-03-26.md`
- Meetings: `meeting-project-name-2026-03-26.md`
- Lectures: `lecture-topic-2026-03-26.md`
- YouTube: `author-or-channel-topic-2026-03-26.md`

### Step 7: Offer follow-up
"The transcript is saved. Would you like me to:
- Summarize the key points?
- Extract action items?
- Add speaker labels if they're missing?
- Connect it to related notes in your vault?"

## Quality Notes

- AI transcription has errors — suggest the researcher review important transcripts
- Gemini YouTube transcription is surprisingly good — uses both audio and visual cues
- Local models (mlx-whisper) are best for English; multilingual may need cloud
- For long interviews, consider transcribing in sections for better accuracy

## Related

- **MCPs**: markdownify (bundled fallback), mlx-whisper-mcp (local, optional), vox (Gemini YouTube)
- **Skills**: `vault-ops` for file placement
- **Commands**: `/carrel-transcribe` triggers this skill
