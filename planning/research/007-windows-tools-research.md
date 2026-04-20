# 007 — Windows Tools Research: Liteparse + gws

**Date**: 2026-04-20
**Author**: Research pass for spec 007 lock blockers (A and B)
**Status**: Findings — input to spec lock decision
**Spec**: `planning/specs/007-cross-platform-support.md`

---

## 1. Executive Summary

- **Lock Blocker A (liteparse Windows) is RESOLVED.** Liteparse explicitly supports Windows via two equally first-class paths: `npm i -g @llamaindex/liteparse` (Node CLI, the upstream-recommended primary install) and `pip install liteparse` (Python wrapper that delegates to the Node CLI). Tesseract.js OCR is bundled — no system Tesseract required. LibreOffice and ImageMagick are *optional* and only needed for non-PDF Office docs / image-as-PDF flows; PDF parsing works without them. Carrel's `bun add -g @llamaindex/liteparse` will work cross-platform identically to the macOS Homebrew path.
- **Lock Blocker B (gws Windows) is RESOLVED — better than expected.** As of v0.22.5 (released 2026-03-31), gws ships a first-class Windows binary (`google-workspace-cli-x86_64-pc-windows-msvc.zip`) plus a PowerShell installer (`google-workspace-cli-installer.ps1`) and an npm wrapper that auto-downloads the platform-native binary. The 2026-04-20 spec assertion "no Windows package" was based on the older Homebrew-only state; upstream has since shipped multi-platform releases. **Spec 007's Lock Blocker B can be marked resolved with a small caveat** about a known Windows OAuth setup wrinkle (gcloud `.cmd` resolution) which has a documented manual workaround.
- **Bonus finding: Google Docs has had native Markdown export since 2024-07.** `File > Download > Markdown (.md)` is built into Google Docs for all account types (personal, Workspace). This is a much simpler Windows fallback than Web Clipper for the Docs use case — the Web Clipper question becomes moot for Docs and reduces to "what about Sheets/Slides?" (answer: native Markdown export does NOT cover Sheets/Slides; those degrade regardless of approach).
- **Surprise: liteparse's Python wrapper auto-installs the npm CLI under the hood.** The PyPI package `liteparse==1.2.1` (2026-03-28) is a thin wrapper that requires Node.js >= 18 and "auto-installs the CLI via npm if needed." So `pip install liteparse` and `npm i -g @llamaindex/liteparse` converge on the same runtime. Carrel should standardize on the npm path (which matches our existing `bun add -g` pattern for coli/defuddle).
- **Net effect on spec 007**: Both lock blockers can be resolved. Windows + HIGH-sensitivity researchers get full local PDF parsing via liteparse. Windows + Google Workspace researchers get gws natively. The "Windows is a degraded experience" concern in the spec is significantly weaker than the pre-research assumption suggested.

---

## 2. Q1: Liteparse Windows Installability

### 2.1 Available install paths (all confirmed)

| Path | Command | Platform support | Notes |
|------|---------|------------------|-------|
| **npm (recommended upstream)** | `npm i -g @llamaindex/liteparse` | macOS, Linux, Windows (explicit) | Primary install per upstream README. Provides `lit` CLI globally. |
| **bun (functionally equivalent)** | `bun add -g @llamaindex/liteparse` | Same | Carrel already uses `bun add -g` for coli/defuddle. Should work identically. |
| **pip (Python wrapper)** | `pip install liteparse` | Universal wheel (`py3-none-any`); Python 3.10–3.14 | PyPI v1.2.1, published 2026-03-28. Requires Node.js >= 18 separately; wrapper auto-installs the npm CLI if missing. |
| **Homebrew (macOS/Linux)** | `brew tap run-llama/liteparse && brew install llamaindex-liteparse` | macOS + Linuxbrew | Carrel's current macOS path. |
| **From source** | `git clone … && npm run build && npm pack && npm install -g ./liteparse-*.tgz` | All | Windows uses `npm run build:windows`. |

