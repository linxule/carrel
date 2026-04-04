---
description: Save a web page or online article to your vault as markdown
---

# /carrel-capture — Web Content Capture

Fetch web content, convert to clean markdown, and save to the vault.

## When to Use

- Researcher shares a URL
- Researcher says "save this article", "clip this page", "capture this"
- Any web content that should be in the vault

## What Happens

Uses the `web-capture` skill:

1. Fetch the URL using `carrel capture url <url>` — defuddle extracts content cleanly, with markitdown as fallback
2. Strip navigation, ads, boilerplate
3. Add frontmatter: title, source URL, capture date, tags
4. Save to `inbox/` (or researcher-specified folder)
5. Suggest: "Want me to move this to papers/ or notes/?"

## Alternative

Remind researchers they can also use the Obsidian Web Clipper browser extension to clip directly — it saves to the vault without involving Claude.

## Related

- **Skill**: `web-capture`
