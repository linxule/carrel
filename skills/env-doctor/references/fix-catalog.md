# Layer 2 Fix Catalog

These are the deterministic repairs that `carrel env fix --safe` can apply without interpretation when the surrounding fields are consistent.

## Known-Safe Rules

- `sensitivity: prefer_local` or `cautious` → `medium`, with `cloud_consent=false`
- `sensitivity: external` or `permissive` → `low`, with `cloud_consent=true`
- `version` present but outdated → replace with the current Carrel plugin version
- Missing optional fields → populate from safe defaults
- `tools_configured.*` mismatches the live `PlatformToolMatrix` → rewrite to the current platform value
- Unknown top-level keys → move under `_unknown_keys` by default, or strip them with `--no-preserve-unknown`

## Deferred to Layer 3

- Legacy sensitivity labels that conflict with the current `cloud_consent` value
- Any disagreement between CLAUDE.md markers and `environment.json`
- Invalid structures that still fail validation after applying the safe rules

## Revert Path

Layer 2 writes `.carrel/environment.json.bak` before changing the live file. Revert by restoring the backup and re-running `carrel env validate`.
