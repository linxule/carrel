# Review: 004 Scheduled Automation and Shared Agency

## Verdict

This spec is interesting, and the `ResearcherProfile` change itself is compatible with the current codebase, but the overall v0.4 package is not implementation-ready. The main problems are not in `src/carrel/models.py`; they are in the operational contract around scheduling, state, approval, and the meaning of "shared agency." Right now the spec mixes three different products into one release: scheduled maintenance, background batch execution, and autonomous analytical collaboration (`planning/specs/004-scheduled-automation-and-shared-agency.md:47-49`, `planning/specs/004-scheduled-automation-and-shared-agency.md:492-507`).

## Findings

### 1. "Existing commands unchanged" and "existing skill behavior unchanged" are contradicted by the rest of the spec

The spec says "all 9 current commands unchanged" and "existing skill behavior ... continue to work identically in interactive mode" (`planning/specs/004-scheduled-automation-and-shared-agency.md:451-454`). That is not true as written.

- `/carrel-setup` would gain an automation offer during setup (`planning/specs/004-scheduled-automation-and-shared-agency.md:100`, `planning/specs/004-scheduled-automation-and-shared-agency.md:235-246`), but the current command is an 8-phase onboarding flow with no automation phase (`commands/carrel-setup.md:15-61`).
- The spec explicitly changes `vault-ops` and `research-partner` (`planning/specs/004-scheduled-automation-and-shared-agency.md:248-275`), and it extends `convert`/`transcribe` with batch orchestration logic (`planning/specs/004-scheduled-automation-and-shared-agency.md:71`). That is a behavior change, not "identical in interactive mode."

This matters because the current architecture treats commands as thin conversational wrappers and skills as the judgment layer (`CLAUDE.md:20-27`, `commands/carrel-convert.md:15-23`, `skills/convert/SKILL.md:8-21`).

### 2. The governing principle conflicts with the proposed autonomous actions

The philosophy section says autonomous analytical work must be "a prompt for human thinking, never a fait accompli" (`planning/specs/004-scheduled-automation-and-shared-agency.md:21`). But the reorganization table authorizes the agent to file new items automatically and, in "full collaborative," to "move, rename, or reorganize existing files" (`planning/specs/004-scheduled-automation-and-shared-agency.md:327-328`).

That is not just prompting. That is delegated action on the vault. It also cuts against the current vault-ops rule to "never overwrite without asking" (`skills/vault-ops/SKILL.md:178-184`). If the overnight agent acts first and explains in the brief later, the human is no longer deciding before the action.

### 3. The prompt rules contradict full-collaborative mode

The generated prompt says "Never modify researcher's notes, papers, or drafts" (`planning/specs/004-scheduled-automation-and-shared-agency.md:223-228`). The "full collaborative" level says the agent can "move, rename, or reorganize existing files" (`planning/specs/004-scheduled-automation-and-shared-agency.md:328`).

Those two statements cannot both be true. Moving and renaming notes or papers is modifying them at the filesystem level.

### 4. `/carrel-automate` breaks the existing `environment.json` / `CLAUDE.md` sync contract

Current Carrel has an explicit two-track truth model: `environment.json` is the structured truth, and root `CLAUDE.md` is the narrative truth; the two must stay in sync (`CLAUDE.md:79-85`, `skills/environment-setup/SKILL.md:172-188`). The session-start hook even reminds Claude to check whether `CLAUDE.md` exists (`hooks/check-environment.js:95-100`).

But `/carrel-automate` updates `environment.json` and generates `_meta/automation-prompt.md`; it does not say to update root `CLAUDE.md` or `_meta/my-environment.md` (`planning/specs/004-scheduled-automation-and-shared-agency.md:83-99`). That is a spec gap, not just an implementation detail, because the philosophy says the "agreed epistemology" lives in both `environment.json` and the vault's `CLAUDE.md` (`planning/specs/004-scheduled-automation-and-shared-agency.md:19`).

### 5. The open-question recommendation for headless detection is not implementable as written

