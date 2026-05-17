#!/usr/bin/env node

/**
 * UserPromptSubmit Hook: Inject Carrel vault context
 *
 * Per-turn injection of vault state (sensitivity, cloud_consent, trust_level,
 * most recent automation brief) so Claude has fresh context every turn without
 * relying on session-start memory. Silent no-op outside Carrel vaults.
 */

const fs = require('node:fs');
const path = require('node:path');

const DEBUG = process.env.CARREL_HOOK_DEBUG === '1';

function debug(msg) {
  if (DEBUG) process.stderr.write(`[carrel:inject-context] ${msg}\n`);
}

// Walk up from startPath looking for .carrel/ marker. Mirrors
// findCarrelRoot() in check-environment.js so SessionStart and
// UserPromptSubmit see the same vault root from any subdirectory.
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
  const root = findCarrelRoot(process.cwd());
  if (!root) {
    debug('no .carrel/ ancestor — not a carrel vault');
    return;
  }

  const envPath = path.join(root, '.carrel', 'environment.json');
  if (!fs.existsSync(envPath)) {
    debug(`environment.json missing at ${envPath}`);
    return;
  }

  let env;
  try {
    env = JSON.parse(fs.readFileSync(envPath, 'utf8'));
  } catch (err) {
    debug(`environment.json parse failed: ${err.message}`);
    return;
  }

  const sensitivity = env.sensitivity ?? env.interview?.data?.sensitivity ?? 'medium';
  const cloudConsentValue = env.cloud_consent ?? env.interview?.preferences?.cloud_comfort ?? false;
  const cloudConsent = (cloudConsentValue === true || cloudConsentValue === 'cloud_ok')
    ? 'enabled'
    : 'disabled';
  const trustLevel = env.automation?.trust_level ?? 'advisory';

  const lines = [
    'Carrel vault context:',
    `- Sensitivity: ${sensitivity} · Cloud consent: ${cloudConsent} · Trust: ${trustLevel}`,
  ];

  try {
    const briefsDir = path.join(root, '_meta', 'briefs');
    if (fs.existsSync(briefsDir)) {
      const briefs = fs.readdirSync(briefsDir)
        .filter(f => f.endsWith('.md'))
        .map(f => ({ name: f, mtime: fs.statSync(path.join(briefsDir, f)).mtimeMs }))
        .sort((a, b) => b.mtime - a.mtime);
      if (briefs.length > 0) {
        const first = fs.readFileSync(path.join(briefsDir, briefs[0].name), 'utf8').split('\n')[0].trim();
        const title = first.replace(/^#+\s*/, '') || briefs[0].name.replace(/\.md$/, '');
        lines.push(`- Active brief: ${title} (${briefs[0].name.replace(/\.md$/, '')})`);
      }
    }
  } catch (err) {
    debug(`brief enumeration failed: ${err.message}`);
  }

  // CC hook protocol: UserPromptSubmit output must nest under hookSpecificOutput
  // with hookEventName + additionalContext. Top-level keys are ignored.
  // Ref: https://code.claude.com/docs/en/hooks
  const output = {
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: lines.join('\n'),
    },
  };
  process.stdout.write(JSON.stringify(output));
}

try {
  main();
} catch (err) {
  // Never disrupt the user's turn
  debug(`unhandled: ${err.message}`);
}
process.exit(0);
