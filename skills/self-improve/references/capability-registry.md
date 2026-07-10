# Capability Registry

Tracks what Carrel has absorbed, where it came from, and when to check for updates.

## Absorbed Capabilities

| Capability | Source | Reference File | Templates | Absorbed | Last Reviewed | Next Review |
|------------|--------|---------------|-----------|----------|---------------|-------------|
| Obsidian formatting (callouts, embeds, properties) | `kepano/obsidian-skills/skills/obsidian-markdown` @ `a1dc48e68138490d522c04cbf5822214c6eb1202` | `vault-ops/references/obsidian-formatting.md` | — | 2026-04-03 | 2026-07-10 | 2026-10-10 |
| Research databases (Obsidian Bases) | `kepano/obsidian-skills/skills/obsidian-bases` @ `a1dc48e68138490d522c04cbf5822214c6eb1202`; recursive-filter correction `9b736ba8da230341054cc668bedc0bcb041baa98` | `vault-ops/references/research-databases.md` | `paper-tracker.base`, `interview-tracker.base`, `reading-progress.base`, `writing-tracker.base` | 2026-04-03 | 2026-07-10 | 2026-10-10 |
| Concept mapping (JSON Canvas) | `kepano/obsidian-skills/skills/json-canvas` @ `a1dc48e68138490d522c04cbf5822214c6eb1202` | `research-partner/references/concept-mapping.md` | — | 2026-04-03 | 2026-07-10 | 2026-10-10 |
| Knowledge wiki (compiled synthesis) | Karpathy LLM-wiki gist + `NousResearch/hermes-agent/skills/research/llm-wiki` v2.1.0 @ `8e3f9537db21b49ebe796f7b5a6ff489028fe1fb` | `knowledge-wiki/references/wiki-protocol.md` | — | 2026-04-07 | 2026-07-10 | 2026-10-10 |
| Collaborator handbook (vault legibility for others) | Claude Code `/team-onboarding` (v2.1.101) — design pattern only, not the command itself | `collaborator-onboarding/SKILL.md` + `references/handbook-template.md` | — | 2026-04-20 | 2026-04-20 | 2026-07-20 |
| Model teammates (multi-model agent wiring) | `openai/codex-plugin-cc`, `thepushkarp/cc-gemini-plugin`, `linxule/kimi-plugin-cc` — thin wrapper pattern: interview beat + profile field + skill pointing at upstream. Not vendored. | `model-teammates/SKILL.md` + `commands/carrel-teammates.md` | — | 2026-04-22 | 2026-04-22 | 2026-07-22 |

## 2026-07-10 Review Notes

- Obsidian Markdown had no material syntax change; Carrel added current `.base`
  and named-view embed examples for cross-reference.
- Obsidian Bases required a schema migration to plural recursive `filters`,
  mapping-valued formulas/properties/summaries, and view `order`/`groupBy`.
- JSON Canvas 1.0 was unchanged; Carrel corrected invalid example IDs, added
  link nodes, and made optional group labels explicit.
- Hermes llm-wiki 2.1 provenance and quality signals were curated into Carrel's
  existing source-layer and trust contracts. The upstream `raw/` layer and
  global `WIKI_PATH` were deliberately not adopted.

## Evaluated and Skipped

| Capability | Source | Reason Skipped | Date |
|------------|--------|---------------|------|
| Obsidian CLI integration | kepano/obsidian-skills/obsidian-cli | Carrel writes files directly; CLI adds no research value | 2026-04-03 |
| Defuddle (web extraction) | kepano/obsidian-skills/defuddle | Full overlap with Carrel's web-capture skill + CLI adapter | 2026-04-03 |
| Direct reference to `/team-onboarding` | Claude Code v2.1.101 | Generic Claude Code usage tips don't carry vault-specific conventions (sensitivity, wiki schema, custom trackers, active threads). Absorbed the design pattern into `/carrel-share` instead, which reads vault content directly. | 2026-04-20 |
| Hermes `raw/` source layer and `WIKI_PATH` | Hermes llm-wiki v2.1.0 | Carrel already has `papers/`, `transcripts/`, and `inbox/` source layers and keeps the field map inside each vault. Absorbed provenance and quality signals without duplicating storage or adding a global path. | 2026-07-10 |

## Promotion Candidates

Track custom creations that recur across researchers. Add an entry after the first sighting; increment count on each repeat.

| Pattern | Seen In | Times Seen | Notes |
|---------|---------|-----------|-------|
| *(add entries as custom creations recur across vaults)* | | | |

## Promoted from Ad-Hoc to Template

| Template | Promoted | Origin | Times Seen Before Promotion |
|----------|----------|--------|-----------------------------|
| *(none yet — this table populates as custom creations get promoted)* | | | |

## Upstream Watch List

Sources to check during quarterly review:

- [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) -- Obsidian formatting, bases, canvas
- [karpathy/LLM-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — Knowledge wiki pattern (original gist)
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — Hermes Agent skill implementations (llm-wiki, research tools)
- Obsidian changelog — new file types, syntax changes, plugin API updates
- [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) — check for CLI install command drift, new slash commands
- [thepushkarp/cc-gemini-plugin](https://github.com/thepushkarp/cc-gemini-plugin) — check for CLI install command drift, new flags
- [linxule/kimi-plugin-cc](https://github.com/linxule/kimi-plugin-cc) — check for CLI install command drift, new slash commands
