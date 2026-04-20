# Documentation Coherence Audit — v0.5.3

**Date:** 2026-04-20
**Auditor:** Opus (1M context, documentation-coherence pass)
**Scope:** README.md, project CLAUDE.md, vault templates, every `commands/*.md`, every `skills/*/SKILL.md` + `skills/*/references/*.md`, agent prompts (`agents/*.md`), every migration doc + `migrations/registry.json`, planning specs 006/007 internal consistency.
**Out of scope (handled by parallel agents):** code quality of `src/carrel/`, hook runtime correctness, plugin surface integrity (`009-audit-plugin-surface.md` already exists).

---

## Verdict

**Tightened on the v0.5.3 sprint axis (`carrel setup-state`, cross-platform stopgap, version consistency); stale everywhere the sprint didn't touch.** README and project CLAUDE.md are clean and current. The `commands/carrel-setup.md` flow is the gold standard — explicit CLI invocations, pause/resume protocol, OS-branched Obsidian guidance.

The rot is concentrated in three places:

1. **`skills/environment-setup/references/`** — three reference docs (`decision-tree.md` Obsidian section, `obsidian-setup.md`, `cheatsheet-template.md`) and the parent `SKILL.md` Step 7 still recommend `brew install` unconditionally for Obsidian, contradicting the v0.5.3 cross-platform guidance the sprint just added at the top of `decision-tree.md` and in `commands/carrel-setup.md` Phase 6. A Windows researcher who reads the skill instead of the command will be told to run `brew install obsidian`.
2. **`skills/environment-setup/references/cheatsheet-template.md`** is fictional. It documents a Mustache-style template (`{{researcher.name}}`, `{{#if defuddle_available}}`) that has nothing to do with what `render_cheat_sheet()` in `src/carrel/vault/templates.py` actually emits. The whole 180-line file is aspirational.
3. **`skills/environment-setup/references/hardware-audit.md`** documents a JSON schema (`{ "system": {...}, "tools": {...}, "existing_mcps": {...} }`) that does not match the actual `AuditResult` Pydantic model (`os`, `arch`, `ram_gb`, `hardware_capability`, `tools: ToolAvailability`). Anyone reading this skill to understand what `carrel env doctor` returns will guess wrong.

There is also one **HIGH** that crosses the docs/code boundary, already flagged in `009-audit-plugin-surface.md` but worth re-stating because the SKILL doc reinforces it: `render_cheat_sheet()` writes a `/carrel-research` reference into every cheat sheet, and no such command exists. Not a doc-only fix.

Migration docs match commits. Counts in README (13 commands, 10 skills, 2 agents) match the file system. CLI surface in CLAUDE.md is accurate. The Pydantic shape in `interview-protocol.md` matches `ResearcherProfile`. The `setup-state` CLI is correctly threaded through `commands/carrel-setup.md`, `commands/carrel-cheatsheet.md`, and the migration doc.

**Tier breakdown:** 0 BLOCKER, 5 HIGH, 6 MEDIUM. (No LOW issues reported per scope rule.)

---

## BLOCKER

None.

The v0.5.3 sprint closed all the documentation contradictions that would *prevent* a researcher from completing setup. The remaining issues degrade quality, suggest stale CLI commands, or feed Claude bad guidance — but no doc, on its own, will dead-end a deploying researcher.

---

## HIGH (likely to confuse / mislead)

### H1 — `decision-tree.md` Obsidian Setup section still mac-only, contradicts top-of-file v0.5.3 platform note

`skills/environment-setup/references/decision-tree.md:400-418` ("Obsidian Setup" subsection):

```
→ NO:
  - Offer: "brew install obsidian" (if brew available)
  - Or: "Download from obsidian.md"
  - This is a human step — Claude can't click through the installer
```

Compare to the same file's line 1 (added in v0.5.3):

> **Platform note:** Recommendations below are macOS-first. On Windows, prefer `winget install ...`...

The platform note told Claude "adapt brew commands"; the Obsidian Setup section gives Claude no Windows/Linux command to adapt to, just `brew install obsidian`. The v0.5.3 sprint added the OS branches to `commands/carrel-setup.md:80-84` but never propagated them down into the skill reference Claude actually consults during Phase 3 (decision tree consultation).

