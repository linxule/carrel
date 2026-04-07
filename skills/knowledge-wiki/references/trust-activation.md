# Trust Activation — Wiki Graduation Protocol

How the knowledge wiki emerges through carrel's graduated trust model. Original to carrel — the upstream wiki pattern assumes opt-in; carrel earns it through relationship.

---

## Two Paths to Activation

### Path 1: Earned graduation (default)
The researcher didn't ask for a wiki. Claude notices the need and proposes it at the right moment. This is the default path for researchers who go through the setup interview.

### Path 2: Explicit opt-in
The researcher asks directly: "set up a knowledge wiki", "I want a field map", "can you track my sources?" — their request IS the trust grant. Skip to Initialization regardless of current trust level.

---

## Detection Signals

Watch for these during interactive sessions. Any 2-3 of these together suggest the researcher would benefit from a wiki:

**Volume signals:**
- 15+ converted papers in `papers/`
- 5+ transcripts in `transcripts/`
- Researcher mentions they're doing a literature review or systematic review

**Knowledge-slipping signals:**
- Researcher re-asks a question they asked in a previous session
- "What was that paper about...?" / "Which paper discussed...?"
- "I keep losing track of..." / "There's too much to remember"

**Synthesis-seeking signals:**
- "What do my sources say about X?"
- "Which papers contradict each other on Y?"
- "Can you help me see connections across these papers?"
- "What themes are emerging?"
- "Give me an overview of what I've read about Z"

**Workflow signals:**
- Researcher is writing a literature review section
- Researcher is preparing for a comprehensive exam
- Researcher is tracking a fast-moving field over months

**Do NOT propose when:**
- Researcher has fewer than 10 sources
- Researcher has expressed preference for managing their own notes/synthesis
- Trust level is advisory and researcher hasn't shown synthesis-seeking signals
- Researcher is in the middle of a focused task (bad timing)

---

## The Consultative Proposal

When signals are strong enough, propose during a natural pause in the session. Frame it as a capability, not a suggestion:

### The pitch (adapt to context)

> "You've got [N] papers and [N] transcripts now, and you're asking questions that cut across them. I could maintain a field map for you — topic pages that synthesize what your sources say about each concept, entity pages for key researchers and organizations, and I'd flag where sources contradict each other. You'd review what I write. Think of it as a living summary of your field that gets smarter with every paper you add.
>
> Want me to draft a structure? You'd approve it before I create anything."

### If YES: proceed to Schema Drafting

### If NOT NOW:
Set `"wiki_proposal_deferred_until": "YYYY-MM-DD"` in environment.json (2 weeks from now). Don't propose again until that date passes.

### If NO:
Set `"wiki_preference": "researcher-managed"` in environment.json. Respect permanently — never propose again. The researcher can change this manually or via `/carrel-automate`.

---

## Schema Drafting (Consultative)

The researcher said yes. Now draft the SCHEMA.md for their review:

**Step 1 — Gather domain context:**
- Read `environment.json` for researcher field and preferences
- Scan frontmatter tags across `papers/**/*.md` (collect all unique tags)
- Read the vault's root `CLAUDE.md` for domain context
- If the researcher has `notes/` with thematic content, scan for recurring topics

**Step 2 — Draft SCHEMA.md:**
- Domain description from researcher profile + what's in the vault
- Tag taxonomy from existing paper tags, organized into categories
- Page thresholds: default 2+ sources (adjust if researcher has strong opinions)
- Keep conventions standard (from wiki-protocol.md template)

**Step 3 — Present for review:**

> "Here's the structure I'd suggest for your field map:
>
> **Domain:** [from profile]
>
> **Tag categories:**
> - Theories: [list derived from papers]
> - Methods: [list]
> - Topics: [list]
> - People/Orgs: person, organization
>
> **Rules:** I'd create a page when a concept appears in 2+ of your papers, or is central to one. I'd flag contradictions for your review rather than resolving them myself.
>
> Does this look right? Anything to add or change?"

**Step 4 — Incorporate feedback:**
- Adjust taxonomy, thresholds, domain description per researcher input
- This is the CONSULTATIVE contract: agent proposes, researcher approves

---

## Initialization

Once the researcher approves the schema (or explicitly opts in):

