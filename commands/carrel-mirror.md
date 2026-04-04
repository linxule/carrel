---
description: Synthesize your research patterns from reflections, capability log, and friction log
---

# /carrel-mirror — Research Self-Portrait

Reads your vault's metadata and synthesizes a portrait of your intellectual trajectory — what you've been reading, creating, and thinking about, and where you seem to be heading.

## When to Use

- Researcher says "show me my research patterns", "what have I been working on?", "give me a mirror"
- Periodic review (monthly, semester start/end)
- Feeling stuck or wanting to reconnect with the bigger picture
- Scheduled mode: automated monthly snapshot

## What Happens

1. Read `_meta/reflections/` — all entries, or only since the last mirror if one exists in `_meta/mirror/`
2. Read `_meta/capability-log.md` — what has been created
3. Read `_meta/friction_log.md` — what has frustrated
4. Read vault stats:
   - Papers: count by field and year
   - Notes: count by type (literature notes, concept notes, drafts)
   - Draft status (if tracked)
5. Synthesize into a portrait across five dimensions:
   - **Reading**: dominant topics, fields, key authors, any notable gaps or shifts
   - **Creating**: notes, canvases, custom trackers — volume and variety
   - **Recurring themes**: keywords and ideas that keep surfacing in reflections
   - **Friction patterns**: what consistently frustrates — tools, workflows, or concepts
   - **Trajectory**: shifting interests, emerging questions, where you seem to be headed

## Modes

**Interactive** (default): present the portrait conversationally, then discuss. Ask one follow-up question — "Does this match how you see your work right now?" — and let the conversation go where it needs to.

**Scheduled** (with `--write`): skip the conversation. Write the portrait to `_meta/mirror/YYYY-MM.md` using today's year and month. Confirm when saved.

## Output Format

Lead with the synthesis, not the data. Don't recite counts — draw the pattern.

"Here's what your vault says about your research right now:

**What you've been reading**: Mostly institutional theory and organizational ecology — heavy on DiMaggio, Powell, and Hannan. You've pulled in a lot of 2019–2023 work, with a gap in empirical pieces.

**What you've been building**: 14 literature notes this quarter, mostly concept-dense. Three canvases started; one abandoned. You haven't written a draft in six weeks.

**What keeps coming up**: 'boundary conditions' appears in 5 of your last 8 reflections. So does a sense that your framework isn't quite clicking yet.

**What frustrates you**: PDF conversion on scanned documents (flagged three times). Finding older sources you know you've read.

**Where you seem to be heading**: Your recent notes cluster around legitimacy and field-level change — looks like you're narrowing from 'institutions broadly' toward something more specific. The abandoned canvas was about market emergence, which you haven't returned to.

Does this match how you see your work right now?"

## Guidelines

- The value is in patterns, not counts. One sentence of synthesis beats five bullet points of numbers.
- If the metadata is sparse (new vault, few reflections), say so honestly: "There's not enough here yet for a full portrait — here's what I can see so far."
- Don't invent trajectory. If the data doesn't show a clear direction, say "the direction isn't clear yet."
- In interactive mode, let the researcher correct or extend the portrait. Update your reading if they push back.

## Related

- **Commands**: `/carrel-reflect` (captures session reflections that feed this command)
- **Commands**: `/carrel-feedback` (exports friction patterns for tool improvement)
- **Files**: `_meta/reflections/`, `_meta/capability-log.md`, `_meta/friction_log.md`, `_meta/mirror/`
