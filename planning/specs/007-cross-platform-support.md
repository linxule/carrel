# 007: Cross-Platform Support (Windows + Linux)

**Status**: Spec (pre-review)
**Version target**: v0.7.0
**Date**: 2026-04-20

---

## Context

Carrel's install path is cross-platform: `install.sh` covers macOS/Linux, `install.ps1` covers Windows. Both bootstrap the toolchain and install the plugin successfully.

But the configuration plan that `/carrel-setup` hands off to is Mac-centric. Windows users complete `install.ps1`, run `/carrel-setup`, get an interview, and then hit a wall because:

- `src/carrel/env/audit.py` uses macOS-only `mdfind` (Spotlight) to detect Obsidian/Zotero — silently fails on Windows even when those apps are installed
- `src/carrel/env/install.py` constants are all `brew`-prefixed — `brew install ffmpeg`, `brew tap run-llama/liteparse`, `brew install --cask obsidian`
- `skills/environment-setup/references/decision-tree.md` recommends `brew install` unconditionally with no OS branching
- Some tools have no Windows package at all (`gws` Google Workspace CLI, `liteparse` Homebrew tap)

A 2026-04-20 cross-platform audit (background reviewer agent) confirmed each of these and surfaced the gap as the highest-priority deployment blocker for any non-Mac user. Imperial College Business School (Carrel's first deployment target) has Windows users.

This spec defines the cross-platform contract, the per-tool Windows story, and the implementation sequence.

## Philosophy: Honest Gating, Not Lowest-Common-Denominator

The temptation is to ship a "cross-platform" Carrel that pretends every tool exists everywhere. We reject that. Better:

1. **Detect the platform once** (during `carrel env doctor`), pick the correct install paths for that platform, and tell the truth about what's not available.
2. **Some tools are Mac-only** (today: `gws` has no Windows package; `liteparse` has no documented Windows install). Mark them clearly. Offer alternatives where they exist. Don't fake it.
3. **The interview adapts.** If the audit detects Windows, `/carrel-setup` doesn't recommend tools that can't be installed there.
4. **Documentation tells the truth.** The decision tree branches by OS. The interviewer surfaces OS context. The cheat sheet uses the right commands.
5. **Linux is a first-class citizen alongside macOS** — the existing `install.sh` works on Linux but the downstream tooling has the same Mac-bias as for Windows. Fixing Windows fixes Linux too in most cases.

### Feature filter

- Pretends a tool works when it doesn't → reject
- Detects platform and adapts → accept
- Adds branches that drift over time → examine carefully (mitigate via tests)
- Forces all install logic into one matrix → examine (one matrix is good for some tools, bad for others)

---

## The Per-Tool Windows Story

The audit fix is fundamentally about answering, for each tool, "what's the install command on Windows?"

| Tool | Used For | macOS install | Windows install | Linux install | Decision |
|------|----------|---------------|-----------------|---------------|----------|
| **liteparse** | PDF conversion | `brew tap run-llama/liteparse && brew install llamaindex-liteparse` | **TBD** — no documented Windows path | likely `pip install` from PyPI? | Investigate; if no Windows path, mark Mac-only and route to `mineru` (cloud) for Windows |
| **coli** | Audio transcription | `bun add -g @marswave/coli` | `bun add -g @marswave/coli` (works ✓) | same | Already cross-platform |
| **defuddle** | Web capture | `bun add -g defuddle` | `bun add -g defuddle` (works ✓) | same | Already cross-platform |
| **markitdown** | Office docs | bundled with carrel via pip | bundled (works ✓) | bundled | Already cross-platform |
| **ffmpeg** | Audio dependency | `brew install ffmpeg` | `winget install Gyan.FFmpeg` OR `choco install ffmpeg` OR download from gyan.dev | `apt install ffmpeg` / `dnf install ffmpeg` | Branch in install.py |
| **pandoc** | (currently unused?) | `brew install pandoc` | `winget install JohnMacFarlane.Pandoc` | `apt install pandoc` | Branch (low priority) |
| **obsidian** | Researcher GUI | `brew install --cask obsidian` | `winget install Obsidian.Obsidian` OR download from obsidian.md | AppImage from obsidian.md | Branch in SKILL guidance + install.py |
| **gws** | Google Workspace | `brew install googleworkspace-cli` | **No Windows package** | likely build from source | Mark Mac-only; surface in decision tree |
| **zotero** | Reference manager | `brew install --cask zotero` (also direct download) | `winget install Zotero.Zotero` OR direct download | direct download from zotero.org | Branch |
| **mineru** | Cloud PDF service | API key + Python lib | API key + Python lib | same | Already cross-platform (cloud) |
| **groq** | Cloud transcription | API key only | API key only | same | Already cross-platform (cloud) |

**Net**: most "Tier 1 blockers" turn into branches over a small set of canonical commands. The hard cases are `liteparse` and `gws` — both need a real answer ("does it exist on Windows?") before the spec is locked.

---

## Deliverables

All ship in v0.7.0.

### A. Platform detection layer

#### A1. `src/carrel/env/platform.py` (new module)

```python
class Platform(str, Enum):
    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"

def detect_platform() -> Platform:
    """Returns the current platform via sys.platform mapping."""
```

Single source of truth for OS detection. All branching downstream consults this.

#### A2. `AuditResult.platform: Platform` field

Add to `models.py`. `carrel env doctor` populates it from `detect_platform()`. Surfaced in JSON output for the interviewer to use.

#### A3. Shared `ToolAvailability` matrix (consumed by spec 006 validator too)

Add to `models.py`:

```python
class ToolAvailability(BaseModel):
    """Per-tool, per-platform availability matrix.
    
    Single source of truth for "is tool X available on platform Y" — consumed
    by carrel env doctor (reporting), the 006 validator (drift detection),
    and the decision tree (recommendation gating).
    """
    matrix: dict[str, dict[Platform, bool]]

    def is_available(self, tool: str, platform: Platform) -> bool:
        return self.matrix.get(tool, {}).get(platform, False)
```

Populated at startup from per-tool detection (binaries via `shutil.which()`, GUI apps via the platform-aware detection in B1). Spec 006's validator reads this matrix instead of running its own detection — eliminating the cross-cutting risk Kimi flagged.

### B. Audit fixes (`src/carrel/env/audit.py`)

#### B1. Replace `mdfind` calls with platform-branched detection

Current behavior (Mac-only):
- Obsidian detection uses `mdfind 'kMDItemKind == "Application"'`
- Zotero detection same

New behavior:
- macOS: existing `mdfind` path
- Windows: check `%LOCALAPPDATA%\Obsidian` and `%PROGRAMFILES%\Zotero` (registry probe optional, file system probe minimum)
- Linux: existing `shutil.which()` fallback already works

#### B2. Tools availability accuracy

`carrel env doctor` must NOT report a tool as installed if its install would have come from a Mac-only command. Use platform-aware install constants (B3) as the source of truth.

### C. Install constants (`src/carrel/env/install.py`)

#### C1. Platform-keyed install commands

Refactor from flat constants to per-tool dicts keyed by platform:

```python
INSTALLS = {
    "ffmpeg": {
        Platform.MACOS: "brew install ffmpeg",
        Platform.LINUX: "apt install -y ffmpeg  # or dnf install ffmpeg on Fedora",
        Platform.WINDOWS: "winget install Gyan.FFmpeg",
    },
    "obsidian": {
        Platform.MACOS: "brew install --cask obsidian",
        Platform.LINUX: "Download AppImage from https://obsidian.md",
        Platform.WINDOWS: "winget install Obsidian.Obsidian",
    },
    "gws": {
        Platform.MACOS: "brew install googleworkspace-cli",
        Platform.LINUX: "Build from source: https://github.com/...",
        Platform.WINDOWS: None,  # explicitly unavailable
    },
    # ...
}

def install_command(tool: str, platform: Platform) -> str | None:
    """Return install command for tool on platform, or None if unavailable."""
```

`None` is the truth-telling escape hatch — surfaces "this tool isn't available on your OS" cleanly.

### D. Decision tree (`skills/environment-setup/references/decision-tree.md`)

#### D1. OS-branched recommendations

Each tool's "Install" entry becomes platform-aware. Either:
- (a) inline branches (`On macOS: brew ...; On Windows: winget ...; On Linux: apt ...`)
- (b) a single line referencing the install constant (`See INSTALLS["ffmpeg"][platform]`) and a footer table

Lean toward (b) — keeps the prose readable and concentrates branching in one place.

#### D2. Mark Mac-only tools

Liteparse and gws (if they remain Mac-only) get an explicit "**macOS only**" tag with the alternative recommendation:
- liteparse on Windows → recommend `mineru` (cloud) as the primary PDF tool
- gws on Windows → "Google Workspace integration unavailable on Windows; use Web Clipper to manually save Google Docs"

### E. Interviewer (`agents/setup-interviewer.md`)

#### E1. Surface OS context early

Add to the Middle conversation flow:

> "Quick technical detail — what operating system are you on? (Mac, Windows, or Linux.) This shapes what tools I can offer."

Don't ask if `carrel env doctor` already detected it (it always will). The interviewer reads `AuditResult.platform` from Phase 2's output and just confirms verbally if relevant: "I see you're on Windows — a couple of the optional tools (specifically Google Workspace integration) aren't available, so I'll skip those."

### F. SKILL adaptations (`skills/environment-setup/SKILL.md`)

#### F1. Step 6 (Human Steps) — platform-aware Obsidian guidance

```diff
- Install Obsidian (offer `brew install obsidian` or download from obsidian.md)
+ Install Obsidian:
+   macOS: `brew install --cask obsidian`
+   Windows: `winget install Obsidian.Obsidian` (or download from obsidian.md)
+   Linux: download AppImage from obsidian.md
```

### G. Cheat sheet template (`skills/environment-setup/references/cheatsheet-template.md`)

#### G1. Platform-aware tool snippets

The rendered cheat sheet should show install commands for the researcher's actual platform, not always macOS commands. Pass `platform` into `render_cheat_sheet()` and branch.

### H. Hook (`hooks/check-environment.js`)

#### H1. No changes required

The session-start hook is platform-agnostic Node code already. No work here.

### I. Bootstrap script honesty

#### I1. Update `bootstrap.sh` deprecation message

Currently: "DEPRECATED: Use install.sh instead."
Update to: "Legacy macOS-only bootstrap. Use install.sh on macOS/Linux or install.ps1 on Windows."

#### I2. Verify `install.ps1` handles all the same prerequisites

Audit `install.ps1` to confirm it installs (or makes available): node, bun, uv, gh, claude-code. Document any gaps in this spec before implementation.

---

## Acceptance Criteria

### Must Have

| # | Criterion |
|---|-----------|
| 1 | `Platform` enum + `detect_platform()` in `src/carrel/env/platform.py` |
| 2 | `AuditResult.platform: Platform` field populated by `carrel env doctor` |
| 3 | `audit.py` Obsidian/Zotero detection works on Windows (file-system probe) |
| 4 | `install.py` returns the correct install command for each (tool, platform) pair, or `None` when unavailable |
| 5 | `decision-tree.md` shows OS-aware install commands for all listed tools |
| 6 | Mac-only tools (`gws`, possibly `liteparse`) are explicitly marked and have documented alternatives |
| 7 | Interviewer surfaces OS context and skips OS-incompatible tool recommendations |
| 8 | `SKILL.md` Step 6 (Obsidian install) is platform-branched |
| 9 | The cheat sheet renders OS-correct commands (passes platform to render function) |
| 10 | Pytest covers platform detection and install-command lookup for all three platforms (mocked) |

### Should Have

| # | Criterion |
|---|-----------|
| 1 | `install.ps1` is audited and verified to install the same prerequisites as `install.sh` |
| 2 | `bootstrap.sh` deprecation message accurately points to the cross-platform installers |
| 3 | A short `references/platform-support-matrix.md` table that researchers + Claude can read at a glance |
| 4 | `carrel env doctor --format human` output mentions the platform clearly |
| 5 | The README's Installation section lists each platform's prerequisites side-by-side |

### Nice to Have

| # | Criterion |
|---|-----------|
| 1 | Choco fallback alongside winget for Windows (winget is recent; some enterprise-managed Windows machines may not have it) |
| 2 | Per-platform integration test in CI (matrix build) |
| 3 | The friction log auto-tags entries with the platform so we see Windows-specific issues clustered |

---

## Implementation Order

1. **Investigate liteparse + gws Windows availability** — answer the open questions before locking the spec
2. `src/carrel/env/platform.py` (new module: enum + detection)
3. `AuditResult.platform` field on `models.py`
4. `audit.py` Windows/Linux detection paths for Obsidian/Zotero
5. `install.py` refactor to per-tool dicts
6. Tests for platform detection and install-command lookup
7. `decision-tree.md` rewrite with OS-aware commands
8. `setup-interviewer.md` OS-context addition
9. `SKILL.md` platform-branched Step 6
10. `cheatsheet-template.md` + `render_cheat_sheet()` accept platform
11. `bootstrap.sh` deprecation message + `install.ps1` audit
12. Migration `0.6.x-to-0.7.0.md`
13. README cross-platform clarity
14. Version bump to 0.7.0

---

## Lock Blockers (must resolve before implementation)

The following questions MUST be answered (with citations) before this spec is locked. Per Kimi review (2026-04-20): "committing a spec that admits it doesn't know whether a core tool works on Windows creates false confidence and leaves the implementation team with an unscoped research task mid-cycle."

### Lock blocker A: liteparse Windows installability

If liteparse has no Windows install path, Windows researchers with HIGH sensitivity have NO local PDF conversion option. They are forced to either:
- (a) Use mineru (cloud) — violates HIGH-sensitivity local-only default
- (b) Use WSL — adds significant setup friction and breaks the "Carrel works natively on your OS" promise
- (c) Use markitdown for PDFs — but markitdown PDF support is poor (the whole reason liteparse was added)

**Required research before lock**: investigate upstream (`run-llama/liteparse`) for:
1. Is there a `pip install` path? (If yes, Windows works via Python/pip directly.)
2. Is there a `bun add -g` / `npm install -g` package? (If yes, Windows works via Node.)
3. Is the Homebrew formula a wrapper around something installable on Windows directly?
4. If none of the above, is there a documented Windows build-from-source path?

**Decision matrix for the spec lock**:
- If liteparse works on Windows (any path) → spec proceeds as-is
- If liteparse is genuinely Mac-only → spec MUST add an explicit "Windows + HIGH sensitivity" decision tree branch with: WSL recommendation, mineru cloud opt-in with explicit consent capture, or accept the gap and document the limitation prominently in the README

### Lock blocker B: gws Windows alternative

Confirmed no Windows package as of 2026-04-20. The spec's current resolution ("mark Mac-only with Web Clipper as fallback") is acceptable IF the Web Clipper workflow actually covers the Google Workspace use case. Verify before lock that:
- Web Clipper handles Google Docs (yes — it's a documented use case)
- Web Clipper handles Google Sheets (likely degraded; needs testing)
- Web Clipper handles Google Slides (likely degraded; needs testing)

If Sheets/Slides degrade significantly via Web Clipper, document the gap explicitly.

## Open Questions

1. **Liteparse on Windows.** See Lock Blocker A above. Critical to resolve before locking.

2. **Gws on Windows.** Confirmed no Windows package as of 2026-04-20. Options: (a) accept the gap and document it, (b) build a thin Python wrapper around the Google Drive API directly (significant scope), (c) recommend Web Clipper as the manual fallback. Lean toward (a)+(c) — Web Clipper covers most use cases.

3. **Scope of the install.py refactor.** Today the constants are flat; the per-tool dict adds a layer of indirection. Worth it for the platform-aware case, but does it complicate other use cases? Lean: yes worth it; the indirection is small and gives us a single source of truth.

4. **CI matrix testing.** Do we want to actually exercise Windows in CI (GitHub Actions windows-latest)? Useful but adds CI cost + flakiness. Defer to v0.7.1 unless cheap.

5. **Linux distros.** `apt` is Debian/Ubuntu; `dnf` is Fedora; Arch uses `pacman`. Do we branch on distro within Linux, or pick one (Debian/Ubuntu) and document the others as "you know what to do"? Lean: Ubuntu/Debian as default in install constants, document others in a comment.

6. **Coordination with spec 006.** Spec 006 (validator) and spec 007 (cross-platform) both touch `carrel env doctor`. Per Kimi review and the resolution in spec 006's "Cross-Cutting" section: 007 ships first (introduces `Platform`, `AuditResult.platform`, and the `ToolAvailability` matrix in deliverable A3); 006 ships second and consumes the matrix. Sequential, not interleaved. Locked.

---

## Out of Scope (deferred)

- Choco-only environments without winget (rare, niche)
- WSL detection and routing (researchers using WSL get Linux paths — fine)
- Native Windows build of liteparse (upstream project's call)
- ARM Linux specifically (most distros work; not testing)
- Mobile platforms (iOS, Android) — Carrel is desktop-only

---

## Reviews

To be conducted post-spec, per existing pattern:

- Codex (deep adversarial): `planning/reviews/007-review-codex.md`
- Kimi (independent second-pair-of-eyes): `planning/reviews/007-review-kimi.md`
- Code architect (feasibility): `planning/reviews/007-review-architect.md`

Lock decisions after all three reviews complete; then implement. The two open questions about liteparse and gws Windows availability MUST be answered (web research + upstream check) before lock.
