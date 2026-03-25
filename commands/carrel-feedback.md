---
description: Generate an anonymized feedback digest from your reflections to share with the plugin maintainer
---

# /carrel-feedback — Export Feedback

Generate an anonymized summary of reflections and friction log entries for sharing.

## When to Use

- Researcher wants to share feedback with Xule
- Periodic digest for plugin improvement
- Researcher says "generate feedback", "share my experience"

## What Happens

1. Read all files in `_meta/reflections/`
2. Read `_meta/friction_log.md`
3. Generate anonymized digest:
   - Remove names, specific research content, file paths
   - Keep: patterns, pain points, feature requests, what worked well
   - Structure as: highlights, issues, suggestions
4. Present to researcher for review before sharing
5. Save to `_meta/feedback-digest-YYYY-MM-DD.md`
6. Tell researcher: "Copy the contents and email to xule.lin@imperial.ac.uk, or share via LinkedIn."

## Anonymization Rules

- Replace researcher name with "Researcher"
- Replace institution with "University"
- Replace specific research topics with "[research topic]"
- Replace file names with generic descriptions
- Keep tool names, error messages, and workflow descriptions (these are useful)

## Related

- **Commands**: `/carrel-reflect` (generates the reflections this reads)
