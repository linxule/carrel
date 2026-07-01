# Automation

Use this workflow when a researcher wants unattended vault maintenance,
scheduled/background processing, a morning brief, or a change to automation
trust settings. The portable skill persists preferences and prompt files; the
host decides how to schedule the prompt.

## Contents

- Feature Filter
- Automation Contract
- Trust And Unattended Rules
- Prompt And Briefs
- Pending Decisions And Approvals
- Configuration Flow
- Cost Framing

## Feature Filter

Before enabling a capability, ask whether it amplifies the researcher's
judgment or replaces it.

- Accept mechanical work, visibility, and bounded delegation.
- Make intimate work opt-in: draft feedback and gap analysis default off.
- Keep reflection synthesis on by default because it summarizes researcher
  supplied reflections rather than acting on sources.
- Offer field-map maintenance only when `wiki_enabled` is true.

## Automation Contract

Automation preferences live in `.carrel/environment.json` under `automation`.
Supported toggles are `inbox_processing`, `vault_health`,
`cross_linking_suggestions`, `gap_analysis`, `draft_feedback`,
`reflection_synthesis`, and `wiki_maintenance`.

Schedules are `daily`, `weekdays`, or `weekly`. Review cadence is `monthly`,
`quarterly`, or `biannual`. The model field is host-facing preference metadata;
do not make one host's model names required portable behavior.

Persist resolved settings with:

```bash
python3 scripts/carrel.py automation configure --vault <vault> --enabled true --trust-level consultative --schedule daily --review-cadence quarterly
```

The runtime sets `last_reviewed`, preserves existing optional fields unless
overridden, and initializes pending files and `_meta/automation-prompt.md`
without overwriting existing files.

## Trust And Unattended Rules

Trust levels govern what automation may do:

- `advisory`: write suggestions only; no operational changes.
- `consultative`: write proposed actions to `_meta/pending-approvals.md`.
- `delegated`: file new routine items inside configured boundaries and log
  every action.
- `partnership`: allow broader reorganization only after explicit opt-in.

Unattended mode must never ask questions or wait for input. When judgment is
needed, write to `_meta/pending-decisions.md` and skip that item.

Defer rather than act on scanned PDFs needing cloud OCR, audio files with
unknown speaker/sensitivity context, ambiguous file types, or any cloud route
where consent is uncertain.

## Prompt And Briefs

The portable automation prompt must not hard-code an absolute vault path. It
should instruct the agent to find the vault root by locating
`.carrel/environment.json`, then read `.carrel/environment.json` and
`.carrel/agent-context.md`.

Morning briefs should be saved by the running agent under
`_meta/briefs/YYYY-MM-DD.md` when a host supports unattended writing. Include:

- Inbox: processed, failed, and pending-decision counts.
- Vault health: papers, notes, drafts, stale drafts, orphan notes, broken links.
- Suggestions: high-confidence cross-links or gaps only.
- Field map: page counts, contradictions, lint status, and one insight.
- Actions taken: only for delegated or partnership trust, with revert notes.

## Pending Decisions And Approvals

`_meta/pending-decisions.md` is for blocked items that require human input.
Use checklist rows with the date, source, and reason.

`_meta/pending-approvals.md` is for consultative proposed actions. Include
enough structure for an interactive agent to execute after approval, but do not
execute the item in the unattended run.

When the researcher resolves an item interactively, mark it checked and add a
short resolution note.

## Configuration Flow

For first-time automation setup, summarize current defaults, ask which
capabilities should run unattended, explain the selected trust level, choose a
schedule and review cadence, then run `automation configure`.

`automation configure` is itself gated on the vault's *current* trust level
(it requires at least consultative to run at all). On a fresh vault (default:
advisory), write the researcher-approved `trust_level` directly into
`.carrel/environment.json`'s `automation` object first — the same
direct-write mechanism used for every other profile field set during
onboarding — before running `automation configure`. The gate's real
protection is a human explicitly approving the escalation in this
conversation; that protection holds either way, only the write order
changes. The runtime does not enforce one-level-at-a-time jumps, so walk the
researcher through each intermediate level's implications yourself before
applying a multi-level jump.

For returning users, summarize current automation settings and ask what changed.
Update only requested fields.

After configuration, update `.carrel/agent-context.md` and `_meta/my-environment.md`
if those files exist. Do not generate host-specific scheduling files from this
portable workflow.

## Cost Framing

Give approximate cost only when the selected host charges for scheduled model
work. Frame estimates as dependent on vault size, enabled capabilities, model,
and schedule. Weekly runs are roughly one seventh of daily runs.
