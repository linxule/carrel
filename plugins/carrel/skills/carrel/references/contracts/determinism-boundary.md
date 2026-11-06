# Determinism Boundary

Prefer agent proposal and synthesis for work that needs judgment. Add or call a
runtime command only when the operation needs repeatable filesystem behavior,
policy enforcement, or structured output.

## Keep In The Agent

- Literature interpretation, synthesis, critique, and gap analysis.
- Decisions about whether a source belongs in the project.
- Drafting collaborator prose, dashboards, summaries, or research notes before
  persistence.
- Choosing next actions when multiple reasonable workflows exist.
- Explaining tradeoffs and asking for approval.

## Put In Scripts

- Vault-safe path resolution and atomic writes.
- Source hashing, idempotency, frontmatter, and force/skip behavior.
- Environment profile validation, repair, backup, and schema drift reporting.
- Sensitivity, cloud-consent, and trust gates.
- Dated artifact paths for reflection, feedback, mirror, and handoff files.
- Optional adapter probes and deterministic wrapper calls.

## Size Check

If one script module grows beyond roughly 400 lines, split it by domain before
adding new behavior. If a proposed command mostly prints advice or prose, make
it a workflow reference instead of CLI surface.
