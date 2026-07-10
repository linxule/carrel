---
name: automation
description: "This skill should be used when a researcher wants to configure, understand, or adjust unattended vault maintenance. Triggers on 'schedule', 'automate', 'overnight', 'background processing', 'morning brief', 'unattended', 'what did Carrel do', 'review automation settings', 'trust level', or '/carrel-automate'."
---

# automation

Configure and explain unattended vault maintenance. Keep the separation clear: the skill conducts the interview and applies judgment; runtimes validate and persist settings; Cowork or another host owns scheduling.

Read `references/cowork-scheduling-guide.md` before giving scheduling instructions. Read `references/overnight-prompt-guide.md` when customizing the generated prompt contract.

## Feature Filter

Accept capabilities that amplify researcher judgment, expose patterns, or automate mechanical work within agreed boundaries. Do not automate away intellectual decisions. Draft feedback and gap analysis default off; reflection synthesis defaults on.

## Automation Profile

Preferences live under `automation` in `.carrel/environment.json`:

```json
{
  "enabled": false,
  "inbox_processing": true,
  "vault_health": true,
  "cross_linking_suggestions": true,
  "gap_analysis": false,
  "draft_feedback": false,
  "reflection_synthesis": true,
  "wiki_maintenance": false,
  "trust_level": "advisory",
  "model": "sonnet",
  "schedule": "daily",
  "review_cadence": "quarterly",
  "last_reviewed": null
}
```

Schedules are `daily`, `weekdays`, or `weekly`; review cadence is `monthly`, `quarterly`, or `biannual`. Update the vault's behavioral guidance and `_meta/my-environment.md` after profile changes.

## Graduated Trust

| Level | Unattended behavior |
|-------|---------------------|
| Advisory | Write suggestions only; never change research content. |
| Consultative | Write exact proposals to `_meta/pending-approvals.md`; never execute them unattended. |
| Delegated *(experimental)* | File new items within conventions; do not reorganize existing files. Log each action and a concrete revert. |
| Partnership *(experimental)* | May reorganize existing content within the agreed epistemology. Log every action and revert guidance. |

Explain every intermediate level before raising trust. After the researcher explicitly confirms Consultative, invoke configure once with `--trust-level consultative`; both runtimes permit exactly that Advisory-to-Consultative bootstrap and persist the approved configuration in one validated write. A direct Advisory-to-Delegated or Advisory-to-Partnership jump is rejected. Never treat a request to configure unrelated settings as permission to raise trust.

Run an action-specific trust check immediately before a guarded operation. Examples:

```bash
carrel trust check automation:propose --vault .
carrel trust check automation:execute --vault .
carrel trust check vault:reorganize --vault .
```

Stop on a failed check and explain the required level.

## Unattended Contract

An unattended agent must:

- never ask a question or wait for input;
- defer ambiguous type, cloud-consent, sensitivity, OCR, or transcription-quality decisions;
- create/append `_meta/pending-decisions.md` only when a real item is deferred;
- create/append `_meta/pending-approvals.md` only when a real consultative proposal exists;
- continue safe independent items after a defer;
- log every delegated/partnership action with a path and usable revert;
- stop after writing the morning brief.

Use `--unattended` only in scheduled batch invocations. Interactive batches retain confirmations and inline questions.

## Prompt Lifecycle

Automation configure commands persist only the profile and set `last_reviewed`; they do not create prompt or pending files. Generate the prompt as a separate explicit step:

```bash
carrel vault automation-prompt --vault .
```

Pass `--force` to replace an existing prompt. No command creates an automatic `.prev` backup. The generated prompt must locate the vault via `.carrel/environment.json`, not embed an absolute path.
Prompt generation enforces `automation:write-prompt`, a Consultative action,
so an Advisory profile must first complete an explicitly approved automation
configuration step.

## Configuration Interview

For a first setup, cover naturally:

1. Capabilities to enable. Offer wiki maintenance only when a field map exists.
2. Trust level and experimental status of Delegated/Partnership.
3. Sonnet or Opus preference.
4. Daily, weekdays, or weekly schedule.
5. Monthly, quarterly, or biannual review cadence.
6. Local-vault access requirements for the chosen scheduler.

For a returning researcher, summarize current values and change only requested fields. If a field map was activated since the last review, offer wiki maintenance without enabling it automatically.

## Calling Patterns

This is the Claude Code plugin skill; its runtime is the typed `carrel` CLI, which uses boolean switch pairs. Do not pass `true` or `false` after these flags:

```bash
carrel automate configure --enabled --trust-level consultative \
  --model sonnet --schedule daily --review-cadence quarterly \
  --inbox-processing --vault-health --cross-linking \
  --no-gap-analysis --no-draft-feedback --reflection-synthesis \
  --no-wiki-maintenance --vault .
```

On hosts without this plugin, the portable pack's runtime takes explicit boolean values instead; see `skills/carrel/references/workflows/automation.md`.

After configure succeeds, generate the prompt separately, review it, then guide the researcher through Cowork `/schedule` or the Scheduled page. A local-vault task needs the connected folder and Desktop availability when it runs. The host's saved schedule is not modified by Carrel profile changes.

Do not quote fixed dollar estimates. Cowork scheduled tasks use the paid plan's allocation; programmatic/API usage depends on the selected authentication and provider account.

## Morning Brief

Write `_meta/briefs/YYYY-MM-DD.md` with:

- inbox processed/skipped/failed/deferred counts;
- vault health counts, broken links, orphans, and stale drafts;
- high-confidence suggestions only;
- active-plan next steps;
- actions and reverts only for Delegated/Partnership;
- field-map counts when enabled: new/updated pages, low-confidence, contested, contradictions, missing single-source confidence, source drift, orphans, and un-ingested sources;
- one substantive synthesis insight, not only counts.

Advisory and Consultative briefs omit “Actions Taken.” A brief may link to pending files only when those files/items actually exist.

## Suggestion Confidence

- High: shared citation and concept, with substantial notes; include in brief.
- Medium: shared citation or concept; keep in suggestions only.
- Low: loose thematic similarity; keep in suggestions only.

## Wiki Maintenance

Unattended field-map writes require Delegated trust and `wiki:write`. Consultative approval obtained in an earlier interactive session is applied through `wiki:apply-approved`, not converted into general autonomous authority. Follow the `knowledge-wiki` skill for provenance, source digests, quality signals, and lint counts.

## Related

- `/carrel-automate` triggers this skill.
- `convert` and `transcribe` own interactive batch judgment.
- `knowledge-wiki` owns field-map write semantics.
- `references/cowork-scheduling-guide.md` contains current Cowork and `claude -p` setup.
- `references/overnight-prompt-guide.md` contains prompt assembly and trust blocks.
