# Review 013 — Model Teammates: Kimi Second-Pair-of-Eyes

**Reviewer**: Kimi (via linxule/kimi-plugin-cc v0.2.0)
**Date**: 2026-04-21
**Spec**: `planning/specs/013-model-teammates.md`
**Target version**: 0.8.0
**Scope**: Uncommitted working-tree changes — full implementation review

---

## Summary verdict

The implementation is solid and the architecture is sound. No blockers. Two high-severity issues: one factual error in the install protocol that will cause researcher confusion, and one test count inconsistency in the migration file. Several medium issues around schema design trade-offs and marker edge cases. No regressions against the existing marker/validation infrastructure.

---

## Findings

### 1. Kimi CLI install command is a placeholder, not the real protocol — HIGH

**File**: `skills/model-teammates/SKILL.md`, Kimi install block

**The problem**:

```bash
# Install the Kimi CLI (example; consult upstream for current path)
bun add -g @moonshot/kimi-cli   # or the CLI's current distribution
```

The package name `@moonshot/kimi-cli` does not exist as a published npm/bun package. The Kimi CLI (`kimi-cli`) is distributed by MoonshotAI via GitHub, not via a bun/npm global install. The correct install path for the CLI referenced by this plugin — and visible in `scripts/companion.sh` and the plugin README — is:

- The plugin README at `/Users/xulelin/.claude/plugins/cache/kimi-marketplace/kimi/0.2.0/README.md` says: **"Kimi CLI on PATH — requires `--wire`, `--session`, and `--agent-file` support (recent versions)."** It does not prescribe a package manager install command.
- The kimi-cli source is at `https://github.com/MoonshotAI/kimi-cli`. As of the plugin's authorship, the CLI is installed via npm: `npm install -g kimi-cli` (the package name on npm is `kimi-cli`, not `@moonshot/kimi-cli`).

The comment "or the CLI's current distribution" acknowledges the uncertainty but does not resolve it — a researcher following this guide will run `bun add -g @moonshot/kimi-cli`, get a "package not found" error, and stop.

**Fix**: Replace the placeholder block with the actual install path. If the distribution mechanism is still in flux, say that explicitly and point to `https://github.com/MoonshotAI/kimi-cli` for current instructions. Do not invent a package name.

Suggested replacement for the Kimi install block in `skills/model-teammates/SKILL.md`:

```bash
# Install the Kimi CLI — source: https://github.com/MoonshotAI/kimi-cli
# Check the repo for the current install method; as of v0.2.0 of the plugin:
npm install -g kimi-cli

# Log in
kimi login

# Verify (confirms --wire support is available)
kimi --version
```

Note: the `bun` global tool flag is not relevant here. The Kimi CLI is an npm-distributed tool; using `bun add -g` instead of `npm install -g` is fine functionally but adds confusion given the rest of the block uses `kimi login`.

---

### 2. Migration file test count is wrong — HIGH

**File**: `migrations/0.7.1-to-0.8.0.md`

The migration file states:

> 237 passing (228 previously documented + 9 new teammate-specific tests in `tests/test_model_teammates.py` + additional marker/cheatsheet tests).

But `tests/test_model_teammates.py` contains **18 tests**, not 9. And the spec acceptance criteria says "18 new tests added." The arithmetic does not add up regardless: 228 + 18 = 246, not 237.

This is a documentation inconsistency, not a code bug, but migration files are read by researchers and future maintainers. A wrong test count undermines confidence in the record.

**Fix**: Run `uv run pytest --collect-only -q | tail -3` and put the actual passing count in the migration file.

---

### 3. Marker serialization is fragile for future enum additions — MEDIUM

**File**: `src/carrel/vault/sync.py`, `serialize_model_teammates`

The format `codex:configured,gemini:interested,kimi:skipped` uses `:` as field delimiter and `,` as record delimiter. The current four status values (`configured`, `interested`, `skipped`, `removed`) and three teammate names (`codex`, `gemini`, `kimi`) do not contain either character, so the format is safe now.

The risk is additive: if a future teammate name or status value contains `:` or `,`, the marker format silently produces a malformed string. Examples that would break:

- A teammate named `gpt-4o,turbo` (unlikely but the schema allows it — keys are free-form strings)
- A status value like `partially:configured` if the enum is extended

`parse_markers` in `src/carrel/vault/markers.py` uses a regex that matches `.*?` between the HTML comment tags, so the outer parse is not at risk. But any code that further parses the value by splitting on `,` then `:` (e.g., `raw_marker_values` in `env/validation.py`) will silently produce wrong results.

Looking at `raw_marker_values` (lines in `src/carrel/env/validation.py`):

```python
for name in sorted(teammates):
    status = teammates[name]
    if isinstance(status, str):
        teammate_items.append(f"{name}:{status.strip().lower()}")
```

