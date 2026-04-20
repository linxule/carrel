#!/usr/bin/env node

/**
 * Version check helper — imported by check-environment.js
 *
 * Compares the installed plugin version (from .claude-plugin/plugin.json) against
 * the last-seen version stored in .carrel/plugin-state.json. Used by the session-start
 * hook to surface a migration nudge when the plugin has been updated.
 *
 * Returns: { needsMigration: boolean, from: string|null, to: string, firstRun?: boolean }
 */

const fs = require('fs');
const path = require('path');

function getPluginVersion() {
  try {
    const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..');
    const manifest = JSON.parse(
      fs.readFileSync(path.join(pluginRoot, '.claude-plugin', 'plugin.json'), 'utf8')
    );
    return manifest.version || '0.0.0';
  } catch {
    return null;
  }
}

function getLastSeenVersion(carrelRoot) {
  try {
    const statePath = path.join(carrelRoot, '.carrel', 'plugin-state.json');
    const state = JSON.parse(fs.readFileSync(statePath, 'utf8'));
    return state.plugin_version || null;
  } catch {
    return null;
  }
}

function checkVersion(carrelRoot) {
  const pluginVersion = getPluginVersion();
  if (!pluginVersion) return { needsMigration: false, from: null, to: '0.0.0' };

  const lastSeen = getLastSeenVersion(carrelRoot);

  if (!lastSeen) {
    // First run with version tracking — not a migration, just initialize
    return { needsMigration: false, from: null, to: pluginVersion, firstRun: true };
  }

  if (lastSeen !== pluginVersion) {
    return { needsMigration: true, from: lastSeen, to: pluginVersion };
  }

  return { needsMigration: false, from: lastSeen, to: pluginVersion };
}

module.exports = { checkVersion, getPluginVersion, getLastSeenVersion };
