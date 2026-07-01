# Environment Profile Contract

`.carrel/environment.json` is the structured profile every Carrel-capable agent
can read. Keep it host-neutral.

## Required Fields

- `name`: optional researcher name.
- `field`: optional research field.
- `sensitivity`: `high`, `medium`, or `low`.
- `cloud_consent`: boolean.
- `comfort_level`: plain-language experience level.
- `tools_configured`: object mapping tool name to boolean availability.
- `preferences`: object for durable workflow preferences.
- `claude_code_familiarity`: `new`, `some`, `experienced`, or `null`.
- `automation`: object containing `enabled`, `trust_level`, `schedule`, and
  `review_cadence`.

## Adapter-Owned Fields

Some keys belong to another engine's schema and are tolerated, not required
or written, by the portable runtime:

- `version`: the full Claude Code plugin's semver, drift-checked there. The
  portable runtime never writes this field — its own version is surfaced only
  via `env doctor`'s `skill_pack_version` diagnostic, so the two version
  concepts never collide on a vault touched by both engines.

## Onboarding Preferences

Store host-neutral onboarding details in `preferences` rather than adding
host-specific top-level keys. Useful keys include:

- `agent_host`: app or CLI the researcher is using.
- `agent_experience`: new, some, or experienced.
- `timestamp_precision`: `text_only`, `rough`, or `precise`.
- `google_workspace`: `none`, `docs`, `sheets`, `slides`, or `mixed`.
- `cloud_storage`: durable storage location such as local, gdrive, dropbox, or
  onedrive.
- `note_platform`: obsidian, markdown, word, docs, or other.

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
