---
name: vault-ops
description: "This skill should be used when a researcher wants to create, search, organize, or manage notes in their Obsidian vault. Triggers on 'create a note', 'find my notes about', 'organize', 'search vault', 'link notes', 'use template', 'vault status', 'check inbox', 'what's in my vault', or any vault file operation."
---

# vault-ops

Read, write, search, and organize the researcher's Obsidian vault. The CLI handles mechanical operations — this skill provides the judgment layer: which template, what links, when to reorganize.

## When to Use

- Researcher wants to create a new note (paper notes, meeting, reflection, daily)
- Researcher asks to find, search, or organize vault content
- Researcher wants to link notes or explore connections
- Any read/write operation on vault files

## Vault Structure

Standard Carrel vault layout (created via `carrel vault init <path>`):

```
vault/
├── inbox/          # Drop zone — unsorted incoming
├── papers/         # Converted papers — one FOLDER per paper
│   └── corley-gioia-2004/
│       ├── paper.md            # The converted paper content
│       └── images/             # Extracted figures/assets
├── notes/          # Research notes, meeting notes, ideas
├── transcripts/    # Audio transcriptions (filed via carrel transcript)
├── drafts/         # Writing in progress
├── talks/          # Presentation prep
├── admin/          # Committee work, letters, admin tasks
├── _meta/          # Cheat sheet, local scratch, reflections, friction log
│   ├── local/      # Local-only working files and exports
│   └── reflections/ # Structured reflection notes
└── _templates/     # Note templates (meeting, reflection, daily, paper-notes)
```

## Papers vs Notes — Critical Distinction

**Converted papers** and **researcher notes** are different things:

- **Converted paper** = the actual paper content converted from PDF/DOCX → filed to `papers/<author-year>/paper.md` by `carrel paper convert`. NO note template. Just frontmatter + converted content.
- **Paper notes** = researcher's own thinking about a paper → saved to `notes/` using `_templates/paper-notes.md`. Links back with `[[papers/corley-gioia-2004/paper]]`.

NEVER apply a note template to a converted paper. The convert command handles papers; vault-ops handles notes about papers.

## Template Selection Judgment

Use `carrel vault new <name> --template <template>` to create from a template, or apply manually:

1. **paper-notes** — researcher's thinking about a specific paper → `notes/`
2. **meeting** — any synchronous conversation → `notes/`
3. **reflection** — periodic sensemaking, project retrospectives → `_meta/reflections/`
4. **daily** — daily log, task tracking → `notes/`
5. **freeform** — no template, open-ended → `notes/` or `inbox/`

Replace `{{date}}` placeholders with today's date (YYYY-MM-DD). Name files descriptively: `meeting-kevin-2026-03-26.md`, `notes-on-corley-gioia-2004.md`.

## YAML Frontmatter

All notes should have YAML frontmatter for Obsidian's Properties:

```yaml
---
title: The Title
tags: [qualitative, identity, organizational-change]
date: 2026-03-26
status: draft
---
```

For paper notes, include: title, authors, year, journal, doi, tags, status.
For meeting notes: date, participants, project, type.

## Cross-Linking Intelligence

Use Obsidian wiki-link syntax to connect notes:

- `[[note name]]` — link to another note
- `[[note name|display text]]` — link with custom display text
- `[[note name#heading]]` — link to a specific section

When creating or editing notes, actively suggest relevant links based on vault content:
"This paper discusses identity construction — you have notes on that in `[[notes/identity-theory-overview]]`."

Use `carrel vault search <query>` to surface related content before suggesting links.

## Vault Hygiene

- Check `carrel vault status` to see accumulation before suggesting organization
- Use `carrel vault organize` to get sorting suggestions for inbox files
- If inbox has 5+ files, proactively flag: "You have N files in inbox/ — want me to sort them?"
- Update links when moving files: find and replace `[[old-name]]` → `[[new-name]]`
- Every content file has a home; only intentional root control files and selected `.base` trackers stay in the vault root

## Analytical Threads

When a researcher wants to explore material through different theoretical lenses, analytical threads keep the experiments organized without flattening them into a single interpretation.

### Structure

1. Create `notes/threads/<thread-name>/` (e.g., `notes/threads/practice-theory/`)
2. Create a thread overview note at `notes/threads/<thread-name>/README.md` with:
   - **Lens** — what theoretical or methodological frame is being applied
   - **Starting questions** — what the thread is trying to answer or surface
   - **Source material** — wiki-links to the papers/transcripts being analyzed (e.g., `[[papers/corley-gioia-2004/paper]]`)
   - **Status** — one of: `active` / `paused` / `completed` / `abandoned` (with reason)
3. Notes within a thread follow normal vault-ops conventions — templates, frontmatter, cross-links, all the same rules apply

### Principles

- No thread is "primary" — parallel threads are preserved intellectual experiments, not a competition
- Use frontmatter `tags` to mark thread membership (e.g., `tags: [thread/practice-theory]`) so Obsidian Bases can filter across threads
- "Abandoned" threads stay in the vault with a note explaining why — the dead end is data, not failure

### When to Suggest Threads

- Researcher has the same corpus but asks "what if I look at this through a different lens"
- Researcher is comparing two theoretical framings and doesn't want to commit yet
- Researcher has notes that feel like they're pulling in conflicting directions

