# 014 CC-Only Trim — Phase 1 Triage

2026-05-17. Spec 014 scoped to Claude Code only; Phase 2 parked. Triaged on CC-architecture-quality grounds. **M**otiv: CC = stands alone on CC. X = only paid off for Codex/Kimi. B = both.

## Triage

| # | Item | Verdict | M | Rationale |
|---|---|---|---|---|
| 1 | `vault feedback export --redact-list` | KEEP | B | Deterministic anonymization → CLI per three-layer rule. |
| 2 | `migrate apply --plugin-root` | MODIFY | B | Default `--plugin-root` to `${CLAUDE_PLUGIN_ROOT}`; arg optional. |
| 3 | `vault mirror --write --from-stdin` | KEEP | CC | Fixes a real `/carrel-mirror` idempotency bug. |
| 4 | `vault reflect-log --append --from-stdin` | KEEP | CC | Atomic append + template render. |
| 5 | `batch convert/transcribe --unattended` | KEEP | CC | Strongest skill/CLI split fit. |
| 6 | `automate configure` (typed flags, internal trust gate) | KEEP | CC | Deterministic writes; internal gate. |
| 7 | `vault share generate` | KEEP | CC | Deterministic emission + sensitivity redaction. |
| 8 | `setup interview --phase N` | DROP | X | Only existed to resolve agent→skill loss for non-CC. CC keeps agent. |
| 9 | Enrichment: `environment-setup` | DROP | X | Coupled to #8. |
| 10 | Enrichment: `automation` | MODIFY | CC | Move flow + Desktop App walkthrough into skill only. |
| 11 | Enrichment: `convert`+`transcribe`+`automation` (batch) | KEEP | CC | Required by #5. |
| 12 | Enrichment: `collaborator-onboarding` | KEEP | CC | Required by #7. |
| 13 | Wrapper shrinkage (all 15) | MODIFY | CC | Shrink only the ~7 wrappers whose CLI ships. |
| 14 | `${ARGS}` vs `$ARGUMENTS` convention | KEEP | CC | Trivial; needed for shrunk wrappers. |
| 15 | `${CLAUDE_PLUGIN_ROOT}` removal | DROP | X | Kimi-motivated. CC uses it correctly. |
| 16 | Optional `host` field on `plugin-state.json` | DROP | X | Forward-compat for parked Phase 2. |
| 17 | `test_command_wrappers.py` | MODIFY | CC | Scope to the ~7 shrunk wrappers. |
| 18 | `plugin-state.json` schema migration test | DROP | X | Coupled to #16. |
| 19 | Hook-JS test infra (~5 tests) | DROP | X | Sized for #15; no #15 → no infra. |
| 20 | Migration `0.8.1-to-0.9.0.md` | KEEP | CC | Documents prose rehome. |
| 21 | EP-1..EP-4 | DROP | X | All probe Codex/Kimi. |
| 22 | CI residue grep + non-CC discoverability | DROP | X | Non-CC. |
| 23 | CI wrapper structural validation | KEEP | CC | Subsumed by #17. |
| 24 | CI build determinism + byte-diff | DROP | X | Phase 2. |

## Net Phase 1 v0.9.0 (CC-only)

1. **7 CLI subcommands** — `vault feedback export` (S), `migrate apply` (S), `vault mirror` (S), `vault reflect-log` (S), `vault share generate` (S), `batch convert/transcribe --unattended` (M), `automate configure` (M)
2. **3 skill enrichments** absorbing freed prose — `automation`, `convert`+`transcribe`, `collaborator-onboarding` (M total)
3. **Wrapper shrinkage for ~7 commands** + `${ARGS}` convention (S)
4. **~22 tests** — 7 subcommands × ~3 + wrapper structural (M)
5. **Migration `0.8.1-to-0.9.0.md`** (S)

**Effort**: ~1 large unit (orig. Phase 1 was ~2). Eliminated risks: state-machine extraction, hook-JS infra, `${CLAUDE_PLUGIN_ROOT}` removal, plugin-state schema bump, 4 EPs.

**Dropped** (#8, 9, 15, 16, 18, 19, 21, 22, 24): everything that only paid off if Codex/Kimi were build targets.

Survivors enforce the three-layer rule ("skills = judgment, CLI = ops, transports = thin") inside CC. Cuts were non-CC concessions + forward-compat for parked Phase 2.