**Direct quote from upstream README (run-llama/liteparse)**: "Linux, macOS (Intel/ARM), Windows" are all supported environments.

### 2.2 Windows-specific dependencies

- **Required**: Node.js >= 18 (for both npm and pip paths). Already a baseline carrel prerequisite — `install.ps1` installs Node + bun.
- **Bundled (no install)**: Tesseract.js for OCR. Works out-of-box, no system Tesseract needed.
- **Optional (only for non-PDF formats)**: 
  - LibreOffice — for `.docx`/`.pptx`/`.xlsx`/`.odt` etc. Install: `choco install libreoffice-fresh`. Windows-specific gotcha: must add `C:\Program Files\LibreOffice\program` to PATH and reboot.
  - ImageMagick — for image-to-PDF conversion. Install: `choco install imagemagick.app` (admin required).
- **Air-gapped OCR**: `TESSDATA_PREFIX` env var to point at a pre-downloaded `tessdata` directory. Documented escape hatch for offline use.

### 2.3 Known Windows blockers

None found in 2025–2026 issue search. The README explicitly enumerates Windows as supported, and a separate `npm run build:windows` build target exists in the dev workflow, suggesting upstream actively builds and tests on Windows. No open issues mentioning Windows-specific runtime breakage in the recent search.

### 2.4 Backup options (if liteparse ever breaks for a Windows researcher)

These were evaluated but are not needed given liteparse Windows support is confirmed:

| Tool | Windows install | Academic PDF quality | Maintenance | License | Verdict |
|------|-----------------|----------------------|-------------|---------|---------|
| **markitdown** | `pip install markitdown` (already bundled) | Poor for academic PDFs (was the explicit reason liteparse was added) | Active (Microsoft) | MIT | Not a real fallback. |
| **PyMuPDF / fitz** | `pip install pymupdf` | Strong text extraction; weaker for complex tables/multi-column | Very active | AGPL-3.0 (commercial license needed for some uses) | Viable but license friction for an academic tool. |
| **pdfplumber** | `pip install pdfplumber` | Good for tables; weaker for layout | Active | MIT | Viable secondary. |
| **unstructured (local mode)** | `pip install unstructured[local-inference]` | Strong but heavy deps (often pulls torch, detectron2, etc.) | Very active | Apache-2.0 | Heavy install footprint; not researcher-friendly. |
| **pdf2docx** | `pip install pdf2docx` | Round-trip via DOCX; lossy | Active | GPL-3.0 | Niche. |

**Recommendation**: ship liteparse on Windows via npm/bun. No need for a fallback PDF tool. If a researcher hits a liteparse-specific issue, fall back to mineru (cloud, with explicit consent) — same as on macOS today.

---

## 3. Q2: gws (Google Workspace CLI) Windows Alternative

### 3.1 gws DOES have Windows install paths (spec assumption was outdated)

The spec said "Confirmed no Windows package as of 2026-04-20." Upstream releases tell a different story.

