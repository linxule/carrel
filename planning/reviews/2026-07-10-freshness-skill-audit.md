# Carrel freshness and skill-contract readiness — 2026-07-10

**Status:** Ready for local release handoff

**Branch:** `codex/skill-first-carrel`

**Carrel version:** `0.9.0`

**Scope:** Typed CLI, portable skill runtime, all 14 skills, templates, upstream guidance, dependency resolution, packaging, and forward-agent behavior.

## Outcome

The freshness and skill-contract remediation is complete. The typed CLI and portable runtime now agree on profile-aware initialization, feedback redaction, collaborator stdin persistence, approved wiki writes, automation configuration, prompt generation, trust policy, and non-destructive template-drift reporting.

The implementation preserves Carrel's architecture boundary: skills own interviews, synthesis, sensitivity judgment, previews, refinement, and approval; runtimes own validation, policy checks, path safety, deterministic output, and file operations.

No Carrel version or dependency minimum was raised. Existing vault content, customized root trackers, legacy `_templates/*.base` files, old wiki pages, and historical planning/migration records are not destructively rewritten.

## Runtime and contract remediation

- Added `vault init --profile-file PATH` to both runtimes with whole-profile validation before writes, existing-profile reuse, explicit conflict rejection, idempotency, and profile-selected root trackers.
- Added identical non-destructive `outdated_templates` and `unversioned_templates` reporting to initialization and full migration planning.
- Unified feedback rules across runtimes: bare terms, ASCII `->`, legacy Unicode `→`, literal case-insensitive longest-first replacement, `[REDACTED]` defaults, line-numbered malformed-rule errors, automatic `profile.name -> Researcher`, and identical JSON metrics.
- Added `--from-stdin` and `--canonical` to full collaborator generation. Approved stdin is persisted byte-for-byte; the CLI validates destinations and writes files without claiming to sanitize the approved body.
- Added consultative `wiki:apply-approved` while retaining consultative `wiki:propose` and delegated `wiki:write`.
- Made automation configuration profile-only. Prompt generation is a separate trust-gated operation in both runtimes; the portable runtime exposes `vault automation-prompt --vault PATH [--force]`. Pending files are created only for real decisions or proposals.
- Added a fail-closed first-use trust transition: after explicit human approval, configure may move Advisory to Consultative in the same validated profile write; direct Advisory-to-Delegated/Partnership jumps remain rejected.
- Added all-target typed init preflight and safe atomic vault writes so file-vs-directory conflicts and symlinked profile, metadata, tracker, template, or prompt paths fail before any partial or out-of-vault write. Dated and canonical collaborator targets are both validated before either copy is written. This now matches the portable runtime's fail-closed behavior.
- Kept CLI collaborator modes at `quick|full`; conversational interactive work maps to `--mode full --from-stdin`.
- Corrected remaining command, migration, Groq-output, validation-count, and Ruff drift without changing the intended runtime behavior.

## Upstream freshness absorbed

- Rebuilt all four root/portable Obsidian Bases at marker `v0.4.0` using plural `filters`, mapping-valued `properties`, `formulas`, and `summaries`, view `order` and `groupBy`, safe hyphenated-property access, and date-aware transcription semantics. Paired copies are byte-identical and preserve their existing view names and intent.
- Pinned Obsidian guidance to snapshot [`a1dc48e68138490d522c04cbf5822214c6eb1202`](https://github.com/kepano/obsidian-skills/commit/a1dc48e68138490d522c04cbf5822214c6eb1202) and absorbed recursive-filter correction [`9b736ba8da230341054cc668bedc0bcb041baa98`](https://github.com/kepano/obsidian-skills/commit/9b736ba8da230341054cc668bedc0bcb041baa98). The next review is `2026-10-10`.
- Added `.base` and named-view embed guidance and repaired JSON Canvas examples against [JSON Canvas 1.0](https://jsoncanvas.org/spec/1.0/), including valid unique IDs, link nodes, optional group labels, and valid edge endpoints.
- Curated [Hermes LLM Wiki 2.1](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md) at snapshot `8e3f9537db21b49ebe796f7b5a6ff489028fe1fb`: optional confidence/contestation metadata, contradiction links, paragraph provenance markers, body-only SHA-256 `source_digests`, drift/quality lint counts, and approved-only repair. Hermes `raw/` storage and `WIKI_PATH` were intentionally not imported.
- Replaced stale scheduling claims with current Cowork [`/schedule` and Scheduled-page behavior](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork), current [desktop/local-folder availability limits](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile), and credential-dependent [`claude -p`](https://code.claude.com/docs/en/headless) fallback guidance.
- Upgraded `external-refresh.json` to manifest v2 with `last_full_reviewed: 2026-06-30` and per-entry review dates. LiteParse was re-probed at `2.5.0`; maintained install guidance is `npm install -g @llamaindex/liteparse` and the verified `lit parse` contract is retained.

## Dependency resolution

`uv.lock` was refreshed without changing the project version or dependency floors.

| Package | Locked version | Existing floor |
|---|---:|---:|
| Pydantic | 2.13.4 | `>=2.0` |
| Typer | 0.26.8 | `>=0.9` |
| Rich | 15.0.0 | `>=13.0` |
| python-frontmatter | 1.3.0 | `>=1.1` |
| pytest | 9.1.1 | `>=7.0` |
| pytest-asyncio | 1.4.0 | `>=0.21` |
| Ruff | 0.15.21 | `>=0.1` |

Ruff is also present in the default development dependency group so the repository's canonical `uv run ruff check .` gate works after a normal sync; its floor is unchanged.

## Verification evidence

| Gate | Result |
|---|---|
| Focused freshness, skill-pack, packaging, trust, and dashboard tests | 93 passed |
| Full test suite | 388 passed in 6.03s |
| Strict skill validation | All 14 skills valid; all `SKILL.md` files under 500 lines |
| Ruff | `All checks passed!` on Ruff 0.15.21 |
| Lock consistency | `uv lock --check` passed |
| Base pairing | All four root/portable pairs byte-identical |
| Build | Source distribution and wheel built successfully |
| Wheel contents | All 15 runtime templates included under `share/carrel/templates` |
| Clean install smoke | Fresh virtual environment installed the wheel; `carrel --help`, `vault init`, Advisory-to-Consultative configure, and separate automation-prompt generation passed |
| Repository editable smoke | `uv run carrel --help` and source import passed after clearing stale macOS `UF_HIDDEN` metadata from the generated `.venv`; no product-file change was required |
| Diff hygiene | `git diff --check` passed |
| Obsidian visual smoke | Obsidian 1.13.1 opened all four Bases in a disposable vault and rendered their named views, columns, formulas, and summaries without schema errors |

Forward-agent raw-prompt checks covered profile-driven setup and feedback mapping, approved collaborator handoff versus autonomous wiki maintenance, and automation/Groq guidance. All three narratives matched the intended contracts after the first-use automation trust bootstrap was made deterministic. The automation/Groq pass also ran 49 focused typed/portable tests and confirmed that Groq exposes plain transcript text rather than word-level timestamps.

## Delivery boundary

- Work remains on `codex/skill-first-carrel`.
- No merge, push, pull request, tag, package publication, or release was performed.
- No CI system was added.
- The disposable Obsidian vault and isolated install environments were removed after verification.
- There are no deferred manual gates: the optional Obsidian visual smoke was available and passed.
