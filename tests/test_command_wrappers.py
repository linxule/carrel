"""Structural validation for slash-command files in ``commands/``.

Spec: ``planning/specs/014-cc-plugin-v090.md`` — Section A.3.

The seven commands listed in :data:`WRAPPER_FILES` must conform to the thin
wrapper template defined in ``commands/CONVENTIONS.md``. All command files
must parse as Markdown with YAML frontmatter and carry a ``description``
field.
"""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter
import pytest

COMMANDS_DIR = Path(__file__).resolve().parent.parent / "commands"

# The seven thin wrappers shipping in v0.9.0 (spec 014, A.3).
WRAPPER_FILES = frozenset(
    {
        "carrel-automate.md",
        "carrel-batch.md",
        "carrel-feedback.md",
        "carrel-migrate.md",
        "carrel-mirror.md",
        "carrel-reflect.md",
        "carrel-share.md",
    }
)

# Patterns the wrapper body must not contain.
_FORBIDDEN_BODY_PATTERNS = (
    re.compile(r"\bif\b"),
    re.compile(r"\bcase\b"),
)


def _command_files() -> list[Path]:
    return sorted(p for p in COMMANDS_DIR.glob("*.md") if p.name != "CONVENTIONS.md")


@pytest.mark.parametrize("path", _command_files(), ids=lambda p: p.name)
def test_command_file_structure(path: Path) -> None:
    """Every command file parses as frontmatter Markdown.

    Wrappers in :data:`WRAPPER_FILES` must additionally match the thin
    wrapper template: a single ``!carrel ... ${ARGS}`` body line with no
    conditionals, headers, or prose.
    """
    post = frontmatter.loads(path.read_text(encoding="utf-8"))

    assert "description" in post.metadata, (
        f"{path.name}: missing required `description` frontmatter field"
    )

    if path.name not in WRAPPER_FILES:
        # Full skill-prompts are exempt from the strict template.
        return

    assert "argument-hint" in post.metadata, (
        f"{path.name}: thin wrappers must declare `argument-hint`"
    )

    content_lines = [line for line in post.content.splitlines() if line.strip()]
    assert len(content_lines) == 1, (
        f"{path.name}: wrapper body must be exactly one non-empty line, "
        f"found {len(content_lines)}"
    )

    body = content_lines[0]
    assert body.startswith("!carrel "), (
        f"{path.name}: wrapper body must start with `!carrel `, got: {body!r}"
    )
    assert "${ARGS}" in body, (
        f"{path.name}: wrapper body must contain `${{ARGS}}`, got: {body!r}"
    )
    assert "$ARGUMENTS" not in body, (
        f"{path.name}: wrappers use `${{ARGS}}` (skill-constructed), "
        f"not `$ARGUMENTS` (raw user input)"
    )
    assert not body.lstrip().startswith("#"), (
        f"{path.name}: wrapper body must not contain markdown headers"
    )
    for pattern in _FORBIDDEN_BODY_PATTERNS:
        assert not pattern.search(body), (
            f"{path.name}: wrapper body must not contain conditionals "
            f"(matched {pattern.pattern!r}): {body!r}"
        )
