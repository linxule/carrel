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

Automation configuration is persisted with:

```bash
python3 scripts/carrel.py automation configure --vault <vault> --enabled true --trust-level consultative --schedule daily --review-cadence quarterly
```