**Fix:** Replace the bullet with the same three-line OS-branched block already in `commands/carrel-setup.md:81-84` (`macOS: brew install --cask obsidian` / `Windows: winget install Obsidian.Obsidian` / `Linux: AppImage from obsidian.md`).

### H2 — `environment-setup/SKILL.md` Step 7 ("Human Steps") is mac-only

`skills/environment-setup/SKILL.md:147-152`:

```
- Install Obsidian: "Download from obsidian.md, or I can try `brew install obsidian` if you'd like"
```

Same problem as H1, in the parent skill. Phase 6 of `commands/carrel-setup.md` is correctly OS-branched; Step 7 of the underlying skill is not. The skill is what Claude actually loads during `/carrel-setup`. If Claude consults the SKILL flow rather than re-reading the command file, the researcher gets a `brew install` recommendation on Windows.

Note also the bare `brew install obsidian` (without `--cask`) — this is wrong even on macOS (it will fail; Obsidian is a cask). The same bug appears in `references/obsidian-setup.md:152`.

**Fix:** Mirror the OS-branched block from Phase 6 of `commands/carrel-setup.md`.

### H3 — `environment-setup/references/obsidian-setup.md` is mac-centric throughout

`skills/environment-setup/references/obsidian-setup.md`:
- Line 152: `brew install obsidian` (wrong — needs `--cask`; also mac-only)
- Line 154: "Installs to /Applications/Obsidian.app" (mac path)
- Line 158: "Drag to Applications (macOS)" + "Run installer (Windows)" — partial gesture toward Windows but no command
- Line 161: `mdfind "kMDItemCFBundleIdentifier == 'md.obsidian'"` as the existence check (mac-only)

The whole "Installing Obsidian" subsection assumes macOS plus a brief Windows fallback that's just "download and run installer." No `winget`, no AppImage. The audit code in `src/carrel/env/audit.py` was specifically called out in v0.5.3 CLAUDE.md Gotchas as still using `mdfind` — the doc reinforces the same bug rather than warning Claude away from it.

**Fix:** Cross-reference the v0.5.3 install branching, replace `brew install obsidian` with `brew install --cask obsidian`, and add `winget install Obsidian.Obsidian` + AppImage rows.

### H4 — `environment-setup/references/cheatsheet-template.md` describes a fictional Mustache template

`skills/environment-setup/references/cheatsheet-template.md` (180 lines) presents a Mustache/Handlebars-style template with `{{researcher.name}}`, `{{vault_folder_name}}`, `{{#if defuddle_available}}...{{/if}}` blocks, etc. The header (line 3) explicitly claims:

> This template is used by `carrel vault cheatsheet` (and the underlying `render_cheat_sheet()` in `src/carrel/vault/templates.py`) to create a customized reference card. Variables in `{{brackets}}` are replaced with values from `.carrel/environment.json`.

This is false. `render_cheat_sheet()` (`src/carrel/vault/templates.py:153-194`) is a Python f-string. There is no `{{...}}` parser. The actual output uses headings, sections, and structure that bear no resemblance to the documented template. The v0.5.3 migration even calls out that the renderer was "beefed up... with configured-tools matrix, common workflows, and next steps sections" — those sections are nowhere in this reference doc.

This file is a hazard for Claude: if Claude reads it expecting to know what the cheat sheet contains, it will guess wrong (e.g., expect `{{transcription_status}}` to appear and try to fill it in via prompt; or try to extend the "template" by adding new `{{vars}}` that go nowhere).

**Fix:** Either (a) delete the file outright and add a one-line pointer in `environment-setup/SKILL.md` Step 8 saying "the cheat sheet renderer lives in `src/carrel/vault/templates.py:render_cheat_sheet()` — see source for the current sections", or (b) rewrite the file as a genuine description of what `render_cheat_sheet` actually emits in v0.5.3 (Setup, Folders, Configured tools, Common workflows, Next steps).

### H5 — `environment-setup/references/hardware-audit.md` documents a schema that doesn't exist

`skills/environment-setup/references/hardware-audit.md:56-83` shows the "JSON for environment.json" output of the audit:

```json
{
  "system": { "os": "macOS", "os_version": "15.4", "arch": "arm64", "ram_gb": 36, "disk_free_gb": 120, "gpu": "Apple M3 Max" },
  "tools": { "node": { "installed": true, "version": "22.1.0" }, ... },
  "existing_mcps": { "claude_desktop": [], "claude_code_user": [], "project": [] }
}
```

