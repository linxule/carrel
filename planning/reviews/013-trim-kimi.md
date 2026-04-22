# 013-trim-kimi.md — Deletion-First Review of Model Teammates Prose

Goal: shrink the teammate surface by 40–60%. Every paragraph must earn its keep. Claude already knows how npm works, how plugins install, and what HIGH sensitivity means.

---

## 1. `commands/carrel-teammates.md`

**Current:** 57 lines. **Target:** ~15 lines.

- **Delete lines 7–8** ("Most researchers don't realize this is possible…"). This sentence appears in six other files. The command doc should open with the trigger, not the pitch.
- **Delete lines 9–15** ("When to Use" list). Every bullet is either obvious from the description field or duplicates `skills/model-teammates/SKILL.md` lines 24–30.
- **Delete lines 16–25** ("What Happens" six-step recap). The skill already owns this flow. Replace with one sentence: *Delegates to the `model-teammates` skill.*
- **Delete lines 27–37** (Core Framing table). The table is canonical in the skill; the command doc doesn't need its own copy. If the skill is the source of truth, the command should just reference it.
- **Delete lines 39–47** (Sensitivity block). This is repeated almost verbatim in the skill (lines 191–199), the interview protocol, and CLAUDE.md. Sensitivity is a skill-level concern; the command doc shouldn't duplicate policy.
- **Delete lines 49–57** (Related). Reduce to: *Skill: `model-teammates`. Spec: `planning/specs/013-model-teammates.md`.* The upstream plugin list is noise—Claude discovers plugins via `/plugin marketplace`.

---

## 2. `skills/model-teammates/SKILL.md`

**Current:** 221 lines. **Target:** ~80 lines. This file is the canonical home for teammate logic, but it hand-holds Claude through steps Claude can infer.

- **Delete lines 8–10** (opening paragraph). The description field in the YAML front matter already says this. The skill opens twice.
- **Delete lines 24–30** ("When to Use"). Every bullet duplicates the command doc or the setup skill. The trigger list in the YAML front matter is sufficient.
- **Delete lines 46–48** (sensitivity paragraph in Orientation). This is duplicated by the dedicated "Sensitivity gating" section at lines 191–199. One canonical location is enough.
- **Replace lines 50–63** (Conversation flow + long quote + four numbered steps) with two sentences:
  > Start with the research-move framing. Ask which subscriptions they already have, then run the install protocol for each chosen teammate. Record `interested` for deferred, `skipped` for declined.

  The numbered steps (1–4) explain how to have a conversation that any competent interviewer already understands. "Never push all three" (line 63) is good judgment but implicit in "run the install protocol for each chosen teammate."
- **Trim Install Protocols (lines 65–170)** to plugin-specific commands only. Claude knows how `npm install -g`, `codex login`, and `gemini auth` work. The bash blocks for CLI install are upstream documentation, not Carrel logic.
  - **Codex (lines 69–99):** Keep only the `/plugin` commands and `/codex:setup`. Delete the npm install block (lines 73–82). Delete "Research uses" (lines 95–99)—those slash commands appear in `/help` once the plugin is installed.
  - **Gemini (lines 101–137):** Keep only the `/plugin` commands and the verification one-liner. Delete the npm/brew block (lines 105–115). Delete "Research uses" (lines 133–137).
  - **Kimi (lines 139–170):** Keep only the `/plugin` commands and `/kimi:setup`. Delete the npm install block (lines 143–151). Delete lines 153 ("If the npm install fails…")—hedging about distribution drift that adds words without adding certainty. Delete "Research uses" (lines 165–170).
- **Delete lines 172–189** (State writeback). Replace with one sentence:
  > After each change, update `model_teammates` in `.carrel/environment.json` and regenerate the dashboard (`carrel vault dashboard --vault <path> --force`).

  The Python code example (lines 176–180) is something Claude writes in its sleep. Lines 187–189 mention `check-sync` and `add-markers` for a CLAUDE.md marker that **was explicitly dropped in the second trim** (per spec lines 176–181); this is dead text.
- **Trim lines 191–199** (Sensitivity gating). The last two sentences ("Carrel does not enforce at the plugin boundary… That's structural.") add nothing. Claude knows that plugins run out-of-process. Cut to:
  > HIGH → don't propose; record `skipped`. MEDIUM → surface but confirm consent. LOW → proceed.
- **Trim lines 201–210** (Removing a teammate). Four steps is a listicle for `npm uninstall` and a JSON edit. Replace with:
  > Uninstall the plugin, optionally remove the CLI, set status to `removed`, regenerate the dashboard.
