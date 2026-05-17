# Plugin Validation Report: carrel v0.9.0

**Verdict: valid-with-warnings**

No blockers. Two warnings that could cause subtle misbehavior in production. Three info items.

---

## BLOCKERS (0)

None.

---

## WARNINGS (2)

### W1 — `hooks/hooks.json`: `UserPromptSubmit` output key is `additionalContext`, but CC spec uses `context`

**File**: `/Users/xulelin/Documents/Apps/mcp/carrel/hooks/inject-context.js` line 55
**Issue**: The hook writes `{ "additionalContext": ... }` to stdout. The Claude Code UserPromptSubmit hook protocol expects the injected text under the key `"context"` (a top-level string field), not `"additionalContext"`. If the key is wrong, CC silently ignores the output — the hook runs, exits 0, and no context is injected. There is no error surfaced to the user.
**Fix**: Change line 55 from `{ additionalContext: lines.join('\n') }` to `{ context: lines.join('\n') }`. Verify against the CC hook protocol docs for the exact field name before shipping.

### W2 — `hooks/hooks.json`: `sensitivity-gate.js` reads tool input from stdin, but `PreToolUse` delivers payload via stdin as a JSON object — double-parsing may fail silently on malformed edge cases

**File**: `/Users/xulelin/Documents/Apps/mcp/carrel/hooks/sensitivity-gate.js` lines 19–36
**Issue**: The hook reads all of stdin as a string and then `JSON.parse`s it. This is correct in principle. However, the `permissionDecision` field it returns (`"ask"` / `"deny"`) is the mechanism CC uses to block or prompt the user — the hook must exit with code 0 AND write the JSON decision to stdout. The script calls `process.exit(0)` unconditionally on line 98, so the exit code is always 0 regardless of whether it wrote a decision or not. This is correct behavior. The warning is that the `"ask"` value for `permissionDecision` is not documented as a valid value in the public CC PreToolUse hook spec — only `"allow"` and `"deny"` are listed. If `"ask"` is unrecognized, the hook passes silently (no gate fires for MEDIUM sensitivity cases). Verify that CC supports `"ask"` as a `permissionDecision` value before relying on it for the MEDIUM-sensitivity flow.
**Fix**: Audit the CC PreToolUse hook output schema. If `"ask"` is not supported, replace the MEDIUM-sensitivity branch with either `"deny"` (hard block) or a `"allow"` with a prepended warning message, depending on desired UX.

---

## INFO (3)

### I1 — `commands/CONVENTIONS.md`: no YAML frontmatter — will be skipped by CC command loader, which is correct, but verify this is intentional

**File**: `/Users/xulelin/Documents/Apps/mcp/carrel/commands/CONVENTIONS.md`
**Issue**: The file starts with `# Command File Conventions`, no `---` frontmatter block. CC auto-discovery loads `commands/**/*.md` files that have a `description` field in frontmatter. Without frontmatter, this file will not be registered as a slash command — it is treated as a plain markdown file in the directory. This is the correct and intended behavior (it is a conventions doc, not a command). Confirmed: the file contains no frontmatter delimiters. No action needed, but worth a comment in the file header so future editors don't accidentally add frontmatter.

### I2 — `hooks/hooks.json`: `SessionEnd` timeout is 10 s, which is shorter than `SessionStart` (15 s)

**File**: `/Users/xulelin/Documents/Apps/mcp/carrel/hooks/hooks.json` line 21
**Issue**: `session-reflect.js` does filesystem reads across the vault to compute session stats (`getSessionStats` enumerates multiple subdirectories). On large vaults (500+ files) this could approach or exceed 10 s on slow disks. Not a blocker — CC will abort the hook and continue, so the worst case is a missed reflection prompt, not a crash.
**Fix**: Consider raising to 15 s to match SessionStart, or add a guard in `session-reflect.js` to skip the `getSessionStats` walk if file count exceeds a threshold.

### I3 — `marketplace.json`: `keywords` and `tags` are identical arrays

**File**: `/Users/xulelin/Documents/Apps/mcp/carrel/.claude-plugin/marketplace.json` lines 16–18
**Issue**: Both fields carry `["research","obsidian","pdf","transcription","academic","vault","zotero","knowledge-management"]`. This is not wrong — the CC marketplace spec treats them as separate fields — but it is redundant. No functional impact.
**Fix**: Keep as-is, or deduplicate if the marketplace surfaces only one of them in search.

---

## Component Summary

| Component | Found | Valid | Notes |
|-----------|-------|-------|-------|
| Commands | 15 .md files | 15 valid | CONVENTIONS.md correctly lacks frontmatter |
| Skills | 13 SKILL.md files | 13 valid | session-reflection new skill present, frontmatter correct |
| Hooks | 4 hooks in hooks.json | 4 syntactically valid | W1/W2 above are behavioral, not structural |
| Hook scripts | 4 .js files | 4 present | check-version.js is a module (not a hook entry), correct |
| Migration registry | 13 entries | 13 valid | 0.8.1-to-0.9.0.md present and registered |
| Manifest (plugin.json) | version 0.9.0 | valid | name, version, description, author all correct |
| Manifest (marketplace.json) | version 0.9.0 | valid | new fields present (keywords, category, tags, license, repository) |

## Positive Findings

- All 15 command files have valid YAML frontmatter with `description` field present.
- The 7 thin wrappers (`carrel-feedback`, `carrel-migrate`, `carrel-mirror`, `carrel-reflect`, `carrel-share`, `carrel-batch`, `carrel-automate`) correctly use `!carrel <subcmd> ${ARGS}` with `argument-hint` populated — the convention is consistently applied.
- `session-reflection` SKILL.md has correct frontmatter (`name`, `description`), description is detailed and includes trigger phrases.
- `${CLAUDE_PLUGIN_ROOT}` used in all four hook command strings — portability is correct.
- Hook event names (`SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreToolUse`) match current CC spec event names.
- `PreToolUse` matcher is `"Bash"` (tool name, not glob pattern) — correct for CC's tool matcher syntax.
- Migration registry entry for 0.8.1-to-0.9.0 is present with accurate summary, `breaking: false` is correct.
- `CONVENTIONS.md` has no frontmatter, so it will not be registered as a slash command — the concern is a non-issue.

## Overall Assessment

**valid-with-warnings** — The plugin will load and all commands, skills, and hooks will register correctly. W1 (wrong output key in `inject-context.js`) is the only issue likely to cause a silent runtime failure; per-turn context injection simply won't work until the key is corrected. W2 (unverified `"ask"` permission value) is a behavioral risk for the MEDIUM-sensitivity gate path. Both are one-line fixes once the CC protocol is confirmed.
