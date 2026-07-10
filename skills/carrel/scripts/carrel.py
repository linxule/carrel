#!/usr/bin/env python3
from __future__ import annotations

import sys

if sys.version_info < (3, 10):
    sys.stderr.write(
        "Error: carrel requires Python 3.10 or newer; found "
        + sys.version.split()[0]
        + ". Install Python 3.10+ and re-run.\n"
    )
    sys.exit(2)
else:
    sys.dont_write_bytecode = True

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from carrel_core.runtime import main


if __name__ == "__main__":
    raise SystemExit(main())
