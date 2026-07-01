# Setup And Repair

Use this workflow for deterministic vault scaffolding and profile repair. If
the researcher is new, preferences are incomplete, or setup requires an
interview, read `references/workflows/onboarding.md` first.

## Vault Setup

Use `vault init` to create a portable vault. The runtime creates the folder
layout, copies assets from `assets/templates/`, writes
`.carrel/environment.json`, and writes `.carrel/agent-context.md`.

After setup, run:

```bash
python3 scripts/carrel.py env doctor --vault <vault> --format json
python3 scripts/carrel.py env validate --vault <vault> --format json
```

## Guided Repair

If validation reports missing fields, unknown keys, invalid JSON, or schema
drift, use a guarded repair loop:

1. Run `env validate` and classify the issue in plain language.
2. Run `env fix --dry-run --format json` before making changes.
3. Explain what will be preserved, removed, defaulted, or moved into
   `_unknown_keys`. If the result includes `reset_invalid_fields` (any of
   `sensitivity`, `automation.trust_level`, `automation.model`,
   `automation.schedule`, `automation.review_cadence`, or a structurally
   invalid `automation` object entirely), tell the researcher which fields
   were reset to a safe default and why — `env fix` only repairs
   missing/unknown keys and these specific invalid enum values, not
   arbitrary malformed data.
4. Ask before applying when the repair changes meaningful researcher
   preferences or when ambiguity remains.
5. Run `env fix` only after approval or when the user explicitly asked for
   repair.
6. Run `env validate` again and report the final status.
7. Log meaningful repairs in `.carrel/agent-context.md` or `_meta/` when the
   repair affects future agent behavior.

Use:

```bash
python3 scripts/carrel.py env fix --vault <vault> --dry-run --format json
python3 scripts/carrel.py env fix --vault <vault>
```

Agents should update both the structured profile and the neutral context file
when the researcher's preferences materially change.

There is no separate `env fix --safe` command. The safe portable path is dry-run
preview, backup-preserving apply, revalidation, and a human-readable repair
explanation.
