# Trust Levels

Use trust levels to decide how much autonomy Carrel should take.

- `advisory`: suggest only; do not persist operational changes without explicit
  approval.
- `consultative`: prepare changes and ask before meaningful write actions.
- `delegated`: act on routine maintenance within configured boundaries.
- `partnership`: broadest autonomy; use only when the researcher has explicitly
  opted in.

The portable runtime currently stores and validates trust preferences. Agents
must still apply judgment before writes. When in doubt, downgrade to
consultative behavior and write a pending decision instead of acting.

## Portable Action Semantics

Use trust checks before automation, field-map writes, or bulk maintenance.

| Action | Advisory | Consultative | Delegated | Partnership |
| --- | --- | --- | --- | --- |
| Automation setup | Explain and draft only | Persist settings after approval | Persist approved routine settings | Persist broad settings after explicit opt-in |
| Automation prompt (`automation:write-prompt`) | Not allowed | Generate or replace after approved setup | Generate or replace | Generate or replace |
| Unattended inbox processing | Not allowed | Write proposals to pending approvals | File routine low-risk items and log | Same, with broader maintenance boundaries |
| Field-map approved batch (`wiki:apply-approved`) | Not allowed | Apply only the exact approved batch | Apply approved batches and log | Apply approved batches and log |
| Autonomous field-map write (`wiki:write`) | Not allowed | Not allowed | Update schema-conforming pages and log | Reorganize field map within stated goals |
| Field-map query filing | Propose saved query | Save only through an approved batch | Save reusable answers and update index | Save and refactor query structure if useful |

High sensitivity overrides trust. It blocks cloud processing and requires
redaction-aware handoff even at delegated or partnership trust.

Collaborator handoff is not an automation-trust action. An explicit quick-mode
request authorizes the dated fallback draft; an interactive synthesized body
requires sensitivity review, preview, and final approval before the CLI
persists it.

Automation configuration is persisted with:

```bash
python3 scripts/carrel.py automation configure --vault <vault> --enabled true --trust-level consultative --schedule daily --review-cadence quarterly
```

On a fresh Advisory profile, this command is the deterministic bootstrap after
the researcher explicitly approves Consultative. It may not jump directly from
Advisory to Delegated or Partnership. Later transitions use the normal
Consultative action gate.
