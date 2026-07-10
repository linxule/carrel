# planning/

Open planning folder for Carrel. Any model (Claude, Codex, Gemini, Kimi, GPT) can read, review, and contribute.

## Structure

```
planning/
├── specs/      # Task specifications — the "what" and "how"
├── reviews/    # Feedback on specs + post-implementation audits from any model
├── reports/    # Implementation reports — what was built, decisions made
├── research/   # Upstream research that informs or unblocks specs
├── prompts/    # Reusable review/audit prompt scaffolds
└── README.md
```

## Workflow

1. **Spec** goes in `specs/` — numbered, detailed, with acceptance criteria
2. **Open Questions** in the spec must be locked (decision + rationale) before implementation
3. **Any model reviews** — saves feedback in `reviews/` referencing the spec number. Default reviewer set: **Codex (deep adversarial pass) + Kimi (independent second-pair-of-eyes) + a feasibility/architect pass**.
4. **Spec gets refined** based on reviews
5. **Implementation** (often delegated to Codex) — saves report in `reports/` if substantial
6. **Post-implementation review** in `reviews/` if the change had architectural impact
7. **Human decides** what ships

## Naming

- Specs: `001-short-title.md`
- Reviews: `001-review-<model>.md` or `001-<topic>-<model>.md` (e.g., `008-review-codex.md`)
- Reports: `001-report-<model>.md`
- Research: `<spec#>-<topic>-research.md`

## Spec & Review History

