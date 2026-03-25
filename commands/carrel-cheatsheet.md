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

1. Read `.carrel/environment.json` for current state
2. Run `skills/environment-setup/scripts/generate-cheatsheet.js`
3. Write updated cheat sheet to `_meta/cheat_sheet.md`
4. Confirm: "Your cheat sheet has been updated with your current setup."

## Related

- **Skill**: `environment-setup` (cheat sheet generation)
