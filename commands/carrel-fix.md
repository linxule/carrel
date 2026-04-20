---
description: Detect and resolve environment.json drift in your vault
---

# /carrel-fix — Environment Recovery

Checks `.carrel/environment.json` for drift, previews safe repairs, and escalates ambiguous cases into an interactive recovery flow.

## What Happens

1. Run `carrel env validate --vault . --format json`
2. If the file is already valid, report that and stop
3. Run `carrel env fix --safe --dry-run --vault . --format json`
4. Summarize safe fixes in plain language and ask the researcher whether to apply them
5. If approved, run `carrel env fix --safe --vault .`
6. If any issue is ambiguous, hand off to the `env-doctor` skill for interactive resolution

## Researcher Approval

Never apply safe fixes without an explicit yes from the researcher. Batch approval is fine:

- "Apply the safe fixes"
- "Leave it alone for now"
- "Walk me through the ambiguous ones"

## Related

- **Skill**: `env-doctor`
- **CLI**: `carrel env validate`, `carrel env fix --safe`
- **Commands**: `/carrel-setup` if the vault needs full regeneration
