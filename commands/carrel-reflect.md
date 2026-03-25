---
description: Quick end-of-session reflection — what worked, what didn't, what to improve
---

# /carrel-reflect — Session Reflection

A brief conversational check-in at the end of a work session. Captures what worked, what was frustrating, and ideas for improvement.

## When to Use

- End of a work session
- Researcher says "let's reflect", "wrap up", "what did we do today"
- SessionEnd hook prompts reflection

## What Happens

1. Ask 2-3 quick questions (NOT a survey — a conversation):
   - "What was most useful about today's session?"
   - "Was there anything frustrating or that didn't work well?"
   - "Anything you wished you could do but couldn't?"

2. Log answers as a timestamped note in `_meta/reflections/`:
   - Filename: `reflection-YYYY-MM-DD.md`
   - Uses the reflection template from `_templates/reflection.md`

3. If the researcher reported issues, update `_meta/friction_log.md`:
   - Add dated entry with issue, context, workaround, status

4. Thank them: "This helps improve the tool for everyone. See you next time!"

## Guidelines

- Keep it under 2 minutes
- Don't force it — if they want to leave, let them
- Don't ask all questions if the first answer covers everything
- Be genuine, not formulaic

## Related

- **Hooks**: `session-reflect.js` (SessionEnd) prompts this automatically
- **Commands**: `/carrel-feedback` generates exportable digest from reflections