**Step 1 — Create wiki structure:**
```
wiki/
├── SCHEMA.md        (from approved draft)
├── index.md         (empty template with sections)
├── log.md           (creation entry)
├── entities/
├── concepts/
├── comparisons/
└── queries/
```

**Step 2 — Record activation:**
- Set `wiki_enabled: true` in `.carrel/environment.json`
- If automation is configured, set `wiki_maintenance: true` in automation config
- Update vault `CLAUDE.md` with wiki conventions section:
  ```
  ## Knowledge Wiki
  This vault has an active field map in wiki/. Claude maintains synthesized
  topic and entity pages. Review wiki pages in Obsidian (filter graph to path:wiki/).
  Contradictions are flagged for your review.
  ```

**Step 3 — Incremental cold start:**

Do NOT ingest everything at once. Start small:

1. Identify the 5-10 most substantial papers (by length, or most referenced in researcher's notes)
2. Read each paper's abstract, introduction, and conclusion (not full text unless short)
3. Create initial entity pages for key researchers, organizations, models mentioned across multiple papers
4. Create initial concept pages for the 3-5 most prominent themes
5. Cross-link everything (2+ outbound links per page)
6. Write index.md with initial entries
7. Log the cold-start with reasoning

Present the initial wiki to the researcher:

> "I've created your field map with [N] initial pages — [N] entities and [N] concepts from your most substantial papers. Here's what's there:
>
> [list key pages with one-line summaries]
>
> You can browse these in Obsidian under wiki/. I'll add more as you add papers. Want me to prioritize any particular area for the next batch?"

**Step 4 — Incremental expansion:**
Each subsequent session (or automation run) picks up more papers. Priority order:
1. Papers the researcher has notes about (they've engaged with these)
2. Papers cited by multiple other papers in the vault
3. Remaining papers by recency

Don't rush full coverage. 2-3 papers per session is a sustainable pace for quality synthesis.

---

## Trust Upgrades

### Advisory → Consultative (wiki proposal)
Triggered by: detection signals above. The proposal conversation IS the upgrade for wiki purposes.

### Consultative → Delegated (autonomous maintenance)
After the researcher has reviewed wiki pages across several sessions without significant corrections, consider proposing delegation. Check wiki/log.md for patterns: if the last 3-5 ingest entries show no researcher corrections (no "corrected by researcher" or "reverted" entries), the wiki quality is stable enough.

This is a heuristic — the agent reads the log for correction patterns rather than tracking a counter. When ready:

> "Your field map has [N] pages now, and the last few batches have been on track. Want me to update it automatically when you add new papers? I'd log everything and you'd see a summary in your morning brief."

If yes: set trust to delegated in automation config (if not already). Enable `wiki_maintenance` in automation.

### Delegated → Partnership (structural reorganization)
Only after months of stable wiki operation. The agent notices:
- Pages that should be split (>200 lines)
- Overlapping concepts that should be merged
- A taxonomy reorganization that would improve navigation

Propose specific changes. Partnership means the agent can restructure, but should still explain what and why in the morning brief.

---

## Environment Sync

When wiki is activated or trust changes, update both persistence layers:

**environment.json** (mechanical — CLI reads this):
```json
{
  "wiki_enabled": true,
  "wiki_preference": "agent-managed",
  "wiki_proposal_deferred_until": null,
  "automation": {
    "wiki_maintenance": true,
    "trust_level": "consultative"
  }
}
```

`wiki_preference` values: `"agent-managed"` (wiki active), `"researcher-managed"` (researcher declined, never propose), `null` (not yet decided).
`wiki_proposal_deferred_until`: ISO date string or `null`. If set, don't propose wiki until this date.

**Vault CLAUDE.md** (narrative — Claude reads this):
```markdown
## Knowledge Wiki
Active field map in wiki/ with [N] pages. Trust level: consultative.
Claude proposes wiki updates; researcher approves before writing.
Tag taxonomy in wiki/SCHEMA.md. Contradictions flagged for review.
```

Both must reflect the same state. When preferences change, update both.

---

## Deactivation

If the researcher wants to stop the wiki:
- Set `wiki_enabled: false` in environment.json
- Set `wiki_maintenance: false` in automation config
- Update vault CLAUDE.md to note wiki is paused
- Do NOT delete wiki/ — the content is still valuable for manual browsing
- Log the deactivation in wiki/log.md

The researcher can reactivate anytime. The wiki resumes from where it left off.