The spec recommends option (a): "the prompt template sets `CARREL_MODE=unattended` and skills check for it" (`planning/specs/004-scheduled-automation-and-shared-agency.md:542`). But the prompt template is plain markdown pasted into a Desktop scheduled task (`planning/specs/004-scheduled-automation-and-shared-agency.md:94-98`, `planning/specs/004-scheduled-automation-and-shared-agency.md:167-229`). Nothing in the command or prompt format explains how a pasted prompt would set a process environment variable.

So the recommendation is not just underspecified; it assumes a mechanism that the spec never defines.

### 6. `ResearcherProfile` compatibility is plausible, but the new automation contract is too loose for current model patterns

The compatibility part is fine. The current profile loader validates `environment.json` into `ResearcherProfile`, and writes it back through `model_dump_json()` (`src/carrel/env/profile.py:13-37`). Adding `automation` with `Field(default_factory=AutomationConfig)` should be backward-compatible in the Pydantic sense (`planning/specs/004-scheduled-automation-and-shared-agency.md:281-317`, `src/carrel/models.py:115-122`).

The problem is contract quality. Current models use enums for constrained values like `Sensitivity`, `ConvertTool`, `TranscribeTool`, and `HardwareCapability` (`src/carrel/models.py:10-33`). The new automation model uses raw strings for `model`, `schedule`, and `review_cadence` (`planning/specs/004-scheduled-automation-and-shared-agency.md:292-304`). That invites invalid states into the one file the hook and skills are supposed to trust mechanically.

### 7. The schedule and review-cadence fields are internally inconsistent

The `/carrel-automate` interview includes "daily / every-other-day / weekdays / weekly" (`planning/specs/004-scheduled-automation-and-shared-agency.md:85-90`), but the proposed model comment for `schedule` only lists `"daily", "weekdays", "weekly"` (`planning/specs/004-scheduled-automation-and-shared-agency.md:301-303`). An implementer has to invent what happens to "every-other-day."

The same issue appears in review cadence. The model includes `review_cadence: str = "quarterly"` (`planning/specs/004-scheduled-automation-and-shared-agency.md:303`), but the hook warning is hard-coded to ">90 days" (`planning/specs/004-scheduled-automation-and-shared-agency.md:395-396`). If cadence is configurable, the warning threshold cannot be fixed at 90 days.

### 8. The hook expansion is feasible, but the spec assumes state that the codebase does not currently record

Extending `hooks/check-environment.js` is feasible in principle; it already finds the vault root, reads `environment.json`, and prints non-blocking guidance (`hooks/check-environment.js:14-110`). But the spec requires the hook to determine whether a brief is "newer than last session" (`planning/specs/004-scheduled-automation-and-shared-agency.md:382-384`).

I could not find any current "last session" timestamp state. `session-reflect.js` computes counts and emits a reflection prompt, but it does not persist session metadata (`hooks/session-reflect.js:70-142`). The only tracked state I found is plugin version state in `.carrel/plugin-state.json` (`CLAUDE.md:87-93`), which is unrelated.

This is a genuine gap: the hook feature depends on state that the spec does not define.

### 9. `/carrel-batch` is underspecified at the operational boundary

The batch command says to enumerate files, route them, launch "background bash tasks," keep chatting, then "collect results as they complete" (`planning/specs/004-scheduled-automation-and-shared-agency.md:61-69`). The current command style is much thinner: `/carrel-convert` maps to one CLI call plus judgment (`commands/carrel-convert.md:15-23`), and the convert skill's existing batch advice is just "run each with `carrel paper convert`, then summarize" (`skills/convert/SKILL.md:71-74`).

The spec is silent on:

- how concurrency is configured,
- how background jobs are named and tracked,
- how retries work,
- how cancellation works,
- whether failures abort the batch or are accumulated,
- how stdout/stderr are surfaced back into the conversation.

Two implementers would build very different systems here: one could fire off shell jobs opportunistically; another could build a real job queue.

### 10. The spec asserts diff-based efficiency and idempotency for analytical tasks without defining the state model

The prompt rules say "scan diffs since last run, don't re-read entire vault" (`planning/specs/004-scheduled-automation-and-shared-agency.md:228`). The failure-mode table assumes efficient diffing via "SHA hashes, date-based scanning" and says duplicate runs are idempotent (`planning/specs/004-scheduled-automation-and-shared-agency.md:485-488`).

