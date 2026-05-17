# Spec 014 adversarial review — cross-CLI port

Review date: 2026-05-17. Scope: `planning/specs/014-cross-cli-port.md`, all six `planning/reviews/014-investigation-*.md` artifacts, `planning/specs/013-model-teammates.md`, current plugin files under `skills/`, `agents/`, `commands/`, `hooks/`, `.claude-plugin/`, and `.mcp.json`.

Method note: all source artifacts were read before this file was written. I did not browse. Any Codex CLI behavior that depends on current external docs is marked `UNVERIFIABLE — external docs required`.

## Part 1 — Claim Verification

### 1. Plugin inventory check

**Concession.** The spec's top-level inventory is mostly correct if "hooks" means hook events rather than files. The spec states: "Carrel ships as a Claude Code plugin (15 commands + 12 skills + 2 agents + 2 hooks + 0 MCP)" (`planning/specs/014-cross-cli-port.md:11`). The current manifests are minimal: `.claude-plugin/plugin.json` contains only `name`, `version`, `description`, and `author` (`.claude-plugin/plugin.json:1-8`), and `.claude-plugin/marketplace.json` points the marketplace entry at `"source": "./"` (`.claude-plugin/marketplace.json:6-16`).

`ls -1 skills` output:

```text
automation
collaborator-onboarding
convert
env-doctor
environment-setup
knowledge-wiki
model-teammates
research-partner
self-improve
transcribe
vault-ops
web-capture
```

Count: 12. This matches the spec.

`ls -1 agents` output:

```text
research-partner.md
setup-interviewer.md
```

Count: 2. This matches the spec.

`ls -1 commands` output:

```text
carrel-automate.md
carrel-batch.md
carrel-capture.md
carrel-cheatsheet.md
carrel-convert.md
carrel-feedback.md
carrel-fix.md
carrel-migrate.md
carrel-mirror.md
carrel-reflect.md
carrel-setup.md
carrel-share.md
carrel-status.md
carrel-teammates.md
carrel-transcribe.md
```

Count: 15. This matches the spec.

`ls -1 hooks` output:

```text
check-environment.js
check-version.js
hooks.json
session-reflect.js
```

Count: 4 files. This does not match the literal "2 hooks" count if the inventory rule is "count each `hooks/` entry." The current hook config does define two event registrations: `SessionStart` at `hooks/hooks.json:3-13` and `SessionEnd` at `hooks/hooks.json:15-25`.

The MCP claim is correct. The manifest has no `mcpServers` field in its full contents (`.claude-plugin/plugin.json:1-8`), and the repo-root `.mcp.json` is empty: `"mcpServers": {}` (`.mcp.json:1-3`).

**Objection.** The spec should not say "2 hooks" without specifying "2 hook event registrations." The required `ls`-based count is 4 files, while the behavior-based count is 2 configured events. The investigation artifact already made this distinction by listing "hook | 2 | SessionStart -> check-environment.js; SessionEnd -> session-reflect.js" (`planning/reviews/014-investigation-feasibility.md:16-18`) and separately noting "`hooks/` | yes | `hooks.json` + 3 `.js` scripts" (`planning/reviews/014-investigation-carrel-mapping.md:52-56`).

**Fix.** Change the inventory line to: "12 skills, 2 agents, 15 commands, 2 hook event registrations backed by 4 hook files, 0 MCP servers." This removes the count ambiguity while preserving the actual portability point.

### 2. Command classification spot-check

Random sample command output:

```text
commands/carrel-mirror.md
commands/carrel-feedback.md
commands/carrel-capture.md
```

**Concession.** The sampled labels mostly hold.

`/carrel-mirror` is labeled `UNIQUE` in the coverage map: no skill defines the five-dimension synthesis schema or `_meta/mirror/` write target (`planning/reviews/014-investigation-commands-vs-skills.md:18`). The command file supports that. It reads reflections, capability log, friction log, and vault stats (`commands/carrel-mirror.md:18-24`), synthesizes five dimensions (`commands/carrel-mirror.md:25-30`), and has a scheduled write mode to `_meta/mirror/YYYY-MM.md` (`commands/carrel-mirror.md:32-36`). Label: holds.

