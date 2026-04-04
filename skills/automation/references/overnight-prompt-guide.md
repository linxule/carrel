# Overnight Prompt Generation Guide

Detailed patterns for generating the overnight agent prompt. The SKILL.md contains the example; this reference covers edge cases and customization.

## Prompt Assembly Order

1. **Header**: agent identity, UNATTENDED mode declaration
2. **Setup**: plugin load, vault detection (find `.carrel/environment.json`), read preferences and CLAUDE.md
3. **Unattended rules**: no questions, pending-decisions for judgment calls, action logging for trust 3-4
4. **Role**: researcher name, field, sensitivity
5. **Task sections**: one section per enabled capability, marked `[enabled]` or `[disabled — skip]`
6. **Trust level section**: full rules for the chosen level only
7. **Brief instructions**: save to `_meta/briefs/YYYY-MM-DD.md`

## Vault Detection Pattern

The prompt must NOT embed an absolute vault path. Instead:

```
Find the vault root by locating .carrel/environment.json (walk up from cwd).
```

This matches the session-start hook's `findCarrelRoot` pattern and survives:
- iCloud sync folder moves
- External drive mounting
- Folder renames

## Trust Level Prompt Blocks

### Advisory (level 1)
```
- Write all suggestions to _meta/suggestions/. Never act on vault files.
```

### Consultative (level 2)
```
- Write suggestions to _meta/suggestions/.
- Write proposed actions to _meta/pending-approvals.md in structured format:
  `- [ ] **[date] [type]**: [action description]`
- Never execute actions. The researcher approves in the next interactive session.
```

### Delegated (level 3, experimental)
```
- File NEW items following vault conventions (papers/author-year/, transcripts/kind/).
- Never reorganize, move, or rename EXISTING files.
- Log every action in the morning brief with revert instructions.
- Write suggestions for existing-file changes to _meta/pending-approvals.md.
```

### Partnership (level 4, experimental)
```
- Can file new items AND reorganize existing files within the vault epistemology from CLAUDE.md.
- Log every action in the morning brief with specific revert instructions (commands to undo each change).
- The researcher can revert via the session's checkpoint history.
```

## Sensitivity Adjustments

- **High sensitivity**: prompt explicitly states "Do NOT read files in `drafts/` or `_meta/reflections/` unattended. Write pending decisions for any file with unclear sensitivity."
- **Medium sensitivity**: standard behavior
- **Low sensitivity**: no additional restrictions

## Model-Specific Notes

- **Sonnet**: default, sufficient for all tasks. Prompt needs no model-specific adjustments.
- **Opus**: used for deeper synthesis. If Opus is chosen, the reflection synthesis and draft feedback sections can include more detailed analytical instructions.
