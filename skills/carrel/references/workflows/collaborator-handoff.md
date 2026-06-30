# Collaborator Handoff

Use this workflow when a researcher wants to share a Carrel vault with a
co-author, assistant, student, lab member, advisor, or reviewer. The handoff is
vault-specific; do not write a generic Carrel tutorial.

## Source Order

Read available sources in this order and degrade gracefully when they are
missing:

1. `.carrel/environment.json`
2. `.carrel/agent-context.md`
3. `_meta/friction_log.md` and `_meta/friction-log/`
4. `_meta/capability-log.md`
5. recent `_meta/reflections/`
6. latest `_meta/mirror/`
7. active `notes/threads/`
8. `wiki/SCHEMA.md` and `wiki/index.md` when field map is active
9. vault folder structure and `_meta/my-environment.md`

## Modes

Use `quick` mode when the researcher asks for a draft or starter handbook.
Assume a general collaborator and save the dated file.

Use `full` mode when they name a collaborator, describe a role, or need a
polished handoff. Ask one brief exchange:

- Who is joining?
- What should they do in this vault?
- What should they not see or touch?

After synthesis, show the draft and ask one refinement question. Save the final
only after the researcher approves it.

## Synthesis Questions

The handbook should answer:

- What does this researcher study and do?
- What rules and habits must the collaborator respect?
- What is currently active in the vault?
- What should the collaborator do first?

Use patterns and entry points, not raw counts. If a source is empty, say so
briefly instead of inventing material.

## Sensitivity

Default to the vault `sensitivity`. Override only when the collaborator's
access is narrower than the vault-wide policy and the researcher confirms it.

- High: use project-level descriptions, omit unpublished titles, transcript
  filenames, participant identifiers, and sensitive active-thread details.
- Medium: include ordinary file lists, but redact explicitly sensitive or
  private project markers.
- Low: include normal vault-specific detail unless the researcher asks for
  redactions.

When the collaborator role is unclear, choose the more restrictive sensitivity
and say what assumption you made.

## Persistence

For agent-synthesized prose, pipe the approved handbook to:

```bash
python3 scripts/carrel.py share generate --vault <vault> --for "Name" --sensitivity medium --mode full --from-stdin
```

Use `--canonical` only when the researcher explicitly wants the same content
also saved as `_meta/lab-handbook.md`.

The dated snapshot remains the audit trail. Refresh when a new collaborator
joins, sensitivity changes, automation or field-map behavior changes, or the
shared handbook becomes stale.

## Anti-Patterns

- Do not make a general tool manual.
- Do not pretend to know an unnamed collaborator.
- Do not accumulate indefinitely in one handbook.
- Do not expose source filenames or project details that conflict with the
  selected sensitivity level.
