# Carrel Vault Contract

Carrel writes only inside the vault root. Runtime helpers must resolve output
paths through the vault-safe path helper before writing.

## Required Structure

- `.carrel/environment.json`: structured researcher profile.
- `.carrel/agent-context.md`: host-neutral narrative context for future agents.
- `inbox/`: captured web pages and unsorted incoming material.
- `papers/`: converted papers, using `papers/<slug>/paper.md`.
- `transcripts/`: transcript markdown files.
- `notes/`, `drafts/`, `talks/`, `admin/`: researcher workspace folders.
- `_templates/`: copied Markdown note templates. Legacy `.base` copies may remain here but are never deleted.
- Vault root `.base` trackers: `reading-progress.base` always, with paper,
  interview, and writing trackers selected from the validated profile.
- `_meta/`: operational records and generated handoff material.

## Generated Artifact Paths

- Reflection log: `_meta/reflections/reflection-YYYY-MM-DD.md`
- Monthly mirror: `_meta/mirror/YYYY-MM.md`
- Feedback digest: `_meta/feedback-digest-YYYY-MM-DD.md`
- Collaborator handbook: `_meta/handbook/YYYY-MM-DD-for-<slug>.md`
- Pending decisions: `_meta/pending-decisions.md`

## Idempotency

Ingestion outputs include `source_hash` in frontmatter. Re-running the same
source should skip unless the caller passes `--force`.

## Host-Specific Files

Do not treat `CLAUDE.md`, slash commands, hooks, or marketplace manifests as
required vault state. Generate them only from a host adapter.
