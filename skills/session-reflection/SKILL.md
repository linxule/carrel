---
name: session-reflection
description: "This skill should be used when a researcher wraps up a work session and wants a quick check-in on what worked and what didn't ('let's reflect', 'wrap up', 'what did we do today', '/carrel-reflect'), when the SessionEnd hook surfaces a reflection prompt, when issues from a session need to be captured to the friction log for later improvement, or when the researcher wants to share feedback with the plugin maintainer ('share my experience', 'generate feedback', '/carrel-feedback'). Distinct from research-partner (which engages with research content) — this skill is meta: reflection on the tool and workflow, not on the research itself."
---

# session-reflection

A brief conversational check-in at the end of a work session. Captures what was useful, what was frustrating, and what the researcher wished they could do but couldn't. The CLI handles atomic appends to the dated reflect-log; this skill provides the conversational frame and decides what (if anything) flows into the friction log.

## When to Use

- End of a work session, especially when natural pauses appear ("ok, I'm done for today")
- Researcher says "let's reflect", "wrap up", or "what did we do today"
- The SessionEnd hook (`session-reflect.js`) surfaces a reflection prompt
- Researcher reports a frustration mid-session that's worth capturing for the friction log even if they don't want to do a full reflection

## Calling pattern

```
carrel vault reflect-log --append --from-stdin
```

The skill conducts the conversation, then pipes the structured reflection content via stdin. The CLI handles atomic append to `_meta/reflections/reflection-YYYY-MM-DD.md` (creating the file from `_templates/reflection.md` on first write of the day) and writes inside `safe_path.safe_vault_join` so the operation can't escape the vault root.

Do not write to `_meta/reflections/` directly — the CLI is the boundary.

## Conversational shape

This is a conversation, not a survey. Two or three questions is the target — fewer if one answer covers everything.

Open with whichever feels most natural given the session:

- "What was most useful about today's session?"
- "Was there anything frustrating or that didn't work well?"
- "Anything you wished you could do but couldn't?"

Listen for what the answer hands you. If they lead with frustration, the "what worked" question may be redundant. If they're brief, don't probe — researchers who want to leave should be able to leave.

## What ends up where

The reflection content goes through the CLI to `_meta/reflections/reflection-YYYY-MM-DD.md`. Map the conversation into the reflection template's sections:

- **What I Worked On** — one or two sentences naming the session focus
- **What Went Well** — direct answer to the "most useful" question
- **What Was Frustrating** — direct answer to the "didn't work well" question; leave blank if nothing came up
- **Ideas for Next Time** — captures the "wished you could" question
- **Open Questions** — anything the researcher flagged as unresolved or worth returning to

If the researcher only answered one question, only that section gets filled. Empty sections are fine — the template is a scaffold, not a quota.

## Friction log handoff

If the researcher reported a concrete issue (something broke, something was unclear, a workflow had unnecessary friction), also append to `_meta/friction_log.md` with a dated entry:

```markdown
## YYYY-MM-DD
- **Issue**: [one-line description]
- **Context**: [what they were trying to do]
- **Workaround**: [what they did instead, or "none" if they gave up]
- **Status**: open
```

The friction log is what `/carrel-feedback` later anonymizes and digests for sharing with the plugin maintainer. Reflections capture sentiment; the friction log captures concrete improvement signal.

Don't double-log: if the issue is mentioned in the reflection, don't paste the same text into friction_log — just capture the structured version there.

## Guidelines

- **Keep it under 2 minutes.** Reflection has diminishing returns; the value is in the regular check-in, not the depth of any single one.
- **Don't force it.** If the researcher signals they want to leave, close out with thanks and let them go. A skipped reflection is fine; a coerced one is worse than nothing.
- **Don't ask all questions** if the first answer covers everything. One question with a real answer beats three with shrugs.
- **Be genuine, not formulaic.** No script openings. No "as we wrap up our session today" framing. Match the register the researcher has been using.
- **Close warmly.** Something like "Thanks — this helps the tool get better over time" lands better than a checklist confirmation.

## Hook tie-in

