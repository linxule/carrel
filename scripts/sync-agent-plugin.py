"""Copy the canonical portable skill into the installable Agent Plugin package."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "carrel"
DESTINATION = ROOT / "plugins" / "carrel" / "skills" / "carrel"


def files_at(path: Path) -> dict[str, bytes]:
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in path.rglob("*")
        if item.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the published plugin copy differs from skills/carrel",
    )
    args = parser.parse_args()

    if not SOURCE.is_dir():
        print(f"Canonical skill source not found: {SOURCE}", file=sys.stderr)
        return 1

    if args.check:
        if not DESTINATION.is_dir() or files_at(SOURCE) != files_at(DESTINATION):
            print(
                "Agent Plugin skill copy is stale; run "
                "python scripts/sync-agent-plugin.py",
                file=sys.stderr,
            )
            return 1
        print("Agent Plugin skill copy is up to date.")
        return 0

    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    shutil.copytree(SOURCE, DESTINATION)
    print(f"Copied {SOURCE.relative_to(ROOT)} to {DESTINATION.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
