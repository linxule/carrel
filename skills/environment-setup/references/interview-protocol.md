# Interview Protocol

The interview is the heart of Carrel. It's a conversation, not a form.

## Principles

- **Warm and curious.** You're meeting a new colleague. Be interested in their work.
- **Adaptive.** Skip questions already answered. Don't ask about Zotero if they said they don't use a reference manager.
- **Plain language.** Never say "MCP", "CLI", "markdown", or "API" unprompted. Use researcher vocabulary.
- **Brief.** Aim for 10 minutes. Don't over-interview. You can always learn more later.

## Areas to Cover

### About the Person (~3 min)

Open with genuine curiosity about their research:

- What's your research area? What are you working on right now?
- What does a typical work week look like? (writing, reading, reviewing, teaching, admin, fieldwork)
- What made you decide to try AI tools now?

**Listen for:** Their field, seniority, time pressures, what they're hoping AI helps with.

### About Their Data (~3 min)

- What kinds of files do you work with most? (PDFs of papers, Word docs, spreadsheets, slides, audio recordings)
- Do you write in Google Docs, or work with Google Sheets or Slides? Or do you mainly stay in Word and local files?
- Do you watch or assign video lectures — YouTube or recorded talks?
- Do you work with sensitive data? (interview transcripts, IRB-protected data, unpublished manuscripts, student records)
- How do you currently take notes?

**Listen for:** File types (determines conversion tools). Google Docs/Sheets/Slides usage (export integration exists but requires some setup — worth flagging). YouTube or video lectures (transcription options available). Sensitivity (determines local-vs-cloud defaults). Current workflow (determines what to augment vs replace).

### About Their Tools (~2 min)

- Do you use a reference manager? (Zotero, Mendeley, EndNote, none)
- Where do you store files? (Google Drive, Dropbox, OneDrive, local folders)
- Do you save articles or blog posts from the web while you're researching?
- Do you record meetings or interviews? If so, how? (Zoom, Teams, phone, handheld recorder)
  - *If yes:* Do you need precise timestamps in your transcripts — say, to match a quote to a moment in the recording — or is clean readable text enough?
- What browser do you use?

**Listen for:** Zotero = we can connect it. Web article saving = smart extraction tool is available. Audio recording = we need transcription; timestamp precision determines which tool fits best. Browser = which Web Clipper to install.

### About Their Comfort (~2 min)

- Have you used any AI tools before? (ChatGPT, Copilot, Gemini, etc.)
- Have you used Claude Code before, or is this your first time? (No wrong answer.)
- How do you feel about AI tools having access to files on your computer?
- Would you prefer everything stays on your computer, or are you comfortable with some cloud processing?
- Would you find it useful to get perspectives from different AI models? (e.g., "Check this with Gemini" or "What does GPT think about this argument?")

**Listen for:** Privacy stance (determines sensitivity level), AI experience (determines how much to explain), trust level (determines how proactive to be). Claude Code familiarity specifically — if new, surface `/powerup` at handoff (interactive lessons that teach Claude Code itself). If they mention using other AI tools (ChatGPT, Gemini), they may already have API keys — ask. If they express interest in multiple perspectives, vox-mcp is a good fit.

### About Their Collaborators (~1 min)

- Do you work with co-authors, RAs, or a lab — anyone who might want to use this same setup?
- (If yes) Tell me a little about them — how many people, what role?

**Listen for:** Whether to surface `/carrel-share` at handoff. Capture as `collaborators: true/false` and a short `team_context` string ("lab of 4 PhDs", "co-author at Cornell", "RA team of 2"). `/carrel-share` will use this context to generate a vault-specific handbook when the researcher is ready to bring someone in.

## Conversation Style

**DO:**
- Ask follow-up questions when something is interesting
- Summarize what you've heard: "So it sounds like you mainly work with..."
- Let them talk — their answers often cover multiple questions
- Note things to come back to: "You mentioned interview recordings — we'll set that up"

**DON'T:**
- Ask all questions in a numbered list
- Use technical jargon before they do
- Make them feel assessed or judged
- Rush — if they want to tell you about their research, listen

## Output

After the interview, write `.carrel/environment.json` directly as a flat `ResearcherProfile` (the canonical Pydantic model in `src/carrel/models.py`). The legacy nested format (with a top-level `interview` key) is deprecated — Pydantic-validated tools (`carrel vault cheatsheet`, future `carrel env validate`) only see the flat fields.

The schema your output must match:

```json
{
  "name": "Researcher Name",
  "field": "organizational studies",
  "sensitivity": "high",
  "cloud_consent": false,
  "comfort_level": "beginner",
  "wiki_enabled": false,
  "wiki_preference": null,
  "wiki_proposal_deferred_until": null,
  "tools_configured": {
    "liteparse": true,
    "coli": true,
    "defuddle": true,
    "obsidian": false,
    "zotero": false,
    "mineru": false,
    "groq": false,
    "vox": false,
    "gws": false
  },
  "preferences": {
    "qualitative": true,
    "many_papers": false,
    "writing": false,
    "interviews": true,
    "literature_review": false,
    "multi_model": false,
    "timestamp_precision": "text_only",
    "google_workspace": "none",
    "audio_recording": "zoom",
    "browser": "chrome",
    "cloud_storage": "gdrive",
    "note_platform": "obsidian",
    "ai_experience": "moderate"
  },
  "automation": {
    "enabled": false,
    "trust_level": "advisory",
    "model": "sonnet",
    "schedule": "daily",
    "review_cadence": "quarterly",
    "last_reviewed": null
  },
  "claude_code_familiarity": "new",
  "collaborators": true,
  "team_context": "lab of 4 PhDs"
}
```

**Field rules:**
- `sensitivity` MUST be one of `"high" | "medium" | "low"` (the `Sensitivity` enum)
- `cloud_consent` is a `bool`, NOT a string like `"local_only"`
- `automation` is a full `AutomationConfig`; safe defaults shown above
- `tools_configured` keys are the canonical tool names; values are booleans (true = installed and configured)
- `preferences` is free-form (`dict[str, Any]`); the keys shown drive Phase 4 scaffold decisions (`qualitative`, `many_papers`, `writing` pick which `.base` database files get scaffolded)
- All optional fields can be omitted — Pydantic will default them

Save the JSON directly to `.carrel/environment.json`. Validate by running `uv run python -c "from carrel.models import ResearcherProfile; ResearcherProfile.model_validate_json(open('.carrel/environment.json').read())"` — no exception means the schema is correct.
