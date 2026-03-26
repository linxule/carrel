from __future__ import annotations

from pathlib import Path

import frontmatter


def render_frontmatter(content: str, metadata: dict) -> str:
    payload = {key: value for key, value in metadata.items() if value is not None}
    post = frontmatter.Post(content, **payload)
    return frontmatter.dumps(post)


def load_frontmatter(path: Path) -> tuple[dict, str]:
    post = frontmatter.load(path)
    return dict(post.metadata), post.content