`/carrel-feedback` is labeled `UNIQUE`: no skill owns the feedback digest workflow or anonymization rules (`planning/reviews/014-investigation-commands-vs-skills.md:15`). The command file supports that. It reads `_meta/reflections/` and `_meta/friction_log.md` (`commands/carrel-feedback.md:17-18`), generates an anonymized digest with specific removal/retention rules (`commands/carrel-feedback.md:19-25`), and defines anonymization replacements (`commands/carrel-feedback.md:27-33`). Label: holds.

`/carrel-capture` is labeled `REDUNDANT`: the coverage map says it is a 31-line pointer and the `web-capture` skill already triggers on URLs and article-saving phrases (`planning/reviews/014-investigation-commands-vs-skills.md:12`). The command file says "Uses the `web-capture` skill" (`commands/carrel-capture.md:15-18`) and then calls `carrel capture url <url>` (`commands/carrel-capture.md:19-23`). The skill already has the same trigger set (`skills/web-capture/SKILL.md:1-4`), the same CLI call (`skills/web-capture/SKILL.md:18-24`), and the same Obsidian Web Clipper alternative (`skills/web-capture/SKILL.md:45-48`). Label: holds.

**Objection.** The spec turns the classification result into a stronger conclusion than the evidence supports. The classification artifact says REDUNDANT commands are safe to drop for non-Claude targets, but only after PARTIAL orchestration is merged into skills and UNIQUE deterministic parts are promoted to CLI (`planning/reviews/014-investigation-commands-vs-skills.md:57-61`). The spec's Phase 2 table says Codex and Kimi will "DROP" commands and "rely on skill discovery" (`planning/specs/014-cross-cli-port.md:200-208`), but the sampled `UNIQUE` commands prove that at least two current workflows are not discoverable as skills today.

**Fix.** Add explicit new skills or skill sections for `feedback`, `research-mirror`, and `session-reflection`, then keep the CLI subcommands limited to deterministic reads/writes. Do not phrase command deletion as functionally lossless until those new skill surfaces exist and are tested.

### 3. Codex CLI API claims

**Concession.** The spec now records the right categories of Codex risk: plugin root env vars, plugin-bundled agents, agent TOML schema, and subagent control. The local investigation artifact says Codex injects `PLUGIN_ROOT`, `PLUGIN_DATA`, `CLAUDE_PLUGIN_ROOT`, and `CLAUDE_PLUGIN_DATA` for plugin-bundled hooks (`planning/reviews/014-investigation-codex-deep-gaps.md:5-12`). It also says custom agents are documented only under `~/.codex/agents/` or `.codex/agents/`, not plugin directories (`planning/reviews/014-investigation-codex-deep-gaps.md:13-23`), and lists the claimed TOML fields: required `name`, `description`, `developer_instructions`; optional `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`, and `nickname_candidates` (`planning/reviews/014-investigation-codex-deep-gaps.md:19-23`).

**Objection.** These are not locally verified against current external Codex docs in this run. `UNVERIFIABLE — external docs required`: the spec's claim that `${CLAUDE_PLUGIN_ROOT}` works in Codex (`planning/specs/014-cross-cli-port.md:38-41`) depends on external docs and source paths cited inside the spec, not on files available in this repository. The locally cached Codex plugin-creator reference confirms `.codex-plugin/plugin.json` and top-level fields including `skills`, `hooks`, `mcpServers`, and `apps` (`/Users/xulelin/.codex/skills/.system/plugin-creator/references/plugin-json-spec.md:1-20`, `/Users/xulelin/.codex/skills/.system/plugin-creator/references/plugin-json-spec.md:50-67`), but it does not document `CLAUDE_PLUGIN_ROOT`, plugin-bundled agents, or the custom agent TOML schema.

`UNVERIFIABLE — external docs required`: the claim that plugin-bundled Codex agents are unsupported is plausible because the local plugin-creator manifest reference does not list `agents` among top-level plugin fields (`/Users/xulelin/.codex/skills/.system/plugin-creator/references/plugin-json-spec.md:63-67`), but absence from this scaffold reference is not proof of unsupported behavior. The stronger statement in the spec cites external docs lines (`planning/specs/014-cross-cli-port.md:43-55`), which I cannot confirm without browsing.

`UNVERIFIABLE — external docs required`: the agent TOML schema fields in the spec (`planning/specs/014-cross-cli-port.md:43-49`) match the investigation artifact (`planning/reviews/014-investigation-codex-deep-gaps.md:19-23`), but I found no local official schema file to verify them.