That is defined only for file conversion, where Carrel already uses source-hash idempotency as a core rule (`CLAUDE.md:72-73`). It is not defined for:

- cross-linking suggestions,
- gap analysis,
- draft feedback,
- reflection synthesis,
- mirror generation.

The vault structure in C3 has no state file for per-task cursors, last-processed reflection, last-reviewed draft version, or prior suggestion hashes (`planning/specs/004-scheduled-automation-and-shared-agency.md:332-356`). This is spec silence on an operationally central mechanism.

### 11. The plan and approval flows are not specified tightly enough

The plan format says notes are "updated by either party" (`planning/specs/004-scheduled-automation-and-shared-agency.md:374-375`). The reorganization table says "Suggest + confirm" works by surfacing actions in the brief and then executing after the researcher says yes next session (`planning/specs/004-scheduled-automation-and-shared-agency.md:325-328`).

What is missing:

- How an approval is recorded.
- Whether approvals are durable across sessions.
- Whether approvals are tied to a specific file hash or brief date.
- Whether the agent may edit `_meta/plans/` itself, despite the current vault-ops rule to preserve content unless asked (`skills/vault-ops/SKILL.md:178-184`).
- What happens if a pending item is no longer valid when the researcher approves it later.

Without that, "suggest + confirm" is a concept, not a buildable contract.

### 12. The generated prompt omits `CLAUDE.md` even where the spec relies on it

The spec says the shared epistemology lives in `environment.json` and the vault's `CLAUDE.md` (`planning/specs/004-scheduled-automation-and-shared-agency.md:19`), and full collaborative mode says the agent follows vault epistemology from `CLAUDE.md` (`planning/specs/004-scheduled-automation-and-shared-agency.md:328`).

But the example prompt only says "Read .carrel/environment.json for preferences" (`planning/specs/004-scheduled-automation-and-shared-agency.md:168-170`). It never tells the overnight agent to read root `CLAUDE.md`.

That is an internal contradiction in the prompt contract itself.

### 13. The dependency story is mostly right, but the hook work needs an explicit parsing strategy

The spec says the Python core changes only in `models.py`, and that there are no new dependencies or companion plugins (`planning/specs/004-scheduled-automation-and-shared-agency.md:451-454`). `pyproject.toml` supports that: there is nothing here that obviously requires a new Python package if the core change really is model-only (`pyproject.toml:1-15`).

The risk is the JS hook. The hook now needs to inspect markdown frontmatter in `_meta/plans/` and likely parse brief content (`planning/specs/004-scheduled-automation-and-shared-agency.md:382-396`). The spec should explicitly choose one of two paths:

- keep the hook stdlib-only and define a narrow text/frontmatter format it can parse safely, or
- move the parsing behind an existing Python CLI entrypoint and have the hook call that.

Right now the spec says "no new dependencies," but it does not say how the hook parses the new artifacts.

### 14. The spec references checkpoints/undo without any existing contract for them

Full collaborative mode says the researcher can revert via "checkpoints or undo instructions" (`planning/specs/004-scheduled-automation-and-shared-agency.md:328`). The context section mentions checkpoints as a platform capability that inspired the work (`planning/specs/004-scheduled-automation-and-shared-agency.md:13`).

I could not find a Carrel-level checkpoint or undo contract in the current architecture summary (`CLAUDE.md:18-49`) or the current hook/command set (`commands/carrel-setup.md:15-61`, `commands/carrel-status.md:15-20`, `hooks/hooks.json:1-23`). So the revert story is presently aspirational, not specified.

## Module-by-Module Fit

### `src/carrel/models.py`

Adding `automation` is compatible with the current loader/writer path (`src/carrel/env/profile.py:13-37`). I do not see a backward-compatibility blocker here. The issue is that the proposed subfields should be typed more strictly, following the existing enum pattern in `src/carrel/models.py` (`src/carrel/models.py:10-33`, `planning/specs/004-scheduled-automation-and-shared-agency.md:286-304`).

### `hooks/check-environment.js`

The extension is feasible, but only after the spec defines:

