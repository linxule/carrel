"""Deterministic redaction rules for the feedback digest (portable runtime).

A redaction is ``(term, replacement, word_boundary)``. ``word_boundary`` is set
only on auto-injected rules (the profile name) so a short name like "Ann" matches
whole words and cannot corrupt "annual"/"planning"; user-supplied rules keep their
pre-existing, opt-in substring semantics (``word_boundary=False``).

Mirrors the typed exporter in ``src/carrel/feedback/exporter.py`` — the two must
agree on rule grammar, normalization, and match counts (see the runtime-parity
suite).
"""

from __future__ import annotations

import re
from pathlib import Path

from .core import CarrelError


def read_redactions(path: Path) -> list[tuple[str, str, bool]]:
    if not path.exists():
        raise CarrelError("Redact list not found", hint=str(path))
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise CarrelError("Could not read redact list", hint="Provide a readable UTF-8 file") from exc
    redactions: list[tuple[str, str, bool]] = []
    for line_number, line in enumerate(lines, start=1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        arrows = [(value.find(arrow), arrow) for arrow in ("->", "→") if arrow in value]
        if arrows:
            index, arrow = min(arrows)
            source = value[:index].strip()
            replacement = value[index + len(arrow) :].strip()
            if not source:
                raise CarrelError(
                    "Invalid redact list",
                    hint=f"Line {line_number}: mapping source must not be empty",
                )
            redactions.append((source, replacement or "[REDACTED]", False))
        else:
            redactions.append((value, "[REDACTED]", False))
    return redactions


def normalize_redactions(redactions: list[tuple[str, str, bool]]) -> list[tuple[str, str, bool]]:
    unique: dict[str, tuple[str, str, bool]] = {}
    for term, replacement, word_boundary in redactions:
        unique.setdefault(term.casefold(), (term, replacement, word_boundary))
    return sorted(unique.values(), key=lambda item: -len(item[0]))


def apply_redactions(text: str, redactions: list[tuple[str, str, bool]]) -> tuple[str, dict[str, int]]:
    normalized = normalize_redactions(redactions)
    counts = {term: 0 for term, _, _ in normalized}
    if not normalized:
        return text, counts
    by_group = {
        f"rule_{index}": (term, replacement)
        for index, (term, replacement, _word_boundary) in enumerate(normalized)
    }
    pattern = re.compile(
        "|".join(
            f"(?P<rule_{index}>" + (rf"\b{re.escape(term)}\b" if wb else re.escape(term)) + ")"
            for index, (term, _replacement, wb) in enumerate(normalized)
        ),
        flags=re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        if match.lastgroup is None:  # pragma: no cover - every branch is named
            raise AssertionError("redaction regex matched without a rule branch")
        term, replacement = by_group[match.lastgroup]
        counts[term] += 1
        return replacement

    return pattern.sub(replace, text), counts
