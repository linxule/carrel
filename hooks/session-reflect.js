#!/usr/bin/env node

/**
 * SessionEnd Hook: Reflection Prompt
 *
 * Triggers at end of each session to offer a brief reflection.
 * Non-blocking — always bypassable. The researcher can ignore it.
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

function getSessionStats(projectRoot) {
  const stats = {
    vault_files: 0,
    papers: 0,
    notes: 0,
    transcripts: 0,
    drafts: 0,
    reflections: 0
  };

  const countFiles = (dir) => {
    try {
      return fs.readdirSync(dir).filter(f => f.endsWith('.md')).length;
    } catch { return 0; }
  };

  stats.papers = countFiles(path.join(projectRoot, 'papers'));
  stats.notes = countFiles(path.join(projectRoot, 'notes'));
  stats.transcripts = countFiles(path.join(projectRoot, 'transcripts'));
  stats.drafts = countFiles(path.join(projectRoot, 'drafts'));
  stats.reflections = countFiles(path.join(projectRoot, '_meta', 'reflections'));
  stats.vault_files = stats.papers + stats.notes + stats.transcripts + stats.drafts;

  return stats;
}

function getRecentCapabilityLogEntries(projectRoot) {
  const logPath = path.join(projectRoot, '_meta', 'capability-log.md');
  if (!fs.existsSync(logPath)) return [];

  try {
    const content = fs.readFileSync(logPath, 'utf8');
    const today = new Date().toISOString().slice(0, 10);
    const entries = [];
    const lines = content.split('\n');

    for (const line of lines) {
      if (line.startsWith('## ' + today)) {
        const desc = line.replace('## ' + today + ': ', '').trim();
        if (desc) entries.push(desc);
      }
    }
    return entries;
  } catch { return []; }
}

function main() {
  const projectRoot = findCarrelRoot(process.cwd());

  if (!projectRoot) {
    // Not a Carrel project — skip silently
    process.exit(0);
  }

  const envPath = path.join(projectRoot, '.carrel', 'environment.json');
  if (!fs.existsSync(envPath)) {
    process.exit(0);
  }

  let env;
  try {
    env = JSON.parse(fs.readFileSync(envPath, 'utf8'));
  } catch {
    process.exit(0);
  }

  const researcher = env.interview?.researcher;
  if (!researcher) {
    process.exit(0);
  }

  const stats = getSessionStats(projectRoot);
  const recentCreations = getRecentCapabilityLogEntries(projectRoot);
  const name = researcher.name ? researcher.name.split(' ')[0] : 'there';

  // Output structured remediation for machine parsing (follows IO plugin convention)
  // next_commands/next_skills: suggested follow-ups, not requirements
  const remediation = {
    code: 'SESSION_REFLECTION',
    severity: 'info',
    reason: 'Session ending — optional reflection prompt',
    next_commands: ['/carrel-reflect'],
    next_skills: ['research-partner'],
    can_bypass: true,
    details: {
      vault_stats: stats,
      custom_creations_today: recentCreations,
      reflexive_questions: [
        'What was most useful about today\'s session?',
        'Was there anything frustrating or that didn\'t work well?',
        'Anything you wished you could do but couldn\'t?'
      ]
    }
  };
  console.error(JSON.stringify(remediation));

  console.log('');
  console.log(`See you next time, ${name}.`);
  console.log('');

  if (stats.vault_files > 0) {
    console.log(`Your vault: ${stats.papers} papers, ${stats.notes} notes, ${stats.transcripts} transcripts, ${stats.drafts} drafts.`);
    console.log('');
  }

  if (recentCreations.length > 0) {
    console.log(`Custom capabilities created today: ${recentCreations.length}`);
    for (const entry of recentCreations) {
      console.log(`  - ${entry}`);
    }
    console.log('These are logged in _meta/capability-log.md for potential inclusion in future Carrel versions.');
    console.log('');
  }

  console.log('If you have a moment, run /carrel-reflect to share quick feedback.');
  console.log('It takes 2 minutes and helps improve the tool for other researchers.');
  console.log('');

  process.exit(0);
}

try {
  main();
} catch {
  process.exit(0);
}