- where "last session" lives,
- how plan frontmatter is parsed,
- how "recent brief" is computed,
- what happens when malformed markdown is encountered.

Current hook behavior is simple and resilient because it only reads JSON and checks file existence (`hooks/check-environment.js:36-107`).

### `skills/automation/SKILL.md`

This is the right layer for automation policy. It belongs in the skill layer because it is mostly judgment, explanation, and prompt generation, consistent with Carrel's architecture (`CLAUDE.md:20-27`). The problem is not the file's existence; the problem is that the operational contract underneath it is incomplete.

### New reference files for the automation skill

`references/overnight-prompt-guide.md` and `references/desktop-scheduling-guide.md` are low-risk additions because they are documentation, not executable surface area (`planning/specs/004-scheduled-automation-and-shared-agency.md:148`). I do not see an architectural problem with them. The only requirement is that they should not become the sole place where operational behavior is defined; the buildable contract still needs to live in the main spec and the skill itself.

### `commands/carrel-automate.md`

This fits current command conventions best. Existing commands are conversational wrappers over a skill or CLI workflow (`commands/carrel-setup.md:15-61`, `commands/carrel-status.md:15-24`). But it needs to update more than `environment.json`; otherwise it violates the current sync rules for `CLAUDE.md` and `_meta/my-environment.md` (`skills/environment-setup/SKILL.md:172-188`).

### `commands/carrel-batch.md`

This file fits the command layer in theory, but its actual behavior is much more like a transport-level process manager. That is a scope jump compared with current commands such as `/carrel-convert`, which simply invoke one deterministic CLI operation and narrate the result (`commands/carrel-convert.md:15-23`).

### `commands/carrel-mirror.md`

This belongs in the skill/command layer, not the Python core, which is good (`planning/specs/004-scheduled-automation-and-shared-agency.md:451-452`, `CLAUDE.md:20-27`). But the scheduled write mode is underdefined: the spec does not define "since last mirror," the monthly threshold, or overwrite behavior for `YYYY-MM.md` (`planning/specs/004-scheduled-automation-and-shared-agency.md:112-124`, `planning/specs/004-scheduled-automation-and-shared-agency.md:210-213`, `planning/specs/004-scheduled-automation-and-shared-agency.md:340-341`).

### Migration file

Adding a migration is consistent with current version/migration rules (`planning/specs/004-scheduled-automation-and-shared-agency.md:506-507`, `CLAUDE.md:87-93`). The migration will need to do more than announce new folders; it should explain the new automation state, prompt file, and any manual scheduled-task setup.

### Modified existing skills

- Extending `environment-setup` is architecturally fine, but it directly contradicts the claim that existing commands remain unchanged because `/carrel-setup` behavior is defined by that skill (`planning/specs/004-scheduled-automation-and-shared-agency.md:235-246`, `skills/environment-setup/SKILL.md:199-204`).
- Extending `vault-ops` with analytical threads also fits the skill layer, but the thread conventions should preserve the current paper-vs-note distinction rather than blur it (`planning/specs/004-scheduled-automation-and-shared-agency.md:248-265`, `skills/vault-ops/SKILL.md:37-44`).
- Extending `research-partner` is the most philosophically coherent part of the spec because it stays in the "thinking partnership" layer, but it should remain suggestive rather than automatically operational (`planning/specs/004-scheduled-automation-and-shared-agency.md:267-275`, `skills/research-partner/SKILL.md:8-19`).

## Philosophy Challenge

"Shared agency" works when the agent surfaces possibilities and the researcher chooses among them. That matches the current research-partner posture: the researcher is the expert, the agent is a colleague who asks good questions (`skills/research-partner/SKILL.md:17-19`, `skills/research-partner/SKILL.md:23-48`).

It breaks down when the overnight agent acts first and explains later. At that point the relationship is no longer "shared agency"; it is delegated custodianship of the vault. The spec crosses that line at least twice:

- "Act within convention" lets the agent file new items automatically (`planning/specs/004-scheduled-automation-and-shared-agency.md:327`).
- "Full collaborative" lets it reorganize existing files and justify the move afterward (`planning/specs/004-scheduled-automation-and-shared-agency.md:328`).

