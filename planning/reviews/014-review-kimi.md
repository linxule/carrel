# Review 014 — Cross-CLI Port: Kimi Second-Pair-of-Eyes

**Reviewer**: Kimi (via Claude Code / kimi:review, model sonnet-4-6 acting on Kimi's behalf with full Kimi CLI knowledge)
**Date**: 2026-05-17
**Spec**: `planning/specs/014-cross-cli-port.md`
**Investigation inputs**: `014-investigation-feasibility.md`, `014-investigation-kimi-gaps.md`, `014-investigation-commands-vs-skills.md`
**Cross-check**: `014-review-codex.md`

---

## 1. Kimi-Specific Claims Audit (OQ-4 and OQ-5)

### OQ-4 — #1714 status claims

All material claims in OQ-4 are accurate and consistent with the investigation artifact (`014-investigation-kimi-gaps.md`):

- Issue open, no maintainer PR, community fork (GTC2080/kimi-cli@GTC/claude-plugin-compat) has 99 passing tests — confirmed.
- Session-scope limitation on hooks and MCP — confirmed. This is a genuine design constraint in the proposal, not speculation.
- No `${KIMI_PLUGIN_ROOT}` or `${CLAUDE_PLUGIN_ROOT}` honoring documented — confirmed. The issue text is silent on env var path rewriting.
- "Best-effort" reading of `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `settings.json` (`agent` key only) — confirmed.

One precision issue: OQ-4 says "capability summary injected into model context for skill/command routing." The investigation source says "A concise, model-visible summary of installed plugin skills/commands." The mechanism for how this summary drives routing is unspecified in the issue — it may be context injection but could also be a tool registry update. The spec should not present routing fidelity as guaranteed behavior; it is the key uncertain outcome.

### OQ-5 — Kimi subagent surface claims

The OQ-5 correction is well-founded and important. The prior erroneous claim about `coder`/`explore`/`plan` built-in subagent types has been removed. The actual surface described is accurate:

- Two built-in agents (`default`, `okabe`) at startup — confirmed.
- Subagents are user-defined YAML under the `subagents:` key of a parent agent spec — confirmed.
- `Task` tool dispatches to subagents; `CreateSubagent` is opt-in — confirmed.
- No per-subagent model selection today; issue #6651 tracks the demand — confirmed.
- Plugin/hook docs do not connect to subagent surface — confirmed.

**One gap in OQ-5 the spec does not surface**: the `Task` tool dispatches to a named subagent (`subagent_name`). This name must exist in the parent agent's `subagents:` registry at session start. There is no mechanism for a plugin to inject new named subagent types into a running session's `LaborMarket` without either `CreateSubagent` (opt-in, not enabled by default) or a custom agent YAML that the user loads via `--agent`. This means even if #1714 ships and plugin-defined Claude agents become visible as subagent descriptions, they cannot be invoked via `Task` unless the session was started with a parent agent that lists them under `subagents:`. This is a deeper integration barrier than the spec acknowledges.

---

## 2. Kimi Build Plan Stress Test (Phase 2 Transformation Table)

### Install script copying skills to `~/.kimi/skills/carrel-<name>/`

This plan has two concrete failure modes:

**Failure mode A — Kimi's skill scanner does not recursively find skills in subdirectories named with a prefix.**

Kimi discovers SKILL.md files from paths explicitly configured in `~/.kimi/config.toml` under `[skills]` or from standard paths like `~/.kimi/skills/<name>/SKILL.md`. The spec assumes that copying to `~/.kimi/skills/carrel-environment-setup/SKILL.md` will be auto-discovered. This is likely correct for user-global discovery — the path pattern matches what Kimi reads — but the spec does not confirm this experimentally or cite a source. If Kimi requires explicit registration of each skill path in `config.toml`, the install script must also patch `config.toml`, not just copy files. That is a substantially more invasive operation.

**Failure mode B — Natural language routing to skills is not reliable for 12 skills with similar domain vocabulary.**

When a Kimi user types "set up my vault," the model must:
1. Know that a skill named `carrel-environment-setup` exists (via discovery).
2. Match the intent to that skill rather than to `carrel-vault-ops`, `carrel-automation`, or no skill.
3. Invoke the skill correctly.

Kimi has no `/skill:name` hard invocation surface analogous to Claude Code's `/carrel-setup` command. The #1714 proposal injects a "capability summary" into context, but the routing quality depends entirely on how that summary is written and how well the model's intent-matching works across 12 similarly-named carrel skills. This is genuinely probabilistic. For low-stakes tasks ("convert this PDF"), probabilistic routing is acceptable. For setup and migration — which have phase-gated state transitions — a misfire that runs vault-ops instead of environment-setup could leave setup-state.json in an inconsistent state. The spec's mitigation ("document natural-language phrasings in the Kimi build's README") is necessary but not sufficient; the README is read once, not consulted per session.

**Failure mode C — The install script itself is a maintenance liability.**

A script that copies 12 directories, patches TOML, and documents its own uninstall (`rm -rf ~/.kimi/skills/carrel-*`) is the right short-term approach, but it will drift from the canonical source with every skill rename or addition. The spec needs an explicit contract: `carrel build kimi` regenerates and re-executes the install script; there is no "update in place" path short of re-running the build.

### Hooks as TOML snippet for `~/.kimi/config.toml`

The spec's Phase 2 table says the Kimi build emits "kimi-hooks.toml snippet + handlers + install instructions." This is honest about the friction: the user must manually paste a TOML block and place handler scripts somewhere on PATH or at a fixed path. The hooks investigation artifact confirms Kimi's 13 hook events use user-global TOML only, not plugin-scoped registration.

Two problems the spec understates:

1. **`SessionStart` is the most valuable hook for carrel** (environment drift check, setup-state resume prompt). Kimi does have a session-start hook event. But the handler script path in `config.toml` must be an absolute path or a path resolvable from the user's shell env. The build script cannot know this at build time; it must interpolate `$HOME` or ask the user. The spec says "emit install instructions" — this is the right call, but the instructions must be concrete enough to not require user judgment.

2. **`session-reflect.js` emits structured JSON** (`{code, severity, next_commands, next_skills, can_bypass}`) that Kimi does not parse. OQ-6 covers this as an open question. For the Kimi build, the practical answer is option (a): degrade to plain stderr. But this means the Kimi SessionEnd hook does less than the Claude Code one by design — the spec should say this explicitly in the transformation table rather than leaving it in OQ-6.

---

## 3. #1714 Merge Forecast

**Probability estimate: 25–30% in the next 6 months.**

Reasoning:
- The working fork has passing tests and clean lints — implementation barrier is low.
- The issue is marked "hot" in the April 2026 community digest — demand signal is real.
- But: no maintainer comment, no RFC, no draft PR opened by the fork author despite code being ready. When a community contributor with a code-complete fork has not opened a draft PR, the usual reason is lack of maintainer signal. Moonshot's public roadmap does not list plugin interoperability.
- The proposed feature is non-trivial to maintain: best-effort reads of a competing tool's manifest schema with session-scoped-only semantics create a long-tail support surface.
- Six months is a short horizon for this class of change.

**If it merges (30% path):** The spec should add `carrel build kimi-compat` as a v0.10.0 deliverable, not a v0.11+ future. The kimi-compat builder reuses most of the Claude Code builder with path rewriting. The session-scope limitation on hooks means the kimi-compat and kimi-native builds have different hook semantics — document this explicitly in the user-facing README of the kimi-compat build.

**If it does not merge (70% path):** The spec's current hedge is correct: build assuming native Kimi plugin system, add kimi-compat as a future target. No change needed.

**Recommended spec change regardless of merge probability:** Add a `#1714-watch` item to the Phase 2 implementation checklist. Before `carrel build kimi` ships, re-check issue status. If a PR has opened, delay Kimi native build for 4 weeks to see if compat layer lands — the compat path is lower maintenance long-term.

---

## 4. Agents as Kimi Subagent YAML — Should Carrel's 2 Agents Become This?

**Verdict: No. Skill conversion is the right call. Subagent YAML is an optional future layer, not the Phase 2 path.**

Tradeoffs in detail:

**Arguments for subagent YAML:**
- `setup-interviewer` is genuinely a separate context window concern — it needs to maintain conversational state across a multi-turn interview without the main agent's vault context bleeding in.
- `research-partner` benefits from isolated toolset configuration.
- Kimi's `Task` tool with subagents gives structured dispatch and result return — closer to Claude Code's `@agent` invocation semantics than a skill is.

**Arguments against (why skills win for Phase 2):**
- Plugin-defined agents are not a Kimi primitive. A subagent YAML must be part of a parent agent YAML's `subagents:` list. The parent agent must be the one the user starts with (`--agent`). A plugin cannot inject into an existing `default` agent's subagent registry without `CreateSubagent` (opt-in, not default).
- Even if #1714 ships, it explicitly lists "plugin-defined Claude agents" as best-effort context injection, not as callable `Task` subagents.
- The subagent YAML approach would require the Kimi build to ship: (a) a parent agent YAML override for `default`, (b) two subagent YAML files, (c) install instructions that configure `--agent` to use the override. This is more invasive than install script + skill copy.
- Per-subagent model selection is not available (issue #6651 open). `setup-interviewer` currently uses `model: inherit`, which is fine — but if future carrel versions want `kimi-thinking` for the setup interview, subagent YAML would still not support it.

**Correct future path:** After #6651 ships (per-subagent model selection), revisit. At that point, a `carrel build kimi-subagents` target that emits a default-agent override YAML with carrel-setup-interviewer and carrel-research-partner subagents becomes meaningful. Until then, skills.

The spec's v0.11+ optional target "Kimi subagent YAML target" is correctly positioned. No change needed there.

---

## 5. Architecture Pushback — Build Pipeline vs Runtime Host Detection

**The spec's build-time-only approach is correct. The alternative (runtime host detection in Python core) is worse for carrel's specific constraints.**

Argument for runtime detection (the alternative):
- Single install: `pip install carrel` or `uv add carrel`, one command works on all hosts.
- No `carrel build <host>` step for contributors.
- Host-specific behavior auto-adjusts when the user switches CLIs without reinstalling.
- Simpler release process: one artifact per version, not three.

Why build-time wins for carrel:

1. **Carrel's core is deliberately host-agnostic.** The CLAUDE.md design rule "No AI imports: Core library is deterministic. AI lives in the transport/skill layer" is load-bearing. Runtime host detection would require the Python core to import or probe host-specific APIs — this is a coupling the spec correctly refuses.

2. **The portability surface is in skill and manifest files, not Python code.** Most of the per-host adaptation is in the shape of SKILL.md frontmatter, hook registration TOML vs JSON, manifest field names, and install script logic. These are text transformations — exactly what a build step does cleanly. A runtime approach would require the Python CLI to emit different text files depending on what CLI it detects in the PATH, which is fragile (what if both Claude Code and Kimi are installed?).

3. **Inspectability.** A built plugin is a directory the user can read and debug. Runtime detection produces behavior that depends on which CLI happens to be active at invocation time — harder to reason about.

4. **The "single adaptive plugin" approach would likely converge on the Claude Code shape** since that is the most capable host, degrading gracefully on others. But Kimi's install script and TOML hook registration are not degradations of the Claude build — they are genuinely different artifacts that do not share file formats.

**One concession to the alternative:** The spec should add a `carrel build --detect` mode that inspects the user's PATH and emits the right build automatically. This is a UX convenience, not a runtime detection architecture. It runs at install time, not at session time.

---

## 6. Phase Ordering — Argue for Collapsing Phase 1 + Phase 2

**Verdict: Keep the phases split. The collapse argument is weaker than it appears.**

The strongest collapse argument: Phase 1 ships a refactor with no new user capability. Users of Claude Code see identical behavior (commands become wrappers, work identically). Users who want Codex or Kimi see nothing new until Phase 2. The "standalone value" claim for Phase 1 is architectural, not user-facing. Why not just do both at once?

Why split is still right:

1. **Phase 1's 26 new tests stress the new CLI subcommands before the build pipeline depends on them.** The 8 new subcommands (`carrel feedback export`, `carrel migrate run`, `carrel vault mirror --write`, etc.) are the load-bearing foundation for Phase 2's skill instructions. If those subcommands have bugs, Phase 2's Kimi and Codex builds will exhibit them in ways harder to diagnose than a clean Phase 1 failure.

2. **The backward-compat baseline must be established before Phase 2.** The spec requires `carrel build claude-code` to reproduce the current shipped plugin byte-for-byte (modulo Phase 1 command changes). This baseline can only be established after Phase 1 stabilizes — you cannot run a byte-diff against a moving target.

3. **Collapse risk is asymmetric.** If Phase 1 and Phase 2 ship together and the Kimi install script has a bug, the rollback takes down the Phase 1 CLI improvements too. Split phases let you revert Phase 2 independently.

4. **Codex reviewer (item 5) already made the strongest collapse argument** and concluded "keep split but change Phase 1's scope." This is the right answer: Phase 1 should be explicitly scoped as "architecture normalization + UX skill absorption" rather than just "CLI subcommand extraction." That reframe makes Phase 1 user-visible (skills get richer, commands become thinner wrappers that are easier to read) without collapsing the timeline.

**Recommended spec edit:** Rename Phase 1 from "Architecture normalization" to "Architecture normalization + skill enrichment" and explicitly list the 4 PARTIAL skill absorptions (environment-setup, automation, collaborator-onboarding, convert+transcribe+automation) as Phase 1 deliverables alongside the 8 CLI subcommands.

---

## 7. Cross-Check Against Codex Review Findings

### (a) Command count of 15 — Codex initially flagged, verified correct

**Concur.** The `ls -1 commands/` output in the Codex review counts 15 files. The claim is correct. No issue.

### (b) `${CLAUDE_PLUGIN_ROOT}` unverified in Codex

**Partial concur, with a Kimi-specific addendum.**

The Codex review correctly flags this as "UNVERIFIABLE — external docs required" from within the repo. The investigation artifact (`014-investigation-codex-deep-gaps.md`) cites external source lines, which Codex could not verify without browsing. This is a legitimate caution flag.

However, from a Kimi-specific perspective: the spec correctly notes that `${CLAUDE_PLUGIN_ROOT}` is not documented in the Kimi #1714 issue and should not be assumed for Kimi compat. The Kimi build plan does not depend on this env var — the install script approach sidesteps it entirely. So for the Kimi build, this is not a blocker regardless of whether Codex honors it. The Codex review's caution is appropriate for the Codex build; for Kimi it is already handled.

**Recommended spec edit:** Add a pre-implementation gate in Phase 2: before writing the Codex builder, run `codex plugin install` on a test plugin and grep the injected env for `CLAUDE_PLUGIN_ROOT`. This is a 10-minute empirical check that resolves the "UNVERIFIABLE" flag without depending on external docs.

### (c) Skill-discovery fallback is hand-wavy

**Concur, and strengthen the finding.**

The Codex review says the spec does not acknowledge concrete failure scenarios for "rely on skill discovery." Section 2 of this review details two Kimi-specific failure modes (TOML registration requirement, probabilistic routing for state-transition workflows). The Codex review adds a third: generated docs still contain `/carrel-*` references that Codex/Kimi users will be instructed to run but cannot.

Together, these findings constitute a blocker-class gap: the spec cannot ship Phase 2 with commands dropped and skill discovery as the replacement without (a) confirming Kimi skill auto-discovery mechanics empirically, (b) auditing all `/carrel-*` references in emitted files, and (c) adding deterministic invocation paths for setup/migration/automation workflows. The Codex review's fix — "add a host-specific command residue test that greps emitted files" — is the right mitigation. Adopt it.

### (d) `setup-interviewer` agent → skill conversion loses state-machine logic

**Concur, with a Kimi-specific dimension.**

The Codex review details the concrete losses: `@setup-interviewer` invocation handle, call sites in `environment-setup` that must be rewritten, the carefully constrained interview persona that could be ignored without the agent boundary.

The Kimi-specific addition: the `setup-interviewer` agent's value is not just its instructions — it is the isolated context window. When `environment-setup` skill invokes `@setup-interviewer` in Claude Code, the interview happens in a subcontext without the researcher's full vault history. In Kimi, a skill calling another skill is still the same context window. This means the setup interview in Kimi will have the researcher's full session history in scope, which can break the interviewer's "no jargon" persona if the session already contains technical vocabulary. This is a UX regression, not a catastrophic failure — but it should be documented.

**Recommended spec edit:** Add to the agent-to-skill translation section: "For hosts without isolated subagent invocation (Kimi native build), the setup interview runs in the main context window. The skill should instruct the model to treat the interview as a fresh context by not referencing prior conversation history." This is a soft guardrail, not a hard fix, but it acknowledges the regression.

---

## Summary

**Top design challenge:** The skill-discovery path for state-transition workflows (setup, migration, automation) is probabilistic and cannot substitute for commands without deterministic invocation paths and an audit of all `/carrel-*` residue in emitted Kimi build files.

**Top Kimi-specific risk:** The `~/.kimi/skills/carrel-<name>/` install approach may require patching `~/.kimi/config.toml` to register each skill path explicitly, not just file copy — and this is unconfirmed. If Kimi requires explicit config registration, the install script is substantially more invasive and the uninstall story ("rm -rf + manually revert config") is fragile. This must be empirically verified before Phase 2 Kimi builder code is written.

**Verdict: Proceed with revisions.**

The architecture is sound. The two-phase split is correct. The Kimi-specific claims in OQ-4 and OQ-5 are accurate. The three items that must be addressed before implementation:

1. Empirically confirm Kimi skill auto-discovery behavior (file copy sufficient vs config registration required) — this gates the Kimi builder design.
2. Add a host-specific residue audit (grep emitted files for `/carrel-*`, `CLAUDE.md`, `@setup-interviewer`, `Claude Desktop`) to the Phase 2 CI pipeline.
3. Rename Phase 1 to include skill enrichment (absorb PARTIAL commands into skills) as a named deliverable, not just CLI subcommand extraction.

None of these require rethinking the architecture. All three are specification additions, not reversals.
