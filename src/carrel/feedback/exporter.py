"""Anonymized feedback export from reflections, friction logs, and capability logs.

The CLI walks those source locations, applies a redact list, and emits a single
flat ``_meta/feedback-digest-YYYY-MM-DD.md`` file. This module is deterministic: no judgment calls,
no fabrication. Researchers and skills decide what to redact; the CLI just
applies the list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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

# The fixed structural sweep-dir names (derived from the sweep list above, not
# hardcoded twice). Their `_meta/<dir>/` prefix is never redacted — it is fixed
# carrel vocabulary, never sensitive — while every user-named path segment below
# it and the basename are redacted, so a project codename can't leak through a
# nested directory name in a shareable digest.
SWEEP_DIRS = frozenset({FRICTION_DIR, CAPABILITY_DIR, REFLECTIONS_DIR})


@dataclass(frozen=True)
class FeedbackExportResult:
    path: Path
    sources: list[Path]
    redacted_terms: int
    redaction_rules: int
    redactions_applied: int
    zero_match_terms: list[str]
    action: str  # "created" | "overwritten"
    # Sources that were swept but could not be read (OSError/UnicodeDecodeError).
    # They are excluded from `sources` (and therefore from every count) so the
    # digest never claims to cover a file it silently dropped.
    skipped: list[Path] = field(default_factory=list)


@dataclass(frozen=True)
class RedactionRule:
    source: str
    replacement: str
    # Auto-injected rules (e.g. the profile name) match whole words only so a
    # short name like "Ann" cannot corrupt "annual"/"planning". User-supplied
    # rules keep their pre-existing, opt-in substring semantics.
    word_boundary: bool = False


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


def _rule_pattern(rule: RedactionRule) -> str:
    escaped = re.escape(rule.source)
    return rf"\b{escaped}\b" if rule.word_boundary else escaped


def _split_structural_prefix(rel: Path) -> tuple[str, str]:
    """Split a vault-relative source path into (structural prefix, redactable tail).

    The structural prefix is ``_meta`` plus the fixed sweep-dir name when the
    source lives under one; everything below it (user-named subdirectories and
    the basename) is the redactable tail. Both are POSIX strings; the tail is
    always non-empty (a source always has a basename).
    """

    parts = rel.parts
    prefix_len = 1  # "_meta"
    if len(parts) > 2 and parts[1] in SWEEP_DIRS:
        prefix_len = 2
    return "/".join(parts[:prefix_len]), "/".join(parts[prefix_len:])


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
            f"(?P<{group_name}>{_rule_pattern(rule)})"
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
    vault_root: Path,
) -> tuple[str, dict[str, int], list[Path], list[Path]]:
    """Assemble the anonymized digest.

    Returns the digest text, per-rule match counts, the sources actually read,
    and the sources skipped because they could not be read. Section headings use
    the vault-relative path so same-basename files in different ``_meta``
    subdirectories stay distinct. Redaction applies to the redactable tail
    (user-named subdirectories + basename) and the body, but never to the fixed
    structural prefix (``_meta/<sweep-dir>/``): a rule cannot eat characters
    inside a fixed path component (e.g. an "i" rule inside ".../reflections/"),
    yet a project codename in a user-named nested directory is still redacted.
    """

    header = (
        f"# Feedback Digest — {today}\n\n"
        "Anonymized export of reflection, friction-log, and capability-log entries. "
        "Redaction rules applied literally (case-insensitive). Review before sharing.\n\n"
    )

    normalized = _normalize_rules(rules)
    total_counts = {rule.source: 0 for rule in normalized}
    sections: list[str] = []
    read_sources: list[Path] = []
    skipped: list[Path] = []
    for source in sources:
        try:
            body = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped.append(source)
            continue
        read_sources.append(source)
        # Redact the redactable tail (user-named subdirs + basename) and the
        # body, but never the fixed structural prefix (`_meta/<sweep-dir>/`): a
        # rule must not eat characters inside a fixed path component (an "i" rule
        # inside ".../reflections/"), yet a project codename in a user-named
        # nested directory must still be redacted, not leaked.
        prefix, tail = _split_structural_prefix(source.relative_to(vault_root))
        redacted_tail, tail_counts = _apply_redactions(tail, normalized)
        redacted_body, body_counts = _apply_redactions(body.rstrip(), normalized)
        for rule_source in total_counts:
            total_counts[rule_source] += tail_counts[rule_source] + body_counts[rule_source]
        sections.append(f"## {prefix}/{redacted_tail}\n\n{redacted_body}".rstrip() + "\n")

    if not sections:
        sections.append("_No reflection, friction-log, or capability-log entries found._\n")

    return header + "\n".join(sections), total_counts, read_sources, skipped


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
        rules.append(RedactionRule(profile_name, "Researcher", word_boundary=True))
    iso_today = today or date.today().isoformat()
    vault_root = vault.expanduser().resolve()
    sources = _collect_sources(vault)
    digest, counts, read_sources, skipped = render_digest(
        sources, rules, iso_today, vault_root
    )
    hits = sum(counts.values())
    zero_match_terms = [source for source, count in counts.items() if count == 0]
    existed = output_path.exists()
    safe_atomic_write(vault, output_path, digest)
    return FeedbackExportResult(
        path=output_path,
        sources=read_sources,
        redacted_terms=hits,
        redaction_rules=len(counts),
        redactions_applied=hits,
        zero_match_terms=zero_match_terms,
        action="overwritten" if existed else "created",
        skipped=skipped,
    )
