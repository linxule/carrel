from __future__ import annotations

import json
import tomllib
from pathlib import Path

from carrel import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_all_packaged_versions_match() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )

    versions = {
        pyproject["project"]["version"],
        __version__,
        plugin["version"],
        marketplace["plugins"][0]["version"],
    }

    assert len(versions) == 1