- **Delete lines 212–221** (Related). The skill knows its own name.

---

## 3. `skills/environment-setup/references/interview-protocol.md`

**Current:** 179 lines. **Target for teammate section:** ~12 lines (down from 27).

- **Delete lines 69–79** (Capture block + JSON example + status value glossary). The skill's Orientation already shows the JSON shape and defines the four statuses. The interview protocol should capture intent, not teach the schema.
- **Delete line 80** (Sensitivity caveat). This duplicates the skill's Sensitivity gating section and the setup skill's Step 6b. One sentence in the skill is canonical; the interview protocol shouldn't carry policy.
- **Keep lines 54–68** (the script and "Listen for"), but trim the script if the skill is also keeping its quote. Actually, the interview script is the only place a literal script belongs. The skill should drop its quote and just say "use the research-moves framing from the interview protocol."

---

## 4. `commands/carrel-setup.md`

**Current:** 173 lines. **Target for Phase 5b:** ~3 lines (down from 9).

- **Delete lines 84–92** and replace with:
  > **Phase 5b: Model Teammates.** Delegate to the `model-teammates` skill. Record status in `model_teammates`. HIGH sensitivity → default `skipped`. No setup-state transition—`/carrel-teammates` is re-runnable standalone.

  The current text repeats the research framing ("Codex for adversarial review…") that lives in the skill and interview protocol. It also repeats the "state-neutral / why this isn't a tracked phase" rationale that is explained in the skill and the spec.

---

## 5. `skills/environment-setup/SKILL.md`

**Current:** 250 lines. **Target for Step 6b:** ~3 lines (down from 7).

- **Delete lines 153–159** and replace with:
  > **Step 6b: Offer Model Teammates.** Delegate to `model-teammates` skill. Record status. HIGH sensitivity → default `skipped`.

  "Most researchers don't realize…" appears in the skill's own intro, the command doc, the interview protocol, and the spec—five times. We don't need it again here. "If you wait for them to ask, they never will" is motivational poster text, not instructions. "This step doesn't block setup progression…" is already explained in `/carrel-setup` Phase 5b and the spec.

---

## 6. `migrations/0.7.1-to-0.8.1.md`

**Current:** 89 lines. **Target:** ~35 lines.

- **Delete lines 6–15** ("What's new" teammate list). Replace with one sentence: *Adds `/carrel-teammates` and the `model-teammates` skill for Codex, Gemini, and Kimi integration.*
- **Delete lines 17–21** (Onboarding paragraph). This duplicates the setup command and the spec. One sentence is enough: *Interview protocol, `/carrel-setup` Phase 5b, and dashboard rendering updated.*
- **Delete lines 23–32** (Profile schema block). Replace with one line: *New `model_teammates: dict[str, ModelTeammateStatus]` field on `ResearcherProfile`.*
- **Delete lines 34–37** (Dashboard paragraph). Replace with one line: *Dashboard renders a "Model Teammates" section via `carrel vault dashboard --force`.*
- **Delete lines 50–57** ("Note for researchers already past setup"). This is explaining that a standalone command works standalone. The command doc and the spec already cover this. It's redundant with the existence of `/carrel-teammates`.
- **Trim lines 76–83** (Design note). It's useful context, but the sentences about why the marker was dropped are repetitive with the spec's "Second trim" section. Keep one sentence: *CLAUDE.md marker and cheat-sheet section were dropped as duplicative.*
- **Delete lines 85–89** (Related). If the reader is in the migration file, they already know where the spec lives.

---

## 7. `planning/specs/013-model-teammates.md`

**Current:** 190 lines. **Target:** ~90 lines.

- **Trim lines 9–23** (Problem). The first paragraph says "researchers have paid subscriptions and plugins make this easy." That's the whole problem. Delete the three "gaps" sentences (lines 19–23)—they're just restating the goals.
- **Delete lines 25–27** ("Why Now"). This is a user-requested feature; the spec doesn't need a market-analysis paragraph. Replace with one sentence: *Requested by user; pilot cohort already holds these subscriptions.*
- **Delete lines 29–34** (Goals). These four bullets are obvious from the rest of the spec and the acceptance criteria. They add no decisions.
- **Trim lines 41–51** (Research framing). The table is canonical, but the paragraph before it ("Not 'bring in other models.' That's technical framing.") is tone-setting that could be one sentence. Actually, delete the paragraph—Claude can read the table.
- **Trim Locked Decisions (lines 53–63)**. Several cells are essays:
  - "CLI install responsibility" (lines 61): The rationale is longer than the decision. Replace rationale with: *Interactive auth requires human hands.*
  - "Sensitivity gating" (lines 62): A paragraph that says the same thing as the skill. Replace with: *Skill-level advisory; code enforcement can't intercept runtime plugin calls.*
  - "Version bump" (lines 63): Delete the parenthetical—it's a changelog, not a decision rationale.
