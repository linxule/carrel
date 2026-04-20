# 008: Codex Adversarial Review

**Date**: 2026-04-20
**Reviewer**: Codex (via `codex:codex-rescue` agent in diagnosis-only mode)
**Mode**: read-only fresh adversarial pass; range = `1788485..HEAD` (everything since v0.5.0)

**Verdict**: 2 BLOCKERS, 2 HIGH, 5 MEDIUM. The architectural insight (procedural coupling of state transitions) is the most leveraged single fix.

---

## BLOCKERS (must fix before Imperial deployment)

### B1. Windows onboarding is still Mac-coded at the moment of use

`commands/carrel-setup.md:66`, `src/carrel/env/install.py:1`. Even after `install.ps1` landed (commits `a7f18d8`, `07977b9`), the live setup flow still tells users to use `brew` for Obsidian, and install constants are entirely brew-based. Windows faculty hit wrong instructions during actual `/carrel-setup`. Documenting the gap in CLAUDE.md doesn't fix the flow.

### B2. Public docs oversell Windows readiness

`README.md:49, :71`, `CLAUDE.md:140`. README says the install script "handles everything else"; CLAUDE.md gotcha now acknowledges Windows users "hit walls during /carrel-setup". The contradiction is not deployable documentation. Commit `07977b9` made the limitation explicit in CLAUDE.md without reconciling README.

---

## HIGH

### H1. Resumable setup is procedurally coupled, not code-driven

`commands/carrel-setup.md:21`, `src/carrel/vault/scaffold.py:97`, `hooks/check-environment.js:26, :244`. Only the initial Phase 4 write to `setup-state.json` is deterministic; every later phase depends on Claude manually editing the file. The hook silently drops resume behavior on any JSON read failure because `readJsonFile()` returns `null`. (Commits `a7f18d8`, `9251bd5`.)

### H2. 007 → 006 sequencing is correct, but 007 is not lock-ready

`planning/specs/007-cross-platform-support.md:278, :320`, `planning/specs/006-environment-validation-and-self-healing.md:312`. Sequencing resolution is sound, but spec 007 itself still declares `liteparse Windows` and `gws fallback` as unresolved Lock Blockers. Implementation should NOT start just because the order is "locked". The spec needs to make this status more visible. (Commits `17ae1d2`, `ecf937e`.)

---

## MEDIUM

### M1. SetupState is under-specified for a real state machine

`src/carrel/models.py:158, :160`, `hooks/check-environment.js:248`. Model accepts phases 0-3 even though persistence only begins after Phase 4. Both `version` and `completed_at` are free-form strings; semantically bad-but-parseable states are accepted as canonical. (Commit `9251bd5`.)

### M2. `carrel vault cheatsheet` is schema-correct but too thin for its documented role

`commands/carrel-setup.md:74`, `src/carrel/cli/vault.py:140`, `src/carrel/vault/templates.py:59`. Phase 7 treats the cheat sheet as a core handoff artifact, but the renderer only emits vault path, sensitivity/cloud-consent, one audio flag, and folder names — not the working tool matrix, workflows, troubleshooting, or next steps the surrounding docs imply. (Commits `3e90f6f`, `a7f18d8`.)

### M3. 0.5.2 migration's manual "mark complete" path is Unix-only

`migrations/0.5.1-to-0.5.2.md:45`. The documented fallback uses shell interpolation plus `date -u`, making it wrong for the Windows cohort this release claims to support. (Commit `a7f18d8`.)

### M4. Command/skill surface area is ahead of its information architecture

`README.md:17, :27`, `planning/specs/006-environment-validation-and-self-healing.md:320`. README still advertises "9 commands/6 skills" and omits `/carrel-automate`, `/carrel-batch`, `/carrel-mirror`, `/carrel-share`. Adding `/carrel-fix` (planned in spec 006) before cleaning that up will make the surface harder to teach. (Commit `17ae1d2`.)

### M5. Session-start hook handles "paused setup + morning brief" only by serialized print order

`hooks/check-environment.js:69, :125, :244, :353`. In the mixed case (paused setup AND active automation), the hook emits both messages with no arbitration or validation boundary. Nearly every branch fails silently with `catch {}`, absorbing complexity as missing output instead of explicit behavior. (Commit `a7f18d8`.)

---

## #1 Recommendation

**Add a deterministic state-transition CLI before deployment.**

`carrel setup-state advance --phase N` and `carrel setup-state complete`, and make `/carrel-setup`, migration docs, and the hook all depend on that instead of manual JSON edits. Touches `commands/carrel-setup.md:21`, `src/carrel/models.py:149`, `hooks/check-environment.js:244`. (Commits `a7f18d8`, `9251bd5`.)

This single change removes the most fragile hidden coupling in this sprint and is the highest-leverage fix before rolling out to mixed Mac/Windows Imperial faculty.
