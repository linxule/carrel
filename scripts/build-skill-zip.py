"""Build carrel.zip: the portable skill packaged for Claude.ai / Claude app / Cowork upload.

Claude's skill upload wants the ZIP to contain one folder at its root whose name
matches the skill's name, with SKILL.md inside it. A GitHub "Download ZIP" of
linxule/carrel-skill does not qualify (its folder is ``carrel-skill-main``), so
we build the archive ourselves: ``carrel/SKILL.md``, ``carrel/scripts/...``.

The archive is deterministic (sorted entries, fixed timestamps) so rebuilding an
unchanged skill produces identical bytes.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "carrel"
SKILL_NAME = "carrel"
IGNORED_NAMES = {"__pycache__", ".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def _ignored(relative: Path) -> bool:
    return any(part in IGNORED_NAMES for part in relative.parts) or (
        relative.suffix in IGNORED_SUFFIXES
    )


def build(output: Path) -> Path:
    if not (SOURCE / "SKILL.md").is_file():
        raise SystemExit(f"Canonical skill not found: {SOURCE / 'SKILL.md'}")
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(
        path
        for path in SOURCE.rglob("*")
        if path.is_file() and not _ignored(path.relative_to(SOURCE))
    )
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            arcname = f"{SKILL_NAME}/{path.relative_to(SOURCE).as_posix()}"
            info = zipfile.ZipInfo(arcname, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 if not path.name.endswith(".py") else 0o755) << 16
            archive.writestr(info, path.read_bytes())
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / f"{SKILL_NAME}.zip",
        help="where to write the archive (default: dist/carrel.zip)",
    )
    args = parser.parse_args()
    path = build(args.output)
    print(f"Built {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