**Fix.** Downgrade OQ-1/OQ-2/OQ-3 from "RESOLVED" to "locally adopted from investigation; externally verify before implementation." Add a pre-implementation gate: check current Codex docs or installed source for env var injection, plugin manifest fields, and subagent schema before writing builder code.

### 4. Hard-coded Claude tool name check

**Concession.** The spec's clean-spot claim holds for tool references. A targeted grep for `allowed-tools`, `disallowedTools`, `^tools:`, `Bash(`, `Edit(`, `Read(`, `Write(`, `tool_use`, and `tool_name` across `commands/`, `agents/`, `skills/`, and `hooks/` returned no matches. The broader grep did find ordinary prose verbs, not Claude tool references: for example, `commands/carrel-mirror.md` says "Read `_meta/reflections/`" (`commands/carrel-mirror.md:18-21`), `commands/carrel-feedback.md` says "Read all files" (`commands/carrel-feedback.md:17-18`), and `skills/transcribe/SKILL.md` says "Edit the file in place" (`skills/transcribe/SKILL.md:64`). Those are workflow instructions, not hard-coded Claude tool names.

**Objection.** The relevant hard-coding is not Claude tool names; it is Claude runtime nouns and command names. Current files hard-code `CLAUDE.md` as the memory bridge (`skills/environment-setup/SKILL.md:100-143`), `/carrel-*` command names inside skills (`skills/web-capture/SKILL.md:50-54`, `skills/environment-setup/SKILL.md:201-202`), Claude Desktop scheduling (`skills/environment-setup/SKILL.md:195-202`), and `${CLAUDE_PLUGIN_ROOT}` in the migration command (`commands/carrel-migrate.md:11-24`) and hooks (`hooks/hooks.json:8-22`).

**Fix.** Keep the "no Claude tool-name hard-coding" claim, but add a separate "Claude runtime language and memory-file hard-coding" checklist. That checklist is more important for the port than `Bash`/`Edit`/`Read`/`Write`.

## Part 2 — Design Challenge

### 5. Two-phase split analysis

**Concession: strongest argument for collapsing v0.9.0 + v0.10.0.** The Codex investigation says a Codex CLI port is "feasible, single-phase port viable" (`planning/reviews/014-investigation-feasibility.md:51-62`). The spec itself says Phase 1 no longer needs `${CLAUDE_PLUGIN_ROOT}` cleanup for Codex compatibility because Codex allegedly honors it (`planning/specs/014-cross-cli-port.md:38-42`). If the immediate user value is "make Carrel usable in Codex," then shipping a host-independent refactor first creates a release where no new host works, while the riskiest UX change, dropping commands for Codex/Kimi, remains untested until the next release.

**Objection: strongest argument for keeping them split.** The command migration is not a packaging chore. It changes where workflow authority lives. The spec proposes eight new CLI surfaces (`planning/specs/014-cross-cli-port.md:124-138`), skill updates (`planning/specs/014-cross-cli-port.md:139-150`), and about 26 new tests (`planning/specs/014-cross-cli-port.md:152-156`) before the host builder even exists. Spec 013 is a useful reference here: it shipped a small, coherent vertical slice, with the final shape explicitly trimmed to "interview beat + Phase 5b + profile field + skill + command + one dashboard line" and six tests (`planning/specs/013-model-teammates.md:54-62`). Spec 014 is much larger; splitting reduces review blast radius.

**Fix / verdict.** Keep the phases split, but change the phase boundary. Phase 1 should not claim "all command logic -> CLI" (`planning/specs/014-cross-cli-port.md:30`). It should first create a cross-host command-replacement inventory: which parts become CLI, which become skills, and which remain Claude-only ergonomics. Phase 2 should then build adapters against that canonical inventory. Shipping both phases together would hide UX regressions and make byte-compat failures harder to attribute.

### 6. "Drop commands, rely on skill discovery" — UX viability

**Concession.** The direction is viable for low-risk wrappers. `/carrel-capture` already delegates to `web-capture` (`commands/carrel-capture.md:15-23`), and the `web-capture` skill already exposes matching triggers and the same `carrel capture url` operation (`skills/web-capture/SKILL.md:1-4`, `skills/web-capture/SKILL.md:18-24`). Dropping that command in Codex/Kimi is a manageable UX downgrade.

