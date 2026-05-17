# Carrel plugin survey + Claude Code plugin spec

Date: 2026-05-17. Repo audited: `/Users/xulelin/Documents/Apps/mcp/carrel/` (v0.8.1).

---

## Part A — Carrel as a Claude Code plugin

### 1. Manifest files

**`.claude-plugin/plugin.json`** (full contents):

```json
{
  "name": "carrel",
  "version": "0.8.1",
  "description": "AI-augmented research environment. Interview-first onboarding, Obsidian vault setup, document conversion, scheduled automation, and ongoing research tools for academics.",
  "author": { "name": "Xule Lin (Imperial College London)" }
}
```

Fields present: `name`, `version`, `description`, `author.name`.
Fields *not* present (all valid manifest keys): `homepage`, `repository`, `license`, `keywords`, `$schema`, `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `outputStyles`, `lspServers`, `experimental.themes`, `experimental.monitors`, `userConfig`, `channels`, `dependencies`. Carrel relies entirely on the **default folder discovery** for components.

**`.claude-plugin/marketplace.json`** (full contents):

```json
{
  "name": "carrel",
  "owner": { "name": "Xule Lin" },
  "plugins": [
    {
      "name": "carrel",
      "description": "AI-augmented research environment. ...",
      "version": "0.8.1",
      "author": { "name": "Xule Lin (Imperial College London)" },
      "source": "./",
      "homepage": "https://github.com/linxule/carrel"
    }
  ]
}
```

Marketplace fields used: `name`, `owner.name`, `plugins[]` with `name`, `description`, `version`, `author`, `source` (relative path `./` — repo *is* the plugin), `homepage`.
Not used: `owner.email`, `$schema`, `description`, `metadata.pluginRoot`, `allowCrossMarketplaceDependenciesOn`, plus all marketplace plugin entry extras (`category`, `tags`, `keywords`, `strict`, `repository`, `license`, plus the per-entry component-path fields `skills`/`commands`/`agents`/`hooks`/`mcpServers`/`lspServers`).

### 2. Plugin component directories at top level

| Dir | Present? | Notes |
|---|---|---|
| `.claude-plugin/` | yes | Manifest + marketplace catalog only |
| `skills/` | yes | 12 skills |
| `agents/` | yes | 2 agents |
| `commands/` | yes | 15 commands (flat `.md` files) |
| `hooks/` | yes | `hooks.json` + 3 `.js` scripts |
| `.mcp.json` | yes but empty (`{"mcpServers": {}}`) — at repo root, not part of plugin asset spec; effectively a no-op |
| `monitors/`, `bin/`, `themes/`, `outputStyles/`, `.lsp.json`, `settings.json` | none |
| Other plugin-adjacent dirs at repo root | `templates/` (vault scaffolding), `migrations/` (with `registry.json`, consumed by `/carrel-migrate`), plus the Python project: `src/`, `tests/`, `pyproject.toml`, `install.sh`, `install.ps1`, `bootstrap.sh`, `planning/`, `docs/`, `README.md`, `CLAUDE.md`, `LICENSE` |

Note: per Claude Code spec, plugins can use **either** the default folder names (what carrel does) **or** the `commands` field — carrel's `commands/` directory is officially "flat Markdown files" and the spec recommends new plugins use `skills/` instead. Carrel mixes both.

### 3. Skills (12) — name + description (frontmatter `description` field)

| Skill | Description (trigger summary) |
|---|---|
| `automation` | Configure/understand/adjust overnight vault maintenance. Triggers: schedule, automate, overnight, morning brief, trust level, `/carrel-automate`. |
| `collaborator-onboarding` | Share a Carrel vault with someone else (RA, co-author, lab member). Triggers: share with, onboard a collaborator, generate a handbook, `/carrel-share`. |
| `convert` | Convert PDF/Word/PPTX/XLSX/image to markdown. Triggers: convert, import, dropped file path. |
| `env-doctor` | Guided recovery for environment.json drift. Triggers: `/carrel-fix`, environment drift, broken setup state. |
| `environment-setup` | Set up AI research environment. Triggers: setup, get started, configure, onboard, opening a project with no `.carrel/`. |
| `knowledge-wiki` | Build/query/maintain synthesized knowledge base across sources. Triggers: field map, synthesize, literature review, wiki, contradictions. |
| `model-teammates` | Add/remove/review multi-model teammates (Codex/Gemini/Kimi). Triggers: teammates, multi-model, second opinion, `/carrel-setup` Phase 5b. |
| `research-partner` | Think through ideas, get feedback on arguments, brainstorm. Triggers: help me think, push back, what am I missing. |
| `self-improve` | Evaluate external skills/MCPs/tools for absorption; log custom artifacts; promote to templates; quarterly upstream review. |
| `transcribe` | Audio/video files or YouTube URL → transcript. Triggers: transcribe, get the transcript, audio/video/YouTube URL. |
| `vault-ops` | Create/search/organize/manage notes in Obsidian vault. Triggers: create a note, find my notes about, organize, search vault. |
| `web-capture` | Save web content to vault. Triggers: URLs, save this article, clip this page. |

### 4. Agents (2) — name + model + description

| Agent | Model | Description |
|---|---|---|
| `research-partner` | `inherit` (color: cyan) | Use when a researcher wants to think through ideas, get feedback on arguments, explore connections, discuss a paper. Triggers on "help me think about", "what do you think of", "push back on this". |
| `setup-interviewer` | `inherit` (color: green) | Use when onboarding a new researcher. Conducts an adaptive interview about research area, data types, sensitivity, existing tools. Triggers on "set up", "get started", "configure", "onboard", or when `.carrel/` is missing. |

Both agents use only `name`, `description`, `model`, `color` frontmatter — they don't use `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, or `isolation`.

