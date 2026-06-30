# Reflection And Feedback

Use this workflow for end-of-session reflection, friction capture, feedback
digest generation, and research mirror synthesis.

## Session Reflection

Keep reflection under two minutes. Ask one to three questions, depending on
what the researcher already volunteered:

- What was useful today?
- What was frustrating or did not work?
- What did you wish you could do?

Map answers into a dated reflection with sections for what was worked on, what
went well, what was frustrating, ideas for next time, and open questions.

Persist the final reflection with:

```bash
printf '%s\n' "<reflection body>" | python3 scripts/carrel.py reflection append --vault <vault>
```

## Friction Log

If the researcher reports a concrete tool or workflow problem, also append a
compact entry to `_meta/friction_log.md` with issue, context, workaround, and
status. Do not duplicate the full reflection text.

## Feedback Digest

When the researcher wants to share experience feedback, build a redaction list
first. Include names, institutions, project names, and revealing filenames.
Keep tool names, command names, workflow descriptions, and error messages.

The redaction list can contain one term per line or `original -> replacement`
mappings. Then run:

```bash
python3 scripts/carrel.py feedback export --vault <vault> --redact-list <path>
```

Preview the digest path and leave sharing to the researcher.

## Research Mirror

Use mirror mode when the researcher asks for a self-portrait, research pattern
summary, semester review, monthly review, or "what have I been working on?"

Read:

- `_meta/reflections/`
- latest `_meta/mirror/`, if any
- `_meta/capability-log.md`
- `_meta/friction_log.md`
- high-level vault stats from papers, notes, drafts, and threads

Synthesize through five lenses:

- reading: topics, fields, authors, gaps, shifts;
- creating: notes, canvases, trackers, drafts;
- recurring themes: terms and questions that keep appearing;
- friction: repeated workflow or conceptual blockers;
- trajectory: where the work appears to be moving.

Lead with synthesis, not counts. If evidence is sparse, say so. In interactive
mode, ask whether the portrait matches the researcher's own view before saving.

Persist only approved or scheduled mirror prose:

```bash
printf '%s\n' "<mirror synthesis>" | python3 scripts/carrel.py mirror write --vault <vault>
```