**Objection.** The spec does not acknowledge at least two concrete failure scenarios:

1. Muscle-memory and document residue. The spec says non-Claude users should use natural language or direct bash rather than slash commands (`planning/specs/014-cross-cli-port.md:229-233`), but current skills and templates still tell users to run slash commands. `environment-setup` says interested users should run `/carrel-automate` (`skills/environment-setup/SKILL.md:195-202`), `web-capture` says `/carrel-capture` triggers the skill (`skills/web-capture/SKILL.md:50-54`), and the setup skill points to `/carrel-share` and `/powerup` in generated `CLAUDE.md` guidance (`skills/environment-setup/SKILL.md:131-136`). A Codex/Kimi user can be handed commands their host does not support.

2. Unique workflows become undiscoverable. The command map says `/carrel-feedback`, `/carrel-migrate`, `/carrel-mirror`, and `/carrel-reflect` are UNIQUE (`planning/reviews/014-investigation-commands-vs-skills.md:15-19`, `planning/reviews/014-investigation-commands-vs-skills.md:27-29`). The spec's Phase 1 "Skill updates" mentions only "4 PARTIAL skills" (`planning/specs/014-cross-cli-port.md:139-140`), but these UNIQUE workflows need new skill homes, not just CLI subcommands. A user saying "give me a mirror" will not reliably load a nonexistent `research-mirror` skill.

**Fix / assessment.** This is a manageable gap, not a fatal flaw, if the spec adds a host-specific UX audit and explicit new skills for the unique workflows. It becomes fatal only if Phase 2 ships with commands dropped while generated docs, skills, and cheat sheets still mention `/carrel-*` as the primary interaction model.

### 7. Architecture layer violations

**Concession.** The spec is right to use the three-layer rule as the organizing principle. It states the rule directly: Phase 1 aligns commands with "skills = judgment, CLI = ops, transports = thin" (`planning/specs/014-cross-cli-port.md:18-21`). The command-coverage investigation reaches the same architecture: "intellectual logic" belongs in skills, "mechanical logic" in CLI (`planning/reviews/014-investigation-commands-vs-skills.md:57-61`).

**Objection.** The proposals break that rule in three places.

First, the locked decision says "Translate all command logic -> `carrel <subcmd>`" (`planning/specs/014-cross-cli-port.md:27-31`). That is too broad. `/carrel-mirror` contains intellectual synthesis across Reading, Creating, Recurring themes, Friction patterns, and Trajectory (`commands/carrel-mirror.md:25-30`). Moving "all command logic" into `carrel vault mirror --write` would put judgment in the CLI. The fix is to put the schema and interpretation in a skill and only put deterministic file append/write behavior in CLI.

Second, `/carrel-feedback` anonymization is framed as deterministic, but current rules include judgment about "specific research content" and what is safe to keep (`commands/carrel-feedback.md:19-33`). That is not purely mechanical unless the spec defines a concrete transformation algorithm. The CLI can assemble source files and write a draft; the skill should own researcher review and ambiguous redaction.

Third, the memory-file plan is under-specified. The spec lists memory-file handling as optional per-host output (`planning/specs/014-cross-cli-port.md:200-211`) and leaves OQ-7 open (`planning/specs/014-cross-cli-port.md:101-102`), but current setup treats `CLAUDE.md` as "critical" because Claude loads it every session (`skills/environment-setup/SKILL.md:100-143`) and later declares `environment.json` the structured truth while `CLAUDE.md` is the narrative truth (`skills/environment-setup/SKILL.md:229`). A cross-CLI port that leaves this as optional breaks the transport-thin rule: host memory conventions are transport concerns, but the current skill embeds a Claude-specific transport.

**Fix.** Replace "all command logic -> CLI" with a three-column migration table: `skill judgment`, `CLI deterministic operation`, `host wrapper/transport`. Make `CLAUDE.md`/`AGENTS.md`/Kimi memory handling part of the host adapter contract, not an optional afterthought.

### 8. Biggest hidden assumption + missing edge case

**Concession.** The hidden assumption is visible and understandable: if skills are sufficiently descriptive, agents will infer the right workflow from natural-language requests. The spec makes this explicit by saying non-Claude users invoke via natural language or direct bash (`planning/specs/014-cross-cli-port.md:229-233`) and mitigates Codex command loss by documenting phrasings in the Codex README (`planning/specs/014-cross-cli-port.md:243-244`).

