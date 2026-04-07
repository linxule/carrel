# Capability Registry

Tracks what Carrel has absorbed, where it came from, and when to check for updates.

## Absorbed Capabilities

| Capability | Source | Reference File | Templates | Absorbed | Next Review |
|------------|--------|---------------|-----------|----------|-------------|
| Obsidian formatting (callouts, embeds, properties) | kepano/obsidian-skills/obsidian-markdown @ v1.0.1 | `vault-ops/references/obsidian-formatting.md` | — | 2026-04-03 | 2026-07-01 |
| Research databases (Obsidian Bases) | kepano/obsidian-skills/obsidian-bases @ v1.0.1 | `vault-ops/references/research-databases.md` | `paper-tracker.base`, `interview-tracker.base`, `reading-progress.base`, `writing-tracker.base` | 2026-04-03 | 2026-07-01 |
| Concept mapping (JSON Canvas) | kepano/obsidian-skills/json-canvas @ v1.0.1 | `research-partner/references/concept-mapping.md` | — | 2026-04-03 | 2026-07-01 |
| Knowledge wiki (compiled synthesis) | karpathy/LLM-wiki gist + NousResearch/hermes-agent/skills/research/llm-wiki @ v2.0.0 | `knowledge-wiki/references/wiki-protocol.md` | — | 2026-04-07 | 2026-07-07 |

## Evaluated and Skipped

| Capability | Source | Reason Skipped | Date |
|------------|--------|---------------|------|
| Obsidian CLI integration | kepano/obsidian-skills/obsidian-cli | Carrel writes files directly; CLI adds no research value | 2026-04-03 |
| Defuddle (web extraction) | kepano/obsidian-skills/defuddle | Full overlap with Carrel's web-capture skill + CLI adapter | 2026-04-03 |

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
