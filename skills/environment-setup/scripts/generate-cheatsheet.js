#!/usr/bin/env node

/**
 * generate-cheatsheet.js — Create customized reference card from environment.json
 *
 * Reads .carrel/environment.json and generates _meta/cheat_sheet.md
 */

const fs = require('fs');
const path = require('path');

function parseArgs(args) {
  const parsed = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].slice(2).replace(/-/g, '_');
      parsed[key] = args[i + 1] || true;
      if (typeof parsed[key] === 'string') i++;
    }
  }
  return parsed;
}

function status(configured) {
  return configured ? '✅' : '—';
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectPath = args.project_path || process.cwd();

  const envPath = path.join(projectPath, '.carrel', 'environment.json');
  if (!fs.existsSync(envPath)) {
    console.error(JSON.stringify({ error: 'No .carrel/environment.json found. Run setup first.' }));
    process.exit(1);
  }

  const raw = fs.readFileSync(envPath, 'utf8').trim();
  if (!raw) {
    console.error(JSON.stringify({ error: 'environment.json is empty. Run /carrel-setup again.' }));
    process.exit(1);
  }
  const env = JSON.parse(raw);
  const researcher = env.interview?.researcher || {};
  const tools = env.tools_configured || {};
  const vaultName = path.basename(projectPath);

  const hasTranscripts = tools.coli || tools.groq;

  let cheatsheet = `# Carrel — Your AI Research Environment

*Your private desk in the library.*

*Customized for: ${researcher.name || 'Researcher'}*
*Set up: ${env.setup_date || new Date().toISOString().split('T')[0]}*
*Carrel version: ${env.version || '0.1'}*

---

## Starting a Work Session

Open **Claude Desktop** → select your **${vaultName}** folder → start chatting.
Claude remembers your setup and preferences automatically.

---

## Your Setup at a Glance

| Capability | Status | Notes |
|------------|--------|-------|
| Claude Desktop | ✅ | App + Claude Code |
| Obsidian | ${status(tools.obsidian)} | Vault at: \`${projectPath}\` |
| Web Clipper | ${status(tools.web_clipper)} | ${researcher.browser || 'Browser'} extension |
| PDF conversion | ✅ | liteparse (local) |
| Other documents | ✅ | markitdown (Word, slides, spreadsheets) |
| Web capture | ${status(tools.defuddle)} | ${tools.defuddle ? 'defuddle (local)' : 'Not configured'} |
| YouTube | ${status(tools.youtube_captions || tools.gemini)} | ${tools.gemini ? 'gemini (cloud) + local captions fallback' : 'youtube-transcript-api (local captions)'} |
| Google Docs | ${status(tools.gws)} | ${tools.gws ? 'gws export (local CLI)' : 'Not configured'} |
| Complex PDFs | ${status(tools.mineru)} | ${tools.mineru ? 'MineRU (API)' : 'Not configured — add later if needed'} |
| Audio transcription | ${status(tools.coli || tools.groq)} | ${tools.coli ? 'coli (local)' : tools.groq ? 'groq (cloud)' : 'Not available'} |
| Zotero | ${status(tools.zotero)} | ${tools.zotero ? 'Connected to library' : 'Not configured'} |

---

## Getting Content INTO Your Vault

**A paper (PDF or Word):**
Tell Claude: *"Convert this paper to markdown and save it to my papers folder."*
Drop the file into Claude's chat, or tell Claude the file path.

**A web article or blog post:**
Option 1: Use the Obsidian Web Clipper in your browser → goes straight to vault.
Option 2: Tell Claude: *"Save this article to my vault: [paste URL]"*

**Meeting notes or ideas:**
Open Obsidian → create a new note in \`notes/\` → type directly.
Or tell Claude: *"Create a meeting note for today's supervision with [name]."*
`;

  if (hasTranscripts) {
    cheatsheet += `
**An audio recording:**
Tell Claude: *"Transcribe this recording and save it to my transcripts folder."*
Drop the audio file or give Claude the file path.
`;
  }

  cheatsheet += `
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

\`\`\`
${vaultName}/
├── inbox/          ← Unsorted incoming stuff (web clips land here)
├── papers/         ← Converted papers as markdown
├── notes/          ← Research notes, meeting notes, ideas
├── transcripts/    ← Audio transcriptions
├── drafts/         ← Writing in progress
├── talks/          ← Talk prep, presentation notes
├── admin/          ← Recommendation letters, committee work
├── _meta/          ← This cheat sheet + reflection logs
└── _templates/     ← Note templates
\`\`\`

Feel free to add folders or reorganize. It's your vault. Claude will adapt.

---

## If Something Isn't Working

**Claude can't find a file:**
Make sure it's in your vault folder. Tell Claude the exact filename or path.

**Conversion looks wrong:**
Tell Claude: *"The conversion of [file] lost the tables / formatting. Can you try a different tool?"*

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
To share feedback: tell Claude *"Generate my feedback for Xule"* — then email to xule.lin@imperial.ac.uk.

---

## What's Next?

Things to explore as you get comfortable:

- **Obsidian graph view**: See visual connections between your notes
- **Internal links**: Use \`[[note name]]\` in any note to link to another note
- **Templates**: Use the pre-built templates for papers, meetings, reflections
- **Advanced search**: Ask Claude to search across your entire vault for themes or patterns

---

*This cheat sheet lives in your vault at \`_meta/cheat_sheet.md\`. Claude can update it if your setup changes.*
`;

  const outputPath = path.join(projectPath, '_meta', 'cheat_sheet.md');
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, cheatsheet, 'utf8');

  console.log(JSON.stringify({
    success: true,
    output: outputPath,
    researcher: researcher.name || 'Unknown',
    tools_shown: Object.entries(tools).filter(([, v]) => v).map(([k]) => k)
  }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({ error: error.message }));
  process.exit(1);
}