**Objection.** The biggest hidden assumption is that skill discovery is behaviorally equivalent to command invocation. It is not. Commands provide a stable, user-visible, documented handle; skills provide a probabilistic routing surface. That assumption is most dangerous for setup, migration, reflection, and automation because those flows have state transitions, safety gates, or scheduled/headless modes. The command map explicitly warns that PARTIAL commands add state-tracking discipline, safety gates, and unattended-mode contracts that are easy to skip without checklist structure (`planning/reviews/014-investigation-commands-vs-skills.md:9-11`, `planning/reviews/014-investigation-commands-vs-skills.md:57-59`).

The most important missing risk is generated and embedded slash-command residue. Current files contain many `/carrel-*` references outside `commands/`: `environment-setup` points users to `/carrel-automate` (`skills/environment-setup/SKILL.md:195-202`), `automation` documents `/carrel-automate`, `/carrel-batch`, and `/carrel-mirror` as related command surfaces (`skills/automation/SKILL.md:421-457`), and `web-capture` names `/carrel-capture` as the trigger (`skills/web-capture/SKILL.md:50-54`). Dropping commands in Codex/Kimi without rewriting these strings creates broken in-product instructions.

**Fix.** Add a "host-specific command residue" test: build each target, grep its emitted files for `/carrel-`, `CLAUDE.md`, `Claude Desktop`, `${CLAUDE_PLUGIN_ROOT}`, `/plugin`, and `/reload-plugins`, then whitelist only intentional compatibility text.

### 9. Locked vs. open decisions audit

**Concession.** The locked decisions are clear and reviewable. The table locks six decisions: single repo/build per host, build-time adapter only, `carrel build` in the main CLI, aggressive command translation, Phase 1 before Phase 2, and byte-for-byte Claude Code reproduction (`planning/specs/014-cross-cli-port.md:23-33`).

**Objection + fix per decision.**

1. Single repo, build per host (`planning/specs/014-cross-cli-port.md:27`): keep locked. The current repo already relies on one plugin source tree with default discovery (`planning/reviews/014-investigation-carrel-mapping.md:47-60`), and spec 013 benefited from keeping the final surface small and centralized (`planning/specs/013-model-teammates.md:54-62`).

2. Build-time only (`planning/specs/014-cross-cli-port.md:28`): keep locked, with one caveat. The Python core should stay host-agnostic, but emitted skills are host-facing artifacts, so build-time substitution must cover memory-file names and command wording, not just manifest shape.

3. `carrel build` in the main CLI (`planning/specs/014-cross-cli-port.md:29`): re-open lightly. It is discoverable, but putting plugin packaging in the main researcher-facing CLI risks expanding support surface. If kept, hide it under a contributor-oriented group such as `carrel plugin build` or document it as maintainer tooling.

4. Translate all command logic to CLI (`planning/specs/014-cross-cli-port.md:30`): re-open. This violates the architecture rule for mirror/feedback/reflection judgment. The command map recommends CLI for deterministic parts and skills for synthesis/reflection prompts (`planning/reviews/014-investigation-commands-vs-skills.md:46-49`), not blanket CLI migration.

5. Phase 1 before Phase 2 (`planning/specs/014-cross-cli-port.md:31`): keep locked, but make Phase 1 an architecture and UX normalization release, not just a CLI-subcommand extraction release.

6. Byte-for-byte reproduction required (`planning/specs/014-cross-cli-port.md:32`): re-open because the spec contradicts itself. Phase 1 deliberately changes all 15 command files into wrappers (`planning/specs/014-cross-cli-port.md:141-148`). Phase 2 then says the Claude build must be byte-identical "sans the soon-deleted command files" (`planning/specs/014-cross-cli-port.md:215`). "Byte-for-byte" and "sans soon-deleted command files" cannot both be true against the current v0.8.1 tree. This is especially important because current commands contain substantive content, not just wrappers; `/carrel-mirror` alone defines the five-dimension synthesis schema (`commands/carrel-mirror.md:25-30`).

**Fix.** Replace byte-for-byte compatibility with two explicit baselines: (a) v0.8.1 source-tree compatibility before Phase 1, expected to fail only in approved command files; (b) post-Phase-1 Claude build determinism, expected to be byte-identical to the canonical Phase 1 plugin source. Test both, but do not pretend Phase 2 can reproduce pre-Phase-1 bytes after Phase 1 intentionally rewrites commands.

