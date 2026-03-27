#!/usr/bin/env node

/**
 * SessionStart Hook: Check Carrel environment and surface researcher profile
 *
 * Runs at session start to verify .carrel/ exists, tools are available,
 * and surface the researcher's preferences so Claude can act on them.
 * Non-blocking — provides guidance, never prevents work.
 */

const fs = require('fs');
const path = require('path');

function findCarrelRoot(startPath) {
  let currentPath = startPath;
  while (currentPath !== path.parse(currentPath).root) {
    if (fs.existsSync(path.join(currentPath, '.carrel'))) {
      return currentPath;
    }
    currentPath = path.dirname(currentPath);
  }
  return null;
}

function main() {
  const projectRoot = findCarrelRoot(process.cwd());

  if (!projectRoot) {
    console.log('');
    console.log('Welcome! This folder doesn\'t have a Carrel research environment yet.');
    console.log('Run /carrel-setup to get started, or just tell me about your research.');
    console.log('');
    process.exit(0);
  }

  const envPath = path.join(projectRoot, '.carrel', 'environment.json');

  if (!fs.existsSync(envPath)) {
    console.log('');
    console.log('Carrel detected but environment isn\'t configured yet.');
    console.log('Run /carrel-setup to complete the setup.');
    console.log('');
    process.exit(0);
  }

  // Version check
  try {
    const { checkVersion } = require('./check-version.js');
    const versionInfo = checkVersion(projectRoot);
    if (versionInfo.needsMigration) {
      console.log('');
      console.log(`Carrel has been updated: ${versionInfo.from} → ${versionInfo.to}`);
      console.log('Run /carrel-migrate to see what\'s new and apply any changes.');
    }
  } catch {
    // Version check is non-blocking
  }

  try {
    const env = JSON.parse(fs.readFileSync(envPath, 'utf8'));

    // Detect format: flat (Python ResearcherProfile) or nested (legacy JS interview)
    const isFlat = env.name !== undefined || env.sensitivity !== undefined || env.cloud_consent !== undefined;
    const isNested = env.interview?.researcher !== undefined;

    if (!isFlat && !isNested) {
      console.log('');
      console.log('Carrel is partially set up but the interview wasn\'t completed.');
      console.log('Run /carrel-setup to finish configuration.');
      console.log('');
      process.exit(0);
    }

    // Read fields: flat (canonical) first, fall back to nested (legacy)
    const rawName = env.name || env.interview?.researcher?.name || null;
    const name = rawName ? ` ${rawName.split(' ')[0]}` : '';
    const sensitivity = env.sensitivity || env.interview?.data?.sensitivity || 'medium';
    const cloudConsent = env.cloud_consent ?? env.interview?.preferences?.cloud_comfort ?? 'prefer_local';
    const toolsConfigured = env.tools_configured || {};

    console.log('');
    console.log(`Welcome back${name}. Carrel research environment is ready.`);

    // Surface key preferences so Claude knows how to behave
    console.log('');
    console.log('Researcher profile:');
    console.log(`  Sensitivity: ${sensitivity}`);
    console.log(`  Cloud preference: ${cloudConsent}`);

    // Surface configured tools
    const activeTools = Object.entries(toolsConfigured)
      .filter(([, v]) => v === true)
      .map(([k]) => k);
    if (activeTools.length > 0) {
      console.log(`  Active tools: ${activeTools.join(', ')}`);
    }

    // Check for preference/reality mismatches
    // Flat: env.preferences.multi_model_providers; Legacy: env.interview.preferences.multi_model_providers
    const wantedTools = env.preferences?.multi_model_providers || env.interview?.preferences?.multi_model_providers || [];
    for (const tool of wantedTools) {
      const key = tool.toLowerCase();
      if (toolsConfigured[key] === false || !toolsConfigured[key]) {
        console.log(`  Note: ${tool} was requested during setup but is not yet configured.`);
      }
    }

    // Remind Claude to check CLAUDE.md is in sync
    const claudeMdPath = path.join(projectRoot, 'CLAUDE.md');
    if (!fs.existsSync(claudeMdPath)) {
      console.log('');
      console.log('Note: No CLAUDE.md found in vault. Consider running /carrel-setup to generate one.');
    }

    console.log('');

  } catch (error) {
    console.log('');
    console.log('Note: Could not read environment config. Run /carrel-status to check.');
    console.log('');
  }

  process.exit(0);
}

try {
  main();
} catch (error) {
  // Never block the session
  process.exit(0);
}