This constructs the format correctly. The parsing of the CLAUDE.md marker value back into a dict (the reverse direction) does not appear to be implemented anywhere yet — only `parse_markers` extracts the raw string, and `compare_markers` / `detect_raw_marker_conflicts` compare it as a string equality check. So there is no round-trip parse today, which means the fragility is latent, not currently exploitable.

**Recommendation**: Document the format constraint explicitly in `serialize_model_teammates`'s docstring — teammate names must not contain `:` or `,`. Add a validator in `ResearcherProfile` or a guard in `serialize_model_teammates` that raises on malformed keys, rather than silently producing unparseable output.

---

### 4. Profile schema — free-form dict is the right call, but KNOWN_MODEL_TEAMMATES is under-used — MEDIUM

**File**: `src/carrel/models.py`

`dict[str, ModelTeammateStatus]` with no key restriction is correct for extensibility. A `TeammateName` enum would require a schema change every time a new plugin ships — wrong trade-off for something this peripheral.

However, `KNOWN_MODEL_TEAMMATES = ("codex", "gemini", "kimi")` is defined in `models.py` and imported in `dashboard.py` for ordering purposes, but it is not used anywhere for validation or warnings. If a researcher types `"Codex"` (capital C) rather than `"codex"`, the profile accepts it silently, the dashboard renders it in the "unknown teammates" bucket (correct), but the cheat sheet's `TEAMMATE_COMMANDS` lookup (`templates.py`) returns `["/Codex:help"]` — a nonexistent command — because the dict key is case-sensitive.

This is not a blocker but is a UX trap. The skill instructs Claude to write lowercase keys (`model_teammates["codex"]`), so in practice this only triggers if a researcher hand-edits `environment.json`. Still worth a note-to-self.

**Recommendation**: Add a `field_validator` on `model_teammates` that normalizes keys to lowercase, or document the casing requirement in the field's docstring.

---

### 5. Test coverage gap: marker round-trip and drift detection are not integration-tested — MEDIUM

**File**: `tests/test_model_teammates.py`

The 18 tests cover:

- Enum values (1 test)
- `KNOWN_MODEL_TEAMMATES` contents (1 test)
- Profile defaults, round-trip, invalid status, unknown key (4 tests)
- Dashboard rendering — empty, configured, unknown teammate (3 tests)
- Marker serialization — determinism, empty dict, `marker_values` output, `MARKER_FIELDS` membership (4 tests)
- `raw_marker_values` — with and without model_teammates (2 tests)
- Cheat sheet — configured shows, none-configured hides (2 tests)
- Scaffold — CLAUDE.md marker present after vault init (1 test)

**What's not tested**:

1. **`compare_markers` drift detection for `model_teammates`**: `compare_markers` in `sync.py` calls `marker_values` which includes `model_teammates`. There is no test that sets up a profile with one teammate state, parses a CLAUDE.md with a different `model_teammates` marker value, and verifies that `compare_markers` returns a drift item for that field. The drift detection path for this field is untested.

2. **`detect_raw_marker_conflicts` for `model_teammates`**: Same gap at the `raw_marker_values` level. `test_raw_marker_values_handles_model_teammates` tests the value construction but not the conflict detection downstream.

3. **Dashboard template placeholder**: `render_dashboard` replaces `{{model_teammates}}` in the template. There is no test verifying the template actually contains that placeholder. If someone edits `templates/dashboard.md` and removes or renames the placeholder, `render_dashboard` silently succeeds with the replacement applied to an empty match — the section disappears from generated output with no error. The scaffold test (`test_scaffold_renders_claude_md_with_model_teammates_marker`) tests scaffold but not the dashboard template.

4. **`setup-state advance --phase 5`** sequence: Phase 5b advances state via `carrel setup-state advance --phase 5`. There is no test checking that the setup state correctly transitions when Phase 5b is skipped vs completed.

The first gap (drift detection) is the most likely to allow a bug to slip through — it is exactly the integration path that matters for the vault health check.

---

### 6. Dashboard shows all statuses including `removed`; cheat sheet shows only `configured` — coherent — LOW

**Files**: `src/carrel/vault/dashboard.py`, `src/carrel/vault/templates.py`

The asymmetry is intentional and correct. The dashboard is a state-of-record view (`_meta/my-environment.md`) — showing `removed` preserves history and lets a researcher remember what they've tried. The cheat sheet is a quick-reference card for what works right now.

The dashboard's `_render_model_teammates` also renders `interested` and `skipped`, which makes it the natural answer to "what did we discuss but not install?" The cheat sheet hides those correctly.

One minor coherence issue: the dashboard renders an entry for `removed` teammates with the full description suffix ("Adversarial review / second opinions (ChatGPT)"). A researcher who has removed Codex will see "`codex`: `removed` — Adversarial review / second opinions (ChatGPT)" — which might read as an advertisement for something they explicitly uninstalled. Consider suppressing the description suffix for `removed` entries, or adding a "(uninstalled)" qualifier.

