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
  } catch (error) {
    if (error instanceof SyntaxError) {
      console.error(`Note: Could not parse ${filePath}: ${error.message}`);
    }
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

function logHookError(context, error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error('carrel-hook:', `${context}:`, message);
}

function shouldShowMigrationPrompt(pluginState, pluginVersion, now) {
  if (pluginState.last_acknowledged_version !== pluginVersion) {
    return true;
  }
  if (!pluginState.last_acknowledged_at) {
    return true;
  }
  const lastAcknowledged = new Date(pluginState.last_acknowledged_at);
  if (Number.isNaN(lastAcknowledged.getTime())) {
    return true;
  }
  return now.getTime() - lastAcknowledged.getTime() >= 24 * 60 * 60 * 1000;
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
    let briefs = [];
    try {
      briefs = fs.readdirSync(briefsDir)
        .filter(f => f.endsWith('.md') && /^\d{4}-\d{2}-\d{2}\.md$/.test(f))
        .sort()
        .reverse();
    } catch (e) {
      logHookError('briefs read', e);
    }

    // 2. Check for new morning briefs
    try {
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
            // Field Map section (wiki status)
            if (env && env.wiki_enabled) {
              try {
                const fieldMapSection = briefContent.match(/## Field Map\n([\s\S]*?)(?=\n##|$)/);
                if (fieldMapSection) {
                  const fmContent = fieldMapSection[1];
                  const pagesMatch = fmContent.match(/Pages:\s*(\d+)/);
                  const contradictionsMatch = fmContent.match(/Contradictions:\s*(\d+)/);
                  if (pagesMatch) parts.push(`wiki: ${pagesMatch[1]} pages`);
                  if (contradictionsMatch && contradictionsMatch[1] !== '0') {
                    parts.push(`${contradictionsMatch[1]} contradiction${contradictionsMatch[1] === '1' ? '' : 's'}`);
                  }
                }
              } catch (e) {
                logHookError('brief field map parse', e);
              }
            }
            if (parts.length > 0) summary = ` — ${parts.join(', ')}`;
          } catch (e) {
            logHookError('brief summary read', e);
          }
          console.log(`  Morning brief ready (${latestDate})${summary}`);
        }
      }
    } catch (e) {
      logHookError('morning brief check', e);
    }

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
          } catch (e) {
            logHookError('active plan read', e);
          }
        }
        for (const title of activePlans) {
          console.log(`  Active plan: '${title}'`);
        }
      }
    } catch (e) {
      logHookError('active plans check', e);
    }

    // 4. Check for pending decisions
    try {
      const decisionsPath = path.join(projectRoot, '_meta', 'pending-decisions.md');
      const count = countUncheckedItems(decisionsPath);
      if (count > 0) {
        console.log(`  ${count} pending decision${count === 1 ? '' : 's'} from overnight processing`);
      }
    } catch (e) {
      logHookError('pending decisions check', e);
    }

    // 5. Check for pending approvals
    try {
      const approvalsPath = path.join(projectRoot, '_meta', 'pending-approvals.md');
      const count = countUncheckedItems(approvalsPath);
      if (count > 0) {
        console.log(`  ${count} pending approval${count === 1 ? '' : 's'} — review with /carrel-automate or approve inline`);
      }
    } catch (e) {
      logHookError('pending approvals check', e);
    }

    // 6. Check automation status
    try {
      const automation = env.automation;
      if (automation && automation.enabled) {
        // Check if no briefs in last 7 days
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
    } catch (e) {
      logHookError('automation status check', e);
    }

    // 7. Write last_session_start (after all output)
    try {
      pluginState.last_session_start = now.toISOString();
      safeWriteJson(statePath, pluginState);
    } catch (e) {
      logHookError('plugin-state write', e);
    }

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

  // Setup pause detection — surface a resume prompt if the researcher
  // stopped between phases (last_completed_phase < 9 and not marked complete).
  const setupStatePath = path.join(projectRoot, '.carrel', 'setup-state.json');
  const setupState = readJsonFile(setupStatePath);
  if (setupState != null) {
    const phase = setupState.last_completed_phase;
    if (!Number.isInteger(phase) || phase < 4 || phase > 9) {
      console.log('');
      console.log('Note: .carrel/setup-state.json is malformed — run `carrel setup-state show` to inspect.');
      console.log('');
    } else if (phase < 9 || setupState.completed_at == null) {
      const phaseLabel = {
        4: 'after the vault was scaffolded',
        5: 'after optional MCPs',
        6: 'after the human steps',
        7: 'after the cheat sheet',
        8: 'after the automation step',
        9: 'during the final handoff',
      }[phase] || `at phase ${phase}`;
      console.log('');
      console.log(`Setup paused ${phaseLabel}. Run /carrel-setup to resume from here.`);
      console.log('');
    }
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
    const cloudConsentValue = env.cloud_consent ?? env.interview?.preferences?.cloud_comfort ?? false;
    const cloudConsent = cloudConsentValue === true || cloudConsentValue === 'cloud_ok'
      ? 'cloud OK'
      : 'prefer local';
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
      const statePath = path.join(projectRoot, '.carrel', 'plugin-state.json');
      const pluginState = readJsonFile(statePath) || {};
      const now = new Date();
      if (shouldShowMigrationPrompt(pluginState, versionResult.to, now)) {
        console.log('');
        console.log(`  Carrel updated: ${versionResult.from} → ${versionResult.to}. Run /carrel-migrate to see what's new.`);
        pluginState.last_acknowledged_version = versionResult.to;
        pluginState.last_acknowledged_at = now.toISOString();
        safeWriteJson(statePath, pluginState);
      }
    }

    // Automation checks (gated on _meta/briefs/ existence)
    checkAutomation(projectRoot, env);

    // Wiki status fallback (when no brief surfaced wiki info)
    if (env && env.wiki_enabled) {
      try {
        const wikiSchema = path.join(projectRoot, 'wiki', 'SCHEMA.md');
        if (fs.existsSync(wikiSchema)) {
          const wkBriefsDir = path.join(projectRoot, '_meta', 'briefs');
          const hasBrief = fs.existsSync(wkBriefsDir) &&
            fs.readdirSync(wkBriefsDir).filter(f => /^\d{4}-\d{2}-\d{2}\.md$/.test(f)).length > 0;
          if (!hasBrief) {
            const wikiDirs = ['entities', 'concepts', 'comparisons', 'queries'];
            let pageCount = 0;
            for (const dir of wikiDirs) {
              const dirPath = path.join(projectRoot, 'wiki', dir);
              if (fs.existsSync(dirPath)) {
                pageCount += fs.readdirSync(dirPath).filter(f => f.endsWith('.md')).length;
              }
            }
            if (pageCount > 0) {
              console.log(`  Wiki active: ${pageCount} pages`);
            }
          }
        }
      } catch (e) {
        logHookError('wiki fallback check', e);
      }
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
