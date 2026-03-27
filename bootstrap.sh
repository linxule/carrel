#!/bin/bash
set -e

# Carrel Bootstrap — gets a Mac ready for AI-augmented research
#
# DEPRECATED: Use install.sh instead (cross-platform).
#   curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
#
# This script is kept for backward compatibility.
#
# Usage (local):
#   bash bootstrap.sh
#
# What it installs:
#   1. Xcode Command Line Tools (includes git)
#   2. Homebrew
#   3. Node.js (for MCP servers)
#   4. uv (Python package manager)
#   5. GitHub CLI (gh)
#   6. Claude Code CLI
#
# After this script: open Claude Desktop → Code tab → install Carrel plugin

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

step() { echo -e "\n${BLUE}[$1/8]${NC} $2"; }
ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
info() { echo -e "  ${YELLOW}→${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         Carrel Bootstrap for macOS       ║"
echo "║  Sets up your Mac for AI-augmented       ║"
echo "║  research with Claude Desktop            ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# --- 1. Xcode Command Line Tools ---
step 1 "Xcode Command Line Tools (includes git)"
if xcode-select -p &>/dev/null; then
  ok "Already installed"
else
  info "Installing — a dialog may pop up. Click 'Install' and wait."
  xcode-select --install 2>/dev/null || true
  echo ""
  info "Press Enter when the installation finishes..."
  read -r < /dev/tty
  # Verify it worked
  if ! xcode-select -p &>/dev/null; then
    echo "  ✗ Installation may not have completed. Try running: xcode-select --install"
    exit 1
  fi
  ok "Installed"
fi

# --- 2. Homebrew ---
step 2 "Homebrew (package manager)"
if command -v brew &>/dev/null; then
  ok "Already installed"
else
  info "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Add to PATH for Apple Silicon Macs
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
    # Persist for future terminal sessions (only if not already added)
    if ! grep -q '/opt/homebrew/bin/brew' ~/.zprofile 2>/dev/null; then
      echo '' >> ~/.zprofile
      echo '# Homebrew' >> ~/.zprofile
      echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    fi
  fi
  ok "Installed"
fi

# --- 3. Node.js ---
step 3 "Node.js (needed for document conversion)"
if command -v node &>/dev/null; then
  ok "Already installed ($(node --version))"
else
  info "Installing via Homebrew..."
  brew install node
  ok "Installed ($(node --version))"
fi

# --- 4. uv (Python) ---
step 4 "uv (Python package manager)"
if command -v uv &>/dev/null; then
  ok "Already installed ($(uv --version 2>/dev/null | head -1))"
else
  info "Installing via Homebrew..."
  brew install uv
  ok "Installed"
fi

# --- 5. GitHub CLI ---
step 5 "GitHub CLI"
if command -v gh &>/dev/null; then
  ok "Already installed"
else
  info "Installing via Homebrew..."
  brew install gh
  ok "Installed"
fi

# Check GitHub auth
if gh auth status &>/dev/null 2>&1; then
  ok "Already signed in to GitHub"
else
  echo ""
  info "Sign in to GitHub (needed for plugin updates and syncing your work)"
  info "Choose 'Login with a web browser' for the easiest option"
  echo ""
  gh auth login < /dev/tty
  ok "Signed in"
fi

# --- 6. Claude Code CLI ---
step 6 "Claude Code CLI"
if command -v claude &>/dev/null; then
  ok "Already installed"
else
  info "Installing via official installer..."
  curl -fsSL https://claude.ai/install.sh | bash
  ok "Installed"
fi

# --- 7. Install Carrel plugin ---
step 7 "Carrel plugin"
info "Registering plugin marketplace and installing..."
claude plugin marketplace add linxule/carrel 2>/dev/null && ok "Marketplace registered" || info "Marketplace registration — you may need to do this in Claude Desktop"
claude plugin install carrel@carrel --scope user 2>/dev/null && ok "Plugin installed" || info "Plugin install — you may need to do this in Claude Desktop"

# --- 8. Verify ---
step 8 "Verifying installation"
MISSING=""
command -v git    &>/dev/null || MISSING="$MISSING git"
command -v brew   &>/dev/null || MISSING="$MISSING brew"
command -v node   &>/dev/null || MISSING="$MISSING node"
command -v uv     &>/dev/null || MISSING="$MISSING uv"
command -v gh     &>/dev/null || MISSING="$MISSING gh"
command -v claude &>/dev/null || MISSING="$MISSING claude"

if [[ -n "$MISSING" ]]; then
  echo -e "  ${YELLOW}⚠${NC}  Missing:$MISSING"
  echo "  You may need to open a new terminal window and try again."
else
  ok "All tools ready"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║              All done!                   ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "  1. Create a folder for your research:"
echo "     mkdir -p ~/Documents/Research"
echo ""
echo "  2. Open Claude Desktop → Code tab"
echo "  3. Select your research folder as the project"
echo "  4. Say: \"I'd like to set up my research environment\""
echo ""
echo "If the plugin didn't install automatically, tell Claude:"
echo -e "  ${GREEN}Install the Carrel plugin from linxule/carrel${NC}"
echo ""
