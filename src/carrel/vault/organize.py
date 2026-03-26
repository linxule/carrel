from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}
TRANSCRIPT_MEDIA_EXTENSIONS = {
    ".aac",
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".mov",
    ".ogg",
    ".wav",
    ".webm",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "untitled"


def _author_slug(authors: str) -> str:
    parts = re.split(r"\s*(?:,|;| and | & )\s*", authors.strip())
    last_names = []
    for part in parts:
        if not part:
            continue
        tokens = [token for token in re.split(r"\s+", part) if token]
        if tokens:
            last_names.append(slugify(tokens[-1]))
    if not last_names:
        return "unknown"
    return "-".join(last_names[:2])


def _short_title_slug(title: str, max_words: int = 3) -> str:
    words = [slugify(word) for word in re.split(r"\s+", title) if slugify(word)]
    filtered = [word for word in words if word not in STOPWORDS]
    chosen = filtered[:max_words] or words[:max_words]
    return "-".join(chosen) if chosen else "untitled"


def paper_dirname(
    authors: str | None,
    year: str | None,
    title: str | None,
    source_filename: str | None = None,
) -> str:
    if authors and year:
        return f"{_author_slug(authors)}-{slugify(year)}"
    if authors and title:
        return f"{_author_slug(authors)}-{_short_title_slug(title)}"
    if title:
        return slugify(title)
    if source_filename:
        return slugify(Path(source_filename).stem)
    return "untitled-paper"


def _youtube_slug(source: str) -> str:
    parsed = urlparse(source)
    query = parse_qs(parsed.query)
    if "v" in query and query["v"]:
        return slugify(query["v"][0])
    path_bits = [bit for bit in parsed.path.split("/") if bit]
    if path_bits:
        return slugify(path_bits[-1])
    return "video"


def transcript_filename(
    source: str,
    date: str,
    kind: str = "recording",
    title: str | None = None,
) -> str:
    parsed = urlparse(source)
    is_url = bool(parsed.scheme and parsed.netloc)
    if is_url:
        base = slugify(title) if title else f"youtube-{_youtube_slug(source)}"
        return f"{base}-{date}.md"

    source_stem = slugify(Path(source).stem)
    base = slugify(title) if title else source_stem
    prefix = slugify(kind or "recording")

    if prefix == "recording":
        if base.startswith("recording-"):
            return f"{base}-{date}.md"
        return f"recording-{base}-{date}.md"

    if base == prefix or base.startswith(f"{prefix}-"):
        return f"{base}-{date}.md"
    return f"{prefix}-{base}-{date}.md"


def sort_inbox(vault: Path) -> list[dict]:
    inbox = vault / "inbox"
    if not inbox.exists():
        return []

    suggestions: list[dict] = []
    for item in sorted(path for path in inbox.iterdir() if path.is_file()):
        suffix = item.suffix.lower()
        if suffix == ".pdf":
            destination = vault / "papers" / paper_dirname(None, None, item.stem, item.name) / "paper.md"
            reason = "paper conversion target"
        elif suffix in TRANSCRIPT_MEDIA_EXTENSIONS:
            destination = vault / "transcripts" / transcript_filename(item.name, "YYYY-MM-DD")
            reason = "transcript target"
        elif suffix in {".md", ".txt"}:
            destination = vault / "notes" / f"{slugify(item.stem)}.md"
            reason = "note target"
        else:
            destination = vault / "notes" / f"{slugify(item.stem)}{suffix}"
            reason = "general filing target"
        suggestions.append(
            {"source": str(item), "destination": str(destination), "reason": reason}
        )
    return suggestions
