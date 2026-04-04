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
const { checkVersion } = require('./check-version');

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

function readJsonFile(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return null;
  }
}

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const result = {};
  for (const line of match[1].split('\n')) {
    const idx = line.indexOf(':');
    if (idx > 0) {
      const key = line.slice(0, idx).trim();
      const val = line.slice(idx + 1).trim();
      result[key] = val;
    }
  }
  return result;
}

function countUncheckedItems(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const matches = content.match(/^- \[ \]/gm);
    return matches ? matches.length : 0;
  } catch {
    return 0;
  }
}

function daysBetween(dateA, dateB) {
  return Math.floor(Math.abs(dateA - dateB) / (1000 * 60 * 60 * 24));
}

function safeWriteJson(filePath, data) {
  const tmpPath = filePath + '.tmp';
  fs.writeFileSync(tmpPath, JSON.stringify(data, null, 2) + '\n', 'utf8');
  fs.renameSync(tmpPath, filePath);
}

function checkAutomation(projectRoot, env) {
  const briefsDir = path.join(projectRoot, '_meta', 'briefs');
  if (!fs.existsSync(briefsDir)) return;

  try {
    // 1. Read last_session_start from plugin-state.json
    const statePath = path.join(projectRoot, '.carrel', 'plugin-state.json');
    const pluginState = readJsonFile(statePath) || {};
    const lastSessionStart = pluginState.last_session_start
      ? new Date(pluginState.last_session_start)
      : null;

    const now = new Date();

    // 2. Check for new morning briefs
    try {
      const briefs = fs.readdirSync(briefsDir)
        .filter(f => f.endsWith('.md') && /^\d{4}-\d{2}-\d{2}\.md$/.test(f))
        .sort()
        .reverse();

      if (briefs.length > 0) {
        const latestDate = briefs[0].replace('.md', '');
        const latestBriefTime = new Date(latestDate + 'T00:00:00Z');
        if (!lastSessionStart || latestBriefTime > lastSessionStart) {
          // Try to extract summary counts from the brief
          let summary = '';
          try {
            const briefContent = fs.readFileSync(path.join(briefsDir, briefs[0]), 'utf8');
            const parts = [];
            const processedMatch = briefContent.match(/Processed:\s*(\d+)/);
            const pendingMatch = briefContent.match(/Pending decisions:\s*(\d+)/);
            const suggestionsSection = briefContent.match(/## Suggestions\n([\s\S]*?)(?=\n##|$)/);
            if (processedMatch) parts.push(`${processedMatch[1]} processed`);
            if (pendingMatch && pendingMatch[1] !== '0') parts.push(`${pendingMatch[1]} pending`);
            if (suggestionsSection) {
              const suggCount = (suggestionsSection[1].match(/^- \*\*/gm) || []).length;
              if (suggCount > 0) parts.push(`${suggCount} suggestion${suggCount === 1 ? '' : 's'}`);
            }
            if (parts.length > 0) summary = ` — ${parts.join(', ')}`;
          } catch {}
          console.log(`  Morning brief ready (${latestDate})${summary}`);
        }
      }
    } catch {}

    // 3. Check for active plans
    try {
      const plansDir = path.join(projectRoot, '_meta', 'plans');
      if (fs.existsSync(plansDir)) {
        const planFiles = fs.readdirSync(plansDir)
          .filter(f => f.endsWith('.md'))
          .sort((a, b) => {
            try {
              const statA = fs.statSync(path.join(plansDir, a)).mtimeMs;
              const statB = fs.statSync(path.join(plansDir, b)).mtimeMs;
              return statB - statA;
            } catch { return 0; }
          })
          .slice(0, 5);

        const activePlans = [];
        for (const file of planFiles) {
          if (activePlans.length >= 3) break;
          try {
            const content = fs.readFileSync(path.join(plansDir, file), 'utf8');
            const fm = parseFrontmatter(content);
            if (fm.status === 'active') {
              activePlans.push(fm.title || file.replace('.md', ''));
            }
          } catch {}
        }
        for (const title of activePlans) {
          console.log(`  Active plan: '${title}'`);
        }
      }
    } catch {}

    // 4. Check for pending decisions
    try {
      const decisionsPath = path.join(projectRoot, '_meta', 'pending-decisions.md');
      const count = countUncheckedItems(decisionsPath);
      if (count > 0) {
        console.log(`  ${count} pending decision${count === 1 ? '' : 's'} from overnight processing`);
      }
    } catch {}

    // 5. Check for pending approvals
    try {
      const approvalsPath = path.join(projectRoot, '_meta', 'pending-approvals.md');
      const count = countUncheckedItems(approvalsPath);
      if (count > 0) {
        console.log(`  ${count} pending approval${count === 1 ? '' : 's'} — review with /carrel-automate or approve inline`);
      }
    } catch {}

    // 6. Check automation status
    try {
      const automation = env.automation;
      if (automation && automation.enabled) {
        // Check if no briefs in last 7 days
        const briefs = fs.readdirSync(briefsDir)
          .filter(f => f.endsWith('.md') && /^\d{4}-\d{2}-\d{2}\.md$/.test(f))
          .sort()
          .reverse();

        if (briefs.length > 0) {
          const latestDate = new Date(briefs[0].replace('.md', '') + 'T00:00:00Z');
          if (daysBetween(now, latestDate) > 7) {
            console.log('  Automation configured but no recent briefs — is the Desktop scheduled task running?');
          }
        } else {
          console.log('  Automation configured but no recent briefs — is the Desktop scheduled task running?');
        }

        // Check if review is stale
        if (automation.last_reviewed && automation.review_cadence) {
          const lastReviewed = new Date(automation.last_reviewed);
          const cadenceMap = { monthly: 30, quarterly: 90, biannual: 180 };
          const maxDays = cadenceMap[automation.review_cadence];
          if (maxDays && daysBetween(now, lastReviewed) > maxDays) {
            const reviewDate = automation.last_reviewed.slice(0, 10);
            console.log(`  Automation preferences last reviewed ${reviewDate}. Run /carrel-automate to update.`);
          }
        }
      }
    } catch {}

    // 7. Write last_session_start (after all output)
    try {
      pluginState.last_session_start = now.toISOString();
      safeWriteJson(statePath, pluginState);
    } catch {}

  } catch {}
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

    // Check for plugin version changes
    const versionResult = checkVersion(projectRoot);
    if (versionResult.needsMigration) {
      console.log('');
      console.log(`  Carrel updated: ${versionResult.from} → ${versionResult.to}. Run /carrel-migrate to see what's new.`);
    }

    // Automation checks (gated on _meta/briefs/ existence)
    checkAutomation(projectRoot, env);

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
