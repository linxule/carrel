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

### Step 1: Fetch and convert

Use `markitdown` to fetch and convert the URL:

```bash
markitdown "https://example.com/article"
```

This strips navigation, ads, and boilerplate. Returns clean markdown to stdout.

### Step 2: Add frontmatter

```yaml
---
title: [extracted from page]
source: [URL]
captured: [today's date]
tags: []
---
```

### Step 3: Save to vault
Default save location: `inbox/`
If the researcher specifies a folder: save there instead.

Filename: slugified title, e.g., `how-organizations-change-identity.md`

### Step 4: Suggest organization
"I've saved the article to inbox/. Want me to move it to papers/ or notes/?"

## Alternative: Web Clipper

Remind researchers they can clip directly from their browser:
"You can also use the Obsidian Web Clipper extension to save pages directly to your vault — just click the clipper icon in your browser toolbar."

## Related

- **Skills**: `vault-ops` for file placement
- **Commands**: `/carrel-capture` triggers this skill
