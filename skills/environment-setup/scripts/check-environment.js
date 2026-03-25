#!/usr/bin/env node

/**
 * check-environment.js — Audit hardware and installed tools
 *
 * Runs silently during setup or as a SessionStart hook.
 * Returns structured JSON for environment.json.
 */

const { execSync, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function run(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8', timeout: 10000 }).trim();
  } catch {
    return null;
  }
}

function which(tool) {
  return run(`which ${tool}`) !== null;
}

function getVersion(cmd) {
  const output = run(cmd);
  if (!output) return null;
  const match = output.match(/(\d+\.\d+[\.\d]*)/);
  return match ? match[1] : output.split('\n')[0];
}

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

function main() {
  const args = parseArgs(process.argv.slice(2));
  const projectPath = args.project_path || process.cwd();
  const platform = process.platform;

  const result = {
    system: {},
    tools: {},
    existing_mcps: { claude_desktop: [], project: [] },
    carrel_state: null
  };

  // --- System info ---
  result.system.os = platform === 'darwin' ? 'macOS' : platform === 'win32' ? 'Windows' : 'Linux';
  result.system.arch = process.arch === 'arm64' ? 'arm64' : 'x86_64';

  if (platform === 'darwin') {
    const swVers = run('sw_vers -productVersion');
    if (swVers) result.system.os_version = swVers;

    const memBytes = run('sysctl -n hw.memsize');
    if (memBytes) result.system.ram_gb = Math.round(parseInt(memBytes) / 1073741824);

    const gpu = run("system_profiler SPDisplaysDataType 2>/dev/null | grep 'Chipset Model' | head -1");
    if (gpu) result.system.gpu = gpu.replace(/^\s*Chipset Model:\s*/, '');
  }

  try {
    const dfOutput = execFileSync('df', ['-h', projectPath], { encoding: 'utf8', timeout: 10000 }).trim();
    const lastLine = dfOutput.split('\n').pop();
    const parts = lastLine.split(/\s+/);
    result.system.disk_free = parts[3] || 'unknown';
  } catch { /* ignore */ }

  // --- Installed tools ---
  const tools = [
    { name: 'node', check: 'node --version' },
    { name: 'python', check: 'python3 --version' },
    { name: 'uv', check: 'uv --version' },
    { name: 'bun', check: 'bun --version' },
    { name: 'pandoc', check: 'pandoc --version' },
    { name: 'ffmpeg', check: 'ffmpeg -version 2>&1 | head -1' },
    { name: 'brew', check: 'brew --version' },
  ];

  for (const tool of tools) {
    const installed = which(tool.name);
    result.tools[tool.name] = {
      installed,
      version: installed ? getVersion(tool.check) : null
    };
  }

  // Obsidian (macOS app detection)
  if (platform === 'darwin') {
    const obsidianPath = run('mdfind "kMDItemCFBundleIdentifier == \'md.obsidian\'" 2>/dev/null');
    result.tools.obsidian = { installed: !!obsidianPath, path: obsidianPath || null };
  } else {
    result.tools.obsidian = { installed: which('obsidian') };
  }

  // Zotero
  if (platform === 'darwin') {
    const zoteroPath = run('mdfind "kMDItemCFBundleIdentifier == \'org.zotero.zotero\'" 2>/dev/null');
    result.tools.zotero = { installed: !!zoteroPath };
  } else {
    result.tools.zotero = { installed: which('zotero') };
  }

  // --- Existing MCP configs ---
  if (platform === 'darwin') {
    const desktopConfig = path.join(
      process.env.HOME, 'Library', 'Application Support', 'Claude', 'claude_desktop_config.json'
    );
    if (fs.existsSync(desktopConfig)) {
      try {
        const config = JSON.parse(fs.readFileSync(desktopConfig, 'utf8'));
        result.existing_mcps.claude_desktop = Object.keys(config.mcpServers || {});
      } catch { /* ignore parse errors */ }
    }
  }

  const projectMcp = path.join(projectPath, '.mcp.json');
  if (fs.existsSync(projectMcp)) {
    try {
      const config = JSON.parse(fs.readFileSync(projectMcp, 'utf8'));
      result.existing_mcps.project = Object.keys(config.mcpServers || {});
    } catch { /* ignore */ }
  }

  // --- Carrel state ---
  const envFile = path.join(projectPath, '.carrel', 'environment.json');
  if (fs.existsSync(envFile)) {
    try {
      result.carrel_state = JSON.parse(fs.readFileSync(envFile, 'utf8'));
    } catch { /* ignore */ }
  }

  console.log(JSON.stringify(result, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({ error: error.message }));
  process.exit(1);
}