### 10. Agent-to-skill translation

**Concession.** The "both could become skills without losing much" claim (`planning/specs/014-cross-cli-port.md:52-55`) is directionally true for static instruction content. Both agents use minimal frontmatter: `name`, `description`, `model: inherit`, and `color` (`agents/research-partner.md:1-11`, `agents/setup-interviewer.md:1-11`). The investigation artifact also says neither agent uses tool allowlists, memory, background mode, or isolation (`planning/reviews/014-investigation-carrel-mapping.md:79-87`).

For `research-partner`, most content ports cleanly: identity and principles (`agents/research-partner.md:13-28`), must-do items like reading `CLAUDE.md` and searching the vault (`agents/research-partner.md:29-36`), engagement patterns (`agents/research-partner.md:45-69`), and vault-awareness rules (`agents/research-partner.md:71-87`).

For `setup-interviewer`, most content also ports: adaptive interview principles (`agents/setup-interviewer.md:21-28`), required outputs (`agents/setup-interviewer.md:29-35`), conversation flow (`agents/setup-interviewer.md:45-72`), sample dialogue (`agents/setup-interviewer.md:73-106`), and context-awareness (`agents/setup-interviewer.md:108-110`).

**Objection.** "Can become skills cleanly" is too strong unless the spec names the concrete losses and rewrites call sites.

For `research-partner`, the concrete loss is the `@research-partner` agent handle and dedicated role boundary (`agents/research-partner.md:13`). A skill can preserve the instructions, but it does not automatically preserve a subagent-like invocation boundary or a separate conversational mode. The content also assumes `CLAUDE.md` (`agents/research-partner.md:31`), which is not host-neutral.

For `setup-interviewer`, the concrete loss is more operational. `environment-setup` currently says "Deploy the `@setup-interviewer` agent for a conversational interview, or follow the protocol ... directly" (`skills/environment-setup/SKILL.md:36-40`). If the agent becomes a skill, that call site must be rewritten; otherwise Codex/Kimi users get an instruction to deploy an agent that the plugin does not bundle. The setup agent also owns a carefully constrained interview persona, including "Never say MCP, CLI, API, markdown, or configuration unless the researcher uses these words first" (`agents/setup-interviewer.md:21-28`) and a long opening script (`agents/setup-interviewer.md:47-50`). That is portable as prose, but only if the setup skill makes it the active mode rather than a reference the main agent may ignore.

**Fix.** Translate each agent into a host-neutral skill plus rewrite every caller:

- `research-partner` -> `skills/research-partner/SKILL.md` remains the intellectual-engagement mode, but replace `CLAUDE.md` with a host memory abstraction.
- `setup-interviewer` -> either fold into `environment-setup` as the primary interview section or create a `setup-interviewer` skill and update `environment-setup` line 38 to invoke that skill, not `@setup-interviewer`.
- Add a regression grep that no Codex/Kimi build contains `@setup-interviewer`, `@research-partner`, or "Deploy the agent" language unless the target actually supports plugin-bundled agents.

## Summary

Top 3 concrete fixes the spec needs:

1. Replace "Translate all command logic -> CLI" with a command-by-command migration table separating skill judgment, deterministic CLI operations, and host wrapper text.
2. Add a host-specific residue audit for `/carrel-*`, `CLAUDE.md`, `${CLAUDE_PLUGIN_ROOT}`, Claude Desktop scheduling, and `@agent` references in every emitted non-Claude build.
3. Rewrite the byte-for-byte compatibility requirement into two baselines: approved Phase 1 source changes against v0.8.1, then deterministic byte identity against the post-Phase-1 canonical Claude build.

Top 1 design challenge that warrants reconsideration:

The spec underestimates how much slash commands function as stable UX handles, not just wrappers. The sampled commands show the split: `/carrel-capture` is safely redundant, while `/carrel-feedback` and `/carrel-mirror` are currently the only named homes for important workflows. Skill discovery can replace commands only after the same names, prompts, safety gates, and generated docs are re-homed. Otherwise the port works architecturally but feels unreliable at the exact moments researchers need the most determinism: setup, migration, automation, reflection, and sharing.

Overall verdict: proceed with revisions.
