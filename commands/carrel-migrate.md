---
description: Check for plugin updates, review current environment, and suggest improvements
---

# Carrel Migrate

Review the researcher's current Carrel setup, check for plugin updates, and make suggestions.

## Steps

1. **Read the current plugin version** from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`

2. **Read the user's last-seen version** from `.carrel/plugin-state.json` in the current project. If the file doesn't exist, this is either a fresh install or a pre-versioning install.

3. **Assess the current environment**:
   - Read `.carrel/environment.json` — check what tools are configured, what preferences are set
   - Check what's actually installed on the machine (`node`, `uv`, `coli`, `liteparse`, etc.)
   - Note any gaps: tools the user wanted during setup but aren't configured yet
   - Check if vault CLAUDE.md exists and is in sync with environment.json

4. **Check for version changes**: Read `${CLAUDE_PLUGIN_ROOT}/migrations/registry.json`. Find any applicable migrations between the last-seen version and current version. If no last-seen version exists but `.carrel/environment.json` does, this is a pre-versioning install — all migrations from the earliest version apply.

5. **For each applicable migration** (in order):
   - Read the migration file from `${CLAUDE_PLUGIN_ROOT}/migrations/`
   - Tell the user what's new and what changed
   - Run any automatic migration steps
   - Guide the user through any manual steps
   - If no action is required, say so clearly

6. **Make suggestions** based on the environment assessment:
   - New commands or skills available since their last version
   - Tools they could install to unlock capabilities they expressed interest in
   - Configuration improvements (e.g., cloud tools if they've since become comfortable)
   - Vault structure changes if the plugin has evolved

7. **Update the version marker**: Write `.carrel/plugin-state.json`:
   ```json
   {
     "version": "<current plugin version>",
     "last_migrated": "<today's date>",
     "install_source": "marketplace"
   }
   ```

8. **If already up to date** (versions match and no gaps found): Tell the user they're on the latest version and everything looks good. Show the current version and last check date.

## Tone

Be brief and friendly. Researchers aren't developers — explain what changed in terms of what they can do, not what the code looks like. Frame suggestions as options, not requirements.
