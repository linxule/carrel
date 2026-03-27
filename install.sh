#!/bin/bash
set -e

# Carrel Installer — cross-platform setup for AI-augmented research
#
# macOS:
#   curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
#   (or locally: bash install.sh)
#
# Linux:
#   curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
#
# Windows (PowerShell):
#   See install.ps1
#
# What it does:
#   1. Detects your OS
#   2. Installs prerequisites (git, Node.js, uv, GitHub CLI, Claude Code)
#   3. Signs you in to GitHub
#   4. Installs the Carrel plugin for Claude Code

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
info() { echo -e "  ${YELLOW}→${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }

OS="$(uname -s)"
ARCH="$(uname -m)"
TOTAL_STEPS=7

step() { echo -e "\n${BLUE}[$1/$TOTAL_STEPS]${NC} $2"; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           Carrel Installer               ║"
echo "║  Sets up AI-augmented research with      ║"
echo "║  Claude Desktop on any platform          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Detected: $OS ($ARCH)"
echo ""

# ─── Platform-specific package installer ───

install_package() {
  local name="$1"
  local brew_name="${2:-$1}"
  local apt_name="${3:-$1}"

  case "$OS" in
    Darwin)
      brew install "$brew_name"
      ;;
    Linux)
      if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y -qq "$apt_name"
      elif command -v dnf &>/dev/null; then
        sudo dnf install -y -q "$apt_name"
      elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm "$apt_name"
      else
        fail "No supported package manager found (need apt, dnf, or pacman)"
        exit 1
      fi
      ;;
    *)
      fail "Unsupported OS: $OS"
      fail "For Windows, use install.ps1 in PowerShell"
      exit 1
      ;;
  esac
}

# ─── 1. System prerequisites ───

step 1 "System prerequisites"

case "$OS" in
  Darwin)
    # macOS: Xcode CLI tools
    if xcode-select -p &>/dev/null; then
      ok "Xcode CLI tools already installed"
    else
      info "Installing Xcode Command Line Tools — a dialog may pop up. Click 'Install' and wait."
      xcode-select --install 2>/dev/null || true
      echo ""
      info "Press Enter when the installation finishes..."
      read -r < /dev/tty
      if ! xcode-select -p &>/dev/null; then
        fail "Installation may not have completed. Try: xcode-select --install"
        exit 1
      fi
      ok "Xcode CLI tools installed"
    fi

    # Homebrew
    if command -v brew &>/dev/null; then
      ok "Homebrew already installed"
    else
      info "Installing Homebrew..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        if ! grep -q '/opt/homebrew/bin/brew' ~/.zprofile 2>/dev/null; then
          echo '' >> ~/.zprofile
          echo '# Homebrew' >> ~/.zprofile
          echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        fi
      fi
      ok "Homebrew installed"
    fi
    ;;
  Linux)
    # Ensure git is available
    if command -v git &>/dev/null; then
      ok "git already installed"
    else
      info "Installing git..."
      install_package git
      ok "git installed"
    fi

    # Ensure curl is available
    if command -v curl &>/dev/null; then
      ok "curl already installed"
    else
      info "Installing curl..."
      install_package curl
      ok "curl installed"
    fi
    ;;
esac

# ─── 2. Node.js ───

step 2 "Node.js"
if command -v node &>/dev/null; then
  ok "Already installed ($(node --version))"
else
  info "Installing Node.js..."
  case "$OS" in
    Darwin)
      brew install node
      ;;
    Linux)
      # Use NodeSource for a recent version
      if command -v apt-get &>/dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y -qq nodejs
      else
        install_package nodejs nodejs nodejs
      fi
      ;;
  esac
  ok "Installed ($(node --version))"
fi

# ─── 3. uv (Python) ───

step 3 "uv (Python package manager)"
if command -v uv &>/dev/null; then
  ok "Already installed ($(uv --version 2>/dev/null | head -1))"
else
  info "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Add to current session
  export PATH="$HOME/.local/bin:$PATH"
  ok "Installed"
fi

# ─── 4. GitHub CLI ───

step 4 "GitHub CLI"
if command -v gh &>/dev/null; then
  ok "Already installed"
else
  info "Installing GitHub CLI..."
  case "$OS" in
    Darwin)
      brew install gh
      ;;
    Linux)
      if command -v apt-get &>/dev/null; then
        # Official GitHub CLI apt repo
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt-get update -qq && sudo apt-get install -y -qq gh
      elif command -v dnf &>/dev/null; then
        sudo dnf install -y -q 'dnf-command(config-manager)'
        sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
        sudo dnf install -y -q gh
      else
        info "Install GitHub CLI manually: https://cli.github.com"
        exit 1
      fi
      ;;
  esac
  ok "Installed"
fi

# GitHub auth
if gh auth status &>/dev/null 2>&1; then
  ok "Already signed in to GitHub"
else
  echo ""
  info "Sign in to GitHub (needed for the Carrel plugin)"
  info "Choose 'Login with a web browser' for the easiest option"
  echo ""
  gh auth login < /dev/tty
  ok "Signed in"
fi

# ─── 5. Claude Code CLI ───

step 5 "Claude Code CLI"
if command -v claude &>/dev/null; then
  ok "Already installed"
else
  info "Installing Claude Code..."
  case "$OS" in
    Darwin)
      curl -fsSL https://claude.ai/install.sh | bash
      ;;
    Linux)
      curl -fsSL https://claude.ai/install.sh | bash
      ;;
  esac
  # Add to current PATH if installed to ~/.local/bin or ~/.claude/bin
  for p in "$HOME/.local/bin" "$HOME/.claude/bin"; do
    [[ -d "$p" ]] && export PATH="$p:$PATH"
  done
  ok "Installed"
fi

# ─── 6. Carrel plugin ───

step 6 "Carrel plugin"
info "Adding marketplace and installing..."

if claude plugin marketplace add linxule/carrel 2>/dev/null; then
  ok "Marketplace registered"
else
  info "Marketplace may already be registered, continuing..."
fi

if claude plugin install carrel@carrel --scope user 2>/dev/null; then
  ok "Plugin installed"
else
  info "Plugin install needs Claude Desktop — see next steps"
fi

# ─── 7. Verify ───

step 7 "Verifying installation"
MISSING=""
command -v git    &>/dev/null || MISSING="$MISSING git"
command -v node   &>/dev/null || MISSING="$MISSING node"
command -v uv     &>/dev/null || MISSING="$MISSING uv"
command -v gh     &>/dev/null || MISSING="$MISSING gh"
command -v claude &>/dev/null || MISSING="$MISSING claude"

if [[ -n "$MISSING" ]]; then
  echo -e "  ${YELLOW}⚠${NC}  Missing:$MISSING"
  echo "  Open a new terminal window and try again — some tools need a PATH refresh."
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
echo "If the plugin didn't install, tell Claude:"
echo -e "  ${GREEN}Install the Carrel plugin from linxule/carrel${NC}"
echo ""
