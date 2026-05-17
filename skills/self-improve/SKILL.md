---
name: self-improve
description: "This skill should be used when evaluating an external skill, MCP, or tool for absorption into Carrel ('should we absorb this', 'evaluate for absorption', 'does this overlap'), when Claude has just created a custom artifact for a researcher and needs to log it and update their environment dashboard, when promoting a recurring custom solution to a template ('promote this to a template', 'make this official'), when walking a researcher through a plugin version upgrade ('check for updates', 'what changed', '/carrel-migrate'), or during quarterly upstream review ('review upstream sources', 'what capabilities have we added', 'check registry')."
---

# self-improve

Carrel grows by absorbing capabilities from the ecosystem and by learning from what researchers actually need. This skill manages the full lifecycle — from ecosystem evaluation to researcher-facing environment tracking.

## When to Use

- **During development**: evaluating a new external skill, MCP, or tool for absorption
- **After creating custom artifacts**: Claude built a custom .base file, callout pattern, canvas, or workflow for a researcher — log it and update their environment dashboard
- **When the researcher's environment changes**: new tool installed, MCP configured, custom tracker created — update `_meta/my-environment.md`
- **Periodic review**: checking upstream sources for changes, reviewing what researchers have been requesting
- **Promotion decision**: a custom solution keeps recurring — time to make it a template

## Three Layers of Capability Tracking

Every capability in a researcher's environment belongs to one of three layers:

| Layer | Owner | What it tracks | Where it lives |
|-------|-------|---------------|----------------|
| **Plugin registry** | Dev team | What Carrel absorbed from the ecosystem | Plugin source: `self-improve/references/capability-registry.md` |
| **Capability log** | Claude | What Claude created in this vault | Vault: `_meta/capability-log.md` |
| **My environment** | Researcher | Everything — tools, MCPs, customs, what's available, what's not set up yet | Vault: `_meta/my-environment.md` |

The **plugin registry** is for development — evaluating, absorbing, tracking upstream. The researcher never sees it.

The **capability log** is the feedback channel — Claude logs what it creates, dev team mines it for promotion candidates.

The **my-environment dashboard** is the researcher's own view. It's the living answer to "what can I do?" and "what else is available?" Claude maintains it, but the researcher owns it and can edit it directly.

### Maintaining the Researcher's Dashboard

`_meta/my-environment.md` is created during setup (Step 8) from the `templates/my-environment.md` template. It should be updated whenever:

- A tool is installed or removed → update the Installed Tools table
- A cloud service is configured → update Cloud Services table
- A plugin-shipped tracker is added to the vault → add to "From Carrel" section
- Claude creates a custom tracker → add to "My Custom Trackers" section
- The researcher installs an Obsidian community plugin → add to Obsidian Setup section
- A skipped capability becomes available ("I got a Gemini key") → move from "Available but Not Configured" to the appropriate section

Present it to the researcher: "Your environment dashboard is at `_meta/my-environment.md` — it shows everything that's set up and what's available if you want to add more."

## The Growth Loops

### Loop 1: Absorb from Ecosystem (dev team)

External capability appears (new skill repo, MCP server, CLI tool, community template) → evaluate against criteria → absorb what's useful → reshape for research context → ship in next plugin version → researchers benefit.

### Loop 2: Learn from Researchers (Claude → dev team)

Researcher needs something templates don't cover → Claude creates a custom solution using references → logs in capability log → updates researcher's dashboard → pattern emerges across users → dev team promotes to template → all researchers benefit.

### Loop 3: Researcher Grows Their Environment (researcher)

Researcher discovers a need → asks Claude or does it themselves → adds tools, MCPs, Obsidian plugins, custom workflows → dashboard reflects the growth → "Available but Not Configured" shrinks as capabilities activate.

## What NOT to Absorb (fast reject)

Before evaluating, rule out the obvious:
- Code patterns or architecture docs — derive from reading the code
- Anything already in Carrel's core library — the CLI is the source of truth
- Capabilities with no clear research use case — just because it exists doesn't mean researchers need it
- Capabilities that would bloat context without proportional value

If it passes the fast reject, proceed to the full evaluation.

## Evaluating External Capabilities

When considering whether to absorb something, walk through these steps:

### Step 1: Overlap Check
Does it duplicate something Carrel already has?
- **Full overlap** → Skip (e.g., defuddle in obsidian-skills when Carrel has web-capture)
- **Partial overlap** → Consider enriching what exists
- **No overlap** → Evaluate further

### Step 2: Specificity
- **Generic infrastructure** (syntax refs, format specs, tool docs) → Good absorption candidate. Reshape for research context.
- **Domain-specific** (research workflows, methodology) → Write internally. This is Carrel's moat.
- **Mixed** → Split: absorb the generic layer, write the domain layer.

### Step 3: Freshness Sensitivity
- **High** (actively evolving upstream, like Obsidian features) → Absorb with quarterly review cadence
- **Low** (stable specs, mature formats) → Absorb freely — won't drift meaningfully

