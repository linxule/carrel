#!/usr/bin/env node

/**
 * PreToolUse Hook: Sensitivity gate for cloud-routing carrel subprocesses
 *
 * Re-invokes the targeted carrel command with --explain and surfaces the
 * routing decision to Claude before the cloud subprocess fires. Does NOT
 * replace policy.sensitivity:select_tool — that stays the authoritative
 * enforcement at the CLI boundary. This hook is a UX checkpoint.
 *
 * Triggers only on `carrel (paper|transcript|capture|google) <verb> ... --tool (mineru|mistral_ocr|groq|gemini)`.
 * Silent pass-through on anything else, on `# bypass-gate` comment, and on any error.
 */

const { execFileSync } = require('node:child_process');

const DEBUG = process.env.CARREL_HOOK_DEBUG === '1';

function debug(msg) {
  if (DEBUG) process.stderr.write(`[carrel:sensitivity-gate] ${msg}\n`);
}

// Minimal POSIX-ish shell-word tokenizer. Splits a command line into argv the
// way a shell would for the simple cases we re-invoke: whitespace separators,
// single quotes (fully literal), double quotes (with backslash escapes), and
// backslash escapes outside quotes. Returns an array of tokens, or `null` on
// any uncertainty — an unterminated quote, a trailing backslash, or an
// UNQUOTED shell control operator (`;& | < > ` + "`" + ` $`) that means the line
// does more than a single carrel invocation or expands a value we cannot see.
// Per the hook's fail-open convention, `null` makes the caller pass through.
function shellTokenize(input) {
  const CTRL = new Set([';', '&', '|', '<', '>', '`', '$']);
  const tokens = [];
  let cur = '';
  let started = false;
  let i = 0;
  const n = input.length;
  while (i < n) {
    const c = input[i];
    if (c === "'") {
      started = true;
      i++;
      let closed = false;
      while (i < n) {
        if (input[i] === "'") {
          closed = true;
          i++;
          break;
        }
        cur += input[i];
        i++;
      }
      if (!closed) return null; // unterminated single quote
      continue;
    }
    if (c === '"') {
      started = true;
      i++;
      let closed = false;
      while (i < n) {
        const d = input[i];
        if (d === '"') {
          closed = true;
          i++;
          break;
        }
        if (d === '\\') {
          const nx = input[i + 1];
          if (nx === undefined) return null; // trailing backslash
          if (nx === '"' || nx === '\\' || nx === '$' || nx === '`') {
            cur += nx;
            i += 2;
            continue;
          }
          cur += d; // literal backslash otherwise
          i++;
          continue;
        }
        cur += d; // `$`, `` ` `` kept literal inside our re-invocation
        i++;
      }
      if (!closed) return null; // unterminated double quote
      continue;
    }
    if (c === '\\') {
      const nx = input[i + 1];
      if (nx === undefined) return null; // trailing backslash / line continuation
      cur += nx;
      started = true;
      i += 2;
      continue;
    }
    if (c === ' ' || c === '\t' || c === '\n' || c === '\r') {
      if (started) {
        tokens.push(cur);
        cur = '';
        started = false;
      }
      i++;
      continue;
    }
    if (CTRL.has(c)) return null; // unquoted shell control operator → uncertainty
    cur += c;
    started = true;
    i++;
  }
  if (started) tokens.push(cur);
  return tokens;
}

// `capture` deliberately excluded — `carrel capture` has no --tool flag today.
// `google` retained even though its cloud-route is implicit, in case --tool is added later.
// Match both the spaced (`--tool mineru`) and equals (`--tool=mineru`) forms;
// the equals form otherwise slips past the checkpoint entirely.
const GATE_REGEX = /\bcarrel\s+(paper|transcript|google)\s+\S+\s+.*--tool[=\s]+(mineru|mistral_ocr|groq|gemini)\b/;

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

  // Re-execute the same command with --explain appended. execFileSync passes
  // argv literally (no shell), so we tokenize the command ourselves rather than
  // splitting on whitespace — naive splitting mangles quoted paths
  // ('/path/with spaces/scan.pdf') into broken argv, the --explain subprocess
  // fails, and the gate silently passes the original cloud command through.
  // The tokenizer returns null on any uncertainty (unbalanced quotes, unquoted
  // shell operators); we then pass through per the fail-open convention.
  const subcmd = m[1];
  const tokens = shellTokenize(command);
  if (tokens === null) {
    debug('tokenizer uncertainty (quotes/escapes/shell operators); passing through');
    return;
  }
  // Locate the carrel invocation: bare `carrel` or a path ending in `/carrel`
  // (e.g. /usr/local/bin/carrel). Everything after it is the argv we re-run.
  const carrelIdx = tokens.findIndex((t) => t === 'carrel' || t.endsWith('/carrel'));
  if (carrelIdx < 0) return;
  const carrelBin = tokens[carrelIdx];
  const args = tokens.slice(carrelIdx + 1);
  args.push('--explain');

  let stdout = '';
  try {
    stdout = execFileSync(carrelBin, args, {
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
