# Codex CLI Plugin and Extensibility Investigation Report

Scope note: This report is based on OpenAI Codex documentation, live web research (May 17, 2026), and GitHub search. Network repository cloning was unavailable; claims cite doc URLs and GitHub search results where possible. Some findings correct earlier assumptions that may have been based on an older version of Codex CLI.

---

## Q1 — Formal Plugin System

**Verdict:** Confirmed. Codex CLI has a formal plugin system built around `.codex-plugin/plugin.json`.

**Evidence:**
- Plugin overview: https://developers.openai.com/codex/plugins
- Build docs: https://developers.openai.com/codex/plugins/build
- Scaffold command: `$plugin-creator` generates the manifest and directory structure.
- Documented plugin structure:
  - `.codex-plugin/plugin.json` — manifest
  - `skills/` — bundled skills
  - `hooks/hooks.json` — lifecycle hooks
  - `.app.json` — app/connector config
  - `.mcp.json` — MCP server config
  - `assets/` — static assets
- Note: GitHub path `docs/plugins.md` in the `openai/codex` repo returned 404 during live check. Canonical source is the OpenAI Developers docs above.

**Gap vs Claude Code:**
Structurally very similar to Claude Code's `.claude-plugin/plugin.json`. The main differences are in specific sub-features (see Q3–Q8 below).

---

## Q2 — AGENTS.md, prompts/, ~/.codex/ Config

**Verdict:** AGENTS.md confirmed as the primary instruction injection mechanism. Config file is `~/.codex/config.toml` (not `.json`). `prompts/` directory and `~/.codex/instructions.md` not confirmed in current docs.

**Evidence:**
- AGENTS.md guide: https://developers.openai.com/codex/guides/agents-md
- Config reference: https://developers.openai.com/codex/config-reference
- Global instructions discovery order:
  1. `~/.codex/AGENTS.override.md`
  2. `~/.codex/AGENTS.md`
- Project instructions: `AGENTS.override.md` → `AGENTS.md` → configured fallback names, merged root-to-leaf (closer files override distant)
- `~/.codex/config.toml` config keys include: `model`, `model_provider`, `approval_policy`, `sandbox_mode`, `instructions`, `model_instructions_file`, `project_doc_fallback_filenames`, `mcp_servers`, `hooks`, `skills.config`
- `project_doc_fallback_filenames` allows alternate instruction filenames when AGENTS.md absent
- Project-scoped config: `.codex/config.toml` — only loaded for trusted projects

**Gap vs Claude Code:**
AGENTS.md ≈ CLAUDE.md in role. The merge/override hierarchy is similar. Claude Code's `CLAUDE.md` also merges parent→child. No confirmed `prompts/` system; Claude Code has no direct equivalent either (its custom commands are separate).

---

## Q3 — Custom Slash Commands / Prompts

**Verdict:** Built-in slash commands exist and are documented. No confirmed equivalent to Claude Code's user-authored `commands/*.md` files with YAML frontmatter.

**Evidence:**
- CLI slash commands: https://developers.openai.com/codex/cli/slash-commands
- Documented built-in commands include: `/permissions`, `/agent`, `/apps`, `/plugins`, `/hooks`, `/init`, `/mcp`, `/review`, `/model`, `/fast`, `/personality`, `/keymap`
- `/init` scaffolds an `AGENTS.md`
- `/plugins` opens the plugin browser
- `/hooks` lists active hooks
- Not found: any mechanism to define custom slash commands as files with frontmatter triggers

**Gap vs Claude Code (SIGNIFICANT):**
Claude Code's `commands/*.md` with YAML frontmatter allows researchers to define custom prompts as slash commands (e.g., `/carrel-setup`). No equivalent mechanism found in Codex CLI. This is the largest portability gap for the carrel plugin.

---

## Q4 — Hooks / Lifecycle Events

**Verdict:** Confirmed. Codex CLI has a documented lifecycle hook system. Earlier finding was stale.

**Evidence:**
- Hooks docs: https://developers.openai.com/codex/hooks
- Hook config sources (merged, not replaced):
  - `~/.codex/hooks.json`
  - `~/.codex/config.toml`
  - `<repo>/.codex/hooks.json`
  - `<repo>/.codex/config.toml`
