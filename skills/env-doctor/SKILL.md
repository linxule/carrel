---
name: env-doctor
description: "Guided recovery for environment.json drift. Use when the researcher runs /carrel-fix, mentions environment drift, broken setup state, or wants help repairing conflicting settings."
---

# env-doctor

Diagnoses `.carrel/environment.json`, offers safe repairs with approval, and walks the researcher through ambiguous drift without hiding the tradeoffs.

## Mode Detection

Always work in order:

1. **Layer 1: Validate**
   Run `carrel env validate --vault . --format json`.
   If status is `valid`, say so plainly and stop.

2. **Layer 2: Safe fix preview**
   Run `carrel env fix --safe --dry-run --vault . --format json`.
   Group the safe fixes into a short plain-language summary and ask whether to apply them.
   Only run `carrel env fix --safe --vault .` after explicit approval.

3. **Layer 3: Interactive doctoring**
   If validation or the dry-run reports deferred items, shift into guided recovery.
   Explain the ambiguity in ordinary language, present 2-3 options, and ask the researcher to choose.

## Interaction Rules

- Use plain language. Avoid "ValidationError", "enum", or other implementation terms unless the researcher asks.
- Group related fixes. Do not dump every field unless the researcher wants the raw detail.
- If the ambiguity is about sensitivity or cloud consent, explain the practical consequence:
  "This setting decides whether cloud tools are okay by default."
- If CLAUDE.md and environment.json disagree, say explicitly that `environment.json` is the structured source of truth, but ask which one reflects the researcher's current intent before changing either.
- Re-run `carrel env validate --vault . --format json` after any applied fix to confirm the vault is clean.

## Questions for Ambiguous Drift

Use short, concrete questions. Examples:

- "Your sensitivity setting uses an older label. Should I treat this as `medium` sensitivity, which keeps cloud tools off by default?"
- "CLAUDE.md says cloud tools are okay, but environment.json says no. Which one is current?"
- "This tool is marked configured in your profile, but it is not installed on this machine. Should I mark it unavailable here?"

## Logging

After every applied change, append an entry to `_meta/capability-log.md` that includes:

- Timestamp
- What changed
- Why it changed
- How to revert it

Use a compact format, for example:

```markdown
- 2026-04-20 14:03 UTC — Updated `.carrel/environment.json` sensitivity from `cautious` to `medium`; revert by restoring `.carrel/environment.json.bak`.
```

## References

- `references/fix-catalog.md` for the safe-fix rules supported by Layer 2
- `/carrel-fix` for the slash-command wrapper