Don't suggest threads for normal note accumulation — threads are for deliberate parallel analysis, not general organization.

## Obsidian Formatting

Use Obsidian-specific formatting to make notes more readable in the GUI. See `references/obsidian-formatting.md` for full syntax.

### When to Use Callouts

Use callouts in **reading notes** and **interview summaries** — the files researchers revisit most:

- `> [!quote]` — direct quotes with attribution (paper notes, interview excerpts)
- `> [!question]` — open questions the researcher should return to
- `> [!important]` — key findings worth highlighting
- `> [!warning]` — sensitivity alerts on files with participant data

Don't over-use callouts in converted papers or transcripts — those are raw content. Callouts belong in the researcher's own notes.

### When to Use Embeds

Use `![[file#heading]]` embeds when a note references a specific section of a paper or transcript. This lets the researcher see the relevant passage inline without switching files.

Note: block-ID embeds (`![[file#^block-id]]`) require a `^block-id` marker to already exist in the source file. Only use them if you've confirmed or placed the marker — otherwise the embed silently breaks.

### When to Use Foldable Callouts

For long quotes or extended passages (10+ lines), use collapsed-by-default callouts: `> [!quote]- Click to expand`. This keeps reading notes scannable. Short quotes (1-3 lines) should never be folded.

### Frontmatter for Bases

All notes should include structured frontmatter (tags, status, date) because Research Databases query these fields. See YAML Frontmatter section above and `references/research-databases.md` for which fields the database templates expect.

## Research Databases

Obsidian Bases (`.base` files) give researchers live, filterable views over their vault — like Notion databases but local. See `references/research-databases.md` for full syntax and `templates/*.base` for research templates.

### When to Suggest a Database View

- Researcher has **10+ papers** and asks "what have I read?" or "I'm losing track"
- Researcher asks to **sort, filter, or compare** across multiple files
- Qualitative researcher managing **interview coding progress**
- Researcher tracking **writing progress** across draft sections
- Any "show me everything that matches X" request

### Available Templates

| Template | Best for | Key fields |
|----------|----------|-----------|
| `paper-tracker.base` | Literature management | title, authors, year, status, method, key-finding, tags + days-in-vault formula |
| `interview-tracker.base` | Qualitative research | participant, date, kind, transcribed, coded, themes, follow-up + coding-status formula |
| `reading-progress.base` | Reading pipeline | title, status, tags + days-in-vault, is-stale formulas |
| `writing-tracker.base` | Active writing projects | section, status, word-count, due-date, blockers + days-until-due formula |

Before creating a custom database, check whether an existing template already covers the researcher's need — the fields above are often sufficient with minor customization.

### Creating a Database View

1. Choose the right template from `templates/*.base`
2. Copy it to the vault root (or relevant folder)
3. Customize filters/columns for the researcher's specific needs
4. Tell the researcher: "Open `paper-tracker.base` in Obsidian — you'll see a sortable table of all your papers."

### Custom Database Views

The 4 templates are starting points. Researchers often need something the templates don't cover — grant applications, student supervision, conference submissions, teaching evaluations, fieldwork sites, you name it.

When a researcher asks to track something not covered by the templates, **create a custom .base file** using `references/research-databases.md` as the syntax guide:

1. Ask what they want to track and what columns matter
2. Identify which vault folder (or frontmatter tags) to query
3. Start with a plural `filters` block using `file.inFolder()` plus 3-5 frontmatter properties the researcher named; add formulas only if they ask for calculations
4. Write the `.base` file, then run through the validation checklist in `references/research-databases.md` before saving (verify folder paths, escaped strings, property type alignment)
5. Save to the vault root with a descriptive name (e.g., `grant-tracker.base`) — do NOT add a `carrel-template:` marker (this is vault-local)
6. Tell the researcher: "Open `grant-tracker.base` in Obsidian — you can sort and filter it."

Also customize existing templates when they're close but not quite right — add columns, change filters, add views. The templates are meant to be adapted, not used verbatim.

The same applies to **callouts and canvas files**. If a researcher's discipline has specific annotation patterns (e.g., field notes with `[!observation]` and `[!memo]` callouts), create those patterns using `references/obsidian-formatting.md`. If they need a visual map beyond the standard concept map, build it using the canvas syntax in `skills/research-partner/references/concept-mapping.md`.

### Keeping Databases Useful

Database views are only as good as the frontmatter in the notes they query. When creating or editing notes:
- Always include `status` (unread, reading, noted, cited)
- Always include `tags` for thematic filtering
- For transcripts: store `transcribed` as the ISO transcription date; use booleans for `coded` and `follow-up`

## Guidelines

- Always preserve existing content — never overwrite without asking
- Add frontmatter to files that lack it
- Use the researcher's vocabulary (from CLAUDE.md profile)
- Suggest connections proactively when context is recognizable
- Keep file paths relative within the vault for Obsidian compatibility

## Related

- **CLI**: `carrel vault init` creates vault structure; `carrel paper convert` files papers; `carrel transcript` files transcripts
- **Skills**: `convert` adds converted documents; `environment-setup` bootstraps the workspace
- **References**: `references/obsidian-formatting.md` (callouts, embeds, properties), `references/research-databases.md` (bases syntax + templates)
