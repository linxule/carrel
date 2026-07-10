#!/usr/bin/env bash
set -euo pipefail

# Syncs skills/carrel (the standalone Carrel skill pack) to its dedicated
# distribution repo, so it can be installed by hosts that only support Agent
# Skills (npx skills, .agents/skills/, Kimi Code, Claude.ai zip upload, etc.)
# without pulling in the 13 skills meant only for the Claude Code plugin.
#
# Same pattern already used for skills/inquiry -> linxule/inquiry-skill:
#   git subtree push --prefix=skills/inquiry https://github.com/linxule/inquiry-skill.git main
#
# Usage:
#   scripts/sync-skill-repo.sh                          # dry run against the default repo
#   scripts/sync-skill-repo.sh --push                    # actually push to the default repo
#   scripts/sync-skill-repo.sh <url> --push              # push to a different repo
#
# Defaults to --dry-run so nobody pushes by accident.

PREFIX="skills/carrel"
BRANCH="main"
DEFAULT_URL="https://github.com/linxule/carrel-skill.git"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

URL="$DEFAULT_URL"
PUSH=false

for arg in "$@"; do
  case "$arg" in
    --push)
      PUSH=true
      ;;
    --dry-run)
      PUSH=false
      ;;
    -h|--help)
      echo "Usage: $0 [url] [--push|--dry-run]"
      echo "  url     Target repo (default: $DEFAULT_URL)"
      echo "  --push  Actually run git subtree push (default is dry run)"
      exit 0
      ;;
    *)
      URL="$arg"
      ;;
  esac
done

# Refuse to run on a dirty working tree — subtree push reads from HEAD, and
# uncommitted modifications to tracked files mean what gets pushed may not
# match what's actually reviewed. Untracked files don't matter here (subtree
# push only ever publishes committed history), so they're excluded — otherwise
# an unrelated new scratch file would block even a dry run.
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "✗ Working tree has uncommitted changes to tracked files. Commit or stash before syncing." >&2
  exit 1
fi

# Packaging hygiene: no generated files under skills/carrel. Mirrors
# tests/test_carrel_skill_pack.py::test_carrel_skill_pack_has_no_generated_files.
BANNED="$(find "$PREFIX" \( -name "__pycache__" -o -name "*.pyc" \) 2>/dev/null || true)"
if [[ -n "$BANNED" ]]; then
  echo "✗ Generated files found under $PREFIX — clean before syncing:" >&2
  echo "$BANNED" >&2
  exit 1
fi

echo "→ git subtree push --prefix=$PREFIX $URL $BRANCH"

if [[ "$PUSH" == true ]]; then
  git subtree push --prefix="$PREFIX" "$URL" "$BRANCH"
else
  echo "(dry run — pass --push to actually push)"
fi
