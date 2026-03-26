---
name: web-capture
description: "Use when a researcher wants to save web content to their vault. Triggers on URLs, 'save this article', 'clip this page', 'capture this website', or 'add this to my vault' with a URL."
---

# web-capture

Fetch web content, convert to clean markdown, add metadata, and save to the vault.

## When to Use

- Researcher shares a URL
- Researcher says "save this article", "clip this", "capture this page"
- Any web content that should be preserved in the vault

## Capture Flow

### Step 1: Capture

```bash
carrel capture url <url>
```

The CLI uses defuddle (smart content extraction — strips navigation, ads, sidebars) with markitdown as fallback. It extracts metadata (title, author, published date) and adds YAML frontmatter automatically.

### Step 2: Review and organize

The article lands in `inbox/` by default. After capture, suggest:
"I've saved the article to inbox/. Want me to move it to papers/ or notes/?"

Use `--dry-run` if the researcher wants to preview where it will go first.

### Step 3: Suggest connections

If the article relates to existing vault content, suggest links:
"This discusses identity construction — you have notes on that in `[[notes/identity-theory-overview]]`."

## Judgment Calls

- **Academic paper on a website** (not PDF): Use `carrel capture url` — defuddle extracts article content cleanly
- **PDF hosted online**: Download it first, then `carrel paper convert` — the paper pipeline handles PDFs better
- **YouTube video page**: Use `carrel transcript create <youtube-url>` instead — the transcript pipeline is purpose-built for this

## Alternative: Web Clipper

Remind researchers they can clip directly from their browser:
"You can also use the Obsidian Web Clipper extension to save pages directly to your vault — just click the clipper icon in your browser toolbar."

## Related

- **CLI**: `carrel capture url`, with `--force`, `--dry-run`, `--format` flags
- **Skills**: `vault-ops` for file placement
- **Commands**: `/carrel-capture` triggers this skill
