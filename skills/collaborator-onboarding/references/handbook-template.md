# Handbook Template

Use this structure when generating a collaborator handbook. Each section has source material and a "skip if" rule. Lead with substance — one paragraph per section is plenty for most.

---

## Template

```markdown
# Working in [Researcher Name]'s Vault — for [Collaborator Name]

> Generated [YYYY-MM-DD]. This is a snapshot of how this vault works right now. Ask [researcher] if anything looks out of date.

## About This Vault

[1-2 paragraphs: who the researcher is, their field, what they're working on right now, what this vault is for. Pull from CLAUDE.md "About This Researcher" + recent reflections for current focus.]

## Sensitivity & What You Can and Can't Do

[Pull from environment.json sensitivity + CLAUDE.md Preferences. Be explicit:
- HIGH: "All transcripts and unpublished work stay local. Never use cloud APIs without checking first. The configured tools default to local for this reason."
- MEDIUM: "Most things are local by default; cloud tools are available for non-sensitive work."
- LOW: "Cloud and local tools both available; use what fits."

If automation is enabled, mention what it does and doesn't touch.]

**Skip if:** sensitivity is undefined.

## Vault Layout

[Top-level folders that exist, what each is for. Pull from actual vault structure, not the default Carrel scaffold. Example:
- `papers/` — converted PDFs and articles
- `transcripts/` — interview recordings, transcribed
- `notes/` — your concept notes, literature notes, drafts
- `notes/threads/` — analytical threads (active investigations)
- `inbox/` — drop new files here for processing
- `_meta/` — environment metadata, briefs, friction log; mostly Claude's territory
- `wiki/` — agent-maintained knowledge synthesis (if wiki is active)]

## Tools Available

[From environment.json tools_configured. Brief, plain language:
- PDF conversion: liteparse (local) [+ mineru or mistral_ocr (cloud) if configured]
- Audio: coli (local) [+ groq (cloud) if configured]
- Web pages: defuddle
- YouTube: youtube_captions [+ Gemini if configured]
- Reference manager: zotero (if configured)
- Multi-model perspectives: vox (if configured)
- Google Workspace: gws (if configured)]

## How [Researcher] Works

[Synthesize from reflections + capability log + mirror. Examples of what to extract:
- Workflow patterns: "Drops PDFs into inbox/ in batches, processes with /carrel-batch weekly"
- Note conventions: "Literature notes go in notes/lit/, concept notes in notes/concepts/"
- Custom trackers added: "Reading-progress.base in the root — open in Obsidian to see the pipeline"
- Active habits: "Reflects most weeks; uses analytical threads for multi-week investigations"]

**Skip if:** no reflections or capability log entries yet.

## Conventions to Know

[From CLAUDE.md, capability log, wiki SCHEMA.md. Things that aren't obvious from the folder structure:
- File naming
- Frontmatter conventions
- Tagging
- Wiki entity/concept naming if wiki is active
- Citation style if specified
- Anything the researcher has explicitly noted as "do this, not that"]

**Skip if:** no documented conventions beyond defaults.

## What's Currently in Flight

[From notes/threads/ with status: active. List title + 1-line description for each, max 5. Example:
- **Hospital merger identity construction** — analyzing 12 interviews, draft due May 15
- **Boundary conditions in field theory** — early-stage reading, no draft yet

If no threads exist, look at the most recent reflection for current preoccupations.]

**Skip if:** no active threads and no recent reflections.

## Friction & Workarounds

[From friction_log.md. Recurring pain points + what's been tried. Example:
- Scanned PDFs sometimes fail conversion → manually re-scan or use mistral_ocr/mineru when policy allows cloud tools
- Long interview recordings (>2 hr) timeout coli → split into chunks first

Don't include one-off frustrations. Three+ occurrences is the threshold.]

**Skip if:** friction log is empty or has no recurring patterns.

## How to Ask Claude for Help in This Vault

[From CLAUDE.md "How to Work With" section + comfort level + claude_code_familiarity. Example:
- The vault auto-loads CLAUDE.md every Claude Desktop session — you don't need to brief Claude on context.
- Comfort level is [beginner/advanced]: "Ask in plain language; Claude will explain its steps" or "Ask concisely; Claude knows the tools."
- For multi-step workflows, mention /carrel-status to see what's set up.
- For converting a file, just drop it in inbox/ and ask "convert these."]

## Where to Start

[Concrete first actions tailored to the collaborator's role. Examples:
- "Read the cheat sheet at _meta/cheat_sheet.md to see the daily commands."
- "Open Obsidian on this folder to see the vault visually."
- "Try converting a PDF: drop one in inbox/ and ask Claude 'convert this'."
- "If you need your OWN Carrel vault separately, run /carrel-setup in a new folder."]

If the collaborator is described as a co-author working on a specific project, point at that project's folder/thread. If they're a new RA, point at the cheat sheet first.

## Questions to Ask [Researcher]

[A short list of things the collaborator should clarify before getting started. Tailored to their role. Examples for a new RA:
- Where do you want me to put new files I'm processing?
- Are there specific naming conventions for transcripts I should use?
- What's the priority order for the stack of papers in inbox/?

For a co-author:
- Which thread are we working on together?
- Do you want me to add reflections, or is that just for you?]
```

---

## Rules for Filling the Template

1. **One paragraph per section is the target.** Bullet lists are fine for vault layout and tools, but the substance sections (About This Vault, How [Researcher] Works) should read like sentences, not lists.

2. **Skip empty sections rather than padding them.** If `notes/threads/` is empty, don't write "No threads currently active" — just omit "What's Currently in Flight" entirely. Keep the doc lean.

3. **Use the researcher's own framing where possible.** Pull phrases from CLAUDE.md and reflections. Don't paraphrase into generic research-speak.

4. **Don't reproduce the cheat sheet.** Point at it. The cheat sheet is the daily reference; the handbook is orientation.

5. **End with "Questions to Ask [Researcher]"** — this seeds the conversation between researcher and collaborator. The handbook is starting point, not a replacement for talking.
