# 014 Investigation — Kimi CLI Gaps (#1714 + Subagent Surface)

*Research date: 2026-05-17. Agent: kimi:kimi-ask. Captures Kimi's own account of its plugin and subagent systems verbatim.*

## Gap 1 — Kimi CLI Issue #1714 (Claude-compatible local plugin layer)

Issue #1714 on the MoonshotAI/kimi-cli repository is **open** as of mid-May 2026. View at https://github.com/MoonshotAI/kimi-cli/issues/1714. No associated PR has been merged from the official team, but the feature-request author (GTC2080) has a working implementation on a fork branch and states they are willing to open a draft PR if the maintainers signal alignment.

What the issue proposes is a **v1 compatibility shim** rather than full runtime parity:

- **CLI flag**: `--plugin-dir /path/to/plugin` for session-scoped loading
- **Auto-discovery**: Plugins placed in `~/.kimi/claude-plugins/` would be picked up automatically
- **Manifest recognition**: Reads `.claude-plugin/plugin.json` to identify the plugin namespace and metadata
- **Component support (best-effort)**: `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, and `settings.json` (only the `agent` key). Hooks and MCP would remain **session-scoped only**
- **Capability summary**: A concise, model-visible summary of installed plugin skills/commands would be injected into context so the model can route to plugin capabilities without relying on a broad natural-language hard router
- **Explicit non-goals**: No marketplace/install/reload workflow, no `.lsp.json`, and no mutation of the user's persistent MCP config such as `~/.kimi/mcp.json`

The issue does **not** specify environment variables such as `${KIMI_PLUGIN_ROOT}` or `${CLAUDE_PLUGIN_ROOT}`. The closest mention of path resolution is the standard plugin practice of using plugin-relative paths inside hooks and MCP configs, but the Kimi issue text itself stays silent on how those paths would be rewritten at runtime.

Working fork: `GTC2080/kimi-cli` on branch `GTC/claude-plugin-compat`. The author reports 99 passing pytest tests, clean ruff, and clean pyright. Related discussions: #1566 (general Claude-style plugin interoperability) and #1705 (skill discovery from installed plugins). The community digest from April 2026 lists #1714 as a "hot issue," which suggests real demand, but there is no public RFC or maintainer comment explicitly committing to merge it. Safest read: a credible, code-complete community proposal awaiting maintainer buy-in.

## Gap 2 — Kimi CLI Subagent Surface: the Full Picture

**Correction to prior premise**: Kimi CLI does **not** ship fixed built-in subagent types named `coder`, `explore`, or `plan` in the way Claude Code does. Kimi has two built-in **agents** selectable at startup (`--agent`): `default` and `okabe` (an experimental agent that adds `SendDMail`). Subagents in Kimi are a user-defined, YAML-driven layer beneath those agents.

How the system actually works:

- **Defining subagents**: Users define subagents inside an agent YAML file under the `subagents` key. Each subagent points to another YAML file via `path` and carries a `description`:
  ```yaml
  subagents:
    coder:
      path: ./coder-sub.yaml
      description: "Handle coding tasks"
  ```
  The subagent file itself is a standard agent spec that typically `extend`s the parent and excludes the `Task` tool to prevent nesting loops.

- **Invocation**: Subagents are dispatched through the built-in **`Task` tool** (`kimi_cli.tools.multiagent:Task`). The caller passes `subagent_name`, a short `description`, and a detailed `prompt`. The subagent runs in an isolated context and returns its result to the parent.

- **Dynamic creation**: A **`CreateSubagent`** tool (`kimi_cli.tools.multiagent:CreateSubagent`) lets the AI define a new subagent type at runtime. It is **not enabled by default**; you must add it to the agent's `tools` list. Dynamically created subagents are persisted with the session and restored on resume.

- **Parallelism**: The official docs explicitly state that "multiple independent tasks can be processed in parallel" via the `Task` tool, and the `LaborMarket` registry inside the runtime manages the available subagent types. So yes, Kimi can orchestrate multiple subagents concurrently.

- **Per-subagent model selection**: This is the largest gap in the current surface. As of the latest public docs and source references, **there is no documented parameter on the `Task` tool to override the model for a specific subagent.** Subagents inherit the parent session's model. Community issue #6651 ("Dynamic model selection for subagents") has been filed requesting exactly this capability (18 comments, 24 up-votes as of early 2026), and third-party tools like OpenClaw have reported bugs where subagents ignore configured model overrides. In other words, forcing `kimi-k2` for one subagent and `kimi-thinking` for another is **not currently possible** through the native Kimi CLI `Task` tool.

- **Recent releases**: The changelog at https://moonshotai.github.io/kimi-cli/en/release-notes/changelog.html shows v1.39.0 shipped on 2026-04-24 with skill-scope fixes, DeepSeek reasoning-content round-tripping, and `KIMI_MODEL_THINKING_KEEP` support. By early May 2026 the latest version reported was v1.41.0. There was no single headline release that "expanded the subagent system," but incremental changes — such as PR #8954 (April 2026) propagating MCP configs to subagents and commit `ebc5cb8` adding `work_dir` override for subagent dispatch — show the subagent surface is maturing.

- **Plugin/hook docs touching subagents**: The user-facing plugin and hook documentation does **not** mention subagents specifically. Subagent configuration lives entirely in the Agent Spec/YAML layer. The repo's internal `AGENTS.md` describes `LaborMarket` as the "builtin subagent type registry" and notes that the `Agent` tool (the internal name for what users see as `Task`) persists instance metadata under `session/subagents/<agent_id>/`, but that is architectural documentation, not plugin-author guidance.

- **Conceptual distinction**: In Kimi's world, a "skill" is a markdown-based slash command (a `SKILL.md` file), not a runtime subagent. A "subagent defined in a plugin" is not yet a real category because Kimi does not natively load Claude-style plugin agents. A "subagent invoked via the Agent tool" is simply the `Task` tool dispatching to a YAML-defined subagent. There is no separate "skill that acts like a subagent" primitive; skills give the model instructions, while subagents give it an isolated context window and toolset.

## Honest Uncertainties

- Whether Issue #1714's compatibility layer would expose plugin-defined Claude agents as Kimi subagents or merely surface them as static context.
- Whether `Task` will ever accept a `model` parameter; the demand is visible in the issue tracker, but Moonshot has not published a roadmap for it.
- Environment-variable substitution for plugin roots (`${CLAUDE_PLUGIN_ROOT}`) is not mentioned in the Kimi issue, so any spec should treat path rewriting as an open implementation detail.