The actual `AuditResult` Pydantic model (`src/carrel/models.py:123-130`):

```python
class AuditResult(BaseModel):
    os: str
    arch: str
    os_version: str | None = None
    ram_gb: int | None = None
    disk_free: str | None = None
    hardware_capability: HardwareCapability
    tools: ToolAvailability
```

Differences:
- Top-level fields are flat (`os`, `arch`, `ram_gb`), not nested under `"system"`
- No `gpu` field, no `disk_free_gb` (it's `disk_free: str`)
- New `hardware_capability` enum field is documented nowhere
- `tools` is `ToolAvailability` (`binaries: dict[str, BinaryInfo]`, `api_keys: dict[str, ApiKeyStatus]`, `mcp_servers: list[str]`), not the documented `{ tool_name: { installed, version } }` shape
- `existing_mcps` is not a thing — `mcp_servers` is a flat list inside `tools`

If Claude reads this skill to understand `carrel env doctor --format json` output (which is what `commands/carrel-status.md` and `commands/carrel-setup.md` Phase 2 tell Claude to do), it will index into the wrong fields.

**Fix:** Rewrite the "Output Format" section against the real `AuditResult` shape (run `carrel env doctor --format json` against any vault and copy the output as the canonical example).

---

## MEDIUM (sloppy but recoverable)

### M1 — `decision-tree.md` Prerequisites section still says bootstrap.sh is canonical

`skills/environment-setup/references/decision-tree.md:7-20` (Prerequisites section):

> The bootstrap script (`bootstrap.sh`) handles machine-level prerequisites before the plugin runs.

But `CLAUDE.md:52` explicitly marks `bootstrap.sh` as legacy:

> bootstrap.sh          # Mac-focused machine prep (legacy; install.sh preferred)

And the README (line 82-87) tells researchers to use `install.sh` / `install.ps1`, not `bootstrap.sh`. This isn't load-bearing — Claude is unlikely to invoke `bootstrap.sh` itself — but it's pre-v0.5.3 framing that survived the cross-platform sprint.

**Fix:** Replace the first sentence with "The install scripts (`install.sh` / `install.ps1`) handle machine-level prerequisites...".

### M2 — `interview-protocol.md` JSON schema example omits AutomationConfig per-capability booleans

`skills/environment-setup/references/interview-protocol.md:118-125` shows the `automation` object as:

```json
"automation": {
  "enabled": false,
  "trust_level": "advisory",
  "model": "sonnet",
  "schedule": "daily",
  "review_cadence": "quarterly",
  "last_reviewed": null
}
```

Compare to `commands/carrel-automate.md:66-80` and `skills/automation/SKILL.md:58-73`, both of which include the full eight per-capability booleans (`inbox_processing`, `vault_health`, `cross_linking_suggestions`, `gap_analysis`, `draft_feedback`, `reflection_synthesis`, `wiki_maintenance`).

The interview-protocol's note "All optional fields can be omitted — Pydantic will default them" is technically true (Pydantic backfills `True`/`False` defaults from `AutomationConfig`), but the inconsistency between the three docs that all show the same JSON object will confuse anyone tracing what fields belong where. The setup-interviewer agent emits the truncated form; `/carrel-automate` writes the full form on top of it, which works but reads as drift to anyone diffing two versions of the same researcher's profile.

**Fix:** Either show the full eight booleans in interview-protocol.md (matching automation/SKILL.md) or add a one-line comment clarifying that `automation` is intentionally minimal here because Pydantic will fill defaults.

### M3 — `docs/self-setup-guide.md` Step 6 Obsidian section is mac-only

`docs/self-setup-guide.md:80-90`:

```
## Step 6: Install Obsidian
- **Mac**: Claude may offer to install it for you, or download from [obsidian.md](https://obsidian.md)
```

Only macOS is listed. README's Platform Support matrix (lines 19-28) shows Obsidian as "Full" on Linux and Windows; commands/carrel-setup.md Phase 6 has the OS branches. The self-setup guide is the doc a researcher reads BEFORE invoking Claude — for Windows users, this is the first place they see "Carrel" and they're told there's no install path for them.

**Fix:** Add Windows + Linux rows mirroring `commands/carrel-setup.md:81-84`.

### M4 — `vault-ops/SKILL.md` describes a vault structure missing `_meta/local/` and `_meta/reflections/`

`skills/vault-ops/SKILL.md:21-35` "Vault Structure" diagram:

```
vault/
├── inbox/          # Drop zone — unsorted incoming
├── papers/         # Converted papers — one FOLDER per paper
...
├── _meta/          # Cheat sheet, reflections, friction log
└── _templates/     # Note templates (meeting, reflection, daily, paper-notes)
```

But `templates/vault-scaffold.json` actually creates `_meta/reflections` AND `_meta/local`. `_meta/local/` is specifically called out in `self-improve/SKILL.md` as the namespace for vault-local capabilities (no carrel-template marker), and the scaffold creates it. The diagram in `vault-ops/SKILL.md` doesn't mention either, so anyone reading the skill to understand "where do reflections go?" or "where do my custom patterns live?" won't see the reserved subdirectory.

The cheatsheet template's "Vault Structure" block (lines 113-127) has the same omission.

**Fix:** Add `_meta/local/` and `_meta/reflections/` rows to the vault-ops diagram.

### M5 — `agents/setup-interviewer.md` references `interview-protocol.md` for the JSON schema, but doesn't note the AutomationConfig truncation

`agents/setup-interviewer.md:67`:

> After the interview, structure the profile as JSON (see `skills/environment-setup/references/interview-protocol.md` for the schema) and save to `.carrel/environment.json`.

The agent inherits whatever ambiguity is in the protocol doc. If M2 isn't fixed, the agent will emit the truncated `automation` block and there's no signal to it (or to a reviewing human) that this is intentional Pydantic-default behavior vs. a bug.

**Fix:** Either resolve M2 in interview-protocol, or add a one-liner here noting that `automation` is "minimal — `/carrel-automate` will populate the rest if the researcher opts in".

### M6 — Phase/Step numbering between `commands/carrel-setup.md` (Phases 1-9) and `skills/environment-setup/SKILL.md` (Steps 1-10) is off by one after Step 4

The command and the skill cover the same flow but use different counters:

| Command (Phases) | Skill (Steps) |
|---|---|
| Phase 5: Optional MCPs | Step 6: Configure Optional Tools |
| Phase 6: Human Steps | Step 7: Human Steps |
| Phase 7: Cheat Sheet & Verification | Step 8: Verify, Cheat Sheet & Environment Dashboard |
| Phase 8: Overnight Maintenance | Step 9: Overnight Maintenance (optional) |
| Phase 9: Handoff | Step 10: Wrap Up |

Cross-doc references are inconsistent: `commands/carrel-automate.md:13` says "Phase 8 of `/carrel-setup`"; `commands/carrel-automate.md:143` says "Step 9 offers automation opt-in"; `skills/automation/SKILL.md:407` says "Step 9 in environment-setup". They all point to the same place, but the labels disagree. `self-improve/SKILL.md:36` says my-environment.md is "created during setup (Step 8)" — which matches the SKILL numbering but not the COMMAND numbering.

This is not load-bearing for behavior, but it's the kind of drift that compounds — each new doc that picks one convention reinforces the split.

**Fix:** Pick one convention (recommend: command's Phase numbering, since that's the user-facing surface) and align all cross-references. Or add a one-line "Phase N (skill Step N+1)" note at the top of `environment-setup/SKILL.md`.

---

## Cross-Doc Consistency Spot-Check (no findings, included for completeness)

The following potential drifts were checked and confirmed coherent:

- **README ↔ CLAUDE.md ↔ migrations/0.5.2-to-0.5.3.md** all agree on v0.5.3 changes (setup-state CLI, install.ps1 verification, cross-platform stopgap, cheatsheet beef-up, version-consistency test).
- **`.claude-plugin/plugin.json` (0.5.3) ↔ `.claude-plugin/marketplace.json` (0.5.3) ↔ `pyproject.toml` (0.5.3) ↔ `src/carrel/__init__.py` (0.5.3)** all match — the new version-consistency test enforces this.
- **README command count (13)** matches `ls commands/*.md | wc -l`. **Skill count (10)** matches `ls skills/`. **Agent count (2)** matches `ls agents/`.
- **`migrations/registry.json`** entries are in chronological order, all `.md` files referenced exist, and each `summary` reasonably describes the corresponding doc.
- **`CLAUDE.md` test count (62)** matches `uv run pytest --collect-only` (verified live). The triangulated review still says "49 tests" but that was pre-v0.5.3.
- **`ResearcherProfile` Pydantic schema** (with `wiki_enabled`, `wiki_preference`, `wiki_proposal_deferred_until`, `claude_code_familiarity`, `collaborators`, `team_context`, `automation: AutomationConfig`) matches the canonical example in `interview-protocol.md` (modulo M2).
- **`SetupState` Pydantic schema** matches what `commands/carrel-setup.md` and `migrations/0.5.2-to-0.5.3.md` describe (`last_completed_phase ∈ [4,9]`, semver `version`, ISO `completed_at`, mutual-implication invariant). The CLI `carrel setup-state {advance,complete,show,reset}` surface in `src/carrel/cli/setup_state.py` matches the docs exactly.
- **`carrel setup-state advance --phase N`** is correctly invoked at the end of Phases 5, 6, 7, 8 in `commands/carrel-setup.md`, with `complete` at Phase 9.
- **`/carrel-share` ↔ `collaborator-onboarding/SKILL.md`** are aligned. The handbook template's expected sources match what the SKILL reads.
- **`/carrel-automate` ↔ `automation/SKILL.md`** are aligned. The 10-step workflow in the command matches the SKILL contract; the JSON example for `automation` in environment.json appears identically in both (full eight booleans).
- **`/carrel-mirror` ↔ no skill file** — by design; the command is self-contained. Confirmed not a skill omission.
- **Knowledge wiki `wiki_enabled`/`wiki_preference`/`wiki_proposal_deferred_until` Pydantic fields** are referenced consistently across `knowledge-wiki/SKILL.md`, `knowledge-wiki/references/trust-activation.md`, `commands/carrel-automate.md`, and `CLAUDE.md`.
- **Capability registry** (`skills/self-improve/references/capability-registry.md`) tracks the v0.5.0 wiki absorption (Karpathy + Hermes) and the v0.5.1 collaborator-handbook absorption (with explicit "design pattern only, not the command" note). No stale entries.
- **Specs 006 and 007** correctly defer to each other via the "Cross-Cutting" / "Coordination" sections; spec 007 ships `PlatformToolMatrix` first, spec 006 consumes it; spec 006 explicitly defers `setup-state` drift to `carrel setup-state` (added v0.5.3, reflected in spec 006 line 146). The `ToolAvailability` rename to `PlatformToolMatrix` (per Kimi review) is consistent across both spec files.
- **Migration files match commit history** — each migration's "What Changed" file list aligns with what would have been touched. (Verified for 0.5.0 → 0.5.1, 0.5.1 → 0.5.2, 0.5.2 → 0.5.3 by spot-checking three "new file" claims per migration against the file system.)

---

## Issues Forwarded to the Plugin Surface Audit (009-audit-plugin-surface.md)

These are runtime/integration issues already covered there; documenting here only to confirm the doc layer reinforces them rather than warns Claude away:

- **`render_cheat_sheet()` writes `/carrel-research`** (a non-existent command). The skill doc layer has no warning about this; `commands/carrel-cheatsheet.md` doesn't note that the regenerated cheat sheet may contain a broken slash command; `environment-setup/SKILL.md` Step 8 also doesn't warn. Doc-layer fix: once the code is fixed (replace with `/carrel-status` or remove), nothing to do. Until then, no doc alerts Claude to the issue.
- **`hooks/session-reflect.js` reads legacy nested profile shape** — out of scope for this audit, but `interview-protocol.md`'s explicit deprecation of the nested format ("The legacy nested format (with a top-level `interview` key) is deprecated") is correct doc-layer guidance. The hook is what's stale, not the docs.

---

## Recommended Fix Sequence

If applying these incrementally:

1. **Tier A (blocking-feeling for Windows researchers):** H1, H2, H3 — get Obsidian install advice consistent with v0.5.3 cross-platform stopgap. ~30 min.
2. **Tier B (quality of Claude's understanding):** H4 (delete or rewrite cheatsheet-template.md), H5 (rewrite hardware-audit output schema), M4 (add `_meta/local/` to vault-ops diagram). ~45 min.
3. **Tier C (cosmetic/reduces drift):** M1 (`bootstrap.sh` → `install.sh` framing), M2 + M5 (interview-protocol AutomationConfig clarity), M3 (self-setup-guide cross-platform), M6 (Phase/Step numbering alignment). ~30 min.

Total: ~2 hours of doc edits, no code changes required.
