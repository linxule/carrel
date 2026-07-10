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

**Listen for:** Zotero = we can connect it. Web article saving = smart extraction tool is available. Audio recording = we need transcription; precise timestamp requirements may need a separate workflow because Carrel's Groq adapter returns plain text. Browser = which Web Clipper to install.

### About Their Comfort (~2 min)

- Have you used any AI tools before? (ChatGPT, Copilot, Gemini, etc.)
- Have you used Claude Code before, or is this your first time? (No wrong answer.)
- How do you feel about AI tools having access to files on your computer?
- Would you prefer everything stays on your computer, or are you comfortable with some cloud processing?

**Listen for:** Privacy stance (determines sensitivity level), AI experience (determines how much to explain), trust level (determines how proactive to be). Claude Code familiarity specifically — if new, surface `/powerup` at handoff (interactive lessons that teach Claude Code itself).

### About Model Teammates (~1-2 min) — proactive offer

Most researchers don't realize this is possible, so **say it first**.

> "Quick thing that's worth flagging: Claude Code already supports multi-agent workflows, but by default that's Claude talking to Claude. You can also bring other foundation models in as teammates — Codex (ChatGPT) for adversarial review, Gemini for long-context synthesis, Kimi for delegated work.
>
> 1. Do you already pay for any of these? (ChatGPT Plus/Pro, Gemini Advanced, Kimi) — if yes, we can hook them up with just a login.
> 2. Even if not, are you curious about trying one? ChatGPT has a free tier and Gemini has generous free long-context use."

**Listen for:** which subscriptions they already hold, which they're curious about, which they decline. Populate `model_teammates` on the profile with `interested` / `skipped`. Schema details and sensitivity handling live in `skills/model-teammates/SKILL.md`.

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
    "inbox_processing": true,
    "vault_health": true,
    "cross_linking_suggestions": true,
    "gap_analysis": false,
    "draft_feedback": false,
    "reflection_synthesis": true,
    "wiki_maintenance": false,
    "trust_level": "advisory",
    "model": "sonnet",
    "schedule": "daily",
    "review_cadence": "quarterly",
    "last_reviewed": null
  },
  "claude_code_familiarity": "new",
  "collaborators": true,
  "team_context": "lab of 4 PhDs",
  "model_teammates": {
    "codex": "interested",
    "gemini": "skipped"
  }
}
```

**Field rules:**
- `sensitivity` MUST be one of `"high" | "medium" | "low"` (the `Sensitivity` enum)
- `cloud_consent` is a `bool`, NOT a string like `"local_only"`
- `automation` is a full `AutomationConfig`; safe defaults shown above
- `tools_configured` keys are the canonical tool names; values are booleans (true = installed and configured)
- `preferences` is free-form (`dict[str, Any]`); Phase 4 selects paper tracking from `many_papers|literature_review`, interview tracking from `qualitative|interviews`, and writing tracking from `writing|thesis|dissertation`
- All optional fields can be omitted — Pydantic will default them

Save this as a temporary profile JSON and pass it to `carrel vault init <path> --profile-file <profile.json>`. The command validates the complete profile before creating any vault files; do not scaffold defaults and patch `environment.json` afterward.