### Step 4: Token Cost vs. Value
- Curate aggressively. Drop what researchers won't encounter.
- Use the `references/` pattern for heavy content — only loaded on demand.
- If value is marginal, skip entirely regardless of cost.

### Step 5: Audience
- **All researchers** → Core inclusion
- **Subset** → Include but gate behind decision tree (setup interview determines if it's relevant)

## Absorbing a New Capability

Once evaluation passes:

1. **Curate**: Extract only research-relevant content. Drop generic padding, decorative examples, edge cases researchers won't hit.
2. **Place**:
   - Reference file → `skills/<relevant-skill>/references/<name>.md`
   - Templates → `templates/<name>.<ext>`
   - Judgment → add section to the relevant `SKILL.md`
3. **Track**: Add upstream source header to the reference file:
   ```markdown
   <!-- Source: owner/repo/path @ version (date) -->
   <!-- Curated for Carrel research context -->
   <!-- Review cadence: quarterly (next: YYYY-MM-DD) -->
   ```
4. **Register**: Add entry to `references/capability-registry.md`
5. **Enable custom creation**: Ensure the reference is complete enough for Claude to create new variations, not just use pre-built templates
6. **Wire into decision tree**: If the capability should be offered during setup, add a branch to `skills/environment-setup/references/decision-tree.md`

## Plugin-Shipped vs. Vault-Local Capabilities

Two namespaces of capabilities coexist in every vault. They must never collide.

### Plugin-shipped (updates with Carrel)

These come from Carrel's `templates/` directory, copied to the vault during scaffold. Each has a **source marker** (format varies by file type):

| File type | Marker syntax |
|-----------|---------------|
| `.base` | `# carrel-template: name v0.0.0` (YAML comment) |
| `.md` | `<!-- carrel-template: name v0.0.0 -->` (HTML comment, first line) |
| `.json` | `"_carrel_template": "name v0.0.0"` (top-level key) |

Example for `.base` files:
```yaml
# carrel-template: paper-tracker v0.3.0
# Do not remove this marker — it helps Carrel detect updates.
# Safe to customize everything below.
```

**Rules:**
- Plugin updates NEVER overwrite vault copies. Templates in `templates/` update; vault copies are untouched.
- `/carrel-migrate` compares the marker version against the plugin's current templates. If there's a newer version, it shows the diff and asks: "Your paper tracker is customized. The new plugin version has improvements — want to see what changed?"
- Researchers can freely edit plugin-shipped files. The marker stays for version tracking, but the content is theirs.

### Vault-local (researcher's own)

These are capabilities Claude creates during sessions or the researcher builds themselves. They have **no `carrel-template:` marker**.

**Where they live:**
- `.base` files → vault root (alongside plugin-shipped ones)
- Custom references, callout patterns, workflows → `_meta/local/`
- The capability log → `_meta/capability-log.md`

**Rules:**
- Plugin updates NEVER touch files without a `carrel-template:` marker.
- Plugin updates NEVER touch `_meta/local/` or `_meta/capability-log.md`.
- `/carrel-migrate` ignores vault-local files entirely — they're the researcher's.
- When creating a new vault-local capability, NEVER add a `carrel-template:` marker. That namespace is reserved for plugin-shipped content.

### How to tell them apart

| | Plugin-shipped | Vault-local |
|---|---|---|
| **Has `carrel-template:` marker** | Yes | Never |
| **Updated by plugin** | Template source updates; vault copy untouched | Never touched |
| **Created by** | `carrel vault init` (scaffold) | Claude during sessions, or researcher manually |
| **Migrate behavior** | Compares versions, offers diff | Ignored |
| **Examples** | `paper-tracker.base`, `interview-tracker.base` | `grant-tracker.base`, custom callout patterns |

### Scaffold behavior

When `carrel vault init` copies a template to the vault:
1. Check if a file with the same name already exists
2. If yes AND it has a `carrel-template:` marker → skip (already installed, possibly customized)
3. If yes AND it has NO marker → skip (it's vault-local; don't overwrite)
4. If no → copy the template (marker included)

This means: scaffolding is always safe to re-run. It never overwrites anything.

## Logging Custom Creations

When Claude creates a custom artifact for a researcher (a .base file not from templates, a novel callout pattern, a custom canvas layout, a new workflow), do two things:

### 1. Save the artifact without a marker

Save to the vault root (for .base files) or `_meta/local/` (for references, patterns, workflows). Do NOT include a `carrel-template:` marker — this marks it as vault-local.

### 2. Append to the capability log

Add an entry to `_meta/capability-log.md` in the researcher's vault:

```markdown
## YYYY-MM-DD: [short description]
- **Type**: base | callout-pattern | canvas | workflow | other
- **What**: [what was created and why]
- **Researcher need**: [what the researcher asked for]
- **Based on**: [which reference was used, e.g., "research-databases.md"]
- **Reusable?**: yes | maybe | no (one-off)
- **Template candidate?**: [if yes, what would the template look like]
```

This log lives in the researcher's vault (in `_meta/`), not in the plugin source. The dev team aggregates across vaults during review sessions.

When logging a custom creation, also mention it to the researcher: "I created a custom grant tracker for you — noted it in your capability log for potential inclusion in future Carrel versions."

The session reflection hook (`hooks/session-reflect.js`) reads `_meta/capability-log.md` at session end and surfaces any entries from today: "Custom capabilities created today: 2 — grant-tracker, field-notes-callouts." This closes the feedback loop without requiring the researcher to do anything.

## Promoting Vault-Local to Plugin-Shipped

When the same kind of custom artifact appears across multiple researchers (or the same researcher requests it repeatedly):

1. **Extract the pattern**: What's common across instances? What varies?
2. **Create a template**: Add to plugin's `templates/` with a `carrel-template:` marker and sensible defaults
3. **Add to decision tree**: Under what interview conditions should this be offered?
4. **Update the relevant SKILL.md**: Add to the "Available Templates" section
5. **Update capability registry**: Mark as promoted from ad-hoc to template
6. **Migration note**: In the next version's migration file, mention: "New template available: `grant-tracker.base`. If you created one locally, you can keep yours or switch to the official version."

Researchers who already created a local version keep it. The plugin-shipped version is available for new vaults and for researchers who want to switch.

## Walking a Researcher Through a Plugin Upgrade

When the researcher invokes `/carrel-migrate` (or asks "what's new", "check for updates", "anything I should upgrade"), orchestrate the upgrade as a brief conversation around a single CLI call. The CLI does the registry walk, version comparison, and `plugin-state.json` write atomically; the skill handles assessment, framing, and any manual steps each migration calls out.

### Calling pattern

```
carrel migrate apply [--plugin-root <path>]
```

`--plugin-root` defaults to `${CLAUDE_PLUGIN_ROOT}` — only override when the researcher is running migrations against a non-active plugin install (rare). The CLI returns the list of applied migrations with their manual steps; the skill narrates them.

### Before calling the CLI

Quickly assess the current environment so suggestions land in context, not in the abstract:

- Read `.carrel/environment.json` — note configured tools, sensitivity, trust level, what the researcher said they wanted but skipped
- Check what's actually installed on the machine (the env-doctor skill already knows how) and flag gaps the researcher might want to close in this session
- Confirm the vault `CLAUDE.md` exists and looks current — if it's stale, mention that the upgrade is a good moment to refresh it

This is a 15-second pass, not a full audit. The point is to have one or two concrete suggestions ready alongside the version bump.

### After the CLI returns

For each applied migration:

- Tell the researcher what changed in terms of what they can now do — not in terms of code changes or refactors
- Walk them through any manual steps the migration flagged (the CLI surfaces these; the skill paces them)
- Confirm when a step is done before moving to the next
- If a migration reports no action required, say so explicitly so the researcher doesn't wonder what they missed

Then offer the 1-2 suggestions you noted in the pre-pass:

- New commands or skills that became available since their last version
- Tools they expressed interest in at setup but haven't configured (cloud tools if comfort has grown, Zotero if they've started a literature review, etc.)
- Vault structure or configuration improvements the upgrade enables