The SessionEnd hook (`hooks/session-reflect.js`) reads session stats and surfaces a reflection prompt non-blockingly. When the hook fires, this skill is the right responder — the hook surfaces, the skill engages. The hook does not call the CLI directly; it prompts, and if the researcher engages, the skill conducts the conversation and pipes to `carrel vault reflect-log`.

If the researcher routinely declines the hook prompt, the prompt's value drops — note this pattern but don't act on it from inside the skill (frequency tuning belongs in hook configuration, not skill judgment).

## Exporting a feedback digest

When the researcher wants to share their experience with the plugin maintainer ("generate feedback", "share my experience", `/carrel-feedback`), this skill builds the redact list from the same source files it writes to, then calls the CLI to produce the digest. The CLI applies the redactions and writes the dated file; the skill owns redact-list construction and the sharing handoff.

### Calling pattern

```
carrel vault feedback export --redact-list <path>
```

The CLI reads reflections plus the friction and capability logs, applies the redactions from the list, and writes `_meta/feedback-digest-YYYY-MM-DD.md`. The skill's job is upstream (build the list, then preview with the researcher) and downstream (tell them where to send it).

### Building the redact list

Before calling the CLI, scan the source files (`_meta/reflections/*.md`, `_meta/friction_log.md`) and `.carrel/environment.json` for identifying content. Write literal mappings with canonical ASCII `original -> replacement`, one rule per line. Bare terms mean `term -> [REDACTED]`; legacy Unicode `original → replacement` remains accepted. Comments and blank lines are ignored.

Always include:

- Researcher's name (from `environment.json` → `name`) -> `Researcher`
- Institution, when present at `environment.json` → `preferences.institution`, or detected in the source scan -> `University`
- Specific research topics or project names mentioned in reflections → `[research topic]`
- File names that reveal research content (e.g., `dimaggio-isomorphism-1983.pdf`) → generic descriptions like `[paper]`

Keep (do NOT redact):

- Tool names (`liteparse`, `mineru`, `defuddle`, `coli`, etc.)
- Error messages verbatim
- Workflow descriptions and friction patterns
- Carrel command names

The CLI applies literal case-insensitive rules longest-first and adds the profile `name -> Researcher` fail-safe when no explicit name rule exists. The skill still owns the sensitive-term scan and meaningful replacement choices. After export, review `redactions_applied` and `zero_match_terms`; a zero-match rule may indicate a typo or stale identifier.

If the redact list was created as a temporary file, remove it after the digest has been generated and reviewed; it contains the identifiers the digest is designed not to expose.

### After the CLI writes

Show the researcher the digest path and offer a quick preview. Then surface the sharing options exactly once:

"The digest is at `_meta/feedback-digest-YYYY-MM-DD.md`. Copy the contents and email them to xule.lin@imperial.ac.uk, or share via LinkedIn."

Don't push. Sharing is the researcher's decision; the skill's contribution is making the digest easy to share if they want to.

### What the digest is for

The digest closes the outer loop: researcher friction → plugin maintainer → next release. Reflections capture sentiment in the researcher's own voice; the friction log captures concrete issues; the digest anonymizes both into something shareable. If a researcher has been reflecting regularly, the digest is the natural way to contribute back without writing a separate report.

## Related

- **CLI**: `carrel vault reflect-log --append --from-stdin` (atomic append to dated reflection file); `carrel vault feedback export --redact-list <path>` (anonymized digest from reflections + friction log)
- **Commands**: `/carrel-reflect` (thin wrapper for the reflection check-in); `/carrel-feedback` (thin wrapper for the digest export)
- **Hooks**: `session-reflect.js` (SessionEnd; non-blocking prompt that hands off to this skill)
- **Templates**: `_templates/reflection.md` (the per-day reflection scaffold the CLI writes into on first append)
- **Skills**: `self-improve` (the capability log is the dev-team feedback channel; the friction log is the researcher-experience feedback channel — distinct surfaces, both feed plugin evolution); `research-partner` (the `mirror` synthesis reads the same reflections + friction log to surface patterns back to the researcher)