---

### 7. Sensitivity gating is advisory-only, not code-enforced — correct layering — LOW

**File**: `skills/model-teammates/SKILL.md`, sensitivity gating section

The spec decision says: "Cloud routing for the teammates uses the plugin's own path — it does not go through Carrel's converter/transcriber policy matrix." The skill gating is advisory in conversation, not a hard enforcement at the tool layer.

This is the right call. The policy matrix (`src/carrel/policy/sensitivity.py`) gates Carrel's own tools (paper convert, transcript create, google export). Teammate plugins are separate processes with their own auth — Carrel has no hook into whether a researcher calls `/codex:review` directly. Trying to gate at the Carrel layer would be security theater.

The skill correctly warns on HIGH-sensitivity and defaults to `skipped` in the conversation. The command (`commands/carrel-teammates.md`) also calls out the sensitivity check. This is as far as Carrel can reach, and it is the right boundary.

No action required.

---

### 8. Interview beat reads naturally — LOW

**File**: `skills/environment-setup/references/interview-protocol.md`, "About Model Teammates" section

The beat fits the conversational pattern of the rest of the protocol. The framing ("Most researchers don't realize this is possible, so say it first") is consistent with the "proactive" decision in the spec. The pitch script is concrete without being a numbered list. The sensitivity caveat is present.

One note: the beat is placed after "About Their Comfort" and before "About Their Collaborators." The ordering is reasonable — comfort/trust comes first, then the offer to add more infrastructure. But the beat could also feel slightly abrupt immediately after asking about privacy stance ("are you comfortable with cloud processing?") and then immediately offering three cloud-backed tools. Depending on the researcher's answer, Claude may need to bridge the tension explicitly ("you mentioned preferring local — these teammates are also cloud-backed, which is why we'll go carefully through each one"). The skill instructions handle this via the sensitivity caveat, so it is not a gap, just a note for Claude to execute well in the moment.

---

### 9. Migration completeness — LOW

**File**: `migrations/0.7.1-to-0.8.0.md`

The migration file covers:
- New feature description (complete)
- Profile schema change (`model_teammates` field)
- Dashboard + cheat sheet surfacing
- CLAUDE.md marker addition
- Automatic steps (none required)
- Manual steps (`carrel vault add-markers`, `/carrel-teammates`)
- Acceptance verification

Missing items:
- **No mention that `/carrel-setup` has a new Phase 5b**. Researchers who completed setup before 0.8.0 won't know Phase 5b exists. The migration file should mention they can run `/carrel-teammates` as the standalone equivalent.
- **`carrel vault cheatsheet --force` is not listed** as a way to pick up the new cheat sheet section. Dashboard is mentioned; cheat sheet regeneration is not. Researchers who read only the migration file and run `dashboard --force` will update `my-environment.md` but leave `cheat_sheet.md` stale.

Both are low-impact because the manual steps do cover `/carrel-teammates` (which triggers writeback + dashboard regen), but explicit mention would reduce confusion.

---

## Summary table

| # | Area | Severity | File | Action |
|---|------|----------|------|--------|
| 1 | Kimi CLI install protocol is incorrect (`@moonshot/kimi-cli` does not exist) | HIGH | `skills/model-teammates/SKILL.md` | Replace with real install command; link to `github.com/MoonshotAI/kimi-cli` |
| 2 | Migration test count wrong (says 237/9; actual 18 tests, real count TBD) | HIGH | `migrations/0.7.1-to-0.8.0.md` | Run pytest --collect-only and put real number |
| 3 | Marker serialization fragile for future keys/values containing `:` or `,` | MEDIUM | `src/carrel/vault/sync.py` | Add docstring constraint; consider guard |
| 4 | Free-form keys silently accept casing variants (`Codex` vs `codex`) | MEDIUM | `src/carrel/models.py` | Normalize keys to lowercase in validator |
| 5 | Drift detection path for `model_teammates` is untested | MEDIUM | `tests/test_model_teammates.py` | Add `compare_markers` drift test; add template placeholder test |
| 6 | Dashboard shows description for `removed` teammates | LOW | `src/carrel/vault/dashboard.py` | Suppress or qualify description for `removed` |
| 7 | Sensitivity gating advisory-only | LOW | (by design) | No action |
| 8 | Interview beat ordering | LOW | `skills/environment-setup/references/interview-protocol.md` | No action; execution note only |
| 9 | Migration missing Phase 5b mention and cheat sheet regen step | LOW | `migrations/0.7.1-to-0.8.0.md` | Add both |

---

## Blocking items before merge

1. Fix the Kimi CLI install command. `bun add -g @moonshot/kimi-cli` will fail for every researcher who follows it.
2. Fix the test count in the migration file to match reality.

Everything else can ship as-is or be addressed in a fast follow.
