# Spec 013: Model Teammates — Multi-Model Agent Integration

**Status**: Shipped in v0.8.1 (2026-04-22)
**Origin**: User request — integrate Codex, Gemini, Kimi as agent teammates via existing CC plugins

---

## Problem

Claude Code's multi-agent workflow support is already rich — but by default, every "agent" is another Claude. The undertapped unlock is **using paid subscriptions researchers already hold** (ChatGPT Plus/Pro, Gemini Advanced, Kimi) as additional teammates. Three community plugins now make this one-plugin-install easy: `openai/codex-plugin-cc`, `thepushkarp/cc-gemini-plugin`, `linxule/kimi-plugin-cc`.

Carrel's job is to **surface this proactively** during onboarding — most researchers won't ask because they don't know the option exists.

## Naming

**Teammates**, not "agents" — disambiguates from Carrel's Claude-side `agents/` (setup-interviewer, research-partner) and from human `collaborators` (co-authors/RAs captured by `/carrel-share`). Supported v1: `codex`, `gemini`, `kimi`; schema is extensible.

## Research framing (canonical — lives in the skill)

| Teammate | Research move |
|---|---|
| **Codex** (ChatGPT) | Adversarial / second-opinion review |
| **Gemini** | Whole-corpus / long-PDF synthesis |
| **Kimi** | Delegated work with CLI-auth privacy |

## Locked Decisions

| Question | Decision |
|---|---|
| Proactive or gated on interview signal? | **Proactive** — always surface |
| Where in `/carrel-setup`? | **Phase 5b, state-neutral** — doesn't block setup advancement |
| Standalone command? | **Yes** — `/carrel-teammates`, re-runnable anytime |
| Profile field shape | `model_teammates: dict[str, ModelTeammateStatus]` with `configured \| interested \| skipped` |
| CLI install responsibility | Skill guides; researcher runs — interactive auth needs human hands |
| Sensitivity gating | Skill-level advisory; code can't intercept runtime plugin calls |
| Version bump | 0.8.1 |

## Implementation

- `ModelTeammateStatus` enum + `model_teammates` field on `ResearcherProfile` (`src/carrel/models.py`)
- `skills/model-teammates/SKILL.md` — positioning, install pointers to upstream, state writeback
- `commands/carrel-teammates.md` — thin delegate to the skill
- Interview beat in `skills/environment-setup/references/interview-protocol.md`
- State-neutral Phase 5b in `commands/carrel-setup.md`
- Single line in dashboard Setup block (`src/carrel/vault/dashboard.py`)
- Migration: `migrations/0.7.1-to-0.8.1.md`

## Non-goals

- No bundled MCP bridges — each plugin is standalone
- No API-key management — each plugin handles its own CLI-level auth
- No automatic plugin installation — researcher runs commands; Claude guides

## Review arc + trim history

Three passes shaped the final scope. In order:

1. **Initial review (Codex + Kimi adversarial, v0.8.0 draft).** Flagged a code-level sensitivity policy + vendored install references as hardening needs. **Declined** — teammate plugins run out-of-process, skill-level guidance is the appropriate boundary. Factual fixes applied: Kimi CLI install command corrected (`@moonshot/kimi-cli` → `kimi-cli`), migration test counts corrected.
2. **First trim (pre-release).** Dropped the CLAUDE.md marker and cheat-sheet rendering — both duplicated state/surfaces already covered by `environment.json` and `/help`.
3. **Second trim (deletion-first pass, Codex + Kimi).** Collapsed `ModelTeammateStatus` from 4 values to 3 (dropped `removed`), removed `KNOWN_MODEL_TEAMMATES` + `TEAMMATE_DESCRIPTIONS` dicts, shrank the skill from 221 → ~80 lines by deleting vendored install bash blocks, compressed the dashboard from a dedicated section to a single line in the Setup block, and trimmed cross-file prose duplication (the research-moves table and sensitivity rule each appeared up to 7 times).

Final shape: interview beat + Phase 5b + profile field + skill + command + one dashboard line. Six tests. 234 passing total.

## Reviews

- `planning/reviews/013-review-codex.md` — initial adversarial pass
- `planning/reviews/013-review-kimi.md` — initial second-pair-of-eyes
- `planning/reviews/013-trim-codex.md` — deletion-first pass (code)
- `planning/reviews/013-trim-kimi.md` — deletion-first pass (prose)
