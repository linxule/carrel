# Adversarial Review — Spec 013: Model Teammates

## Review metadata
- Date: 2026-04-21
- Reviewer: Codex
- Spec version: `planning/specs/013-model-teammates.md` (`Status: Proposed`, target `0.8.0`)
- Files read:
  `planning/specs/013-model-teammates.md`,
  `src/carrel/models.py`,
  `src/carrel/vault/sync.py`,
  `src/carrel/vault/scaffold.py`,
  `src/carrel/vault/dashboard.py`,
  `src/carrel/vault/templates.py`,
  `src/carrel/env/validation.py`,
  `src/carrel/vault/markers.py`,
  `skills/model-teammates/SKILL.md`,
  `commands/carrel-teammates.md`,
  `skills/environment-setup/references/interview-protocol.md`,
  `commands/carrel-setup.md`,
  `tests/test_model_teammates.py`,
  `migrations/0.7.1-to-0.8.0.md`,
  `src/carrel/policy/sensitivity.py`,
  `src/carrel/cli/setup_state.py`,
  `skills/environment-setup/SKILL.md`,
  `hooks/check-environment.js`,
  `templates/dashboard.md`,
  `CLAUDE.md`

## Executive summary
- BLOCKER: the spec promises teammate installs will reuse Carrel's sensitivity policy, but the implementation is explicitly advisory-only text; there is no teammate-aware enforcement hook in `src/carrel/policy/sensitivity.py`.
- BLOCKER: the install/auth contract is not actually verified in-repo. The Kimi block is explicitly speculative (`"example; consult upstream for current path"`), so the most failure-prone commands are currently UNVERIFIABLE.
- HIGH: setup-state cannot represent `Phase 5b`, so pause/resume collapses `5` and `5b`; the hook cannot know whether to resume at optional MCPs or model-teammates.
- MEDIUM: dashboard behavior contradicts the spec and tests codify the contradiction: the spec says hide the section when absent, but the implementation always renders `## Model teammates`.
- LOW: the feature framing improves later in the docs, but the first-contact copy still leads with model jargon and brands instead of research moves.

## Findings

### [BLOCKER] Sensitivity gating is advisory-only, not the policy-matrix reuse promised by the spec
- File: `planning/specs/013-model-teammates.md:61-62`, `skills/model-teammates/SKILL.md:191-195`, `commands/carrel-teammates.md:39-42`, `src/carrel/policy/sensitivity.py:6-18`, `src/carrel/policy/sensitivity.py:75-220`
- Quote: `The gating here is advisory in the conversation, not a hard enforcement at the tool layer.`
- Analysis: Spec 013 locked the decision that cloud-backed teammates "`respect the same policy matrix as other cloud tools`" and explicitly said this "`Reuses existing policy module; no new gate.`" The code does not do that. `src/carrel/policy/sensitivity.py` only models `ConvertTool | TranscribeTool`; there is no teammate enum, no teammate selection API, and no call site from `/carrel-teammates` or the `model-teammates` skill into deterministic policy code. If Claude ignores the skill text, or a future command variant skips the warning, HIGH-sensitivity researchers can still be walked into Codex/Gemini/Kimi installs. That is a real policy gap, not just a documentation nit.
- Recommended fix: add a deterministic teammate-policy boundary in code before shipping. Either extend `src/carrel/policy/sensitivity.py` to cover teammate installs, or add a sibling policy function such as `select_teammate_install(...)` that returns `allow / require-explicit-consent / block`. Then require `/carrel-teammates` and Phase `5b` to consult that code path before any install/writeback, and add tests for HIGH/MEDIUM/LOW behavior.

