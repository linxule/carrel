# Carrel cross-CLI port feasibility

*Investigation date: 2026-05-17. Sources: WebFetch of Kimi plugin docs, kimi-ask agent (Kimi explaining Kimi CLI), codex-rescue agent (Codex investigating Codex CLI), general-purpose agent mapping carrel + Claude Code plugin spec. Raw reports: `/tmp/codex-cli-plugin-investigation.md`, `/tmp/carrel-and-claude-plugin-survey.md`.*

## TL;DR

- **Codex CLI: ~70% portable today.** Closest sibling to Claude Code. Same `plugin.json`-style manifest, same hook event names, first-class MCP, marketplace accepts `.claude-plugin/marketplace.json` for legacy compat. **Real wall: no user-defined `/commands/`** — which is carrel's most-used surface (15 commands).
- **Kimi CLI: ~30% portable today, ~80% if issue #1714 ships.** Native Kimi plugin is a tool-execution registry, not a Claude-style bundle. Strong overlap on skills (Kimi reads `.claude/skills/` natively). Commands, agents, hooks, MCP bundling, marketplaces have no plugin-scoped equivalent — degrades to install scripts + manual config edits.

## What carrel actually ships (Claude Code plugin)

| Type | Count | Names |
|---|---|---|
| skill | 12 | automation, collaborator-onboarding, convert, env-doctor, environment-setup, knowledge-wiki, model-teammates, research-partner, self-improve, transcribe, vault-ops, web-capture |
| agent | 2 | research-partner (Sonnet/inherit), setup-interviewer (inherit) |
| command | 15 | /carrel-{automate, batch, capture, cheatsheet, convert, feedback, fix, migrate, mirror, reflect, setup, share, status, teammates, transcribe} |
| hook | 2 | SessionStart → check-environment.js (15s); SessionEnd → session-reflect.js (10s) |
| mcp | 0 | manifest has no mcpServers; root `.mcp.json` is `{"mcpServers": {}}` |

Carrel uses a thin slice of Claude Code's surface — 4 of ~20 manifest fields, only 2 of ~29 hook events, no MCP, no output styles, no LSP, no userConfig, no channels, no settings.json.

## Comparison matrix

| Surface | Claude Code | Codex CLI | Kimi CLI |
|---|---|---|---|
| Manifest | `.claude-plugin/plugin.json` | `plugin.json` near-identical | `plugin.json` (tool registry shape) |
| Marketplace | `marketplace.json`; `claude plugin marketplace add` | `codex plugin marketplace add`; accepts CC `marketplace.json` | None |
| Skills | `skills/<name>/SKILL.md` | `.agents/skills/`, same format | Same SKILL.md format, but only 1 per plugin, nested not scanned. Reads `.claude/skills/`, `.codex/skills/` |
| Agents | `agents/*.md` (YAML+prose) | TOML files | None (built-in subagent types only) |
| Slash commands | `commands/*.md` + frontmatter | **None — biggest gap** | None for users — model invokes tools |
| Hooks | `hooks/hooks.json` + JS | Same event names, `command`-type hooks | 13 events, user-global TOML only |
| MCP | `mcpServers` auto-loads | First-class `.mcp.json` parity | Separate from plugins (`~/.kimi/mcp.json`) |
| Install scope | user / project | user / project | user only |
| Plugin root env var | `${CLAUDE_PLUGIN_ROOT}` (carrel uses) | Unconfirmed equivalent | None |
| Memory file | `CLAUDE.md` | `AGENTS.md` | Multiple, but no plugin-defined |

## Carrel's Claude-Code-isms (friction points)

1. **`${CLAUDE_PLUGIN_ROOT}`** — used in `hooks/hooks.json`, `check-version.js`, several command `.md` files including `carrel-migrate.md`
2. **Hook schema** — `hooks.{Event}[].matcher.hooks[].{type,command,timeout}` is Claude-shaped
3. **Structured stderr JSON** — `session-reflect.js` emits `{code, severity, next_commands, next_skills, can_bypass}` — Claude IO convention
4. **15 `/carrel-*` slash commands** — no Codex target, Kimi requires conversion to skill or tool
5. **Vault `CLAUDE.md` as cross-session memory** — Codex wants `AGENTS.md`
6. **`/carrel-teammates`** wraps three CC plugins — recursive CC dependency
7. Hook event names `SessionStart` / `SessionEnd` — match Codex; absent from Kimi plugin scope

**Clean spots:** no hard-coded Claude tool names (`Bash`, `Edit`, etc.), no `allowed-tools` frontmatter, Python core has zero Claude SDK imports.

## Feasibility verdict

### Codex CLI — feasible, single-phase port viable

| Component | Effort | Notes |
|---|---|---|
| Manifest | trivial | Rename/symlink `.claude-plugin/` |
| Skills (12) | drop-in | Move to `.agents/skills/` per Codex docs |
| Hooks (2) | small | Same event names. Swap `${CLAUDE_PLUGIN_ROOT}` + strip Claude stderr schema |
| Agents (2) | medium | Convert YAML+md → TOML |
| Commands (15) | **HARD** | No user command system. Options: (a) inline into skills, (b) wait for/lobby Codex, (c) ship as `carrel <cmd>` shell entry points |
| MCP | none | Carrel ships zero |

**Effort: 1–2 weeks** if (a) or (c) is acceptable.

### Kimi CLI — partially feasible today, fully feasible later

| Component | Effort | Notes |
|---|---|---|
| Skills (12) | medium | Flatten — Kimi only auto-discovers 1 SKILL.md per plugin, nested ignored. Install script copies to `~/.kimi/skills/` |
| Agents (2) | small | Convert to skills, invoke via `/skill:research-partner` |
| Commands (15) | **medium-large** | Each → skill (`/skill:carrel-setup`) or tool. Loses `/name` ergonomic |
| Hooks (2) | medium | Standalone scripts + README with TOML to paste into `~/.kimi/config.toml`. Script self-detects vault via `cwd` |
| MCP | none | Not used |
| Manifest | new | Write native `plugin.json` for executable tools |

**Effort: 2–3 weeks**, plus UX regression.

**Better path: track issue #1714** — Claude-compatible plugin compatibility layer for Kimi. If it lands, existing `.claude-plugin/` works with minimal changes.

## Recommended next moves

1. **Build `carrel-cli-adapter` abstraction layer** in Python core for memory file location, plugin-root env var, hook output schema. Prep work that lowers cost of either port.
2. **Codex first, Kimi later** — lower-risk port, unlocks teammate symmetry. Commands gap needs a decision first.
3. **Wait on Kimi #1714, port to Codex now** — highest leverage for least redundant work.
4. **File `commands/` feature request on Codex CLI** and design port around the answer.