Frame these as options, not requirements. Researchers aren't obligated to adopt every new capability the moment it ships.

### Already up to date

If the CLI reports no migrations applied and your pre-pass found no gaps: tell the researcher they're on the latest version and the setup looks good. Show the current version and the last-check date from `plugin-state.json`. Don't manufacture suggestions to justify the conversation.

### Pre-versioning installs

If `.carrel/environment.json` exists but `.carrel/plugin-state.json` doesn't, the researcher is on a pre-versioning install. The CLI treats this as "apply all migrations from the earliest tracked version forward" — the skill's job is to set expectations: "Your vault predates the migration system, so I'll walk you through everything that's changed since you installed."

### Tone

Be brief and friendly. Researchers aren't developers — keep language at the level the setup interview established. Frame suggestions as options. Don't recite the migration file verbatim; translate it.

## Reviewing Upstream Sources

Quarterly (or when a major upstream release happens):

1. Check each entry in `references/capability-registry.md`
2. Visit the upstream source — has anything changed?
3. If new features are research-relevant: update the reference file
4. If upstream has breaking changes: update templates and references
5. If upstream is abandoned: note in registry, consider the content frozen
6. Update the "next review" date in each reference file header

## Related

- **CLI**: `carrel migrate apply` (walks the migration registry and updates `plugin-state.json`)
- **Commands**: `/carrel-migrate` (thin wrapper that invokes this skill)
- **References**: `references/capability-registry.md` (what's been absorbed and when)
- **Skills**: `vault-ops` (where most absorbed Obsidian capabilities land), `environment-setup` (decision tree for offering capabilities), `env-doctor` (the pre-upgrade install check)
- **Hooks**: `session-reflect.js` (captures what Claude built during a session); `check-version.js` (surfaces the upgrade prompt on session start)
