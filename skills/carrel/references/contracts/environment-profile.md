# Environment Profile Contract

`.carrel/environment.json` is the structured profile every Carrel-capable agent
can read. Keep it host-neutral.

## Required Fields

- `version`: runtime or skill-pack version.
- `name`: optional researcher name.
- `field`: optional research field.
- `sensitivity`: `high`, `medium`, or `low`.
- `cloud_consent`: boolean.
- `comfort_level`: plain-language experience level.
- `tools_configured`: object mapping tool name to boolean availability.
- `preferences`: object for durable workflow preferences.
- `automation`: object containing `enabled`, `trust_level`, `schedule`, and
  `review_cadence`.

## Repair

`python3 scripts/carrel.py env validate --vault <vault> --format json` returns:

- `0` for valid profile.
- `1` for invalid JSON or invalid field values.
- `2` for drift such as unknown or missing top-level keys.

`python3 scripts/carrel.py env fix --vault <vault>` preserves known values,
fills missing defaults, moves unknown top-level keys into `_unknown_keys`, and
writes a backup before changing an existing profile.

## Host Context

The neutral narrative companion is `.carrel/agent-context.md`. Host-specific
memory files are adapter outputs, not canonical profile state.
