#!/usr/bin/env node

/**
 * SessionStart Hook: Check Carrel environment
 *
 * Runs at session start to verify .carrel/ exists and tools are available.
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
    // No .carrel/ found — suggest setup
    console.log('');
    console.log('Welcome! This folder doesn\'t have a Carrel research environment yet.');
    console.log('Run /carrel-setup to get started, or just tell me about your research.');
    console.log('');
    process.exit(0);
  }

  // .carrel/ exists — check environment
  const envPath = path.join(projectRoot, '.carrel', 'environment.json');

  if (!fs.existsSync(envPath)) {
    console.log('');
    console.log('Carrel detected but environment isn\'t configured yet.');
    console.log('Run /carrel-setup to complete the setup.');
    console.log('');
    process.exit(0);
  }

  try {
    const env = JSON.parse(fs.readFileSync(envPath, 'utf8'));
    const researcher = env.interview?.researcher;

    if (!researcher) {
      console.log('');
      console.log('Carrel is partially set up but the interview wasn\'t completed.');
      console.log('Run /carrel-setup to finish configuration.');
      console.log('');
      process.exit(0);
    }

    // Everything looks good — brief welcome
    const name = researcher.name ? ` ${researcher.name.split(' ')[0]}` : '';
    console.log('');
    console.log(`Welcome back${name}. Your Carrel research environment is ready.`);
    console.log('');

  } catch (error) {
    // Corrupted env file — don't block, just note it
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
