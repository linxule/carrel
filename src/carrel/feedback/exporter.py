"""Anonymized feedback export from friction-log + capability-log.

The CLI walks the two log directories, applies a redact list (one term per
line) plus structural anonymization, and emits a single dated digest under
``_meta/feedback-export/``. This module is deterministic: no judgment calls,
no fabrication. Researchers and skills decide what to redact; the CLI just
applies the list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from carrel.errors import CarrelError

# Three source directories we sweep. Any may be absent.
# `reflections/` is included because session-reflection writes there;
# the digest is the read-side of the same surface (skill→CLI symmetry).
FRICTION_DIR = "friction-log"
CAPABILITY_DIR = "capability-log"
REFLECTIONS_DIR = "reflections"

# Single-file fallbacks (older vaults keep these as flat files).
FRICTION_FILE = "friction_log.md"
CAPABILITY_FILE = "capability-log.md"


@dataclass(frozen=True)
class FeedbackExportResult:
    path: Path
    sources: list[Path]
    redacted_terms: int
    action: str  # "created" | "overwritten"


def read_redact_list(redact_path: Path) -> list[str]:
    """Parse a redact list (one term per line, blank lines + '#' comments ignored)."""

    if not redact_path.exists():
        raise CarrelError(
            f"Redact list not found: {redact_path}",
            hint="Create a text file with one term per line (names, institutions, project codenames).",
        )
    terms: list[str] = []
    for raw_line in redact_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        terms.append(line)
    return terms


def _collect_sources(vault_meta: Path) -> list[Path]:
    sources: list[Path] = []
    for directory_name in (FRICTION_DIR, CAPABILITY_DIR, REFLECTIONS_DIR):
        directory = vault_meta / directory_name
        if directory.is_dir():
            sources.extend(sorted(directory.rglob("*.md")))
    for fallback in (FRICTION_FILE, CAPABILITY_FILE):
        flat = vault_meta / fallback
        if flat.is_file():
            sources.append(flat)
    return sources


def _apply_redactions(text: str, terms: list[str]) -> str:
    redacted = text
    # Longest terms first so 'Acme Corp' is redacted before 'Acme'.
    for term in sorted(set(terms), key=len, reverse=True):
        if not term:
            continue
        redacted = re.sub(re.escape(term), "[REDACTED]", redacted, flags=re.IGNORECASE)
    return redacted


def render_digest(sources: list[Path], terms: list[str], today: str) -> tuple[str, int]:
    """Assemble the anonymized digest. Returns (markdown, total redacted-term hits)."""

    header = (
        f"# Feedback Digest — {today}\n\n"
        "Anonymized export of friction-log + capability-log entries. "
        "Redact list applied verbatim (case-insensitive). Review before sharing.\n\n"
    )

    total_hits = 0
    sections: list[str] = []
    for source in sources:
        try:
            body = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        redacted = _apply_redactions(body, terms)
        # Count redactions per source (lower bound: re-count [REDACTED] occurrences).
        total_hits += redacted.count("[REDACTED]") - body.count("[REDACTED]")
        sections.append(f"## {source.name}\n\n{redacted.rstrip()}\n")

    if not sections:
        sections.append("_No friction-log or capability-log entries found._\n")

    return header + "\n".join(sections), max(total_hits, 0)


def export_feedback(
    vault: Path,
    redact_list: Path,
    *,
    output_path: Path,
    today: str | None = None,
) -> FeedbackExportResult:
    """Walk friction/capability sources, apply redactions, write the digest."""

    terms = read_redact_list(redact_list)
    iso_today = today or date.today().isoformat()
    sources = _collect_sources(vault / "_meta")
    digest, hits = render_digest(sources, terms, iso_today)
    existed = output_path.exists()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.parent / f"{output_path.name}.tmp"
    tmp.write_text(digest, encoding="utf-8")
    tmp.replace(output_path)
    return FeedbackExportResult(
        path=output_path,
        sources=sources,
        redacted_terms=hits,
        action="overwritten" if existed else "created",
    )
