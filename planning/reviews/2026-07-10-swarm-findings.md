# Swarm review cycle — 2026-07-10

**Branch:** `codex/skill-first-carrel`
**Reviewed commit:** `cf66e06`
**Carrel version:** `0.9.0`
**Status:** Findings triaged; high/medium routed into fix waves A–E; low-severity backlog deferred below.

## What ran

- **kimi-review** — independent second-pair-of-eyes over the branch diff.
- **40-agent verification workflow** — confirmed the 8 pre-known branch bugs and the bun-vs-npm context item; no disagreements returned.
- **kimi-swarm (10 targets)** — read-only parallel audit fanned across `policy/`, `convert/`, `transcribe/`, `vault/`+`env/`, `cli/`, `feedback/`+`share/`+`migrate/`, portable `carrel_core/`, skill docs + contracts, hooks/install, and tests. Report: `/tmp/swarm-report.md`. Every subagent returned findings beyond the known list.

## Maintainer decisions

1. **Host-split (earlier, 2026-07-10)** — the portable runtime is a strict subset of the typed CLI; a small enumerated set of `vault init` surfaces is owned by exactly one host. Pinned by `TYPED_ONLY_INIT_FILES` / `PORTABLE_ONLY_INIT_FILES` in `tests/test_runtime_parity.py` (drift alarm).

2. **Advisory bootstrap (2026-07-10)** — `carrel automate configure`'s Advisory→Consultative first-use transition **stays as-is**. No approval artifact is written; the `automation` skill's interview-approval flow is the contract of record. Deliberately narrow: only Advisory→Consultative, only in this command; Advisory→Delegated/Partnership stays rejected. Documented (not changed) in CLAUDE.md trust-enforcement gotcha, `src/carrel/cli/automate.py` comment, `skills/automation/SKILL.md`, and `skills/carrel/references/contracts/trust-levels.md`.

3. **YouTube captions network-lite (2026-07-10)** — captions are a public network fetch, not a cloud upload: no vault data egresses. LOW/MEDIUM route without `cloud_consent`; HIGH blocks by default but honors an explicit `--tool youtube_captions` override with a warning (the researcher asserts the URL is not sensitive). `--tool gemini` remains a true cloud tool (uploads audio/video), blocked on HIGH regardless of consent. Code lives in `src/carrel/policy/sensitivity.py` (`NETWORK_TOOLS`); docs in CLAUDE.md YouTube routing + `skills/transcribe/SKILL.md`.

## By-design dismissals (not bugs)

- **`vault dashboard --force` whole-file regeneration** (swarm flagged high, `cli/vault.py:278-282` / `vault/dashboard.py:90`): `_meta/my-environment.md` is a **documented-deterministic** artifact — regenerated from profile state on demand, not a hand-edited surface. Regeneration replacing it is the intended contract, matching the other `--force` regenerators (cheatsheet, automation-prompt).
- **Tests encoding the advisory bootstrap** (swarm flagged high/medium, `tests/test_automate_cli.py:99`, `tests/test_runtime_parity.py:729`): these pin the **intended** contract per decision 2. Marked in-file with `INTENDED CONTRACT` comments; assertions unchanged.

## Test-honesty hardening (this cycle)

The malformed-`cloud_consent` cases (`tests/test_runtime_parity.py`, `tests/test_carrel_skill_pack.py`) ran with an empty-bin `PATH`, so no cloud tool could ever be available and `selected_tool is None` was trivially true — it only proved the rationale wording. Both now additionally drive the policy `select_tool` directly with a cloud tool genuinely available, proving a non-consent value never routes to cloud even when cloud is reachable, plus a converse control (flip only consent → cloud IS selected).

## LOW-severity follow-ups (all resolved this cycle)

