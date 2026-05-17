#!/usr/bin/env node

/**
 * PreToolUse Hook: Sensitivity gate for cloud-routing carrel subprocesses
 *
 * Re-invokes the targeted carrel command with --explain and surfaces the
 * routing decision to Claude before the cloud subprocess fires. Does NOT
 * replace policy.sensitivity:select_tool — that stays the authoritative
 * enforcement at the CLI boundary. This hook is a UX checkpoint.
 *
 * Triggers only on `carrel (paper|transcript|capture|google) <verb> ... --tool (mineru|groq|gemini)`.
 * Silent pass-through on anything else, on `# bypass-gate` comment, and on any error.
 */

const { execFileSync } = require('node:child_process');

const DEBUG = process.env.CARREL_HOOK_DEBUG === '1';

function debug(msg) {
  if (DEBUG) process.stderr.write(`[carrel:sensitivity-gate] ${msg}\n`);
}

// `capture` deliberately excluded — `carrel capture` has no --tool flag today.
// `google` retained even though its cloud-route is implicit, in case --tool is added later.
const GATE_REGEX = /\bcarrel\s+(paper|transcript|google)\s+\S+\s+.*--tool\s+(mineru|groq|gemini)\b/;

function readStdin() {
  try {
    return require('node:fs').readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

function main() {
  const raw = readStdin();
  if (!raw) return;

  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    return;
  }

  if (payload.tool_name !== 'Bash') return;
  const command = payload.tool_input?.command;
  if (typeof command !== 'string') return;
  if (command.includes('# bypass-gate')) return;
  const m = command.match(GATE_REGEX);
  if (!m) return;

  // Re-execute the same command with --explain appended. To avoid shell-injection
  // risk from quoted operators or unspaced terminators, reject any command whose
  // carrel-invocation tail contains shell metacharacters that can chain commands.
  // execFileSync passes argv literally (no shell), so the worst case is a failed
  // subprocess — but the reject path also catches cases where naive splitting
  // would drop the actual operation. Conservative: only proceed if the tail is
  // a clean argv-shaped command.
  const subcmd = m[1];
  const idx = command.search(/\bcarrel\b/);
  if (idx < 0) return;
  const tail = command.slice(idx);
  // Reject if the tail contains shell control operators (anywhere, quoted or not).
  // A real shell parser would be safer but is overkill for a UX gate;
  // researchers can append `# bypass-gate` if their command needs operators.
  if (/[;&|<>$`]/.test(tail) || /\\$/m.test(tail)) {
    debug('command contains shell control characters; passing through');
    return;
  }
  const args = tail.split(/\s+/).filter(Boolean).slice(1); // drop the leading "carrel"
  args.push('--explain');

  let stdout = '';
  try {
    stdout = execFileSync('carrel', args, {
      timeout: 2500,
      stdio: ['ignore', 'pipe', DEBUG ? 'pipe' : 'ignore'],
      encoding: 'utf8',
    });
  } catch (err) {
    debug(`--explain subprocess failed: ${err.message}`);
    return; // subprocess failure → silent pass-through
  }

  const selectedNone = /selected_tool\s*=\s*None/.test(stdout);
  const rationaleMatch = stdout.match(/rationale\s*=\s*'([^']+)'/);
  const sensitivityMatch = stdout.match(/Sensitivity\.(HIGH|MEDIUM|LOW)/);
  const sensitivity = sensitivityMatch ? sensitivityMatch[1] : null;
  const rationale = rationaleMatch ? rationaleMatch[1] : 'See `carrel ... --explain` for routing rationale';

  let permissionDecision = null;
  let reason = '';
  if (selectedNone) {
    permissionDecision = 'deny';
    reason = `Carrel sensitivity policy denied this cloud route for ${subcmd}: ${rationale}`;
  } else if (sensitivity === 'HIGH' || sensitivity === 'MEDIUM') {
    permissionDecision = 'ask';
    reason = `${sensitivity.toLowerCase()} sensitivity vault: about to send data to a cloud tool. ${rationale}`;
  }

  if (permissionDecision) {
    // CC hook protocol: PreToolUse permission decisions must nest under
    // hookSpecificOutput with hookEventName. Top-level keys are ignored.
    // Ref: https://code.claude.com/docs/en/hooks
    const output = {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision,
        permissionDecisionReason: reason,
      },
    };
    process.stdout.write(JSON.stringify(output));
  }
}

try {
  main();
} catch (err) {
  // Hook errors must never block a tool call
  debug(`unhandled: ${err.message}`);
}
process.exit(0);
