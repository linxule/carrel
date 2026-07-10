# Automation

Use this workflow for unattended maintenance, scheduling discussions, morning
briefs, pending decisions, or automation preference reviews. The skill owns the
interview and judgment; the portable runtime persists settings and generates
deterministic files only when explicitly commanded; the host owns scheduling.

## Profile and Configure

Automation preferences live under `automation` in
`.carrel/environment.json`. Schedules are `daily`, `weekdays`, or `weekly`;
review cadence is `monthly`, `quarterly`, or `biannual`.

The portable runtime accepts explicit boolean values:

```bash
python3 scripts/carrel.py automation configure --vault <vault> \
  --enabled true --trust-level consultative --model sonnet \
  --schedule daily --review-cadence quarterly \
  --inbox-processing true --vault-health true --cross-linking true \
  --gap-analysis false --draft-feedback false \
  --reflection-synthesis true --wiki-maintenance false
```

Configure updates only the profile and `last_reviewed`. It must not create
pending files or `_meta/automation-prompt.md`.

Generate the prompt separately:

```bash
python3 scripts/carrel.py vault automation-prompt --vault <vault>
```

Use `--force` to replace an existing prompt. No `.prev` backup is automatic.
The prompt locates the vault through `.carrel/environment.json`; it never embeds
an absolute vault path.

## Trust

- Advisory: suggestions only.
- Consultative: exact proposals; no unattended execution.
- Delegated *(experimental)*: file new items and log each action/revert.
- Partnership *(experimental)*: may reorganize existing content within the
  agreed epistemology; log every action/revert.

Check the specific action immediately before it. A failed check stops the
write. First-time trust escalation requires the researcher's explicit choice;
do not infer it from an automation setup request. After that choice, configure
may perform exactly one bootstrap transition from Advisory to Consultative in
the same validated profile write. Direct jumps from Advisory to Delegated or
Partnership are rejected.

## Unattended Rules

- Never ask questions or wait for input.
- Create/append `_meta/pending-decisions.md` only when an actual item is
  deferred for ambiguity, sensitivity, OCR, quality, or cloud consent.
- Create/append `_meta/pending-approvals.md` only when an actual Consultative
  proposal exists.
- Continue safe independent items after a defer.
- Use `batch convert|transcribe --unattended` only in unattended runs.
- At Delegated/Partnership trust, log every action and a usable revert.
- Finish with `_meta/briefs/YYYY-MM-DD.md`.

## Morning Brief

Include inbox outcomes, vault health, high-confidence suggestions, active-plan
next steps, and pending-item counts only when they exist. Include Actions Taken
only at Delegated or Partnership trust.

When field-map maintenance is enabled, add counts for new/updated pages, low
confidence, contested pages, contradiction links, single-source confidence
gaps, source drift, orphans, and un-ingested sources, plus one synthesis
insight. Autonomous field-map writes require Delegated trust and `wiki:write`;
an approved Consultative batch uses `wiki:apply-approved`.

## Scheduling

After configuration and explicit prompt generation, schedule through the
current host interface. In Claude Cowork, use `/schedule` or the Scheduled page.
General tasks can run remotely, but a task that needs a local Carrel vault must
have the folder connected and Claude Desktop available when local access is
required. Carrel does not modify the host's saved schedule.

`claude -p` plus a system scheduler is an advanced, credential-dependent
fallback. Do not quote fixed dollar estimates: Cowork uses paid-plan allocation,
while programmatic/API usage depends on the configured account and model.
