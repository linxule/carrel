# Spec 010: Policy Module — Sensitivity-Aware Routing

**Status**: Locked, ready for implementation (2026-04-20)
**Origin**: 009 holistic audit, A2 + B4 stopgap (Codex §2 — "sensitivity is mechanically meaningless")
**Target version**: 0.7.0 (co-ships with spec 007 cross-platform implementation)

---

## Problem

The product promise (README: "Sensitivity-aware by default. Local-first. Nothing leaves the machine unless explicitly chosen") is enforced by hope. Both routers (`src/carrel/convert/router.py:10-31`, `src/carrel/transcribe/router.py:18-47`) accept `sensitivity` as a parameter and immediately discard it. The effective cloud gate is `cloud_consent` alone.

v0.5.4 added a stopgap (B4) in `consent.py:resolve_cloud_consent`: `Sensitivity.HIGH` blocks cloud regardless of `cloud_consent`. This is the minimum viable safety. But:

- The decision lives in a side helper, not in the routing layer where it belongs
- The matrix of (sensitivity × cloud_consent × tool) is implicit, not a single explainable function
- There's no `--explain` surface that tells the researcher WHY a given input routed where it did
- The router still discards `sensitivity` — the stopgap works because consent.py is called separately, but the abstraction is wrong

Codex's predicted Bug Class 2 will surface in pilot: a researcher who once allowed cloud tools for a non-sensitive workflow finds a sensitive PDF later routes to Mineru when the local binary is missing.

## Why Now

The B4 stopgap protects HIGH only. The MEDIUM band ("ask the researcher" vs "default to local") is undefined. As Imperial deployment broadens, researchers with mixed-sensitivity work will need clearer semantics — and the implementer of any future router needs ONE place to read the policy.

## Goals

1. **`src/carrel/policy.py` module** that owns the routing decision. Single function:
   ```python
   def select_tool(
       requested_tool: ConvertTool | TranscribeTool | None,
       available_tools: list[ConvertTool | TranscribeTool],
       sensitivity: Sensitivity,
       cloud_consent: bool,
       tool_class: Literal["convert", "transcribe"],
   ) -> tuple[ConvertTool | TranscribeTool | None, str]:  # (selected_tool, rationale)
       ...
   ```
2. **Both routers consume `policy.select_tool`**. Routers stop owning the decision; they own the dispatch given the decision.
3. **`--explain` flag on `carrel paper convert`, `carrel transcript create`, `carrel google export`**: prints the rationale and exits. For debugging routing surprises in pilot.
4. **Sensitivity matrix made explicit**:
   - `LOW`: local-first; cloud OK if `cloud_consent` and local unavailable
   - `MEDIUM`: local-first; refuse cloud automatically; require explicit `--tool <cloud>` to override (which counts as consent)
   - `HIGH`: local-only; refuse cloud even with explicit `--tool <cloud>` (B4 hardening)
5. **Audit log option**: `_meta/routing-log.jsonl` records every decision (file, tool, sensitivity, consent, selected, rationale). Opt-in via profile flag.

## Locked Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| `cloud_consent` deprecation | **Keep both fields** | Backward compat; zero migration cost. Document the matrix explicitly. LOW+consent→cloud, HIGH+anything→local, MEDIUM→requires explicit `--tool <cloud>` override. |
| Namespace with spec 008 | **Separate modules**: `policy/sensitivity.py` + `policy/trust.py` | Different decision domains; evolve independently. Share nothing except CLI patterns. Rename v0.6.0's top-level `trust.py` to `policy/trust.py` during 010 implementation. |
| `gws` sensitivity exemption | **No exemption** | Data DOES leave the local machine via a Google API call. HIGH sensitivity should block regardless of "it's already in Google's cloud" reasoning — researcher intent for HIGH is "nothing leaves this machine." |
| MEDIUM band UX | **Explicit `--tool <cloud>` = consent** | No separate ask-prompt flow in v1. The explicit tool choice IS the consent. If researcher doesn't provide one and local is unavailable, fail with actionable hint ("Local tool missing; to use cloud, run with `--tool mineru`"). |

## Matrix (locked)

Tool selection resolves as:

```
sensitivity × cloud_consent × requested_tool → (selected_tool, rationale)
```

| sensitivity | cloud_consent | requested_tool | local available? | Result |
|-------------|---------------|----------------|------------------|--------|
| HIGH | any | local | yes | local (preference honored) |
| HIGH | any | local | no | **refuse**: "HIGH sensitivity requires local; local tool missing; install and retry" |
| HIGH | any | cloud (explicit) | n/a | **refuse**: "HIGH sensitivity blocks cloud tools regardless of consent" |
| HIGH | any | none | yes | local (default) |
| HIGH | any | none | no | **refuse** (same as above) |
| MEDIUM | any | local | yes | local |
| MEDIUM | any | local | no | **refuse**: "local tool missing; to use cloud, run with `--tool <cloud>`" |
| MEDIUM | any | cloud (explicit) | n/a | cloud (explicit is consent) |
| MEDIUM | any | none | yes | local |
| MEDIUM | any | none | no | **refuse** (same) |
| LOW | true | cloud (explicit) | n/a | cloud |
| LOW | true | local | no | cloud (consent + no local → auto-route) |
| LOW | true | none | yes | local (local-first default) |
| LOW | true | none | no | cloud (auto-route with consent) |
| LOW | false | cloud (explicit) | n/a | cloud (explicit is consent regardless) |
| LOW | false | none | no | **refuse**: "local tool missing; to use cloud, set cloud_consent=True or run with `--tool <cloud>`" |

## Constraints

- **Backward compatibility**: existing profiles must continue working. New module reads existing `Sensitivity` enum + `cloud_consent: bool`. The matrix happens at the policy boundary; the model fields don't change.
- **`--explain` must be cheap**: no network calls, no subprocess. Just policy evaluation + print.
- **Decision must be deterministic**: same inputs always produce same selection + rationale. No randomness, no time-dependent behavior.

## Lock Blockers

None known.

## Cross-Cutting

- **Spec 008 (trust enforcement)**: same architectural pattern. Both define a single decision boundary that downstream code consumes. Could share infrastructure (logging, `--explain` flag plumbing).
- **Spec 006 (env validation)**: the doctor agent should warn when sensitivity + cloud_consent combinations look incoherent (e.g., `sensitivity=HIGH` + `cloud_consent=True` is technically allowed but signals confusion).

## Adjacent Work (NOT in this spec)

- Per-file sensitivity overrides (e.g., a frontmatter `sensitivity: high` that overrides profile default) — defer to v0.7.
- Network-level enforcement (DNS-block cloud endpoints when sensitivity=HIGH) — out of scope; this is application-level policy only.
- Streaming consent revocation (mid-pipeline cloud reject) — defer.
