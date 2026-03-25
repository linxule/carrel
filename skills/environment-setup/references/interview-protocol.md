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
- Do you work with sensitive data? (interview transcripts, IRB-protected data, unpublished manuscripts, student records)
- How do you currently take notes? (Word, Google Docs, paper notebooks, an existing app)

**Listen for:** File types (determines conversion tools), sensitivity (determines local-vs-cloud defaults), current workflow (determines what to augment vs replace).

### About Their Tools (~2 min)

- Do you use a reference manager? (Zotero, Mendeley, EndNote, none)
- Where do you store files? (Google Drive, Dropbox, OneDrive, local folders)
- Do you record meetings or interviews? If so, how? (Zoom, Teams, phone, handheld recorder)
- What browser do you use? (for Web Clipper)

**Listen for:** Zotero = we can connect it. Audio recording = we need transcription. Browser = which Web Clipper to install.

### About Their Comfort (~2 min)

- Have you used any AI tools before? (ChatGPT, Copilot, Gemini, etc.)
- How do you feel about AI tools having access to files on your computer?
- Would you prefer everything stays on your computer, or are you comfortable with some cloud processing?
- Would you find it useful to get perspectives from different AI models? (e.g., "Check this with Gemini" or "What does GPT think about this argument?")

**Listen for:** Privacy stance (determines sensitivity level), AI experience (determines how much to explain), trust level (determines how proactive to be). If they mention using other AI tools (ChatGPT, Gemini), they may already have API keys — ask. If they express interest in multiple perspectives, vox-mcp is a good fit.

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

After the interview, structure the answers into:

```json
{
  "researcher": {
    "name": "",
    "institution": "",
    "field": "",
    "focus": "",
    "role": "",
    "ai_experience": "none|basic|moderate|advanced"
  },
  "data": {
    "primary_file_types": ["pdf", "docx", "audio", ...],
    "sensitivity": "low|medium|high",
    "sensitivity_notes": "",
    "note_taking": "word|google_docs|paper|obsidian|other"
  },
  "tools": {
    "reference_manager": "zotero|mendeley|endnote|none",
    "cloud_storage": "gdrive|dropbox|onedrive|local|other",
    "audio_recording": "zoom|teams|phone|recorder|none",
    "browser": "chrome|firefox|safari|edge|other"
  },
  "preferences": {
    "cloud_comfort": "local_only|prefer_local|comfortable_with_cloud",
    "gui_only": true,
    "explanation_level": "brief|moderate|detailed",
    "multi_model": "not_interested|interested|has_keys",
    "multi_model_providers": [],
    "existing_api_keys": []
  }
}
```

Save this to `.carrel/environment.json` as the `interview` field.
