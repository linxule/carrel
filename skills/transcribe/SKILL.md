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
carrel transcript create <source> [--vault PATH] [--tool coli|groq|gemini|youtube_captions] \
  [--kind recording|interview|meeting|lecture] [--speakers N] \
  [--force] [--dry-run]
```

The CLI handles tool routing, filing (`transcripts/<kind>-<name>-<date>.md`), and idempotency. Don't re-implement those.

## Judgment Calls Before Running

### Tool selection

- **YouTube URL** → omit `--tool` and the CLI uses local captions (free, no API key, includes timestamps). Run with local captions first (the default). If the output quality is poor (garbled text, missing segments, wrong language), offer to re-run with `--tool gemini` for AI-processed transcription from the actual audio+video.
- **Local audio, sensitive data** → default to `coli` (local). Warn before suggesting `--tool groq`: "This will send audio to Groq's servers — is that okay given the sensitivity?"
- **Local audio, non-sensitive, slow hardware** → `--tool groq` is faster and gives word-level timestamps for better paragraph reconstruction.
- **Default** → omit `--tool` and let the CLI decide (coli for local audio, local captions for YouTube).

For speaker diarization, pass `--speakers N` when the number of speakers is known — coli uses this to improve speaker separation.

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

## Batch Workflow

When the researcher points at a folder of recordings ("transcribe everything from the conference", "process the interviews folder"), shift into batch mode. The folder walk + per-file dispatch lives in the CLI; this skill owns the pre-batch confirmation and the per-file routing summary.

### Pre-batch confirmation

Default folder is `inbox/` inside the vault; any path is accepted. Recognized inputs:

- **Audio/video files**: `.m4a`, `.mp3`, `.wav`, `.mp4`, `.webm`, `.mov`, `.ogg`, `.flac`
- **YouTube URL lists**: `.txt` files containing YouTube URLs (one per line)

Anything else: note it in the summary, skip it.

Show a short report and ask before starting:

> Found 6 items in `inbox/`:
> - 4 audio files → coli (local)
> - 1 video file → coli (local, will pull audio track)
> - 1 txt file with 2 YouTube URLs → youtube_captions
>
> Any files you want handled differently? (e.g., switch to groq for faster turnaround, flag anything sensitive, set `--kind interview` for the recordings)
>
> Ready to start?

Flag in advance anything that looks like it may need special handling — very large files, recordings whose filename suggests sensitive content (`patient-interview.m4a`), YouTube URL files with mixed valid/invalid URLs. coli runtime scales with audio length; tell the researcher upfront if it'll be a long queue.

If `--kind` isn't obvious from filenames, ask whether the whole folder is one kind (e.g., all interviews) or mixed. The CLI uses `--kind` for filing under `transcripts/<kind>/`.

### Calling pattern

Once the researcher confirms, hand off to the CLI:

```bash
carrel batch transcribe <folder> [--vault PATH] [--kind interview|meeting|lecture|recording]
```

The CLI walks the folder, dispatches per file, and respects idempotency (SHA-256 source-hash; already-transcribed files return `action="skipped"`).

### During the batch

Flag judgment calls inline rather than silently failing:
- Transcription quality looks poor → "The coli output for `interview-3.m4a` looks garbled. Want to retry with groq?"
- Sensitive-looking filename → "This filename suggests sensitive content. Confirm local-only processing?"
- YouTube URL file with mixed valid/invalid URLs → "2 of 4 URLs failed. Want me to show which ones?"

Batch non-blocking questions at the end. Stop and ask immediately for blocking ones (ambiguous routing, suspected sensitive content).

### Post-batch summary

When the queue is done, give a single readable summary:

> Batch complete:
> - **Transcribed**: 5 files
> - **Skipped**: 1 (already in vault)
> - **Failed**: 0
> - **Need input**: 1 — `unnamed-audio.m4a` (what kind: interview/meeting/lecture?)
>
> Everything is in `transcripts/`. Want me to clean up any of them now?

Cleanup (typo/punctuation/speaker-label pass) is per-file and interactive — the batch produces raw transcripts; this skill's "After Transcription: Cleanup" section applies once the researcher picks one to work on.

### Unattended-mode batches

If the batch is scheduled (running without the researcher present), the contract is different: skip the confirmation, defer judgment calls to `_meta/pending-decisions.md`, never block. That contract lives in the `automation` skill — invoke it via `carrel batch transcribe <folder> --unattended` from a scheduled prompt, not from interactive use.

### Aborting mid-batch

If the researcher wants to stop mid-batch, files already transcribed are filed and safe — the CLI commits per-file. Resume by re-running the command; idempotency skips what's already done.

## Related

- **Skills**: `vault-ops` for file placement questions
- **Commands**: `carrel transcript list` to review what's been transcribed
