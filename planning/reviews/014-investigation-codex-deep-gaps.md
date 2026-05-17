# 014 Investigation — Codex CLI Deep Gaps

*Research date: 2026-05-17. Agent: codex:codex-rescue. Sandbox blocked /tmp write; this file captures the agent's findings verbatim.*

## Gap 1 — Plugin Root Env Var

**Status: CONFIRMED**

Codex CLI does inject env vars into plugin-bundled hook scripts. The current docs at `developers.openai.com/codex/plugins/build` (lines 930-955) and `developers.openai.com/codex/hooks` (lines 789-808) confirm that hook scripts receive both `PLUGIN_ROOT` and `PLUGIN_DATA`. Additionally, the docs note that `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` are set for compatibility with Claude Code plugins. Source-level evidence is in `codex-rs/hooks/src/engine/discovery.rs` lines 2590-2687.

This means a Claude Code plugin's hook scripts that reference `${CLAUDE_PLUGIN_ROOT}` should work in Codex CLI without modification, or at minimum can use `${PLUGIN_ROOT}` as the direct equivalent.

## Gap 2 — Codex Agent TOML Schema

**Status: UNDOCUMENTED for plugin-bundled agents**

Custom agents are documented only at the user/project level (`~/.codex/agents/` or `.codex/agents/`), not inside plugin directories. The plugin manifest docs at `developers.openai.com/codex/plugins/build` (lines 882-900) make no mention of agents as a plugin-bundled artifact.

Known schema fields from `developers.openai.com/codex/subagents` (lines 655-695):
- Required: `name`, `description`, `developer_instructions`
- Optional: `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`, `nickname_candidates`

No per-agent `tools` or `disallowedTools` allowlist is documented — unlike Claude Code's agent format. Invocation syntax and whether `@agent-name` style addressing works is also undocumented. This is a genuine gap: if you need plugin-distributed agent definitions, you'd have to ship them as user-level config or document a manual install step.

## Gap 3 — Codex Subagent Surface Beyond User-Defined Agents

**Status: UNDOCUMENTED for plugin imperative control**

Codex does have a built-in subagent runtime with built-in types (`default`, `worker`, `explorer`), `/agent` thread management, and experimental `spawn_agents_on_csv`. However, plugin docs only cover skills, apps, MCP servers, and hooks — hooks parse but skip `agent` handlers today (`developers.openai.com/codex/hooks`, lines 739-745).

The distinction between "agents defined in a plugin" and "the Codex agent runtime" is real: Codex orchestrates subagents internally, but plugins have no documented way to imperatively request that Codex spawn subagents on their behalf. `spawn_agents_on_csv` is experimental and not surfaced through plugin APIs. Source: `developers.openai.com/codex/subagents` lines 615-645 and 770-801.

## Spec Implications

- Gap 1 is resolved (use `${PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_ROOT}` interchangeably).
- Gap 2 requires a manual agent install step or a post-install hook to place TOML files in `.codex/agents/` — or simpler, translate carrel's 2 agents to skills (chosen path in spec).
- Gap 3 means multi-agent orchestration cannot be triggered from a plugin command today — that capability lives in Codex's internal runtime only. Available at runtime for review purposes regardless of this spec.