| File | Purpose |
|------|---------|
| `specs/001-core-library-extraction-v3.md` | Core library spec (final) |
| `specs/002-tool-expansion-and-cleanup.md` | Tool expansion: defuddle, YouTube captions, gws |
| `reviews/003-implementation-review.md` | Post-implementation review |
| `reports/002-report-codex.md` | Tool expansion report |
| `reports/003-report-codex.md` | Core library fix report |
| `specs/004-scheduled-automation-and-shared-agency.md` | v0.4 spec: scheduled automation + graduated trust |
| `reviews/004-review-codex.md` | v0.4 adversarial review (Codex) |
| `reviews/004-review-architect.md` | v0.4 feasibility review (architect) |
| `reviews/004-review-implementation.md` | v0.4 post-implementation spec compliance |
| `reviews/005-knowledge-wiki-review.md` | Knowledge wiki: internal + Codex adversarial reviews (2 rounds) |
| `specs/006-environment-validation-and-self-healing.md` | v0.7.0 spec: schema validation, safe repair, `/carrel-fix`, hook surfacing, PlatformToolMatrix-backed re-sync — **fully implemented in v0.7.0** |
| `specs/007-cross-platform-support.md` | v0.7 spec: Windows + Linux first-class support; platform-aware audit, install, decision tree. **Fully implemented in v0.7.0** after the 2026-04-20 blocker resolution. |
| `research/007-windows-tools-research.md` | Research that unblocked spec 007 (liteparse + gws Windows install paths; Web Clipper rejection; native Google Docs Markdown export tip) |
| `reviews/008-deployment-readiness-triangulated.md` | Synthesis of Kimi + Codex + internal code-reviewer findings on the v0.5.0→v0.5.2 sprint; tiered fix plan — **fully implemented in v0.5.3** (B1, B2, A1-A7, S1-S3, H1-H3) |
| `reviews/008-review-kimi.md` | Kimi rounds 1+2: schema drift findings + post-fix re-review |
| `reviews/008-review-codex.md` | Codex fresh adversarial pass: 2 BLOCKERS + #1 recommendation (deterministic state-transition CLI) |
| `reviews/008-review-internal.md` | Internal code-reviewer: 6 HIGH-confidence Python/JS issues |
| `specs/008-trust-enforcement.md` | v0.6.0 spec: `carrel trust check` CLI gates writes by trust level — **fully implemented in v0.6.0** (closes 009 A1 / Codex §4) |
| `reviews/009-holistic-audit-triangulated.md` | Whole-repo audit synthesis: code quality + docs + plugin surface + Codex adversarial. Tier 0-3 **fully implemented in v0.5.4**. Headline insight: "markdown control plane" risk — A1/A2/A3 deferred to specs (trust enforcement, policy module, profile sync) |
| `reviews/009-audit-code-quality.md` | Internal code-reviewer whole-repo pass: 2 critical, 8 HIGH, 10 MEDIUM (error contracts, dead code, idempotency) |
| `reviews/009-audit-documentation.md` | Documentation coherence pass: 5 HIGH, 6 MEDIUM (skill drift, fictional Mustache template, hardware-audit schema mismatch) |
| `reviews/009-audit-plugin-surface.md` | Plugin wiring integrity pass: 3 runtime bugs (session-reflect dead, /carrel-research nonexistent, cloud_consent display) + drift |
| `reviews/009-audit-adversarial.md` | Codex 12-month-on-call lens: trust enforcement gap, sensitivity routing gap, narrative shadow state, 3 predicted bug classes |
| `specs/010-policy-module.md` | v0.7.0 spec: `src/carrel/policy/sensitivity.py` owns sensitivity routing with 16-row matrix; `--explain` rationale flag — **fully implemented in v0.7.0** (closes 009 A2 / Codex §2) |
| `specs/011-profile-sync-architecture.md` | v0.7.0 spec: regenerators for the 4 mirror surfaces (`my-environment.md`, `automation-prompt.md`); drift-check for vault `CLAUDE.md` via HTML-comment markers — **fully implemented in v0.7.0** (closes 009 A3 / Codex §3,§6) |
| `reviews/012-pre-pilot-windows-sweep.md` | Pre-pilot adversarial sweep on Windows-specific code paths (Codex + manual fallback). Four HIGH/MEDIUM fixes shipped before push to origin: Windows Obsidian/Zotero detection paths, cross-platform `disk_free` via `shutil.disk_usage`, `install.ps1` `$LASTEXITCODE` checks, CRLF-tolerant frontmatter regex in `check-environment.js`. |
| `specs/013-model-teammates.md` | v0.8.1 spec: multi-model agent integration (Codex/ChatGPT, Gemini, Kimi) via community CC plugins; interview beat + state-neutral Phase 5b + `/carrel-teammates` + `model-teammates` skill + `model_teammates` profile field + single-line dashboard surface. Three trim passes shaped the final shape — started with a policy module, CLAUDE.md marker, cheat sheet rendering, 4-value enum, and vendored install references; ended with a thin wrapper around the stable upstream plugins. |
| `reviews/013-review-codex.md` | Codex initial adversarial review: 2 BLOCKERs (code-level sensitivity gate; vendored install references) + 1 HIGH (Phase 5b setup-state gap) + 2 MEDIUM + 1 LOW. Most declined as over-engineered; factual Kimi-install fix applied. |
| `reviews/013-review-kimi.md` | Kimi initial second-pair-of-eyes: 2 HIGH fixes (Kimi CLI install command, migration test-count arithmetic). Hardening recs (casing validator, drift plumbing) declined. |
| `reviews/013-trim-codex.md` | Deletion-first review (code): CUT `/carrel-teammates` content (→ delegate), CUT dashboard rendering (→ single line), TRIM `ModelTeammateStatus` (→ 3 values), consolidate constants, trim spec/migration narrative. Applied. |
| `reviews/013-trim-kimi.md` | Deletion-first review (prose): 62% reduction target across 8 files. Research-moves table appeared 7× (collapsed to skill + interview); sensitivity rule appeared 7× (collapsed to skill). Applied. |
| `specs/014-cc-plugin-v090.md` | v0.9.0 spec: CC plugin architecture normalization + feature adds. Originally drafted as cross-CLI port (Codex + Kimi); re-scoped to CC-only after triage. Ships 7 new CLI subcommands (extract deterministic ops from `/feedback`, `/migrate`, `/mirror`, `/reflect`, `/share`, `/batch`, `/automate`), 3 skill enrichments (absorb orchestration prose), ~7 wrapper shrinks with `${ARGS}` convention, 3 CC feature adds (marketplace metadata expansion, `UserPromptSubmit` hook for per-turn context, `PreToolUse` Bash matcher for sensitivity gate). Cross-CLI work parked as Future Work pending demand signal. |
| `reviews/014-investigation-feasibility.md` | Cross-CLI feasibility synthesis: CC / Codex / Kimi comparison + porting verdict (Codex ~70% portable, Kimi ~30% today, ~80% if #1714 lands). |
| `reviews/014-investigation-codex-plugins.md` | Initial Codex CLI plugin system survey. |
| `reviews/014-investigation-codex-deep-gaps.md` | Codex plugin root env var + agent TOML schema + subagent surface. Confirms Codex honors `${CLAUDE_PLUGIN_ROOT}` for CC compat. |
| `reviews/014-investigation-kimi-gaps.md` | Kimi #1714 status (open, 25-30% merge probability in 6 months per Kimi reviewer) + subagent surface (actual built-ins are `default` + `okabe`, not the earlier-cited `coder`/`explore`/`plan`). |
| `reviews/014-investigation-carrel-mapping.md` | Carrel plugin component inventory + CC plugin spec summary. |
| `reviews/014-investigation-commands-vs-skills.md` | Command-to-skill coverage map: 47% REDUNDANT, 27% PARTIAL, 27% UNIQUE. Data behind the v0.9.0 architecture-normalization rationale. |
| `reviews/014-review-codex.md` | Cross-CLI draft Codex adversarial review. 1 factually wrong claim (16 commands; verified 15), 2 valid concerns (skill-discovery fallback, `setup-interviewer` state-machine loss). |
| `reviews/014-review-kimi.md` | Cross-CLI draft Kimi second-pair-of-eyes. Skill auto-discovery mechanism unconfirmed, subagent pre-registration barrier, hook handler path resolution gap. |
| `reviews/014-review-internal.md` | Cross-CLI draft code-architect feasibility pass. 8 CLI naming corrections, `host/` → `build/` rename, `PluginBuilder` ABC → `BUILDERS: dict[Target, Callable]` dispatch dict, templates `importlib.resources` migration. |
| `reviews/014-cc-only-trim.md` | CC-only re-scope: triaged 24 original Phase 1 deliverables; 10 KEEP, 5 MODIFY, 9 DROP. Effort cut from ~2 large units to ~1. |
| `reviews/014-cc-feature-gap.md` | CC plugin feature audit: top 3 unused features adopted in v0.9.0 (marketplace metadata, `UserPromptSubmit`, `PreToolUse` Bash matcher). |
| `reviews/014-impl-review-plugin-validator.md` | Pre-commit audit (1/4): plugin structural validity — valid-with-warnings; 2 hook JSON shape warnings later confirmed as bugs by code-reviewer. |
| `reviews/014-impl-review-codex.md` | Pre-commit audit (2/4): codex adversarial pass — 1 HIGH (mirror prose routing), 4 MED (hook truncation, pending-decisions dedupe, silent failure modes, migration doc gaps). |
| `reviews/014-impl-audit-synthesis.md` | Pre-commit audit synthesis: consolidates all 4 reviewer findings (plugin-validator, code-reviewer, kimi, codex), enumerates the 11 fixes applied + 4 deferred, sign-off for commit. Includes meta-lessons about skill↔CLI contract drift and adversarial-reviewer convergence as quality signal. |
| `reviews/2026-07-10-freshness-skill-audit.md` | Freshness + skill-contract readiness evidence (Codex, skill-first branch): typed/portable runtime alignment, upstream re-pins (Obsidian Bases, Hermes Wiki 2.1, JSON Canvas 1.0, Cowork scheduling), full verification-gate table. |
| `reviews/2026-07-10-swarm-findings.md` | Branch-wide adversarial review log (kimi-review + 40-agent verification workflow + 10-target kimi-swarm): 3 maintainer decisions (host-split, advisory bootstrap, network-lite YouTube), by-design dismissals, falsified reviewer claims, and the low-severity backlog fully resolved with a per-item table. |

## Release arc summary

| Version | Theme | Specs landed |
|---------|-------|--------------|
| v0.5.3 | Deployment readiness sprint | 008 review tier 0-3 fixes |
| v0.5.4 | Holistic audit follow-through | 009 review tier 0-3 fixes |
| v0.6.0 | Trust enforcement | 008 |
| v0.7.0 | Cross-platform + control plane closure | 006, 007, 010, 011 |
| v0.9.0 | CC plugin architecture normalization + feature adds | 014 (CC-only scope) |
