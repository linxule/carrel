# Obsidian Vault Setup Reference

Everything Claude needs to scaffold a functional Obsidian vault from the terminal.

## What Makes a Folder a Vault

A folder becomes an Obsidian vault when it contains a `.obsidian/` directory. Obsidian detects this automatically. No registration or config files outside `.obsidian/` are needed.

## Minimum .obsidian/ Files

### app.json
```json
{
  "newFileLocation": "folder",
  "newFileFolderPath": "inbox",
  "attachmentFolderPath": "inbox",
  "readableLineLength": true,
  "showLineNumber": false,
  "spellcheck": true,
  "strictLineBreaks": false,
  "promptDelete": true
}
```

Key settings:
- `newFileLocation: "folder"` + `newFileFolderPath: "inbox"` → new files go to inbox/ by default
- `attachmentFolderPath: "inbox"` → dropped files land in inbox/
- `spellcheck: true` → researchers want this
- `promptDelete: true` → safety net

### core-plugins.json
```json
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "outgoing-link",
  "tag-pane",
  "properties",
  "page-preview",
  "templates",
  "note-composer",
  "command-palette",
  "editor-status",
  "bookmarks",
  "outline",
  "word-count",
  "file-recovery"
]
```

These are all core (built-in) plugins — no installation needed. Enabled by listing their IDs.

### templates.json
```json
{
  "folder": "_templates",
  "dateFormat": "YYYY-MM-DD",
  "timeFormat": "HH:mm"
}
```

Points the Templates core plugin to the `_templates/` folder.

### workspace.json
```json
{
  "main": {
    "id": "root",
    "type": "split",
    "children": [
      {
        "id": "main-tabs",
        "type": "tabs",
        "children": [
          {
            "id": "empty-leaf",
            "type": "leaf",
            "state": { "type": "empty" }
          }
        ]
      }
    ],
    "direction": "vertical"
  },
  "left": {
    "id": "left-sidebar",
    "type": "split",
    "children": [
      {
        "id": "file-explorer-tab",
        "type": "tabs",
        "children": [
          {
            "id": "file-explorer-leaf",
            "type": "leaf",
            "state": {
              "type": "file-explorer",
              "state": {}
            }
          }
        ]
      }
    ],
    "direction": "horizontal",
    "width": 280
  },
  "right": {
    "id": "right-sidebar",
    "type": "split",
    "children": [],
    "collapsed": true
  },
  "active": "empty-leaf"
}
```

Minimal layout: file explorer on the left, main editor, right sidebar collapsed.

### appearance.json
```json
{}
```

Empty is fine. Obsidian uses its default theme. Researcher can pick a theme later.

### community-plugins.json
```json
[]
```

Empty array. Community plugins require installation through Obsidian's GUI. We can recommend plugins in the cheat sheet but not install them programmatically.

## Recommended Community Plugins (for cheat sheet)

Suggest these to the researcher for later installation via Obsidian Settings → Community Plugins:

| Plugin | Why |
|--------|-----|
| **Calendar** | Visual date-based note navigation |
| **Dataview** | Query your notes like a database |
| **Periodic Notes** | Daily/weekly/monthly notes with templates |

These are nice-to-have, not required. Don't overwhelm the researcher during setup.

## Installing Obsidian

Claude cannot install GUI apps directly. Options:

1. **Homebrew** (if available): `brew install obsidian`
   - Claude CAN run this if the researcher approves the command
   - Installs to /Applications/Obsidian.app

2. **Manual download**: Direct the researcher to obsidian.md
   - Download the installer
   - Drag to Applications (macOS)
   - Run installer (Windows)

3. **Already installed**: Check with `mdfind "kMDItemCFBundleIdentifier == 'md.obsidian'"` on macOS

After installation, the researcher needs to:
1. Open Obsidian
2. Choose "Open folder as vault"
3. Navigate to their project folder
4. Click Open

## Web Clipper Setup

The Obsidian Web Clipper is a browser extension:
- Chrome: Search "Obsidian Web Clipper" in Chrome Web Store
- Firefox: Search in Firefox Add-ons
- Safari: Available in Safari Extensions

After installing:
1. Click the clipper icon in the browser toolbar
2. It should detect the vault automatically (since Obsidian is open)
3. Configure default save location to `inbox/`

This is entirely a human step. Claude can guide verbally but can't click through extension installation.
