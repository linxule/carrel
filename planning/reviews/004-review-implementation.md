# 004: Implementation Compliance Review

**Reviewer**: Claude Opus 4.6 (adversarial)
**Date**: 2026-04-04
**Commits reviewed**: `1b9c620` (implementation), `decb26f` (review fixes)
**Verdict**: Implementation is substantially complete with minor gaps

---

## Acceptance Criteria Audit

### Must Have

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | `ResearcherProfile` supports `automation` field with typed enums and backward compat | **MET** | `models.py` lines 133-156. All types match spec exactly: `AutomationConfig`, `TrustLevel`, `AutomationModel`, `AutomationSchedule`. Default `AutomationConfig()` instantiation provides backward compat. |
| 2 | `/carrel-batch` converts a folder of mixed files sequentially with summary (interactive) | **MET** | `commands/carrel-batch.md` covers all 6 steps: enumerate, route, process sequentially, flag judgment calls, file to vault, summary. Recognized types match spec. |
| 3 | `/carrel-batch` headless mode writes judgment calls to `_meta/pending-decisions.md` | **MET** | "Headless Mode (Unattended)" section at line 98-116 of `carrel-batch.md`. Covers all spec requirements: skip routing confirmation, skip inline questions, write to pending-decisions.md, continue processing. |
| 4 | `/carrel-automate` interviews, updates env.json + CLAUDE.md + my-environment.md, generates prompt | **MET** | `commands/carrel-automate.md` has 10 steps covering all three file updates (Steps 4, 5, 6) and prompt generation (Step 7). |
| 5 | Generated prompt uses vault detection (not absolute path), includes unattended instructions, reads CLAUDE.md | **MET** | `skills/automation/SKILL.md` line 145: "The prompt does NOT embed an absolute vault path." Example prompt (lines 155-216) shows vault detection pattern, UNATTENDED mode declaration, and CLAUDE.md reading in setup step 4. |
| 6 | Session-start hook surfaces morning briefs, active plans, pending decisions, and pending approvals | **MET** | `hooks/check-environment.js` `checkAutomation()` function implements all four checks (checks 2-5 in the spec's C4 list). |
| 7 | `last_session_start` tracked in plugin-state.json with safe write | **MET** | `safeWriteJson()` function (line 62-66) uses temp-file-then-rename pattern. Written at check 7 (line 173-177). |
| 8 | `_meta/plans/` convention with simple frontmatter (regex-parseable) | **MET** | `parseFrontmatter()` function (line 33-46) uses the specified regex `/^---\n([\s\S]*?)\n---/` with line-by-line key-value extraction. Plan format described in automation skill. |
| 9 | `_meta/pending-decisions.md` format with checkbox resolution | **MET** | Format documented in automation skill (lines 264-275) and batch command (line 107). Matches spec exactly. |
| 10 | `_meta/pending-approvals.md` structured executable format | **MET** | Documented in automation skill (lines 279-294). Format matches spec's example with date, type, action description. |
| 11 | Analytical threads convention in vault-ops skill | **MET** | `skills/vault-ops/SKILL.md` "Analytical Threads" section (lines 97-126). Structure, principles, and "when to suggest" all match spec B4. |
| 12 | `/carrel-mirror` synthesizes reflections + capability log + friction log (interactive) | **MET** | `commands/carrel-mirror.md` covers all 5 data sources (reflections, capability-log, friction_log, vault stats) and all 5 synthesis dimensions from spec. |
| 13 | Four trust levels documented and encoded in prompt generation | **MET** | All four levels with correct names and behaviors in automation skill (lines 91-110) and overnight-prompt-guide.md (lines 30-56). Levels 3-4 marked experimental. |
| 14 | All new `_meta/` directories created lazily | **MET** | Automation skill line 354: "`/carrel-automate` initializes `pending-decisions.md` and `pending-approvals.md` with headers. `briefs/`, `suggestions/`, `mirror/`, `feedback/`, and `plans/` are created on first use." Hook gates on `_meta/briefs/` existence (line 70). |

### Should Have

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | Research-partner aware of plans, threads, briefs, pending decisions/approvals | **MET** | `skills/research-partner/SKILL.md` "Automation Awareness" section covers all five artifacts with behavioral guidance. |
| 2 | Environment-setup Step 9 offers automation opt-in | **MET** | `skills/environment-setup/SKILL.md` Step 9 (lines 165-175) matches spec B3 verbatim, including cost mention and skip option. |
| 3 | `/carrel-automate` accessible both standalone and during setup | **MET** | Step 9 in environment-setup says "Run `/carrel-automate` now to configure it, or note it for later." `carrel-automate.md` line 14 says "Phase 8 of `/carrel-setup` (automation opt-in)". |
| 4 | Cost estimates presented during automation setup | **MET** | `carrel-automate.md` Step 10 (lines 122-131). Also in automation skill "Cost Model" section (lines 316-329). |
| 5 | Automation review cadence warning in session-start hook | **MET** | `check-environment.js` lines 161-169. Reads `last_reviewed` and `review_cadence`, computes staleness against cadence map (monthly=30, quarterly=90, biannual=180). |
| 6 | Trust levels 3-4 briefs include specific revert instructions for every action | **MET** | Automation skill example prompt (line 99): "Logs every action + specific revert instructions." Morning brief format (line 252): "Revert: `mv papers/smith-2026/paper.md inbox/smith-2026.pdf`". Overnight prompt guide level 3-4 blocks both include revert instruction requirements. |
| 7 | Confidence rubric for cross-linking suggestions | **MET** | Automation skill lines 104-109. Three tiers: High (shared citation AND shared concept AND substantial), Medium (OR), Low (loose thematic). Only high in brief. Matches spec exactly. |

### Nice to Have

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | `_meta/automation-prompt.prev.md` for diff comparison | **MET** | `carrel-automate.md` Step 7 (line 93): "save the old version as `_meta/automation-prompt.prev.md`". Automation skill line 147 confirms. |
| 2 | Vault health delta tracking (stats compared to last brief) | **MET** | Morning brief format includes delta: "Papers: N (+N since last brief)" (automation skill line 237). |
| 3 | Periodic archiving of resolved items from pending-decisions.md | **PARTIALLY MET** | Mentioned once in automation skill line 275 ("Periodically archive resolved items (nice to have)") but no archiving mechanism is specified. Acceptable for "nice to have." |

---

## Model Code (C1)

Comparing `src/carrel/models.py` against spec section C1.

| Spec element | Spec definition | Implementation | Match? |
|---|---|---|---|
| `TrustLevel` enum | `ADVISORY`, `CONSULTATIVE`, `DELEGATED`, `PARTNERSHIP` | Identical | Yes |
| `TrustLevel` comments | Inline comments describing each level | No inline comments | **Minor omission** — cosmetic only |
| `AutomationModel` enum | `SONNET`, `OPUS` | Identical | Yes |
| `AutomationSchedule` enum | `DAILY`, `WEEKDAYS`, `WEEKLY` | Identical | Yes |
| `AutomationConfig.enabled` | `bool = False` | `bool = False` | Yes |
| `AutomationConfig.inbox_processing` | `bool = True` | `bool = True` | Yes |
| `AutomationConfig.vault_health` | `bool = True` | `bool = True` | Yes |
| `AutomationConfig.cross_linking_suggestions` | `bool = True` | `bool = True` | Yes |
| `AutomationConfig.gap_analysis` | `bool = False` | `bool = False` | Yes |
| `AutomationConfig.draft_feedback` | `bool = False` | `bool = False` | Yes |
| `AutomationConfig.reflection_synthesis` | `bool = True` | `bool = True` | Yes |
| `AutomationConfig.trust_level` | `TrustLevel = TrustLevel.ADVISORY` | Identical | Yes |
| `AutomationConfig.model` | `AutomationModel = AutomationModel.SONNET` | Identical | Yes |
| `AutomationConfig.schedule` | `AutomationSchedule = AutomationSchedule.DAILY` | Identical | Yes |
| `AutomationConfig.review_cadence` | `Literal["monthly", "quarterly", "biannual"] = "quarterly"` | Identical | Yes |
| `AutomationConfig.last_reviewed` | `str \| None = None` | `str \| None = None` | Yes |
| `ResearcherProfile.automation` | `AutomationConfig = Field(default_factory=AutomationConfig)` | Identical | Yes |

**Verdict**: Perfect match on all field names, types, and defaults. The only difference is the absence of inline `# comments` on enum values, which is purely cosmetic.

---

## Hook Expansion (C4)

Comparing `hooks/check-environment.js` `checkAutomation()` against the 7 specified checks.

| Spec check | Implementation | Match? |
|---|---|---|
| 1. Read `last_session_start` from plugin-state.json | Lines 74-78: reads from `pluginState.last_session_start` | Yes |
| 2. Check for new morning briefs in `_meta/briefs/` | Lines 83-96: reads dir, sorts by filename, compares against `lastSessionStart` | Yes |
| 3. Check for active plans in `_meta/plans/` | Lines 99-119: reads up to 5 plan files, regex-extracts frontmatter, outputs max 3 active | Yes |
| 4. Check for pending decisions | Lines 123-129: `countUncheckedItems()` on `_meta/pending-decisions.md` | Yes |
| 5. Check for pending approvals | Lines 133-139: `countUncheckedItems()` on `_meta/pending-approvals.md`, with the spec's suggested output message | Yes |
| 6. Check automation status (no recent briefs + stale review) | Lines 141-170: checks both conditions — no briefs in 7 days AND stale `last_reviewed` against cadence | Yes |
| 7. Write `last_session_start` to plugin-state.json (safe write) | Lines 173-177: `safeWriteJson()` using temp-file-then-rename | Yes |

**Additional spec requirements checked:**
- Gate on `_meta/briefs/` existence: Line 70 — `if (!fs.existsSync(briefsDir)) return;` Yes.
- Regex frontmatter parser: `parseFrontmatter()` at lines 33-46 uses `/^---\n([\s\S]*?)\n---/` exactly as specified. Yes.
- Cap plan listing at 3: Line 108 — `if (activePlans.length >= 3) break;` Yes.
- Timeout increased to 15s: `hooks.json` line 10 — `"timeout": 15`. Yes.
- Stdlib-only (no YAML parser): All parsing is regex/string-based. Yes.

**Findings:**

1. **Brief summary not parsed**: The spec's example output says `"Morning brief ready (YYYY-MM-DD) — inbox: 3 processed, 1 pending. 2 suggestions."` — parsing the brief's content to extract counts. The implementation (line 93) outputs only `"Morning brief ready (${latestDate}) — read it to start your session"` without parsing brief content. This is a **reasonable simplification** — parsing markdown brief content in the hook would be fragile and the hook is already at risk of timeout. However, it is a deviation from the spec's example output format.

2. **Timezone handling in brief date comparison**: Line 91 creates `latestBriefTime` with `new Date(latestDate + 'T00:00:00Z')` (UTC), but `now` at line 80 is local time via `new Date()`. This could cause a brief dated today to appear "new" or "not new" depending on timezone offset. Low severity — worst case is a brief not being surfaced until the next day, or being surfaced one extra time.

3. **Inconsistent timezone within same function**: Line 152 uses `new Date(briefs[0].replace('.md', '') + 'T00:00:00')` (local time, no Z suffix) while line 91 uses UTC (`'T00:00:00Z'`). Two brief date parses in the same function use different timezone conventions.

---

## Commands (A1, A2, A3)

### A1: `/carrel-batch` (`commands/carrel-batch.md`)

| Spec requirement | Implementation | Status |
|---|---|---|
| Enumerate files in folder (default `inbox/`) | Step 1: "Default folder is `inbox/`; accepts any path." | MET |
| Routing per file: PDF->liteparse, docx->markitdown, audio->coli, YouTube | Step 1 recognized types table + Step 2 routing confirmation | MET |
| Process sequentially, no parallelism | Step 3: "Run one file at a time. Do not parallelize." | MET |
| Filer-level idempotency (SHA-256) | Step 3: "The filer checks SHA-256 against existing vault files." | MET |
| Summary: N converted, skipped, failed, need input | Step 6: all four categories shown | MET |
| Interactive: flag judgment calls inline | Step 4: 4 example scenarios with inline questions | MET |
| Headless: write to pending-decisions.md | "Headless Mode" section | MET |
| Performance note (~30s/PDF) | Step 3: "liteparse takes ~30s per PDF. 40 PDFs ≈ 20 minutes." | MET |

### A2: `/carrel-automate` (`commands/carrel-automate.md`)

| Spec requirement | Implementation | Status |
|---|---|---|
| Check current automation state | Step 1 | MET |
| First-time interview (capabilities, trust, model, schedule) | Step 2: covers all 5 interview areas | MET |
| Returning: show config, ask what to change | Step 3 | MET |
| Update environment.json | Step 4 | MET |
| Update vault CLAUDE.md | Step 5 | MET |
| Update `_meta/my-environment.md` | Step 6 | MET |
| Generate prompt template | Step 7 | MET |
| Create `_meta/` dirs + init files | Step 8 | MET |
| Guide Desktop App setup | Step 9 | MET |
| Cost estimates | Step 10 | MET |

### A3: `/carrel-mirror` (`commands/carrel-mirror.md`)

| Spec requirement | Implementation | Status |
|---|---|---|
| Read `_meta/reflections/` (all or since last mirror) | Step 1: "all entries, or only since the last mirror" | MET |
| Read `_meta/capability-log.md` | Step 2 | MET |
| Read `_meta/friction_log.md` | Step 3 | MET |
| Read vault stats | Step 4: "Papers: count by field and year, Notes: count by type, Draft status" | MET |
| Synthesize: reading, creating, themes, friction, trajectory | Step 5: all 5 dimensions listed | MET |
| Interactive mode: present conversationally, discuss | "Interactive (default)" mode section | MET |
| Scheduled mode: write to `_meta/mirror/YYYY-MM.md` | "Scheduled (with `--write`)" mode section | MET |

---

## Skills (B1-B5)

### B1: Automation skill (`skills/automation/SKILL.md`)

| Spec requirement | Implementation | Status |
|---|---|---|
| Triggers: schedule, automate, overnight, background, morning brief, unattended | Description line: covers all trigger words plus extras | MET |
| How scheduled automation works (Desktop App) | "How Scheduled Automation Works" section | MET |
| Automation contract (environment.json) | "The Automation Contract" section with full JSON example | MET |
| Reorganization levels (trust) | "Graduated Trust Levels" section with table and behavioral rules | MET |
| Headless behavior | "Headless Mode Behavior" section | MET |
| Prompt template generation | "Prompt Generation Logic" section + example prompt | MET |
| Morning brief format | "Morning Brief Format" section | MET |
| Pending decisions workflow | "Pending Decisions Workflow" section | MET |
| Desktop task setup guide | "Setting Up a Desktop Scheduled Task" section | MET |
| Reference: `overnight-prompt-guide.md` | File exists at `references/overnight-prompt-guide.md` | MET |
| Reference: `desktop-scheduling-guide.md` | File exists at `references/desktop-scheduling-guide.md` | MET |

### B2: Generated prompt templates

The spec says these are "not shipped as static files" but generated per-researcher by `/carrel-automate`. The implementation matches — the automation skill contains the generation logic and an example prompt, and `/carrel-automate` Step 7 generates it. No static prompt template file exists. **MET**.

### B3: Environment-setup extension

Spec: "Add Step 9 (after cheatsheet generation, before wrap-up)." Implementation adds Step 9 with matching content and renumbers wrap-up to Step 10. **MET**.

### B4: Vault-ops extension (analytical threads)

All spec requirements present: `notes/threads/` structure, thread overview note with lens/questions/sources/status, four status values, "no primary thread" and "abandoned stays" principles. Implementation enriches with tag convention and "when to suggest" guidance. **MET**.

### B5: Research-partner extension

All five awareness areas from spec: active plans, analytical threads, morning brief, pending decisions, pending approvals. Each includes behavioral guidance for how to surface naturally in conversation. **MET**.

---

## Implementation Order (13 steps)

| Step | Description | Completed? | Evidence |
|---|---|---|---|
| 1 | Models: AutomationConfig + enums | Yes | `src/carrel/models.py` lines 30-46, 133-156 |
| 2 | Vault structure: plan format, pending formats, `_meta/` conventions | Yes | Documented in automation skill sections |
| 3 | Session-start hook expansion | Yes | `hooks/check-environment.js` `checkAutomation()` |
| 4 | `/carrel-batch` (interactive mode) | Yes | `commands/carrel-batch.md` Steps 1-6 |
| 5 | Vault-ops extension (analytical threads) | Yes | `skills/vault-ops/SKILL.md` new section |
| 6 | Research-partner extension | Yes | `skills/research-partner/SKILL.md` new section |
| 7 | Automation skill | Yes | `skills/automation/SKILL.md` (388 lines) |
| 8 | Update `/carrel-batch` with headless mode | Yes | `commands/carrel-batch.md` "Headless Mode" section |
| 9 | `/carrel-automate` | Yes | `commands/carrel-automate.md` |
| 10 | `/carrel-mirror` | Yes | `commands/carrel-mirror.md` |
| 11 | Environment-setup extension (Step 9) | Yes | `skills/environment-setup/SKILL.md` new Step 9 |
| 12 | Migration | Yes | `migrations/0.3.0-to-0.4.0.md` + `registry.json` entry |
| 13 | Version bump | Yes | `plugin.json` + `marketplace.json` both at 0.4.0 |

All 13 steps completed.

---

## Additional Findings

### 1. Advisory trust level bleeds into Consultative in example prompt (medium severity)

In the automation skill's example prompt (lines 210-212), the Advisory trust level section says:

```
- Write all suggestions to _meta/suggestions/. Never act on vault files.
- Write proposed actions to _meta/pending-approvals.md if you identify
  clear filing decisions, but do not execute them.
```

The second bullet (writing to `pending-approvals.md`) is a **Consultative** behavior, not Advisory. The spec's C2 table clearly distinguishes:
- Advisory: "Writes all suggestions to `_meta/suggestions/`. Never touches vault files."
- Consultative: "Writes suggestions AND proposed actions to `_meta/pending-approvals.md`"

The trust level table earlier in the same file (lines 96-97) correctly describes Advisory as suggestions-only. This is an **internal inconsistency** within the automation skill. If taken literally by the overnight agent, Advisory would behave like Consultative.

**Fix**: Remove the second bullet from the Advisory block in the example prompt.

### 2. Hook brief output lacks content parsing (low severity)

The spec's example output says: `"Morning brief ready (YYYY-MM-DD) — inbox: 3 processed, 1 pending. 2 suggestions."` The implementation outputs: `"Morning brief ready (${latestDate}) — read it to start your session"`. This is a reasonable simplification — parsing markdown in a 15s-timeout hook is fragile — but deviates from the spec's stated format.

### 3. Timezone inconsistency in hook (low severity)

Two date comparisons in `checkAutomation()` parse dates differently:
- Line 91: `new Date(latestDate + 'T00:00:00Z')` — UTC
- Line 152: `new Date(latestDate + 'T00:00:00')` — local time

Both should use the same convention. Since `last_session_start` is written as `now.toISOString()` (UTC), UTC is the correct convention for all date comparisons.

**Fix**: Line 152 should use `'T00:00:00Z'` for consistency.

### 4. No test coverage for new models (low severity, deferred OK)

The new enums and `AutomationConfig` model have no test verifying serialization/deserialization or backward compatibility (existing `environment.json` without `automation` key). Pydantic v2 handles this correctly by design, but explicit tests would lock it in.

---

## Summary

**Overall**: The implementation is faithful to the spec across all layers. All 14 "must have" criteria are met. All 7 "should have" criteria are met. 2 of 3 "nice to have" met, 1 partially met. All 13 implementation steps completed.

**Action items** (ordered by severity):

1. **Fix Advisory trust level bleed in example prompt** (medium): Remove the `pending-approvals.md` bullet from the Advisory block in `skills/automation/SKILL.md` example prompt (line 210-212). Advisory should only write to `_meta/suggestions/`.

2. **Fix timezone inconsistency in hook** (low): Line 152 of `check-environment.js` should use `'T00:00:00Z'` instead of `'T00:00:00'` for consistency with line 91.

3. **Consider adding model tests** (low, deferred OK): Add a test that validates `ResearcherProfile` instantiation with and without an `automation` key.

4. **Brief content parsing in hook** (informational): The spec showed parsed brief content in the hook output. Current generic message is a reasonable trade-off. If researchers request richer session-start output, this is the gap to close.
