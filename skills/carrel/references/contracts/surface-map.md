# Surface Map

Carrel's portable skill is not a wholesale copy of the legacy CLI. Treat each
legacy surface according to the determinism boundary.

## Runtime Commands

Keep these in `scripts/carrel.py` because they enforce vault safety,
idempotency, policy gates, structured output, or dated artifact paths.

| Legacy surface | Portable runtime surface | Notes |
| --- | --- | --- |
| `vault init` | `vault init` | Validates an optional `--profile-file` before writes; creates folders, note templates, selected root trackers, profile/context, and `.obsidian/` config. |
| `env doctor` | `env doctor` | Reports optional adapter availability without requiring third-party imports. |
| `env validate`, `env fix` | `env validate`, `env fix` | Repairs profile drift with backups and preserves adapter-owned fields. |
| `paper convert` | `convert file` | Uses stdlib text filing or optional adapters; no `src/carrel` import. |
| `capture url` | `capture url` | Captures provided content or optional local adapters. |
| `transcript create` | `transcript create` | Files provided transcripts and enforces sensitivity routing. |
| `google export` | `google export` | Validates Google URLs and uses optional `gws` or provided content. |
| `batch convert`, `batch transcribe` | `batch convert`, `batch transcribe` | Enumerates folders and writes unattended failures to pending decisions. |
| `trust check`, `trust list`, `trust show` | same | Keeps trust gates deterministic across hosts. |
| `automate configure` | `automation configure` | Writes the portable automation profile after trust check. |
| `vault feedback export` | `feedback export` | Writes dated redacted digest. |
| `vault mirror` | `mirror write` | Writes monthly mirror from supplied synthesis. |
| `vault reflect-log` | `reflection append` | Appends dated reflection entries. |
| `vault share generate` | `share generate` | Writes collaborator handoff with sensitivity redactions; accepts agent-synthesized stdin and optional canonical handbook writes. |
| `vault automation-prompt` | `vault automation-prompt` | Generates the deterministic prompt explicitly; `--force` replaces it without a `.prev` backup. |

## Agent Workflows

Keep these as agent workflows or references because the useful work is search,
judgment, summarization, or prose generation. Agents may still use the runtime
for final persistence.

| Legacy surface | Portable disposition |
| --- | --- |
| `vault new` | Agent chooses a template from `assets/templates/`, fills it, and writes the note with vault-safe care. Add a script only if repeated note creation needs idempotent structured output. |
| `vault search` | Agent or host search should inspect vault files directly. A script would add little beyond `rg` or host-native search. |
| `vault status` | Agent can count folders directly or synthesize status from the vault contract. |
| `vault organize` | Agent proposes moves; do not auto-move files without explicit approval. |
| `vault cheatsheet` | Agent drafts from profile, templates, and current tools; persist only after review. |
| `vault dashboard` | Agent synthesizes dashboard prose from profile and activity; runtime should not own judgment-heavy layout. |
| `env profile` | Agent reads `.carrel/environment.json` directly when profile display is needed. |
| `paper list`, `transcript list` | Agent lists `papers/*/paper.md` or `transcripts/*.md` directly. |
| wiki/research partner workflows | Agent proposes and writes only after approval unless the trust profile allows the action. |
| setup interview | `references/workflows/onboarding.md`; the agent converses, audits, and summarizes before deterministic writes. |
| automation behavior | `references/workflows/automation.md`; runtime stores settings, while the host schedules runs. |
| collaborator refinement loop | `references/workflows/collaborator-handoff.md`; runtime persists final approved handbooks. |
| field map and knowledge wiki | `references/workflows/field-map.md`; field-map writes require trust checks and logs. |
| note templates and Obsidian conventions | `references/workflows/vault-ops.md` and `assets/templates/`; agent judgment chooses the note shape. |
| reflection conversation and mirror synthesis | `references/workflows/reflection-and-feedback.md`; runtime stores final reflection, mirror, and digest artifacts. |
| interactive batch protocol | `references/workflows/ingestion.md`; runtime owns file conversion and transcript persistence only. |

## Host Or Adapter Surfaces

Keep these outside the portable core.

| Legacy surface | Portable disposition |
| --- | --- |
| `migrate apply` | Claude/plugin adapter only. It depends on plugin versions and host-specific state. |
| `setup-state advance`, `complete`, `show`, `reset` | Host adapter setup flow only. Portable setup state is `.carrel/environment.json` plus `.carrel/agent-context.md`. |
| `vault check-sync`, `vault add-markers` | Claude adapter only because they manage `CLAUDE.md` markers. |
| Slash commands and hooks | Host adapter only. They should call the bundled runtime or read these references. |
| Host scheduling walkthroughs | Adapter documentation only. Portable Carrel generates the prompt; Cowork or another host owns the saved schedule. |
| marketplace/plugin state | Adapter only. Portable Carrel is the skill folder plus bundled scripts. |
| model teammate install commands | Adapter only. Portable Carrel records `model_teammates`, sensitivity gates, and research use cases. |

## Asset And Template Surfaces

Keep reusable but judgment-light scaffolds in `assets/templates/`: paper,
transcript, agent context, vault scaffold, Obsidian configuration, and other
starter text. Do not encode one-off dashboards, custom trackers, or literature
wiki pages as runtime commands unless they become repeatable deterministic
artifacts.

## Completeness Rule

When adding a new legacy-compatible surface, first update this map. If the row
belongs in "Agent Workflows", prefer a workflow reference over a new command.
If it belongs in "Runtime Commands", keep the implementation in the relevant
domain module and preserve the module size guard.
