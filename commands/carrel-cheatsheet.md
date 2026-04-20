---
description: Regenerate your reference card with current setup information
---

# /carrel-cheatsheet — Regenerate Reference Card

Recreate the cheat sheet at `_meta/cheat_sheet.md` based on current configuration.

## When to Use

- After adding or changing tools
- Researcher asks "what can I do?", "update my cheat sheet"
- Setup has changed since last generation

## What Happens

1. Run `carrel vault cheatsheet --vault <path> --force` (the CLI reads `.carrel/environment.json` via Pydantic and writes `_meta/cheat_sheet.md`)
2. Read the regenerated cheat sheet
3. Optionally edit directly to add researcher-specific touches (workflow examples, named projects, custom shortcuts)
4. Confirm: "Your cheat sheet has been updated with your current setup."

## Related

- **Skill**: `environment-setup` (cheat sheet generation)
