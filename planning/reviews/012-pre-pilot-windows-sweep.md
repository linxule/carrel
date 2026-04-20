---
title: Pre-pilot Windows-paths adversarial sweep
date: 2026-04-20
reviewer: Codex (background) + manual fallback
context: pre-Imperial-pilot; v0.7.0 shipped without exercising Windows code on a real machine
---

# Pre-pilot Windows-paths sweep

## Scope

Spec 007 shipped first-class Windows support in v0.7.0 with all 228 tests passing on macOS, but no Windows machine has exercised the new branches. This pass walks the Windows-specific code paths critically before Imperial College pilot deployment.

Files reviewed:
- `install.ps1` (PowerShell installer)
- `src/carrel/env/platform.py` (Platform enum, detection)
- `src/carrel/env/install.py` (per-tool install commands)
- `src/carrel/env/audit.py` (Windows GUI tool detection, hardware audit)
- `src/carrel/safe_path.py` (vault containment)
- `src/carrel/vault/markers.py` (HTML-comment markers)

## Findings

| # | Severity | Location | Issue | Resolution |
|---|----------|----------|-------|------------|
| 1 | HIGH | `audit.py:99-120` | Windows Obsidian/Zotero detection covered only one install path each. Misses `%LOCALAPPDATA%\Programs\Obsidian` (used by official Obsidian installer's "Programs" install location) and `%LOCALAPPDATA%\Zotero` (used by some Zotero installers). Researchers would see "missing" for tools they have. | **Fixed** (manual) — expanded candidate path lists in both detectors. |
| 2 | MEDIUM | `audit.py:220-225` | `df -h` doesn't exist on Windows. `_run_command` returned `None` silently → disk_free always None. | **Fixed** (manual) — replaced with `shutil.disk_usage` (cross-platform stdlib). |
| 3 | MEDIUM | `install.ps1:133, 165, 177` | `$LASTEXITCODE` not checked after `gh auth login`, `claude plugin marketplace add`, `claude plugin install`. Script would print "Signed in" / "Marketplace registered" / "Plugin installed" even on failure (try/catch doesn't catch external nonzero exits in PowerShell). | **Fixed** (Codex) — explicit exit-code branches; exits with error on gh auth failure, degrades gracefully on plugin command failure. |
| 4 | MEDIUM | `hooks/check-environment.js:39` | `parseFrontmatter` regex `/^---\n([\s\S]*?)\n---/` fails to match CRLF line endings. A Windows researcher's git could produce CRLF in CLAUDE.md → silent frontmatter parse failure → hook reports nothing. | **Fixed** (Codex) — `\r?\n` makes regex CRLF-tolerant. |
| 5 | MEDIUM | `audit.py:_run_command` (44-65) | bun-installed CLI shims on Windows (coli, defuddle, liteparse) may be `.cmd` files. Python's subprocess SHOULD resolve via PATHEXT, but unverified on a real machine. | **Flagged**. Baseline expected to work; first PC pilot is the test. |
| 6 | LOW | `install.ps1:149` | `Anthropic.ClaudeCode` winget ID unverified. | **Flagged** — npm fallback at `:151-152` covers if winget fails. Acceptable. |
| 7 | LOW | `install.ps1:60-65` | curl required check. | OK — Win10/11 ship curl.exe by default. |
| 8 | LOW | `safe_path.py` | `.resolve()` follows OneDrive junctions on Windows. | OK — both vault root and target resolved against same base, containment check still valid. |
| 9 | LOW | `vault/markers.py` | Pathlib text mode auto-translates `\r\n`↔`\n`; regex uses `re.DOTALL`. | OK — CRLF-safe by construction. |

## Deferred / known gaps (not blockers)

- **No Windows CI matrix**. GitHub Actions `windows-latest` was deferred for cost vs flakiness. Real Windows pilot machine remains the test.
- **Zotero portable installs** outside `%PROGRAMFILES%` and `%LOCALAPPDATA%` won't be detected. Edge case; documented friction is acceptable.
- **`gh auth login` interactivity** in `install.ps1:133` — pauses installer mid-script. Expected, no fix needed.

## Process note

The Codex codex-rescue agent dispatched for this review didn't surface its findings through the agent-status channel (~20 min with the stub output file unchanged), but had silently applied two MEDIUM fixes to `install.ps1` and `hooks/check-environment.js` directly to disk. Discovered them via `git status` after starting a manual fallback pass.

Pattern matches the v0.7.0 commit-5 stall noted in the deployment-readiness memo: **agent completion signals are unreliable; verify the working tree directly.** This now applies to "agent stuck" as well — sometimes "stuck" means "done but not reporting." Always inspect `git status` and `git diff` before drawing conclusions.

## Result

Four MEDIUM/HIGH fixes applied across `audit.py`, `install.ps1`, and `hooks/check-environment.js`. Tests still pass (228/228). Mac smoke test of `carrel env doctor` shows expected output. Ready for push to origin/main.