That may still be useful, but it is philosophically different from the principle stated in the intro (`planning/specs/004-scheduled-automation-and-shared-agency.md:21`). In practice, collaboration requires a live opportunity to object before the action, not a morning brief after the fact.

## Scope Risks

### 1. v0.4 is carrying too many orthogonal features

The spec tries to ship three new commands, one new skill, three skill extensions, hook expansion, migration work, and versioning work in one release (`planning/specs/004-scheduled-automation-and-shared-agency.md:51-148`, `planning/specs/004-scheduled-automation-and-shared-agency.md:235-398`, `planning/specs/004-scheduled-automation-and-shared-agency.md:492-507`). That is a large jump from the current plugin surface of thin commands plus simple hooks (`commands/carrel-setup.md:15-61`, `commands/carrel-status.md:15-24`, `hooks/check-environment.js:25-110`).

### 2. Scheduling is the hardest part, and it is also the least specified

The operationally complex part is not writing markdown files; it is the recurring unattended run contract: task creation, mode detection, failure recovery, duplicate runs, stale runs, and state tracking (`planning/specs/004-scheduled-automation-and-shared-agency.md:33-43`, `planning/specs/004-scheduled-automation-and-shared-agency.md:477-488`). That area needs more precision before implementation.

### 3. `/carrel-batch` is a separate product

Background batch conversion with concurrency and result collection (`planning/specs/004-scheduled-automation-and-shared-agency.md:61-69`) is not just a small extension of `/carrel-convert`. It is closer to a job-runner. Shipping that alongside scheduling and shared-agency policy is too much for one bump.

### 4. "Full collaborative" should not be in the first release

The spec has no real undo/checkpoint contract (`planning/specs/004-scheduled-automation-and-shared-agency.md:328`, `planning/specs/004-scheduled-automation-and-shared-agency.md:486`). Without a concrete rollback story, autonomous reorganization of existing researcher files is too risky for the first automation release.

### 5. `/carrel-mirror` is valuable, but it does not need to block scheduling

The mirror feature is analytically rich but operationally separate (`planning/specs/004-scheduled-automation-and-shared-agency.md:104-126`). It can be a later command or even a manual-only first version. It should not be tied to the first scheduled-maintenance release unless the team explicitly wants that as the headline feature.

### 6. The cost model reads as more precise than the implementation contract supports

The spec gives concrete token and monthly cost ranges (`planning/specs/004-scheduled-automation-and-shared-agency.md:459-473`), but there is no current code path for metering or validating those estimates in the plugin or the core library (`CLAUDE.md:18-49`, `pyproject.toml:1-15`). I would treat those numbers as rough product copy unless the spec also defines how usage is sampled or bounded.

## Open Questions

### 1. Headless detection

My answer: none of the listed options is right as written. Option (a) is conceptually closest, but not via an environment variable, because the spec never defines how a pasted scheduled-task prompt sets process env (`planning/specs/004-scheduled-automation-and-shared-agency.md:94-98`, `planning/specs/004-scheduled-automation-and-shared-agency.md:542`). Option (b) is brittle, and option (c) confuses a transient run mode with persisted user preference (`planning/specs/004-scheduled-automation-and-shared-agency.md:281-317`).

Recommendation: encode unattended mode explicitly in the generated prompt text and make skills branch on that instruction, not on ambient process state.

### 2. Analytical thread scope

My answer: keep threads under `notes/threads/` only. That matches the current separation between converted papers, drafts, and the researcher's own notes (`skills/vault-ops/SKILL.md:17-44`). Putting threads under `papers/` or `drafts/` would blur the distinction Carrel is already careful about.

### 3. Brief accumulation

My answer: preserve old briefs. The hook only needs the latest brief, but the archive is useful as a longitudinal research log (`planning/specs/004-scheduled-automation-and-shared-agency.md:336-337`, `planning/specs/004-scheduled-automation-and-shared-agency.md:546`). I do not see a storage concern big enough to justify auto-cleanup in v0.4.

### 4. Pending decisions file vs directory

My answer: a single file is acceptable for v0.4, but only if the spec also defines item IDs, append rules, and when resolved items are trimmed or archived (`planning/specs/004-scheduled-automation-and-shared-agency.md:437-446`, `planning/specs/004-scheduled-automation-and-shared-agency.md:548`). Without that, even the "simple" option will rot.

