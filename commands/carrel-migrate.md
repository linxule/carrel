---
description: Check for plugin updates, show what's new, and apply any needed migrations
---

# Carrel Migrate

Check if the Carrel plugin has been updated and apply any needed migrations to the research environment.

## Steps

1. **Read the current plugin version** from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`

2. **Read the user's last-seen version** from `.carrel/plugin-state.json` in the current project. If the file doesn't exist, this is either a fresh install or a pre-versioning install.

3. **Read the migration registry** from `${CLAUDE_PLUGIN_ROOT}/migrations/registry.json`

4. **Find applicable migrations**: Any migration where `from` matches or is between the last-seen version and the current version. If no last-seen version exists, check if `.carrel/environment.json` exists — if so, this is a pre-versioning install and all migrations from the earliest version apply.

5. **For each applicable migration** (in order):
   - Read the migration file from `${CLAUDE_PLUGIN_ROOT}/migrations/`
   - Tell the user what's new and what changed
   - Run any automatic migration steps
   - Guide the user through any manual steps
   - If no action is required, say so clearly

6. **Update the version marker**: Write `.carrel/plugin-state.json`:
   ```json
   {
     "version": "<current plugin version>",
     "last_migrated": "<today's date>",
     "install_source": "marketplace"
   }
   ```

7. **If already up to date** (versions match): Tell the user they're on the latest version. Show the current version and last migration date.

## Tone

Be brief and friendly. Researchers aren't developers — explain what changed in terms of what they can do, not what the code looks like. If no migration is needed, just confirm everything is current.
