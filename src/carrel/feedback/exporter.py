"""Anonymized feedback export from reflections, friction logs, and capability logs.

The CLI walks those source locations, applies a redact list, and emits a single
flat ``_meta/feedback-digest-YYYY-MM-DD.md`` file. This module is deterministic: no judgment calls,
no fabrication. Researchers and skills decide what to redact; the CLI just
applies the list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from carrel.errors import CarrelError
from carrel.env.profile import read_profile
from carrel.safe_path import safe_atomic_write, safe_vault_join

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
    redaction_rules: int
    redactions_applied: int
    zero_match_terms: list[str]
    action: str  # "created" | "overwritten"


@dataclass(frozen=True)
class RedactionRule:
    source: str
    replacement: str


def read_redact_list(redact_path: Path) -> list[RedactionRule]:
    """Parse bare terms and ASCII/Unicode source-to-replacement mappings."""

    if not redact_path.exists():
        raise CarrelError(
            f"Redact list not found: {redact_path}",
            hint="Create a text file with one term per line (names, institutions, project codenames).",
        )
    try:
        lines = redact_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise CarrelError(
            f"Could not read redact list: {redact_path}",
            hint="Provide a readable UTF-8 text file.",
        ) from error

    rules: list[RedactionRule] = []
    for line_number, raw_line in enumerate(
        lines,
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        separators = [(line.find(arrow), arrow) for arrow in ("->", "→") if arrow in line]
        if not separators:
            source = line
            replacement = "[REDACTED]"
        else:
            index, separator = min(separators)
            source = line[:index].strip()
            raw_replacement = line[index + len(separator) :].strip()
            if not source:
                raise CarrelError(
                    f"Invalid redaction rule on line {line_number}: empty source",
                    hint="Use `term`, `term -> replacement`, or `term → replacement`.",
                )
            replacement = raw_replacement or "[REDACTED]"
        rules.append(RedactionRule(source=source, replacement=replacement))
    return rules


def _collect_sources(vault: Path) -> list[Path]:
    vault_root = vault.expanduser().resolve()
    sources: list[Path] = []
    for directory_name in (FRICTION_DIR, CAPABILITY_DIR, REFLECTIONS_DIR):
        directory = safe_vault_join(vault_root, "_meta", directory_name)
        if directory.is_dir():
            for source in sorted(directory.rglob("*.md")):
                relative = source.relative_to(vault_root)
                sources.append(safe_vault_join(vault_root, *relative.parts))
    for fallback in (FRICTION_FILE, CAPABILITY_FILE):
        flat = safe_vault_join(vault_root, "_meta", fallback)
        if flat.is_file():
            sources.append(flat)
    return sources


def _normalize_rules(rules: list[RedactionRule]) -> list[RedactionRule]:
    unique: dict[str, RedactionRule] = {}
    for rule in rules:
        unique.setdefault(rule.source.casefold(), rule)
    return sorted(unique.values(), key=lambda rule: -len(rule.source))


def _apply_redactions(
    text: str,
    rules: list[RedactionRule],
) -> tuple[str, dict[str, int]]:
    normalized = _normalize_rules(rules)
    counts = {rule.source: 0 for rule in normalized}
    if not normalized:
        return text, counts

    by_group = {f"rule_{index}": rule for index, rule in enumerate(normalized)}
    pattern = re.compile(
        "|".join(
            f"(?P<{group_name}>{re.escape(rule.source)})"
            for group_name, rule in by_group.items()
        ),
        flags=re.IGNORECASE,
    )

    def replace(match: re.Match[str]) -> str:
        if match.lastgroup is None:  # pragma: no cover - every branch is named
            raise AssertionError("redaction regex matched without a rule branch")
        rule = by_group[match.lastgroup]
        counts[rule.source] += 1
        # A callback keeps backslashes and other replacement characters literal.
        return rule.replacement

    return pattern.sub(replace, text), counts


def render_digest(
    sources: list[Path],
    rules: list[RedactionRule],
    today: str,
) -> tuple[str, dict[str, int]]:
    """Assemble the anonymized digest and return per-rule match counts."""

    header = (
        f"# Feedback Digest — {today}\n\n"
        "Anonymized export of reflection, friction-log, and capability-log entries. "
        "Redaction rules applied literally (case-insensitive). Review before sharing.\n\n"
    )

    normalized = _normalize_rules(rules)
    total_counts = {rule.source: 0 for rule in normalized}
    sections: list[str] = []
    for source in sources:
        try:
            body = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        section = f"## {source.name}\n\n{body.rstrip()}\n"
        redacted, counts = _apply_redactions(section, normalized)
        for rule_source, count in counts.items():
            total_counts[rule_source] += count
        sections.append(redacted.rstrip() + "\n")

    if not sections:
        sections.append("_No reflection, friction-log, or capability-log entries found._\n")

    return header + "\n".join(sections), total_counts


def export_feedback(
    vault: Path,
    redact_list: Path,
    *,
    output_path: Path,
    today: str | None = None,
) -> FeedbackExportResult:
    """Walk friction/capability sources, apply redactions, write the digest."""

    rules = read_redact_list(redact_list)
    profile = read_profile(vault)
    profile_name = profile.name.strip() if profile is not None and profile.name else ""
    if profile_name and all(
        rule.source.casefold() != profile_name.casefold() for rule in rules
    ):
        rules.append(RedactionRule(profile_name, "Researcher"))
    iso_today = today or date.today().isoformat()
    sources = _collect_sources(vault)
    digest, counts = render_digest(sources, rules, iso_today)
    hits = sum(counts.values())
    zero_match_terms = [source for source, count in counts.items() if count == 0]
    existed = output_path.exists()
    safe_atomic_write(vault, output_path, digest)
    return FeedbackExportResult(
        path=output_path,
        sources=sources,
        redacted_terms=hits,
        redaction_rules=len(counts),
        redactions_applied=hits,
        zero_match_terms=zero_match_terms,
        action="overwritten" if existed else "created",
    )
