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

Use trust checks before automation, field-map writes, collaborator handoffs, or
bulk maintenance.

| Action | Advisory | Consultative | Delegated | Partnership |
| --- | --- | --- | --- | --- |
| Automation setup | Explain and draft only | Persist settings after approval | Persist approved routine settings | Persist broad settings after explicit opt-in |
| Unattended inbox processing | Not allowed | Write proposals to pending approvals | File routine low-risk items and log | Same, with broader maintenance boundaries |
| Field-map write | Suggest pages only | Write after approval | Update approved schema pages and log | Reorganize field map within stated goals |
| Field-map query filing | Propose saved query | Save after approval | Save reusable answers and update index | Save and refactor query structure if useful |
| Collaborator handoff | Draft only | Write dated handbook after approval | Refresh approved handbook sections | Maintain canonical handbook when requested |

High sensitivity overrides trust. It blocks cloud processing and requires
redaction-aware handoff even at delegated or partnership trust.

Automation configuration is persisted with:

```bash
python3 scripts/carrel.py automation configure --vault <vault> --enabled true --trust-level consultative --schedule daily --review-cadence quarterly
```