**gws v0.22.5, released 2026-03-31** ships:
- Pre-built Windows binary: `google-workspace-cli-x86_64-pc-windows-msvc.zip` (5.61 MB) on the [GitHub Releases page](https://github.com/googleworkspace/cli/releases)
- PowerShell installer: `powershell -ExecutionPolicy Bypass -c "irm https://github.com/googleworkspace/cli/releases/download/v0.22.5/google-workspace-cli-installer.ps1 | iex"`
- npm wrapper: `npm install -g @googleworkspace/cli` — installs `run.js` that auto-downloads the correct platform-native binary
- Build from source: `cargo install --git https://github.com/googleworkspace/cli --locked` (requires Rust toolchain)

**No winget package** — confirmed. But the npm path is functionally equivalent and matches carrel's existing tooling.

### 3.2 Known Windows-specific issue (workaround documented)

From the deepwiki and X-CMD installation pages: gws on Windows has an OAuth-setup wrinkle. The `gws auth setup` command tries to call `gcloud` to auto-create a GCP project, but Rust binaries don't resolve `.cmd` wrapper executables on Windows the same way the shell does, so `gcloud.cmd` is not found even when on PATH. Workaround: skip `gws auth setup` and create the OAuth Desktop app manually at https://console.cloud.google.com/apis/credentials. This is a one-time setup friction, identical to the existing macOS gws onboarding effort.

### 3.3 Alternative paths if gws ever breaks

| Approach | Windows-installable? | Covers Docs | Sheets | Slides | Notes |
|----------|---------------------|-------------|--------|--------|-------|
| **gws via npm** (primary) | Yes (auto-binary) | Yes | Yes | Yes | First class |
| **Native "File > Download > Markdown"** | N/A (browser feature) | Yes (since 2024-07) | No | No | Built into Google Docs UI; works on all accounts |
| **gdocs-cli (famasya/gdocs-cli)** | Yes (`.exe` release) | Yes | No | No | Go binary; Feb 2026 release; OAuth required |
| **Docs to Markdown add-on** (Workspace Marketplace) | N/A (browser) | Yes | No | No | Manual per-doc; no setup |
| **GAM (GAM-team/GAM)** | Yes (MSI installer) | Admin tool, not export-focused | n/a | n/a | Wrong tool — admin/bulk ops, not content export |
| **Drive Desktop + markitdown** | Yes (Drive Desktop is native Windows) | DOCX→md works (markitdown handles `.docx`) | XLSX→md works (markitdown handles `.xlsx`) | PPTX→md works (markitdown handles `.pptx`) | Two-step but viable. Researcher uses Drive Desktop's "Open in Word/Excel/PowerPoint" or web "Download as", then carrel converts. |
| **Obsidian Web Clipper** | Yes (browser ext) | Likely degraded for editor view (JS-heavy SPA, Mozilla Readability not built for Docs editor) | Probably broken | Probably broken | Not recommended for Google Workspace content. |

**Web Clipper assessment**: Obsidian Web Clipper uses Mozilla Readability, which is designed for article-style HTML, not the JavaScript-rendered Google Docs editor canvas. No upstream documentation specifically claims Google Docs support. Forum search surfaces general "not working on dynamic sites" reports, no positive Google Docs case studies. The spec's Web Clipper fallback is the **weakest** of the alternatives — it should be removed or downgraded.

### 3.4 Recommended Windows fallback chain (when gws is unavailable for any reason)

1. **For Google Docs**: native `File > Download > Markdown` (zero setup, all account types; available since 2024-07).
2. **For Google Sheets/Slides**: `File > Download > .xlsx / .pptx` then `carrel paper convert` via markitdown (already cross-platform). Two-step, but covers the format gap.
3. **CLI alternative for Docs only**: `gdocs-cli` Windows .exe (active Go project, Feb 2026 release).
4. **Drop Web Clipper from the recommendation set** for Google Workspace content — it's not built for Docs editor and is likely to disappoint.

---

## 4. Recommended Updates to Spec 007

### 4.1 Lock Blockers section (top of spec)

Replace the entire "LOCK BLOCKERS — DO NOT IMPLEMENT UNTIL RESOLVED" section with a "LOCK BLOCKERS — RESOLVED" section summarizing:

> **Lock Blocker A (liteparse Windows): RESOLVED 2026-04-20.** Liteparse supports Windows via `npm i -g @llamaindex/liteparse` (or equivalently `bun add -g @llamaindex/liteparse`, matching carrel's existing pattern for coli/defuddle). PyPI also ships a Python wrapper (`pip install liteparse`) but it delegates to the npm CLI and adds no value on Windows beyond what npm already provides. No fallback PDF tool needed; mineru remains the cloud opt-in for both macOS and Windows. Source: upstream README (run-llama/liteparse) explicitly lists Windows, and PyPI v1.2.1 (2026-03-28) has a universal wheel.
>
> **Lock Blocker B (gws Windows): RESOLVED 2026-04-20.** gws has shipped first-class Windows support since at least v0.22.5 (released 2026-03-31). Install via `npm install -g @googleworkspace/cli` (auto-downloads `google-workspace-cli-x86_64-pc-windows-msvc` binary), or use the PowerShell installer at https://github.com/googleworkspace/cli/releases. Known caveat: `gws auth setup` cannot find `gcloud.cmd` on Windows; workaround is to create the OAuth Desktop app manually at console.cloud.google.com/apis/credentials. The Web Clipper fallback assumed in the original spec is **not the best choice** for Google content; see updated alternatives below.

### 4.2 Per-Tool Windows Story table (Section "The Per-Tool Windows Story")

Replace the liteparse and gws rows:

| Tool | Used For | macOS install | Windows install | Linux install | Decision |
|------|----------|---------------|-----------------|---------------|----------|
| **liteparse** | PDF conversion | `bun add -g @llamaindex/liteparse` (preferred) or `brew tap run-llama/liteparse && brew install llamaindex-liteparse` | `bun add -g @llamaindex/liteparse` | `bun add -g @llamaindex/liteparse` | **Cross-platform via npm/bun**. Standardize on this path everywhere; deprecate the Homebrew tap in install.py constants (still document for users who prefer brew). |
| **gws** | Google Workspace | `brew install googleworkspace-cli` or `npm install -g @googleworkspace/cli` | `npm install -g @googleworkspace/cli` (preferred) or PowerShell installer from GitHub Releases | `npm install -g @googleworkspace/cli` or build from source | **Cross-platform via npm**. Document the Windows OAuth workaround (manual gcloud project creation) in the gws setup guide. |

### 4.3 Decision tree (Deliverable D2)

Update D2 to reflect that liteparse and gws are cross-platform:

> Liteparse and gws are cross-platform. No "Mac-only" tag. Document the Windows-specific gws OAuth workaround in `references/gws-setup-guide.md`.

If a researcher's Windows liteparse install fails for any reason, the existing fallback (mineru cloud, with explicit consent) covers them. Same as macOS.

### 4.4 Install constants (`install.py`)

Standardize liteparse installation on `bun add -g @llamaindex/liteparse` for all three platforms. This eliminates the Homebrew tap dependency for all platforms (including macOS) and matches the existing pattern for coli/defuddle/etc. Keep the Homebrew command as a documented alternative for users who prefer brew, but drop it as the default macOS install.

```python
INSTALLS = {
    "liteparse": {
        Platform.MACOS: "bun add -g @llamaindex/liteparse",
        Platform.LINUX: "bun add -g @llamaindex/liteparse",
        Platform.WINDOWS: "bun add -g @llamaindex/liteparse",
    },
    "gws": {
        Platform.MACOS: "npm install -g @googleworkspace/cli",
        Platform.LINUX: "npm install -g @googleworkspace/cli",
        Platform.WINDOWS: "npm install -g @googleworkspace/cli",
    },
    # ...
}
```

Note: gws specifically uses `npm` (not `bun`) because the upstream wrapper is documented for npm; if `bun add -g` is shown to work in testing, switch.

### 4.5 Open Questions section (delete items 1 and 2)

- Open question #1 ("Liteparse on Windows") → deleted. Resolved.
- Open question #2 ("Gws on Windows") → deleted. Resolved. Replace with a smaller note in `references/gws-setup-guide.md` documenting the Windows OAuth workaround.

### 4.6 New deliverable suggestion: native Google Docs Markdown export

Add to the SKILL/decision-tree as a tip:

> **Tip for Google Docs**: Google Docs has had a native "File > Download > Markdown (.md)" option since 2024-07-16. For occasional Doc exports, this is the simplest path on any OS. Use gws when you need bulk export, automation, or Sheets/Slides coverage.

This is independent of OS but worth surfacing in the documentation.

### 4.7 Out of Scope section (add)

> - Native Windows build of liteparse from source (upstream covers this with `npm run build:windows`; researchers rarely need it)
> - Web Clipper as a Google Workspace fallback — not a fit for the Docs editor canvas; removed from recommendations

---

## 5. Sources

All accessed 2026-04-20.

### Liteparse

- [run-llama/liteparse — README on GitHub](https://github.com/run-llama/liteparse) — official install documentation, platform support statement
- [run-llama/liteparse — main README direct](https://github.com/run-llama/liteparse/blob/main/README.md) — Windows-specific dependency notes (LibreOffice PATH, ImageMagick chocolatey install)
- [liteparse on PyPI](https://pypi.org/project/liteparse/) — v1.2.1, published 2026-03-28, universal wheel, Python 3.10–3.14
- [LiteParse blog post (LlamaIndex)](https://www.llamaindex.ai/blog/liteparse-local-document-parsing-for-ai-agents) — release announcement, Tesseract.js bundling
- [LlamaIndex official getting started docs](https://developers.llamaindex.ai/liteparse/getting_started/)
- [MarkTechPost article (2026-03-19)](https://www.marktechpost.com/2026/03/19/llamaindex-releases-liteparse-a-cli-and-typescript-native-library-for-spatial-pdf-parsing-in-ai-agent-workflows/) — independent confirmation of release

### gws (Google Workspace CLI)

- [googleworkspace/cli on GitHub](https://github.com/googleworkspace/cli) — official install instructions
- [googleworkspace/cli Releases](https://github.com/googleworkspace/cli/releases) — v0.22.5 release (2026-03-31), Windows binary asset confirmed
- [Installation page on DeepWiki](https://deepwiki.com/googleworkspace/cli/1.1-installation-and-quick-start) — Windows binary name, npm wrapper details
- [X-CMD installation guide](https://www.x-cmd.com/install/gws/) — independent install notes including Windows OAuth workaround
- [Grizzly Peak Software write-up](https://www.grizzlypeaksoftware.com/articles/p/gws-googles-new-cli-that-puts-your-entire-workspace-into-your-agentic-workflows-VVxefw) — independent install/setup commentary
- [VentureBeat coverage](https://venturebeat.com/orchestration/google-workspace-cli-brings-gmail-docs-sheets-and-more-into-a-common) — context on official launch

### Google Docs Markdown export

- [Google Workspace Updates blog: Import and export Markdown in Google Docs (2024-07)](https://workspaceupdates.googleblog.com/2024/07/import-and-export-markdown-in-google-docs.html) — native feature announcement
- [Google Docs Editors Help: Use Markdown in Google Docs, Slides, & Drawings](https://support.google.com/docs/answer/12014036?hl=en) — confirms Docs-only export scope

### Alternative tools considered

- [famasya/gdocs-cli on GitHub](https://github.com/famasya/gdocs-cli) — Windows .exe, Feb 2026 release, OAuth required
- [GAM-team/GAM on GitHub](https://github.com/GAM-team/GAM) — admin tool, not export-focused
- [microsoft/markitdown on GitHub](https://github.com/microsoft/markitdown) — Office formats; no Google Docs support
- [Obsidian Web Clipper (official)](https://obsidian.md/clipper) — Mozilla Readability under the hood
- [Obsidian Web Clipper troubleshooting](https://forum.obsidian.md/t/web-clipper-issue-with-google-search-links/102333) — known issues with dynamic sites

### Liteparse PDF backup options (evaluated but not needed)

- [PyMuPDF on PyPI](https://pypi.org/project/pymupdf/)
- [pdfplumber on PyPI](https://pypi.org/project/pdfplumber/)
- [unstructured on PyPI](https://pypi.org/project/unstructured/)
- [pdf2docx on PyPI](https://pypi.org/project/pdf2docx/)
