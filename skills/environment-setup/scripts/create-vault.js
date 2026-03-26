#!/usr/bin/env node

/**
 * create-vault.js — Scaffold an Obsidian vault with Carrel structure
 *
 * Creates folder structure, .obsidian/ config, .carrel/ state,
 * CLAUDE.md, templates, and cheat sheet. Never overwrites existing files.
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

function safeWrite(filePath, content) {
  if (fs.existsSync(filePath)) {
    return { path: filePath, action: 'skipped', reason: 'already exists' };
  }
  const dir = path.dirname(filePath);
  if (dir.includes('..')) {
    return { path: filePath, action: 'skipped', reason: 'path traversal blocked' };
  }
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(filePath, content, 'utf8');
  return { path: filePath, action: 'created' };
}

function safeDir(dirPath) {
  if (fs.existsSync(dirPath)) {
    return { path: dirPath, action: 'skipped', reason: 'already exists' };
  }
  fs.mkdirSync(dirPath, { recursive: true });
  return { path: dirPath, action: 'created' };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectPath = args.project_path || process.cwd();

  // Validate path
  if (projectPath.includes('..')) {
    console.error(JSON.stringify({ error: 'Path traversal not allowed' }));
    process.exit(1);
  }

  const results = { created: [], skipped: [], errors: [] };

  try {
    // --- Vault folders ---
    const folders = [
      'inbox',
      'papers',
      'notes',
      'transcripts',
      'drafts',
      'talks',
      'admin',
      '_meta',
      '_meta/reflections',
      '_templates',
      '.carrel',
    ];

    for (const folder of folders) {
      const result = safeDir(path.join(projectPath, folder));
      results[result.action === 'created' ? 'created' : 'skipped'].push(result.path);
    }

    // --- .obsidian/ config ---
    const obsidianDir = path.join(projectPath, '.obsidian');
    safeDir(obsidianDir);

    const obsidianFiles = {
      'app.json': JSON.stringify({
        newFileLocation: 'folder',
        newFileFolderPath: 'inbox',
        attachmentFolderPath: 'inbox',
        readableLineLength: true,
        showLineNumber: false,
        spellcheck: true,
        strictLineBreaks: false,
        promptDelete: true
      }, null, 2),

      'core-plugins.json': JSON.stringify([
        'file-explorer', 'global-search', 'switcher', 'graph',
        'backlink', 'outgoing-link', 'tag-pane', 'properties',
        'page-preview', 'templates', 'note-composer', 'command-palette',
        'editor-status', 'bookmarks', 'outline', 'word-count', 'file-recovery'
      ], null, 2),

      'community-plugins.json': '[]',

      'templates.json': JSON.stringify({
        folder: '_templates',
        dateFormat: 'YYYY-MM-DD',
        timeFormat: 'HH:mm'
      }, null, 2),

      'appearance.json': '{}',

      'workspace.json': JSON.stringify({
        main: {
          id: 'root', type: 'split',
          children: [{
            id: 'main-tabs', type: 'tabs',
            children: [{ id: 'empty-leaf', type: 'leaf', state: { type: 'empty' } }]
          }],
          direction: 'vertical'
        },
        left: {
          id: 'left-sidebar', type: 'split',
          children: [{
            id: 'file-explorer-tab', type: 'tabs',
            children: [{
              id: 'file-explorer-leaf', type: 'leaf',
              state: { type: 'file-explorer', state: {} }
            }]
          }],
          direction: 'horizontal', width: 280
        },
        right: { id: 'right-sidebar', type: 'split', children: [], collapsed: true },
        active: 'empty-leaf'
      }, null, 2)
    };

    for (const [filename, content] of Object.entries(obsidianFiles)) {
      const result = safeWrite(path.join(obsidianDir, filename), content);
      results[result.action === 'created' ? 'created' : 'skipped'].push(result.path);
    }

    // --- Note templates (read from vault-ops/templates/ to avoid duplication) ---
    const templateNames = ['paper.md', 'paper-notes.md', 'meeting.md', 'reflection.md', 'daily.md'];
    const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..', '..', '..');
    const templateSourceDir = path.join(pluginRoot, 'skills', 'vault-ops', 'templates');

    for (const name of templateNames) {
      const sourcePath = path.join(templateSourceDir, name);
      let content;
      try {
        content = fs.readFileSync(sourcePath, 'utf8');
      } catch {
        // Fallback: create a minimal template if source not found
        content = `---\ntitle:\ndate: {{date}}\ntags: []\n---\n\n## Notes\n`;
      }
      const result = safeWrite(path.join(projectPath, '_templates', name), content);
      results[result.action === 'created' ? 'created' : 'skipped'].push(result.path);
    }

    // --- .carrel/environment.json ---
    const envData = {
      version: '0.1.0',
      setup_date: new Date().toISOString().split('T')[0],
      vault_path: projectPath,
      interview: null,
      system: null,
      tools_configured: {
        liteparse: false,
        markitdown: true,
        coli: false,
        defuddle: false,
        gws: false,
        mineru: false,
        zotero: false,
        vox: false,
        pandoc: false,
        obsidian: false,
        web_clipper: false
      },
      sensitivity: 'prefer_local'
    };

    const envResult = safeWrite(
      path.join(projectPath, '.carrel', 'environment.json'),
      JSON.stringify(envData, null, 2)
    );
    results[envResult.action === 'created' ? 'created' : 'skipped'].push(envResult.path);

    // --- Friction log ---
    const frictionResult = safeWrite(
      path.join(projectPath, '_meta', 'friction_log.md'),
      `# Friction Log

A running log of issues encountered while using the research environment.
Claude updates this when you report problems. You can also edit it directly.

---

`
    );
    results[frictionResult.action === 'created' ? 'created' : 'skipped'].push(frictionResult.path);

    // Output
    console.log(JSON.stringify({
      success: true,
      vault_path: projectPath,
      created_count: results.created.length,
      skipped_count: results.skipped.length,
      created: results.created,
      skipped: results.skipped
    }, null, 2));

  } catch (error) {
    console.error(JSON.stringify({
      success: false,
      error: error.message,
      created: results.created,
      errors: [error.message]
    }));
    process.exit(1);
  }
}

main();