### [BLOCKER] The install/auth contract is UNVERIFIABLE in-repo, and the Kimi instructions are explicitly speculative
- File: `planning/specs/013-model-teammates.md:89`, `skills/model-teammates/SKILL.md:73-90`, `skills/model-teammates/SKILL.md:105-128`, `skills/model-teammates/SKILL.md:142-158`, `migrations/0.7.1-to-0.8.0.md:15`
- Quote: `# Install the Kimi CLI (example; consult upstream for current path)`
- Analysis: The spec says the skill should "`copy from upstream READMEs, verified 2026-04-21`", but there are no vendored upstream READMEs or pinned references anywhere under `planning/` or `skills/.../references/`. Per the review contract, that makes the CLI/plugin install commands UNVERIFIABLE from the repo. The worst case is the Kimi block, which openly admits it is an example and then still hardcodes `bun add -g @moonshot/kimi-cli`, `/plugin install kimi@kimi-marketplace`, and `/kimi:setup`. That is exactly the hallucinated-command failure mode the review was supposed to catch. The migration doc also muddies the auth contract by saying "`All three route through the researcher's existing subscription`", while the skill says Codex can also use an API key.
- Recommended fix: block shipment until each teammate's install/auth block is backed by a checked-in reference. Vendor the relevant upstream install snippets under `planning/` or `skills/model-teammates/references/`, pin the exact CLI package name and `/plugin install` slug for Codex/Gemini/Kimi, and delete speculative wording like "`or the CLI's current distribution`". If Kimi cannot be pinned yet, remove or quarantine the Kimi section for `v0.8.0`.

### [HIGH] `Phase 5b` is not representable in setup-state, so pause/resume lands on the wrong step
- File: `commands/carrel-setup.md:78-95`, `skills/environment-setup/SKILL.md:28`, `skills/environment-setup/SKILL.md:153-167`, `src/carrel/cli/setup_state.py:17`, `src/carrel/cli/setup_state.py:63-85`, `hooks/check-environment.js:361-371`
- Quote: `carrel setup-state advance --phase 5 --vault <path>`
- Analysis: `setup-state.json` only stores integer phases `4..9`. There is no representation for `5b`. The only advance call for this whole area happens after Phase `5b`, not after Phase `5`. That creates two concrete failure modes. First, if a researcher finishes optional MCPs and pauses before teammates, setup-state still says `4`, so the hook reports "`after the vault was scaffolded`" and resume starts at Phase `5`, not `5b`. Second, if a researcher gets stuck mid-teammate auth, the same collapse happens: there is no durable way to know whether MCPs were already done. The hook's label map only knows `5 => after optional MCPs`, so it literally cannot tell the user "resume at model teammates".
- Recommended fix: make `5` and `5b` distinct persisted states. Either renumber phases so teammates get their own integer, or add a subphase field to `SetupState` and teach both the hook and the environment-setup skill to resume from it. Without that, `5b` is not actually resumable.

### [MEDIUM] Dashboard visibility contradicts the spec, and the tests lock in the contradiction
- File: `planning/specs/013-model-teammates.md:128-131`, `planning/specs/013-model-teammates.md:167`, `templates/dashboard.md:21-23`, `src/carrel/vault/dashboard.py:24-30`, `src/carrel/vault/dashboard.py:161`, `tests/test_model_teammates.py:64-70`
- Quote: `Hide section entirely if no teammate state recorded (backward compat for existing vaults)`
- Analysis: The spec and acceptance criteria both say the dashboard section should be hidden when there is no teammate state. The implementation does the opposite: the template always contains `## Model teammates`, and `_render_model_teammates()` returns a proactive prompt when the dict is empty. The tests then assert that empty profiles still render the section. That is not a harmless interpretation difference; it changes first-run behavior for every existing vault. It also creates an unexplained surface split with the cheat sheet, which intentionally hides teammates until something is actually configured (`src/carrel/vault/templates.py:166-169`).
- Recommended fix: choose one behavior and align all three layers. If the spec is right, remove the section when `profile.model_teammates` is empty. If the implementation is right, update the spec, migration, and tests to say the dashboard intentionally advertises optional teammates even before any state is recorded.

### [MEDIUM] Blocked auth/install flows have no recovery contract and no partial-state cleanup
- File: `skills/model-teammates/SKILL.md:67-68`, `skills/model-teammates/SKILL.md:172-187`, `commands/carrel-teammates.md:23-25`, `commands/carrel-setup.md:91-95`
- Quote: `The researcher runs the commands; Claude guides and waits.`
- Analysis: This flow has no timeout, no rollback, no cleanup instructions, and no persisted transient state. The skill only writes `model_teammates` after install/verify succeeds, so a hung `codex login`, a blocked browser OAuth flow, or a half-finished `/plugin install` leaves Carrel with no durable record of whether the researcher is still interested, wants to defer, or needs cleanup before retrying. Combined with the `5b` setup-state gap, that means reruns can duplicate work and the resume prompt cannot distinguish "never started teammates" from "stopped halfway through auth".
- Recommended fix: define an interruption protocol in the skill/command. On abort, persist `interested` (or explicit `skipped`) immediately, never mark `configured` before verification, and document cleanup commands per teammate for retry. If you want resumable installs rather than just rerunnable installs, add a transient `pending_auth`/`pending_install` note to setup-state or another deterministic store.

### [LOW] The framing still opens with model-centric jargon in places that are supposed to lead with research moves
- File: `commands/carrel-teammates.md:7`, `skills/model-teammates/SKILL.md:8`, `skills/model-teammates/SKILL.md:14`, `skills/environment-setup/references/interview-protocol.md:9`, `skills/environment-setup/references/interview-protocol.md:58`
- Quote: `Bring other foundation models into Claude Code as agent teammates.`
- Analysis: The later tables are much better, but the top-level command/skill copy still leads with "`foundation models`", "`multi-agent workflows`", and brand names. That partially undercuts the spec's "`research moves, not model capabilities`" goal. It also rubs against the interview protocol's own rule to avoid jargon unless the researcher uses it first.
- Recommended fix: rewrite the first sentence of the command, skill, and interview beat to lead with outcomes: second opinions on arguments, long-context synthesis, delegated bug hunts, and background task handoff. Mention Codex/Gemini/Kimi only after that frame is established.

## Verdict
BLOCKED — the ship-stopper issues are the missing hard sensitivity gate and the unverifiable install/auth contract.
