"""HTML-comment markers for profile-state mirrors in vault CLAUDE.md.

Markers look like: <!-- carrel:FIELD -->VALUE<!-- /carrel:FIELD -->
Parsers use a simple regex. Writers update in-place, preserving surrounding content.
"""

import re

MARKER_FIELDS = [
    "sensitivity",
    "cloud_consent",
    "trust_level",
    "tools_configured",
    "wiki_enabled",
]


def parse_markers(text: str) -> dict[str, str]:
    """Return {field: value} for all carrel markers found in text."""
    pattern = re.compile(
        r"<!-- carrel:(?P<field>\w+) -->(?P<value>.*?)<!-- /carrel:\1 -->",
        re.DOTALL,
    )
    return {m.group("field"): m.group("value").strip() for m in pattern.finditer(text)}


def update_marker(text: str, field: str, value: str) -> str:
    """Update a single marker in-place. Raises if marker doesn't exist."""
    pattern = re.compile(
        rf"(<!-- carrel:{re.escape(field)} -->).*?(<!-- /carrel:{re.escape(field)} -->)",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise ValueError(f"Marker '{field}' not found in text")
    return pattern.sub(rf"\g<1>{value}\g<2>", text)


def ensure_markers(text: str, values: dict[str, str]) -> str:
    """Append missing markers to the end of the text. Idempotent."""
    existing = parse_markers(text)
    additions = []
    for field, value in values.items():
        if field not in existing:
            additions.append(f"<!-- carrel:{field} -->{value}<!-- /carrel:{field} -->")
    if not additions:
        return text
    return text.rstrip() + "\n\n" + "\n".join(additions) + "\n"
