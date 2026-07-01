# Onboarding

Use this workflow when Carrel is setting up a researcher for the first time,
refreshing an incomplete profile, adding capabilities, or re-orienting a
returning researcher. The interview is the portable replacement for the legacy
plugin setup flow: keep the conversation in the agent, then use the runtime for
deterministic vault writes and validation.

## Contents

- Mode Detection
- Interview Style
- First-Time Flow
- Setup Plan Rules
- Audit Presentation
- Agent Context
- Returning Users

## Mode Detection

Inspect `.carrel/environment.json` and `.carrel/agent-context.md` if they exist.

| State | Agent behavior |
| --- | --- |
| No `.carrel/environment.json` | Run the first-time interview, propose a setup plan, then scaffold the vault. |
| Valid profile exists | Summarize the known setup and ask whether to check status, add a capability, troubleshoot, or continue work. |
| Invalid or drifted profile | Run `env validate`; propose `env fix`; preserve useful values; ask only for missing research preferences. |
| User asks to add a tool | Ask only the questions needed for that capability, then update `tools_configured`, `preferences`, and context. |
| Prior setup was interrupted | Resume from the profile and context that exist. Do not depend on host-specific setup-state files. |

## Interview Style

Treat setup as a short conversation with a new colleague, not a survey. Aim for
roughly 10 minutes. Ask follow-up questions when answers reveal real research
context, but skip anything already answered.

Use plain research vocabulary. Avoid terms such as MCP, API, command line,
frontmatter, or configuration unless the researcher uses them first. Be honest
about limits and privacy tradeoffs.

Cover these areas naturally:

- Research field, current projects, and typical work.
- File types: PDFs, Word documents, slides, spreadsheets, web pages, audio,
  video, Google Workspace files, and notes.
- Sensitivity: IRB or participant data, student records, unpublished
  manuscripts, confidential documents, and public-only material.
- Existing tools: reference manager, cloud storage, Obsidian or another notes
  app, browser, transcription tools, and citation workflow.
- Working preferences: how much explanation they want, local-only versus cloud
  comfort, and whether they prefer proposals before file changes.
- Agent host context: which app or CLI they are using and how familiar they are
  with it. Store this in `preferences.agent_host` and
  `preferences.agent_experience`, not in a host-specific top-level field.
- Collaborators: co-authors, students, assistants, lab members, or others who
  may need a handoff later.
- Optional model teammates: whether they already use other AI systems and
  whether they want them available for review, long-context synthesis, or
  delegated work.

## First-Time Flow

1. Open with what Carrel will set up: a research vault that agents can use for
   source ingestion, notes, transcripts, privacy-aware routing, reflection, and
   collaborator handoff.
2. Run `python3 scripts/carrel.py env doctor --vault <vault> --format json`
   when a vault path is known. Translate findings into plain language; do not
   paste raw audit output unless asked.
3. Interview the researcher. Summarize what you heard and ask for confirmation
   before writing durable preferences.
4. Convert the confirmed interview into `.carrel/environment.json` fields:

   | Interview signal | Profile location |
   | --- | --- |
   | Name and field | `name`, `field` |
   | Privacy stance | `sensitivity`, `cloud_consent` |
   | Comfort with explanations | `comfort_level` |
   | Tool availability | `tools_configured` |
   | Workflow details | `preferences` |
   | Collaborators | `collaborators`, `team_context` |
   | Other AI systems | `model_teammates` |

5. Propose a setup plan in plain language. Name what will be local, what would
   require a cloud service, and what can wait.
6. After approval, run `vault init`, write or update the profile, update
   `.carrel/agent-context.md`, then run `env validate`.
7. If validation reports drift, run `env fix --dry-run` first, explain the
   proposed repair, then run `env fix` only after approval unless the user
   already asked for repair.
8. Once the profile is written and validated, draft `_meta/my-environment.md`
   from `assets/templates/my-environment.md`: list configured tools, tools the
   researcher deferred ("Available but Not Configured" — Zotero, mineru,
   mistral_ocr, gws, groq, or anything noted as "available later"), and which
   `.base` trackers were installed. This is the researcher's living view of
   their environment; update it whenever tools, cloud services, or preferences
   change.

## Audit Presentation

Show setup audits as a decision tree, not as a raw dump.

1. Start with the current readiness state: ready, usable with caveats, blocked,
   or needs repair.
2. Separate local capabilities from cloud capabilities.
3. Name the next action the researcher can approve: initialize, repair profile,
   install optional adapter, or defer.
4. Keep ambiguous or missing information as explicit questions. Do not invent
   sensitivity, collaborator, or tool-install facts.
5. When a setup step is adapter-specific, point to the relevant adapter/source
   link instead of making the portable workflow depend on that host.

## Setup Plan Rules

- Always set `sensitivity: "high"` and `cloud_consent: false` for IRB data,
  participant recordings, student records, or confidential unpublished material.
- High sensitivity blocks cloud tools even if the researcher generally likes
  cloud services.
- For medium sensitivity, prefer local tools and ask before cloud processing.
- For low sensitivity, cloud tools may be available when `cloud_consent` is
  true, but still explain what leaves the machine.
- Prefer local PDF and audio paths for default setup. Offer Mistral OCR, MinerU,
  Groq, Gemini, Google Workspace, or other cloud adapters only as optional
  capabilities with clear consent.
- Use `preferences.timestamp_precision` to distinguish clean-readable
  transcripts from timestamp-sensitive qualitative analysis.
- Treat Obsidian as a useful vault interface, not a requirement for Carrel to
  function.
- Mention collaborator handoff only when the researcher has collaborators or is
  preparing to share the vault.

## Agent Context

Write `.carrel/agent-context.md` as the readable companion to the structured
profile. Include durable information future agents need for judgment:

- Who the researcher is and what they work on.
- Privacy posture and cloud-processing rules.
- Preferred explanation style and approval expectations.
- Installed or intentionally skipped capabilities.
- Collaboration context and handoff needs.

Do not generate host-specific memory files from the portable onboarding flow.
Those belong to adapters.

## Returning Users

For a valid existing profile, start by reflecting the current setup:

- "I see this vault is set for medium sensitivity, local-first processing, and
  PDF plus web capture. Do you want a status check, a new capability, or should
  we get to work?"

Then update only the fields affected by the user's request. Re-run
`env validate` after profile changes and keep `.carrel/agent-context.md`
consistent with the structured profile.