None were release blockers; all 14 are now fixed. (Two other lows from the swarm's hooks/install target were also fixed this cycle in wave E: `hooks/sensitivity-gate.js:25` `--tool=` regex bypass, and `commands/carrel-capture.md:22` phantom `tags` frontmatter — not listed below.) The last eight were cleared in a dedicated low-tail cleanup pass; the first six had already been swept up by earlier fix waves (verified fixed at HEAD).

| Target | File:Line | Follow-up | Resolution |
|--------|-----------|-----------|------------|
| convert | `convert/adapters/mistral_ocr.py:42` | Broad `except Exception:` during OCR cleanup can mask the original failure cause. | Low-tail cleanup — cleanup `_delete_file` now runs inside its own guarded try/except so it can never replace the re-raised OCR error. |
| convert | `convert/adapters/mineru.py:35` | `file.read_bytes()` loads the whole PDF into memory before upload (OOM risk on large files). | Low-tail cleanup — added `MINERU_MAX_FILE_BYTES = 200 MB` guard (matches MinerU's API limit). Streaming was rejected: an httpx AsyncClient iterator body forces chunked transfer-encoding, which a presigned PUT can reject; the size guard mirrors the sibling `mistral_ocr` adapter. |
| convert | `convert/router.py:24` | `hardware` capability argument is accepted but never influences convert routing. | Low-tail cleanup — dead param removed from `select_convert_tool`, its pipeline caller, and all convert-router tests. (`transcribe/router.py` has the same unused param; out of scope, left for a follow-up.) |
| vault/env | `vault/templates.py:195` | Cheat sheet treats only `coli`/`groq` as enabled audio transcription; `gemini`/`youtube_captions` vaults misreport "available later". | Earlier fix wave — `transcription_tools` now includes `youtube_captions`/`gemini`. |
| cli | `cli/vault.py:652-659` | `--explain --from-stdin` blocks on stdin instead of short-circuiting (`--explain` checked after stdin is consumed). | Earlier fix wave — `--explain` short-circuits before the stdin read and only reads a genuinely piped (non-TTY) body. |
| cli | `cli/env.py:155` | `--unsafe` immediately raises `CarrelError("Only --safe mode is supported")` — a misleading no-op flag. | Earlier fix wave — `--unsafe` removed; `--safe` defaults true and is a documented no-op. |
| cli | `cli/vault.py:684-685` | `share generate --explain` emits indented JSON even with `--format human`, inconsistent with peer `--explain` output. | Earlier fix wave — `--explain` now honors `--format human`/`quiet`/`json`. |
| portable | `carrel_core/core.py:123` | `slugify` has no max length; very long titles can exceed filesystem limits. | Low-tail cleanup — `slugify` caps at 80 chars, cutting at a hyphen boundary (hard-cut for a single long token); covered by `test_carrel_skill_runtime_slugify_caps_length`. |
| portable | `carrel_core/adapters.py:42` | `run_adapter` caps stdout but not stderr; a misbehaving adapter's huge stderr can exhaust memory. | Low-tail cleanup — the same `MAX_ADAPTER_OUTPUT` cap now applies to stderr. |
| portable | `carrel_core/ingestion.py:65` | `source_hash` idempotency check uses substring match (`expected in old`); a note literally containing the 64-char hash is falsely treated as unchanged. | Earlier fix wave — replaced by anchored `frontmatter_source_hash` + exact `==` compare. |
| portable | `carrel_core/maintenance.py:246` | `cmd_share_generate` reads `args.vault / "notes" / "threads"` directly instead of via `safe_vault_join`, bypassing vault-root validation. | Earlier fix wave — now reads via `safe_vault_join(args.vault, "notes", "threads")`. |
| install | `install.sh:2` and curl substitutions (`:109`,`:158`,`:180`,`:198`,`:258`) | `set -e` without `set -o pipefail`; unguarded `$(curl …)` substitutions let steps fail silently. | Low-tail cleanup — added `set -o pipefail` (covers all `curl … \| sh/bash` pipes); the one true `$(curl …)` substitution (Homebrew installer) is now captured explicitly and fails loud on network error. |
| install | `install.sh:110-115` | Post-Homebrew PATH hook persists only Apple Silicon `brew shellenv`; Intel `/usr/local/bin/brew` not added to `~/.zprofile`. | Low-tail cleanup — brew path detected as `/opt/homebrew` **or** `/usr/local`, then eval'd and persisted. |
| tests | `pyproject.toml:40-42` | pytest configured without a coverage tool / `[tool.coverage.*]` settings, so coverage claims are unverifiable. | Low-tail cleanup — added `pytest-cov` to the dev group + `[tool.coverage.run]`/`[tool.coverage.report]`. Opt-in via `uv run pytest --cov` (kept out of default addopts to preserve the fast suite). |

Higher-severity swarm findings (policy fall-through rationales, `gemini-3.5-flash` model id, YouTube slug collisions, scaffold placeholder leakage, `_count_files` NotADirectoryError, feedback/share silent drops and slug collisions, portable ingestion slug/hash bugs, skill-doc `youtube_captions` contract gaps) are routed into fix waves A–D and tracked there, not in this backlog.