### 5. Commands (15)

All commands are flat `.md` files in `commands/` with only a `description:` frontmatter field — none use `allowed-tools` or `argument-hint`.

| Command | Description |
|---|---|
| `/carrel-automate` | Set up or update overnight vault maintenance and analytical tasks |
| `/carrel-batch` | Batch convert or transcribe a folder of files and file them to your vault |
| `/carrel-capture` | Save a web page or online article to your vault as markdown |
| `/carrel-cheatsheet` | Regenerate your reference card with current setup information |
| `/carrel-convert` | Convert a PDF, Word, or other document to markdown and add it to your vault |
| `/carrel-feedback` | Generate an anonymized feedback digest from your reflections to share with the maintainer |
| `/carrel-fix` | Detect and resolve environment.json drift in your vault |
| `/carrel-migrate` | Check for plugin updates, review current environment, and suggest improvements |
| `/carrel-mirror` | Synthesize research patterns from reflections, capability log, and friction log |
| `/carrel-reflect` | Quick end-of-session reflection — what worked, what didn't, what to improve |
| `/carrel-setup` | Set up AI research environment — interview, configure tools, scaffold Obsidian vault |
| `/carrel-share` | Generate a vault-specific onboarding handbook for a collaborator |
| `/carrel-status` | Check what tools are installed and working in your research environment |
| `/carrel-teammates` | Add or review multi-model agent teammates — Codex (ChatGPT), Gemini, Kimi |
| `/carrel-transcribe` | Transcribe an audio recording and save the transcript to your vault |

### 6. Hooks

Config file: `hooks/hooks.json` (matches spec exactly — same schema as inline `hooks` in `plugin.json`).

| Event | Matcher | Script | Timeout | What it does |
|---|---|---|---|---|
| `SessionStart` | `*` | `node ${CLAUDE_PLUGIN_ROOT}/hooks/check-environment.js` | 15s | Find `.carrel/` upward, read `environment.json`, surface researcher profile (sensitivity, cloud preference, active tools, requested-but-not-configured tools), detect partial setup, surface paused setup with phase-specific resume prompt, run `carrel env validate --vault . --format json` once per 24h to detect environment drift, compare plugin version against `.carrel/plugin-state.json` and prompt `/carrel-migrate` if changed, check `_meta/briefs/` for morning briefs + active plans + pending decisions/approvals + automation status + wiki page counts. Always exits 0 (never blocks). |
| `SessionEnd` | `*` | `node ${CLAUDE_PLUGIN_ROOT}/hooks/session-reflect.js` | 10s | Count vault files (papers, notes, transcripts, drafts), surface today's `_meta/capability-log.md` entries, emit a structured `SESSION_REFLECTION` JSON remediation block on stderr (with `next_commands: ["/carrel-reflect"]`, `next_skills: ["research-partner"]`, `can_bypass: true`), print a farewell. Always exits 0. |

Helper module `hooks/check-version.js` (loaded by check-environment.js) reads `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` to detect version changes vs `.carrel/plugin-state.json`.

Hook type: `command` only. No use of `http`, `mcp_tool`, `prompt`, or `agent` hook types. No use of `args`/exec form, `async`, `asyncRewake`, `shell`, `statusMessage`, `if` permission filters.

