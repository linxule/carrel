# Cheat Sheet Template

This template is used by `carrel vault cheatsheet` (and the underlying `render_cheat_sheet()` in `src/carrel/vault/templates.py`) to create a customized reference card. Variables in `{{brackets}}` are replaced with values from `.carrel/environment.json`.

---

# Carrel — Your AI Research Environment

*Your private desk in the library.*

*Customized for: {{researcher.name}}*
*Set up: {{setup_date}}*
*Carrel version: {{version}}*

---

## Your Setup at a Glance

| Capability | Status | Notes |
|------------|--------|-------|
| Claude Desktop | Active | App + Claude Code |
| Obsidian | {{obsidian_status}} | Vault at: `{{vault_path}}` |
| Web Clipper | {{clipper_status}} | {{browser}} extension |
| PDF conversion | Active | liteparse (local) |
| Complex PDFs | {{mineru_status}} | {{mineru_notes}} |
| Other documents | Active | markitdown (Word, slides, spreadsheets) |
| Web capture | {{defuddle_status}} | {{defuddle_notes}} |
| Audio transcription | {{transcription_status}} | {{transcription_notes}} |
| YouTube | {{youtube_status}} | {{youtube_notes}} |
| Google Docs | {{gws_status}} | {{gws_notes}} |
| Zotero | {{zotero_status}} | {{zotero_notes}} |

---

## Starting a Work Session

Open **Claude Desktop** → select your **{{vault_folder_name}}** folder → start chatting.
Claude remembers your setup and preferences automatically.

---

## Getting Content INTO Your Vault

**A paper (PDF):**
Tell Claude: *"Convert this paper to markdown and save it to my papers folder."*
Drop the file into Claude's chat, or tell Claude the file path.

**A Word doc, slide deck, or spreadsheet:**
Tell Claude: *"Convert this file and save it to my papers folder."*
markitdown handles Word, PowerPoint, Excel, and more.

**A web article or blog post:**
Option 1: Use the Obsidian Web Clipper in your browser → goes straight to vault.
{{#if defuddle_available}}
Option 2: Tell Claude: *"Save this article to my vault: [paste URL]"*
{{else}}
Option 2: Tell Claude the URL — Claude will do its best to fetch and save it.
{{/if}}

**Meeting notes or ideas:**
Open Obsidian → create a new note in `notes/` → type directly.
Or tell Claude: *"Create a meeting note for today's supervision with [name]."*

{{#if transcription_available}}
**An audio recording:**
Tell Claude: *"Transcribe this recording and save it to my transcripts folder."*
Drop the audio file or give Claude the file path.
{{/if}}

{{#if youtube_available}}
**A YouTube lecture or talk:**
Tell Claude: *"Transcribe this YouTube video and save it to my transcripts folder: [paste URL]"*
{{/if}}

{{#if gws_available}}
**A Google Doc:**
Tell Claude: *"Import my Google Doc and save it to my papers folder: [paste URL or Doc ID]"*
Note: requires your Google Workspace integration to be configured.
{{/if}}

---

## Working WITH Claude

**Think through an argument:**
*"I'm developing an argument about [topic]. Here's my current thinking: [explain]. What am I missing? Push back on the weak points."*

**Engage with a paper:**
*"I just read [paper in vault]. What are the methodological strengths and limitations? How does it connect to my work on [topic]?"*

**Draft something:**
*"Help me draft an introduction for a talk about [topic]. My audience is [describe]. The key message is [message]."*

**Explore connections:**
*"Look through my recent notes and papers. What themes are emerging? What connections am I not seeing?"*

**Get a different perspective:**
*"I'm stuck on [problem]. Give me three completely different ways to think about this."*

---

## Getting Content OUT of Your Vault

**To a Word doc (for journal submission):**
Tell Claude: *"Export my draft in drafts/paper_name.md as a Word document."*

**To a colleague:**
Tell Claude: *"Create a summary of my notes on [topic] that I can share with [collaborator]."*

---

## Your Vault Structure

```
{{vault_folder_name}}/
├── inbox/          ← Unsorted incoming stuff (web clips land here)
├── papers/         ← Converted papers as markdown
├── notes/          ← Research notes, meeting notes, ideas
{{#if has_transcripts}}
├── transcripts/    ← Audio and video transcriptions
{{/if}}
├── drafts/         ← Writing in progress
├── talks/          ← Talk prep, presentation notes
├── admin/          ← Recommendation letters, committee work
├── _meta/          ← This cheat sheet + reflection logs
└── _templates/     ← Note templates
```

Feel free to add folders or reorganize. It's your vault. Claude will adapt.

---

## If Something Isn't Working

**Claude can't find a file:**
Make sure it's in your vault folder. Tell Claude the exact filename or path.

**Conversion looks wrong:**
Tell Claude: *"The conversion of [file] lost the tables / formatting. Can you try a different approach?"*

**Claude seems confused about your setup:**
Tell Claude: *"Check my environment and remind yourself what tools I have."*

**Something is genuinely broken:**
Tell Claude: *"Something isn't working with [tool]. Can you diagnose it?"*

**Need to restart:**
Quit Claude Desktop fully (not just close the window) and reopen it.

---

## End of Session

When you're done working, you can just close everything. But if you want to help improve this tool for other researchers:

Tell Claude: *"Let's do a quick reflection on today's session."*

Takes 2 minutes. Your feedback (anonymized) helps make this better for everyone.
To share feedback: tell Claude *"Generate my feedback for Xule"* — then email the result to xule.lin@imperial.ac.uk.

---

## What's Next?

Things to explore as you get comfortable:

- **Obsidian graph view**: See visual connections between your notes
- **Internal links**: Use `[[note name]]` in any note to link to another note
- **Templates**: Use the pre-built templates for papers, meetings, reflections
{{#if zotero_available}}
- **Zotero searches**: Ask Claude to search your Zotero library for papers on a topic
{{/if}}
{{#if mineru_available}}
- **Complex PDFs**: Use mineru for scanned documents or papers with difficult layouts
{{/if}}
- **Advanced search**: Ask Claude to search across your entire vault for themes or patterns

---

*This cheat sheet lives in your vault at `_meta/cheat_sheet.md`. Claude can update it if your setup changes.*