- Documented events: `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, `Stop`
- Handler type: only `type = "command"` handlers execute today; `prompt` and `agent` handlers are parsed but skipped
- Plugin-bundled hooks require opt-in via:
  ```toml
  [features]
  plugin_hooks = true
  ```
- Disable hooks entirely:
  ```toml
  [features]
  hooks = false
  ```

**Gap vs Claude Code:**
Event names are nearly identical to Claude Code's hook events. Key limitation: Codex currently only executes `command` type handlers; `prompt` and `agent` hook types are unimplemented. Claude Code hooks are more mature.

---

## Q5 — Subagents / Specialized Assistants

**Verdict:** Confirmed. Codex now documents subagent workflows and custom agent definitions. Earlier finding was stale.

**Evidence:**
- Subagents docs: https://developers.openai.com/codex/subagents
- Codex can spawn specialized agents in parallel
- Built-in agents: `default`, `worker`, `explorer`
- Custom agent definitions: TOML files under `~/.codex/agents/` or `.codex/agents/`
- Required fields: `name`, `description`, `developer_instructions`
- Optional: model, reasoning effort, sandbox mode, MCP servers, skill config
- Subagents enabled by default; Codex only spawns them when explicitly requested

**Gap vs Claude Code (MODERATE):**
Claude Code's `agents/*.md` are Markdown files with YAML frontmatter and explicit tool allowlists. Codex custom agents are TOML config files — different format, not directly portable. No confirmed per-agent Markdown tool allowlist mechanism.

---

## Q6 — MCP Server Support

**Verdict:** Confirmed. MCP is a first-class Codex feature. Config format updated from `.codex/mcp.json` to `config.toml` entries.

**Evidence:**
- MCP docs: https://developers.openai.com/codex/mcp
- Supported transports: STDIO (command-launched) and Streamable HTTP
- Config in `config.toml`:
  ```toml
  [mcp_servers.my-server]
  command = "..."
  args = [...]
  env = {}
  enabled_tools = [...]
  disabled_tools = [...]
  ```
- CLI management: `codex mcp add <name> -- <command>`, `codex mcp --help`
- TUI inspection: `/mcp`
- Plugin `.mcp.json` still used for plugin-bundled MCP servers
- Config keys: `command`, `args`, `env`, `env_vars`, `cwd`, `url`, `bearer_token_env_var`, `startup_timeout_sec`, `tool_timeout_sec`, `enabled`, `required`, `enabled_tools`, `disabled_tools`

**Gap vs Claude Code:**
Very close parity. Claude Code plugins declare `mcpServers` in `plugin.json`; Codex plugins use `.mcp.json`. Both support auto-launch and tool filtering.

---

## Q7 — Skills / Instruction Libraries

**Verdict:** Confirmed. Codex has a dedicated skills system with `SKILL.md`. Earlier finding was stale.

**Evidence:**
- Skills docs: https://developers.openai.com/codex/skills
- Skill = directory containing `SKILL.md` + optional scripts, references, assets, metadata
- `SKILL.md` required fields: `name`, `description`
- Progressive disclosure: Codex sees name+description first, loads full SKILL.md on use
- Activation modes:
  - Explicit: `$skill` reference or `/skills` command
  - Implicit: when task matches skill description
- Skill locations:
  - Repository: `.agents/skills`
  - User: `$HOME/.agents/skills`
  - Admin: `/etc/codex/skills`
  - System bundled skills
- Skills can be distributed with plugins
- Docs state skills build on "the open agent skills standard"

**Gap vs Claude Code:**
High structural similarity to Anthropic skills (`skills/<name>/SKILL.md`). Key difference: Codex skills use `.agents/skills/` path convention vs Claude Code's `skills/<name>/`. Frontmatter trigger syntax may differ. Worth checking whether the open agent skills standard is the same spec underlying both.

---

## Q8 — Marketplace / Registry

**Verdict:** Partially confirmed. Marketplace mechanism exists and is documented. Official self-serve publishing is still "coming soon."

**Evidence:**
- Plugin docs: https://developers.openai.com/codex/plugins
- Build plugin docs: https://developers.openai.com/codex/plugins/build
- CLI commands:
  ```bash
  codex plugin marketplace add owner/repo
  codex plugin marketplace add owner/repo --ref main
  codex plugin marketplace add https://github.com/example/plugins.git --sparse .agents/plugins
  codex plugin marketplace add ./local-marketplace-root
  codex plugin marketplace upgrade
  codex plugin marketplace remove marketplace-name
  ```
- Marketplace files:
  - `$REPO_ROOT/.agents/plugins/marketplace.json`
  - `$REPO_ROOT/.claude-plugin/marketplace.json` (legacy Claude Code compatibility)
  - `~/.agents/plugins/marketplace.json`
- Plugin install cache: `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`
- TUI: `/plugins` opens plugin browser with marketplace tabs
- Self-serve publishing to official Plugin Directory: "coming soon"

**Gap vs Claude Code:**
CLI commands are very similar. Note: Codex marketplace files can be at `.claude-plugin/marketplace.json` for legacy compatibility — this is directly relevant to carrel. Public directory is not yet fully self-serve.

---

## Q9 — Per-project vs Global Config

**Verdict:** Confirmed with nuance. Global under `~/.codex/`; project under `.codex/` (trust-gated). Layers merge rather than simple override for some surfaces.

**Evidence:**
- AGENTS.md guide: https://developers.openai.com/codex/guides/agents-md
- Config reference: https://developers.openai.com/codex/config-reference
- MCP docs: https://developers.openai.com/codex/mcp
- Global:
  - `~/.codex/AGENTS.override.md` → `~/.codex/AGENTS.md`
  - `~/.codex/config.toml`
  - `~/.codex/agents/` (custom agents)
  - `~/.agents/skills/` (user skills)
- Project:
  - `AGENTS.override.md` → `AGENTS.md` (root to cwd, merged)
  - `.codex/config.toml` — only for trusted projects
  - `.codex/agents/` (project agents)
  - `.agents/skills/` (project skills)
- Trust: `projects.<path>.trust_level` in config
- Hook layers merge; some config keys override

**Gap vs Claude Code:**
Claude Code uses user scope vs project scope with `settings.json`. Codex uses file-based discovery with a trust gate on project `.codex/` config. Carrel's project-scope override pattern maps reasonably, but trust gating is an extra step.

---

## Q10 — Recent Changes (2025–2026)

**Verdict:** Confirmed. Codex extensibility is actively developed. Plugins, MCP, hooks, skills, subagents, and marketplace all have recent activity.

**Evidence:**
- GitHub: https://github.com/openai/codex
- Recent PRs/issues found via live GitHub search:
  - "Move MCP tool naming mode into manager"
  - "feat: Update plugin share settings with discoverability"
  - "Remove string-keyed MCP tool maps"
  - "Codex-cli lag on every prompt when background apps/plugins discovery requests not disabled"
  - MCP tool exposure and dispatch issues in Codex CLI/Desktop
- Current docs have dedicated pages for: plugins, build plugins, hooks, skills, subagents, MCP, CLI slash commands
- Note: exhaustive PR/issue audit was not performed; GitHub repo cloning was unavailable

**Gap:**
No exhaustive repo audit. Issue/PR numbers not captured. A targeted GitHub search on `label:plugin` or `label:extensibility` in `openai/codex` would provide more detail.

---

## Summary Table

| Feature | Codex CLI | Claude Code | Gap |
|---------|-----------|-------------|-----|
| Plugin manifest | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` | Minimal — very similar structure |
| Config files | `~/.codex/config.toml`, AGENTS.md | `settings.json`, CLAUDE.md | Format differs (TOML vs JSON), names differ |
| Custom slash commands | Built-in only, no user-authored files | `commands/*.md` with YAML frontmatter | **Significant** — no carrel-style `/carrel-setup` commands |
| Hooks / lifecycle | `SessionStart`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop` | Same events + more | Codex `command` type only; `prompt`/`agent` hook types unimplemented |
| Subagents | TOML files in `.codex/agents/` | Markdown files `agents/*.md` | Format incompatible; no confirmed per-agent tool allowlist |
| MCP servers | `config.toml` + plugin `.mcp.json` | `plugin.json` `mcpServers` field | Near parity; config format differs |
| Skills | `SKILL.md` in `.agents/skills/` | `SKILL.md` in `skills/<name>/` | Path convention differs; same open agent standard claimed |
| Marketplace | `codex plugin marketplace add` | `claude plugin marketplace add` | Commands nearly identical; Codex official directory not yet self-serve |
| Project vs global scope | Trust-gated `.codex/config.toml`; AGENTS.md merges | `settings.json` user/project scope | Trust gate is extra friction; semantics similar |
| Active development | Yes — plugins, MCP, hooks, skills, marketplace all shipping | Yes | Codex moving fast; some surfaces (hook types) still incomplete |