- **Delete lines 102–114** (Interview update block). This is a full copy-paste of the interview protocol's script. The spec should say *"Update interview protocol with the two-question framing; see `references/interview-protocol.md`"*—not reproduce it.
- **Delete lines 116–118** (Setup integration paragraph). This duplicates the setup command and setup skill. Replace with: *Phase 5b: invoke `model-teammates` skill, state-neutral.*
- **Delete lines 120–126** (Dashboard surfacing). This duplicates the migration and the skill. Replace with: *Extend `render_dashboard` with a `{{model_teammates}}` placeholder.*
- **Delete lines 149–161** (Acceptance criteria). This is a shipped feature. The checklist is just proof-of-completion noise. If we must keep it, move it to a comment block or delete it outright. It duplicates the implementation sections above it.
- **Trim lines 162–183** (Review plan / Resolution / Second trim). This is historical color. Keep the resolutions (lines 167–174) and the trim list (lines 178–181), but delete the file references (lines 164–166)—those are in `planning/README.md`. The "Factual fixes" lines (185–189) can be one line.

---

## 8. `CLAUDE.md` (repo root)

**Current:** 193 lines. **Target for Model Teammates section:** ~4 lines (down from 12).

- **Delete lines 116–127** and replace with:
  > **Model Teammates (v0.8.1).** `/carrel-teammates` brings Codex, Gemini, and Kimi into Claude Code via community plugins. Profile field: `model_teammates: dict[str, ModelTeammateStatus]`. Skill: `skills/model-teammates/SKILL.md`.

  The current section has six bullet points that repeat: proactive surfacing, research framing, profile field, sensitivity gating, dashboard, and skill/spec references. All of that is canonical in the skill and command doc. CLAUDE.md is the project's memory, not a second copy of the skill. The vocabulary sentence ("teammates disambiguates from…") is already in the spec's Naming section and adds no operational value here.

---

## Cross-File Redundancy Table

| Prose | Appears In | Count | Verdict |
|---|---|---|---|
| "Most researchers don't realize this is possible" | command doc, skill, interview protocol, setup skill, spec | 5 | **Keep only in interview protocol** (the script). Delete everywhere else. |
| Research-moves table (Codex=adversarial, Gemini=long-context, Kimi=delegated) | command doc, skill, interview protocol, setup command, setup skill, spec, CLAUDE.md | 7 | **Keep only in skill** (canonical). Interview protocol keeps the spoken version; all other copies go. |
| "HIGH sensitivity → default skipped / MEDIUM → confirm consent / LOW → proceed" | command doc, skill (×2), interview protocol, setup command, setup skill, CLAUDE.md | 7 | **Keep only in skill's Sensitivity gating section** (3 lines). Delete all other instances. |
| Full sensitivity explanation (cloud-backed, skill-level advisory, bypass Carrel) | command doc, skill, interview protocol | 3 | **Keep only in skill.** |
| "Phase 5b is state-neutral / re-runnable standalone" rationale | setup command, setup skill, spec, migration | 4 | **Keep only in setup command.** One sentence elsewhere is enough. |
| Profile schema (`model_teammates` dict, 4 statuses) | skill, migration, spec, CLAUDE.md | 4 | **Keep only in spec** (schema extension block) and code (`models.py`). Delete from migration and CLAUDE.md. |
| "No API keys handled by Carrel" | command doc, spec, CLAUDE.md | 3 | **Keep only in spec Non-goals** (one bullet). |
| Install protocol shape (CLI install → auth → plugin install → verify) | skill, spec | 2 | Not 3+, but the skill's per-teammate bash blocks are still deletable because Claude knows npm. |
| "Teammates disambiguates from agents and collaborators" | spec, CLAUDE.md | 2 | Delete from CLAUDE.md; keep in spec Naming. |

---

## Bottom Line

If these cuts land, the teammate prose drops from roughly **1,050 lines** across 8 files to roughly **400 lines** — a **62% reduction**. The remaining text is: the skill's 3-line sensitivity rule, the skill's trimmed install blocks (plugin commands only), the interview protocol's spoken script, the spec's locked-decisions table, and one-line references everywhere else. That's enough for a thin wrapper around upstream plugins.
