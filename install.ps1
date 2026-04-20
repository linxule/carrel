# Carrel Installer for Windows
#
# Usage (PowerShell as Admin):
#   irm https://raw.githubusercontent.com/linxule/carrel/main/install.ps1 | iex
#
# Or locally:
#   .\install.ps1
#
# What it does:
#   1. Installs prerequisites (git, Node.js, bun, uv, GitHub CLI, Claude Code)
#   2. Signs you in to GitHub
#   3. Installs the Carrel plugin for Claude Code

$ErrorActionPreference = "Stop"

function Write-Step($num, $total, $msg) { Write-Host "`n[$num/$total] $msg" -ForegroundColor Blue }
function Write-Ok($msg) { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Info($msg) { Write-Host "  → $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red }

$Total = 7

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗"
Write-Host "║        Carrel Installer (Windows)        ║"
Write-Host "║  Sets up AI-augmented research with      ║"
Write-Host "║  Claude Desktop                          ║"
Write-Host "╚══════════════════════════════════════════╝"
Write-Host ""

# Check for winget
$hasWinget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $hasWinget) {
    Write-Fail "winget not found. Install 'App Installer' from the Microsoft Store first."
    exit 1
}

# ─── 1. Git ───

Write-Step 1 $Total "Git"
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Ok "Already installed ($(git --version))"
} else {
    Write-Info "Installing git..."
    winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "Installed"
}

# ─── 2. Node.js ───

Write-Step 2 $Total "Node.js"
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Ok "Already installed ($(node --version))"
} else {
    Write-Info "Installing Node.js..."
    winget install --id OpenJS.NodeJS.LTS -e --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "Installed"
}

# ─── 3. bun (JS runtime, required for coli + defuddle) ───

Write-Step 3 $Total "bun (JS runtime — required for coli, defuddle, and other research tools)"
if (Get-Command bun -ErrorAction SilentlyContinue) {
    Write-Ok "Already installed ($(bun --version))"
} else {
    Write-Info "Installing bun..."
    # Try winget first (cleanest), fall back to official installer
    $wingetResult = winget install --id Oven-sh.Bun -e --accept-package-agreements --accept-source-agreements 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Info "winget install failed — trying official installer..."
        irm bun.sh/install.ps1 | iex
    }
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "Installed"
}

# ─── 4. uv ───

Write-Step 4 $Total "uv (Python package manager)"
if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Ok "Already installed"
} else {
    Write-Info "Installing uv..."
    irm https://astral.sh/uv/install.ps1 | iex
    Write-Ok "Installed"
}

# ─── 5. GitHub CLI ───

Write-Step 5 $Total "GitHub CLI"
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Ok "Already installed"
} else {
    Write-Info "Installing GitHub CLI..."
    winget install --id GitHub.cli -e --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "Installed"
}

# GitHub auth
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "Already signed in to GitHub"
} else {
    Write-Host ""
    Write-Info "Sign in to GitHub (needed for the Carrel plugin)"
    Write-Info "Choose 'Login with a web browser' for the easiest option"
    Write-Host ""
    gh auth login
    Write-Ok "Signed in"
}

# ─── 6. Claude Code CLI ───

Write-Step 6 $Total "Claude Code CLI"
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Ok "Already installed"
} else {
    Write-Info "Installing Claude Code..."
    # Claude Code Windows installer
    winget install --id Anthropic.ClaudeCode -e --accept-package-agreements --accept-source-agreements 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Info "winget install failed — trying npm..."
        npm install -g @anthropic-ai/claude-code
    }
    Write-Ok "Installed"
}

# ─── 7. Carrel plugin ───

Write-Step 7 $Total "Carrel plugin"
Write-Info "Adding marketplace and installing..."

try {
    claude plugin marketplace add linxule/carrel 2>$null
    Write-Ok "Marketplace registered"
} catch {
    Write-Info "Marketplace may already be registered, continuing..."
}

try {
    claude plugin install carrel@carrel --scope user 2>$null
    Write-Ok "Plugin installed"
} catch {
    Write-Info "Plugin install needs Claude Desktop — see next steps"
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗"
Write-Host "║              All done!                   ║"
Write-Host "╚══════════════════════════════════════════╝"
Write-Host ""
Write-Host "Next steps:"
Write-Host ""
Write-Host '  1. Create a folder for your research:'
Write-Host '     mkdir ~\Documents\Research'
Write-Host ""
Write-Host '  2. Open Claude Desktop → Code tab'
Write-Host '  3. Select your research folder as the project'
Write-Host '  4. Say: "I''d like to set up my research environment"'
Write-Host ""
Write-Host 'If the plugin didn''t install, tell Claude:'
Write-Host '  Install the Carrel plugin from linxule/carrel' -ForegroundColor Green
Write-Host ""
