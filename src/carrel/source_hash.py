from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse


def hash_source(source: str | Path) -> str:
    if isinstance(source, Path):
        payload = source.read_bytes()
    else:
        parsed = urlparse(source)
        if parsed.scheme and parsed.netloc:
            payload = source.encode("utf-8")
        else:
            payload = Path(source).read_bytes()
    return hashlib.sha256(payload).hexdigest()