### 5. Multi-vault researchers

My answer: no for v0.4. The current architecture is vault-local by design (`CLAUDE.md:72-75`, `planning/specs/004-scheduled-automation-and-shared-agency.md:455`, `planning/specs/004-scheduled-automation-and-shared-agency.md:550`). Cross-vault automation would introduce a whole new state and privacy model.

## Ambiguities That Would Produce Divergent Implementations

### 1. What counts as "act within convention"?

The line says "Files NEW items ... never reorganizes existing files" (`planning/specs/004-scheduled-automation-and-shared-agency.md:327`). But if the agent renames an inbox file while filing it, is that still "new"? If it adds backlinks to an existing note, is that "reorganizing"? The boundary is unclear.

### 2. What exactly is approved in "suggest + confirm"?

The spec says the researcher says yes in the next session and then the agent executes (`planning/specs/004-scheduled-automation-and-shared-agency.md:326`). It does not define whether approval is per-item, per-brief, or per-capability.

### 3. What does "since last brief" and "since last mirror" mean operationally?

Inbox processing uses "since last brief" (`planning/specs/004-scheduled-automation-and-shared-agency.md:178-183`), and mirror uses "all entries, or since last mirror" (`planning/specs/004-scheduled-automation-and-shared-agency.md:112-124`). There is no state model for either cursor.

### 4. How are confidence scores defined?

The spec requires high/medium/low confidence for cross-linking suggestions and says only high-confidence items appear in briefs (`planning/specs/004-scheduled-automation-and-shared-agency.md:191-196`, `planning/specs/004-scheduled-automation-and-shared-agency.md:481`). There is no rubric, threshold, or output schema.

### 5. What is the parsing contract for active plans?

The hook is supposed to find `status: active` in plan frontmatter (`planning/specs/004-scheduled-automation-and-shared-agency.md:386-388`). The spec does not define what happens with malformed frontmatter, duplicate titles, or missing `updated`.

### 6. What is the actual scheduled-task payload?

The spec alternates between "generated prompt template," "Desktop App local tasks," and possible headless behavior (`planning/specs/004-scheduled-automation-and-shared-agency.md:43`, `planning/specs/004-scheduled-automation-and-shared-agency.md:152-165`, `planning/specs/004-scheduled-automation-and-shared-agency.md:542`). It never states whether the scheduled task runs a raw prompt, a slash command, or a reproducible command wrapper.

## Recommended Changes Before Implementation

1. Reduce v0.4 to suggest-only automation plus prompt generation, morning briefs, pending decisions, and hook surfacing. Defer `ACT_WITHIN_CONVENTION`, `FULL_COLLABORATIVE`, and probably `/carrel-mirror`.
2. Make `/carrel-automate` update root `CLAUDE.md` and `_meta/my-environment.md`, not just `environment.json`, to preserve the current sync model (`skills/environment-setup/SKILL.md:172-188`, `CLAUDE.md:79-85`).
3. Replace raw string automation fields with enums or other bounded types, especially `schedule`, `model`, and `review_cadence` (`src/carrel/models.py:10-33`, `planning/specs/004-scheduled-automation-and-shared-agency.md:292-304`).
4. Define explicit state files or cursors for "last session," "last run," "last brief seen," and per-capability incremental scans.
5. Specify the approval contract for `pending-decisions.md` and "suggest + confirm" in a way that survives across sessions.
6. Choose and document the parsing strategy for the JS hook before implementation. If the hook should remain minimal, narrow the plan/brief formats to what it can parse safely.
7. Keep dependency additions at zero unless the hook parsing requirement truly forces a new dependency; if that happens, say so explicitly rather than relying on an implicit implementation choice.

## Summary

The model change is compatible. The automation story is not yet. The spec should be tightened around state, approval, scheduling payloads, and the exact boundary between suggestion and action before implementation starts. My recommendation is to treat v0.4 as "scheduled suggestive maintenance" rather than "shared agency" in the strong sense, and to defer autonomous reorganization until the rollback and approval contracts are real.
