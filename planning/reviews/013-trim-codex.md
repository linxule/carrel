## 1. `commands/carrel-teammates.md`

CUT

The command is almost pure indirection: its operative section says it "Delegates to the `model-teammates` skill" and then restates the same read/explain/install/writeback flow already present in the skill (`commands/carrel-teammates.md:16-25`; `skills/model-teammates/SKILL.md:24-31,34-49,65-189`). Its research-move table and sensitivity guidance are also duplicated from the skill rather than adding command-specific behavior (`commands/carrel-teammates.md:27-47`; `skills/model-teammates/SKILL.md:12-23,191-199`). I cannot verify command registration mechanics from the listed files, but content-wise this file is a second wrapper over the same instructions, which does not earn its own surface.

## 2. `ModelTeammateStatus`

TRIM

Nothing in the inspected implementation gives `skipped` or `removed` distinct behavior: the dashboard just stringifies whatever value is present (`src/carrel/vault/dashboard.py:35-45`), and the tests only prove that the values round-trip and render as text (`tests/test_model_teammates.py:14-18,31-47,73-99`). The only explicit defense of `removed` is prose in the skill saying it "preserves history," but no listed consumer reads that history differently from key absence (`skills/model-teammates/SKILL.md:201-210`). `skipped` is likewise interview memory, not product logic (`skills/environment-setup/references/interview-protocol.md:67-80`; `commands/carrel-setup.md:88-90`). Collapse this to `configured | interested`, and let absent mean "not active now" unless a downstream consumer actually needs a four-state taxonomy.

## 3. `KNOWN_MODEL_TEAMMATES` + `TEAMMATE_DESCRIPTIONS`

TRIM

The v1 set is declared twice: once as `KNOWN_MODEL_TEAMMATES` in `src/carrel/models.py:72` and again as the keys of `TEAMMATE_DESCRIPTIONS` in `src/carrel/vault/dashboard.py:17-21`, then pinned a third time in a test (`tests/test_model_teammates.py:21-23`). `_render_model_teammates()` already tolerates unknown keys and appends them after the known set (`src/carrel/vault/dashboard.py:31-39`), so the tuple is not enforcing schema or compatibility; it is only an ordering hint split away from the only human-facing metadata. If this surface stays, make one source of truth and derive the "known teammate" concept from it; if the dashboard goes, both declarations disappear.

## 4. Dashboard rendering

CUT

This is a second presentation layer over data whose canonical home is already `.carrel/environment.json`: the template calls the dashboard "Deterministic" from that file (`templates/dashboard.md:1-3`), and the interview protocol says the flat `ResearcherProfile` JSON is the canonical output (`skills/environment-setup/references/interview-protocol.md:105-107`). The teammate addition is almost entirely view glue: description registry, custom renderer, placeholder wiring, and a dedicated template section (`src/carrel/vault/dashboard.py:17-45,109-162`; `templates/dashboard.md:21-23`). The tests are also mostly renderer-string assertions (`tests/test_model_teammates.py:64-99`). I cannot verify the session-start hook from the listed files, but nothing here looks necessary for state correctness; it only duplicates state that Claude can already read directly.

## 5. Spec + migration + tests

TRIM

The spec is carrying release-process history that does not define the shipped feature: the "Review plan," "Resolution," "Second trim," and "Factual fixes applied" sections are all post-hoc narrative rather than behavior (`planning/specs/013-model-teammates.md:162-189`). The migration repeats that same story and duplicates verification bookkeeping, and its published counts conflict with the spec's later correction: migration says `237 passing / 9 new` while the spec says the actual result was `246 passing / 18 new` (`migrations/0.7.1-to-0.8.1.md:59-83`; `planning/specs/013-model-teammates.md:183-188`). In tests, the constant-value checks and v1-set check are low-signal (`tests/test_model_teammates.py:14-23`), and the dashboard string tests disappear entirely if the renderer is cut (`tests/test_model_teammates.py:64-99`).

## 6. `skills/model-teammates/SKILL.md`

TRIM

The file's longest section is a vendored install manual for three upstream plugins: Codex, Gemini, and Kimi each get hard-coded prereqs, install commands, auth steps, plugin commands, verification, and usage lists (`skills/model-teammates/SKILL.md:65-170`). The file itself shows why that is brittle: the Kimi block already has to warn that distribution details may move and the upstream repo is authoritative (`skills/model-teammates/SKILL.md:153-154`), and the spec explicitly says these install blocks were copied from upstream READMEs (`planning/specs/013-model-teammates.md:84-93`). Keep the research framing, state writeback, and sensitivity guidance (`skills/model-teammates/SKILL.md:12-23,172-199`), then have Claude read the upstream README on demand for current install steps.

## 7. Interview beat + Phase 5b

TRIM

The proactive offer is core UX, but the current wording is repeated across three surfaces: the interview protocol, the setup command, and the setup skill (`skills/environment-setup/references/interview-protocol.md:54-80`; `commands/carrel-setup.md:84-92`; `skills/environment-setup/SKILL.md:153-159`). The interview script alone carries a long quoted pitch with three bullets and two numbered questions (`skills/environment-setup/references/interview-protocol.md:58-65`), then Phase 5b restates the proactive rationale and the same `configured/interested/skipped` mapping (`commands/carrel-setup.md:86-92`). Trim the spoken copy to one sentence plus the two decision questions, and keep the operational detail in a single reference surface.

## 8. Other redundancy

CUT

`src/carrel/vault/templates.py:199-204` adds `/carrel-teammates` to the cheat sheet's "Next steps," which partially reintroduces a discoverability surface the spec and migration both say was intentionally trimmed away because the dashboard and Claude Code `/help` already cover it (`planning/specs/013-model-teammates.md:127-130,176-183`; `migrations/0.7.1-to-0.8.1.md:76-83`). If the dashboard section stays, this cheat-sheet bullet is a third prompt for the same feature; if the dashboard goes, `/carrel-setup` and the skill still surface teammates during onboarding and on demand (`commands/carrel-setup.md:84-92`; `skills/model-teammates/SKILL.md:24-31`). This is small copy, but it is still feature re-growth after an explicit trim decision.