Events used: 2 out of ~29 available. Unused that could be relevant: `UserPromptSubmit`, `PreToolUse`/`PostToolUse`, `Stop`, `Notification`, `SubagentStart`/`SubagentStop`, `InstructionsLoaded`, `CwdChanged`, `FileChanged`, `PreCompact`/`PostCompact`, `TaskCreated`/`TaskCompleted`, `Setup`, `Elicitation`, etc.

### 7. MCP servers shipped via manifest

**None.** `plugin.json` has no `mcpServers` field. Repo root has a `.mcp.json` but it's `{"mcpServers": {}}` — an empty placeholder, not a plugin-shipped server.

### 8. Output styles / themes / monitors / LSP / bin / settings

None. No `outputStyles/`, `themes/`, `monitors/`, `bin/`, `.lsp.json`, or `settings.json` at plugin root.

### 9. Claude Code-specific assumptions in carrel

These are the friction points for porting to another CLI:

1. **`.claude-plugin/` directory + dual `plugin.json` and `marketplace.json` schema** — the entire packaging story is Claude-Code-specific.
2. **`${CLAUDE_PLUGIN_ROOT}` env var** — referenced in `hooks/hooks.json` (twice), `hooks/check-version.js` (with `path.resolve(__dirname, '..')` fallback), and several command files (`carrel-migrate.md` uses it 3+ times to locate plugin assets at runtime).
3. **Hook event names `SessionStart` and `SessionEnd`** — these are Claude Code event names; any port must map them to the host CLI's equivalents.
4. **`hooks/hooks.json` shape** (`hooks.{Event}[].matcher`, `hooks.{Event}[].hooks[].{type,command,timeout}`) — Claude-Code-specific schema.
5. **Structured JSON-on-stderr "remediation" payload in `session-reflect.js`** (`{code, severity, next_commands, next_skills, can_bypass, details}`) — assumes a Claude-Code-style IO/remediation convention.
6. **Vault `CLAUDE.md`** is the cross-session memory bridge — the setup skill writes a personalized `CLAUDE.md` that "Claude loads automatically every session". This name is Claude-specific (vs `AGENTS.md`, `GEMINI.md`, etc.).
7. **Slash-command convention `/carrel-*`** with namespaced expectation (the plugin name `carrel` becomes the prefix). Other CLIs use different invocation grammars.
8. **References to "Claude Desktop" + its local **Schedule** tab** in `carrel-automate.md` (for scheduling automation runs) — this is a Claude Desktop product feature, not generic.
9. **Skill frontmatter convention** (`description:` as a Claude-Code/Anthropic skills idiom; "Triggers on..." phrasing is the Claude-Code skill activation prose pattern).
10. **Agent frontmatter convention** (`model: inherit`, `color`, `<example>` tags inside description) — Claude Code Subagents convention.
11. **`/carrel-teammates` skill registers other CLI plugins** (`openai/codex-plugin-cc`, `thepushkarp/cc-gemini-plugin`, `linxule/kimi-plugin-cc`) — these are Claude-Code-plugin wrappers, so the whole teammates capability is structurally Claude-Code-specific.
12. **Migration UX nudges `/reload-plugins` / `/plugin install` / `/plugin marketplace add` indirectly** via the migration doc system.
13. **Tool names like Bash/Edit/Read/Write** — checked: the **plugin component files** (skills/agents/commands/hooks) do **not** reference these names directly (no `allowed-tools` frontmatter anywhere). This is a clean spot.
14. **`CLAUDE_ENV_FILE`** is not used. **`${CLAUDE_PLUGIN_DATA}`** is not used (state lives under `.carrel/` in the user's vault instead). **`${CLAUDE_PROJECT_DIR}`** is not used (hooks walk up from `process.cwd()` to find `.carrel/`).
15. **The companion Python CLI `carrel` itself is portable** — it doesn't import any Claude SDK, doesn't know about plugins, just provides a CLI. Hooks shell out to `carrel env validate ...` like any other binary.

---

## Part B — Claude Code plugin spec summary

Source pages (host redirected from `docs.claude.com` → `code.claude.com`):
- https://code.claude.com/docs/en/plugins (overview)
- https://code.claude.com/docs/en/plugins-reference (manifest schema, components)
- https://code.claude.com/docs/en/hooks (hook events)
- https://code.claude.com/docs/en/plugin-marketplaces (marketplace schema)
- Related: `/en/skills`, `/en/sub-agents`, `/en/mcp`, `/en/discover-plugins`, `/en/plugin-dependencies`

### 1. `plugin.json` manifest schema

Lives at `<plugin-root>/.claude-plugin/plugin.json`. The manifest is **optional** — if omitted, Claude Code auto-discovers components in default folders and derives the name from the directory.

**Required:** `name` (kebab-case, no spaces — namespace prefix for skills/agents).

**Optional metadata:** `$schema`, `version` (if omitted, git SHA is used; every commit then counts as a release), `description`, `author{name,email,url}`, `homepage`, `repository`, `license`, `keywords`.

**Optional component-path fields** (string | array | object as noted):
- `skills` (string|array — *adds to* default `skills/`)
- `commands` (string|array — *replaces* default `commands/`)
- `agents` (string|array — *replaces* default `agents/`)
- `hooks` (string|array|object — config path or inline)
- `mcpServers` (string|array|object — config path or inline)
- `outputStyles` (string|array — *replaces* default `output-styles/`)
- `lspServers` (string|array|object)
- `experimental.themes` (string|array)
- `experimental.monitors` (string|array)

**Optional advanced:** `userConfig` (typed prompts at enable time; values exposed as `${user_config.KEY}` substitution + `CLAUDE_PLUGIN_OPTION_<KEY>` env vars; `sensitive: true` routes to keychain), `channels` (per-MCP-server message injection — Telegram/Slack/Discord style), `dependencies` (other plugins with optional semver).

### 2. `marketplace.json` schema

Lives at `<marketplace-root>/.claude-plugin/marketplace.json`.

**Required:** `name` (kebab-case; certain names reserved for Anthropic), `owner` (object: `name` required, `email` optional), `plugins` (array).

**Optional top-level:** `$schema`, `description`, `version`, `metadata.pluginRoot`, `allowCrossMarketplaceDependenciesOn`.

**Per-plugin entry — required:** `name`, `source` (relative path starting with `./`, or one of these source types: `github` `{repo, ref?, sha?}`, `url` `{url, ref?, sha?}`, `git-subdir` `{url, path, ref?, sha?}`, `npm` `{package, version?, registry?}`).

**Per-plugin entry — optional:** any `plugin.json` field (description, version, author, homepage, repository, license, keywords, plus all component-path fields), plus marketplace-specific: `category`, `tags`, `strict` (default `true`; `false` makes the marketplace entry the sole authority — useful when curating someone else's repo).

### 3. Officially supported component types + conventions

- **Skills** → `skills/<name>/SKILL.md` (+ optional `references/`, `scripts/`). Namespaced as `/<plugin-name>:<skill>`.
- **Commands** (legacy / flat) → `commands/*.md`. Same namespacing.
- **Agents** → `agents/*.md` with frontmatter (`name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation: "worktree"` only). `hooks`/`mcpServers`/`permissionMode` are **not** allowed in plugin-shipped agents.
- **Hooks** → `hooks/hooks.json` or inline in `plugin.json`. Types: `command`, `http`, `mcp_tool`, `prompt`, `agent`. Per-handler fields: `if`, `timeout`, `statusMessage`, plus type-specific.
- **MCP servers** → `.mcp.json` or inline `mcpServers`. Standard MCP server config with command/args/env, `${CLAUDE_PLUGIN_ROOT}` substitution.
- **LSP servers** → `.lsp.json` or inline `lspServers`. Fields: `command`, `args`, `extensionToLanguage`, `transport`, `env`, `initializationOptions`, `settings`, `workspaceFolder`, `startupTimeout`, `shutdownTimeout`, `restartOnCrash`, `maxRestarts`.
- **Monitors** (experimental) → `monitors/monitors.json`. Array of `{name, command, description, when?}` — long-running shell commands whose stdout lines become notifications.
- **Themes** (experimental) → `themes/*.json` with `{name, base, overrides}`.
- **Output styles** → `output-styles/` directory.
- **`bin/`** → executables on PATH while plugin enabled.
- **`settings.json`** at plugin root → currently only `agent` (set main-thread agent) and `subagentStatusLine` keys honored.

### 4. Hook events (~29) + payload shapes

| Event | Matcher | Can block? |
|---|---|---|
| SessionStart | startup/resume/clear/compact | No (can add context) |
| Setup | init/maintenance | No (CI-mode only) |
| SessionEnd | clear/resume/logout/etc | No |
| UserPromptSubmit | none | Yes (`decision: block`) |
| UserPromptExpansion | command name | Yes |
| Stop | none | Yes |
| StopFailure | rate_limit/auth_failed/etc | No |
| PreToolUse | tool name | Yes (`permissionDecision: deny`) |
| PostToolUse | tool name | "Block" but tool already ran |
| PostToolUseFailure | tool name | Same |
| PostToolBatch | none | Yes |
| PermissionRequest | tool name | Auto-approve/deny |
| PermissionDenied | tool name | `retry: true` |
| InstructionsLoaded | load reason | No (audit) |
| ConfigChange | settings type | Yes |
| CwdChanged | none | No |
| FileChanged | filename pattern | No |
| Notification | notification kind | No |
| SubagentStart | agent type | No |
| SubagentStop | agent type | Yes |
| TeammateIdle | none | Yes |
| TaskCreated | none | Yes (exit 2) |
| TaskCompleted | none | Yes |
| PreCompact / PostCompact | manual/auto | Pre yes, Post no |
| WorktreeCreate / WorktreeRemove | none | Create yes, Remove no |
| Elicitation / ElicitationResult | MCP server name | Yes |

**Common payload keys:** `session_id`, `cwd`, `permission_mode`, `hook_event_name`, plus event-specific fields (`source`, `prompt`, `tool_name`, `tool_input`, `tool_use_id`, `tool_result`, `file_path`, `memory_type`, `load_reason`, etc.).

**Hook output:**
- Exit 0 = success; stdout parsed as JSON if present.
- Exit 2 = blocking error; stderr shown to user.
- Other exit = non-blocking error; stderr first line shown in transcript.
- JSON keys: `continue`, `stopReason`, `suppressOutput`, `systemMessage`, `terminalSequence`, `hookSpecificOutput.{hookEventName, additionalContext, decision, reason, permissionDecision, permissionDecisionReason, modifiedToolInput, retry}`.

**Substitutions in hook commands:** `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_PROJECT_DIR}`, `${user_config.*}`, any env var.

**Env vars provided to hooks:** `CLAUDE_PROJECT_DIR`, plus access to `CLAUDE_ENV_FILE` (for env persistence) on lifecycle events.

### 5. Install / enable mechanisms and scope

Two install modes:
- **Dev:** `claude --plugin-dir ./path` or `claude --plugin-url <url-to-zip>` (session-scoped, hot-reload via `/reload-plugins`).
- **Production:** marketplace registration (`/plugin marketplace add <source>`) then `/plugin install <plugin>@<marketplace>` with a scope flag.

**Scopes** (`enabledPlugins` in the matching settings file):
- `user` → `~/.claude/settings.json` (default)
- `project` → `.claude/settings.json` (team, version-controlled)
- `local` → `.claude/settings.local.json` (gitignored)
- `managed` → managed settings (read-only)

Project scope overrides user scope; `false` overrides `true`. Marketplace plugins are copied to `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Updates kept for ~7 days. `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/<id>/`) survives updates and uninstall (unless `--keep-data` not passed).

Containers/CI: `CLAUDE_CODE_PLUGIN_SEED_DIR` (read-only mounted seed dir mirroring `~/.claude/plugins`) and `CLAUDE_CODE_PLUGIN_CACHE_DIR` for building seeds. `extraKnownMarketplaces` + `strictKnownMarketplaces` in managed settings control which marketplaces users can add.

Private repos use git credential helpers; auto-update needs `GITHUB_TOKEN`/`GITLAB_TOKEN`/`BITBUCKET_TOKEN` env vars.

### 6. Documented portability / non-Claude usage

Effectively **none**. The plugin spec is product-specific:
- Manifest path is literally `.claude-plugin/plugin.json`.
- Env vars are `CLAUDE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_DATA` / `CLAUDE_PROJECT_DIR` / `CLAUDE_ENV_FILE`.
- Hook event names (`SessionStart`, `PreToolUse`, etc.) and tool names (`Bash`, `Edit`, `Write`, `WebFetch`, `Agent`, `AskUserQuestion`, `ExitPlanMode`) match Claude Code's tool surface.
- Skills/commands are namespaced with `<plugin>:<name>` and invoked as slash commands.
- Marketplace cache + install CLI commands (`/plugin install`, `/plugin marketplace add`, `/reload-plugins`, `/doctor`, `/plugin disable`) are Claude Code CLI commands.
- Reserved marketplace names (`claude-code-marketplace`, `anthropic-marketplace`, etc.) enforce Anthropic branding.

The skill *format* (markdown + YAML frontmatter) and MCP server config are portable in principle — but the bundling/discovery/install/enable machinery is not.
