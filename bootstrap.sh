#!/bin/bash
set -e

# Carrel Bootstrap — DEPRECATED shim.
#
# This used to be a separate macOS-only setup script. It now hands off to
# install.sh, the maintained installer for macOS and Linux (Windows: install.ps1):
#   curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
#
# Kept so old instructions that say "run bootstrap.sh" still work.

echo "bootstrap.sh is deprecated — running install.sh instead."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [[ -n "$SCRIPT_DIR" && -f "$SCRIPT_DIR/install.sh" ]]; then
  exec bash "$SCRIPT_DIR/install.sh" "$@"
fi
exec bash -c "$(curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh)"
