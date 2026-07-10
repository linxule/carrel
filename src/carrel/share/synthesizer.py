"""Vault handbook synthesizer for a collaborator.

Skill orchestrates the conversation (who, what role, what access). This module
takes the resolved parameters and walks the vault deterministically to produce
a dated handbook under ``_meta/handbook/``. Sensitivity drives redaction depth:

- ``low``: include researcher name, vault layout, friction log excerpts verbatim
- ``medium``: include researcher name + layout; truncate friction-log excerpts to
  a fixed length cap; drop notes/threads file contents (keep titles only). NOTE:
  MEDIUM does not detect or redact project codenames — that is content-level
  judgment left to the skill/researcher (see future work below).
- ``high``: omit researcher name (use "Researcher"), omit friction-log details,
  drop notes/threads section entirely

The skill explains the redaction depth before the file is produced; the CLI
just applies the rules so the output is reproducible.

Future work: automatic project-codename redaction at MEDIUM would require a
judgment-heavy detector (which strings are codenames vs. ordinary nouns); it is
intentionally not implemented here and belongs in the skill layer if added.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from carrel.env.profile import read_profile
from carrel.errors import CarrelError
from carrel.models import ResearcherProfile, Sensitivity
from carrel.safe_path import safe_atomic_write

QUICK_MODE = "quick"
FULL_MODE = "full"
VALID_MODES = {QUICK_MODE, FULL_MODE}


@dataclass(frozen=True)
class HandbookResult:
    path: Path
    mode: str
    sensitivity: Sensitivity
    action: str  # "created" | "overwritten"
    redactions_applied: list[str]


def slug_name(name: str) -> str:
    if not name or not name.strip():
        raise CarrelError(
            "Collaborator name is required",
            hint="Pass --for <name> (e.g., --for jane or --for 'new ra').",
        )
    if ".." in name or "/" in name or "\\" in name:
        raise CarrelError(
            "Invalid collaborator name",
            hint="Use letters/numbers/spaces only. Names with path separators are rejected.",
        )
    # Transliterate accented characters before stripping non-ASCII so "José"
    # decomposes to "jose" rather than colliding with a literal "Jos".
    decomposed = unicodedata.normalize("NFKD", name.strip())
    slug = decomposed.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise CarrelError(
            "Collaborator name has no usable characters",
            hint="Pass --for <name> with at least one letter or digit.",
        )
    return slug


def validate_mode(mode: str) -> None:
    if mode not in VALID_MODES:
        raise CarrelError(
            f"Unknown share mode: {mode}",
            hint=f"Use --mode {QUICK_MODE} or --mode {FULL_MODE}.",
        )


def _read_optional_text(path: Path, *, max_chars: int | None = None) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        body = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if max_chars is not None and len(body) > max_chars:
        return body[:max_chars].rstrip() + "\n\n_(truncated)_\n"
    return body


def _researcher_label(profile: ResearcherProfile | None, sensitivity: Sensitivity) -> str:
    if sensitivity == Sensitivity.HIGH:
        return "Researcher"
    if profile and profile.name:
        return profile.name
    return "Researcher"


def _field_label(profile: ResearcherProfile | None, sensitivity: Sensitivity) -> str | None:
    if sensitivity == Sensitivity.HIGH:
        return None
    if profile and profile.field:
        return profile.field
    return None


def _vault_layout(vault: Path) -> list[str]:
    folders = [
        "papers",
        "notes",
        "transcripts",
        "inbox",
        "drafts",
        "talks",
        "admin",
        "wiki",
        "_meta",
    ]
    present = [f"{name}/" for name in folders if (vault / name).is_dir()]
    return present


def _redact_friction_excerpts(text: str, sensitivity: Sensitivity) -> str:
    """Trim friction-log excerpts at higher sensitivity levels.

    This is a length cap only — it does not inspect or redact codenames or any
    other content. HIGH omits the section entirely upstream, so it never reaches
    here.
    """

    if sensitivity == Sensitivity.LOW:
        return text
    # MEDIUM: keep first ~400 chars; HIGH never reaches here (section omitted).
    cap = 400 if sensitivity == Sensitivity.MEDIUM else 0
    if cap and len(text) > cap:
        return text[:cap].rstrip() + "\n\n_(excerpt truncated for sensitivity)_\n"
    return text


def synthesize_handbook(
    vault: Path,
    *,
    mode: str,
    name: str,
    sensitivity: Sensitivity,
    today: str | None = None,
) -> tuple[str, list[str]]:
    """Build the handbook markdown plus a list of redactions actually applied."""

    validate_mode(mode)
    iso_today = today or date.today().isoformat()
    profile = read_profile(vault)

    researcher = _researcher_label(profile, sensitivity)
    field = _field_label(profile, sensitivity)
    redactions: list[str] = []

    lines: list[str] = []
    lines.append(f"# Handbook for {name} — {iso_today}")
    lines.append("")
    lines.append(
        f"Vault-specific onboarding. Generated at sensitivity={sensitivity.value}, mode={mode}."
    )
    lines.append("")

    # About-this-vault
    lines.append("## About this vault")
    if field:
        lines.append(f"- Researcher: **{researcher}**")
        lines.append(f"- Field: {field}")
    else:
        lines.append(f"- Researcher: **{researcher}**")
        redactions.append("researcher-field-omitted")
    if profile is not None:
        lines.append(f"- Sensitivity setting: {profile.sensitivity.value}")
        lines.append(f"- Cloud consent: {'on' if profile.cloud_consent else 'off'}")
    lines.append("")

    # Vault layout
    lines.append("## Vault layout")
    layout = _vault_layout(vault)
    if layout:
        for folder in layout:
            lines.append(f"- {folder}")
    else:
        lines.append("- (vault is empty — no top-level folders detected)")
    lines.append("")

    # Tool defaults
    lines.append("## Tools available")
    if profile and profile.tools_configured:
        for tool, enabled in sorted(profile.tools_configured.items()):
            lines.append(f"- {tool}: {'configured' if enabled else 'not configured'}")
    else:
        lines.append("- (no tools_configured entries in environment.json)")
    lines.append("")

    if mode == FULL_MODE:
        # Friction log
        if sensitivity != Sensitivity.HIGH:
            lines.append("## Friction & workarounds")
            friction_dir = vault / "_meta" / "friction-log"
            friction_file = vault / "_meta" / "friction_log.md"
            friction_text = None
            if friction_dir.is_dir():
                pieces: list[str] = []
                for entry in sorted(friction_dir.rglob("*.md")):
                    body = _read_optional_text(entry)
                    if body:
                        pieces.append(f"### {entry.name}\n\n{body.rstrip()}")
                friction_text = "\n\n".join(pieces) if pieces else None
            elif friction_file.is_file():
                friction_text = _read_optional_text(friction_file)
            if friction_text:
                lines.append(_redact_friction_excerpts(friction_text, sensitivity))
            else:
                lines.append("_No friction recorded yet._")
            lines.append("")
        else:
            redactions.append("friction-log-omitted")

        # Notes / threads (titles only at MEDIUM, omitted at HIGH)
        threads_dir = vault / "notes" / "threads"
        if sensitivity == Sensitivity.LOW and threads_dir.is_dir():
            lines.append("## Active threads")
            for thread in sorted(threads_dir.rglob("*.md")):
                body = _read_optional_text(thread, max_chars=600)
                if body:
                    lines.append(f"### {thread.relative_to(vault)}\n\n{body.rstrip()}")
            lines.append("")
        elif sensitivity == Sensitivity.MEDIUM and threads_dir.is_dir():
            lines.append("## Active threads (titles only)")
            for thread in sorted(threads_dir.rglob("*.md")):
                lines.append(f"- {thread.relative_to(vault)}")
            lines.append("")
            redactions.append("threads-contents-omitted")
        elif sensitivity == Sensitivity.HIGH:
            redactions.append("threads-section-omitted")

    # Where to start
    lines.append("## Where to start")
    lines.append("- Read this handbook end-to-end before touching files.")
    lines.append("- Ask before changing files outside `inbox/`.")
    if profile and profile.sensitivity == Sensitivity.HIGH:
        lines.append("- This vault is HIGH-sensitivity: never run cloud-routing tools.")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n", redactions


def write_handbook(
    vault: Path,
    *,
    mode: str,
    name: str,
    sensitivity: Sensitivity,
    output_path: Path,
    today: str | None = None,
) -> HandbookResult:
    body, redactions = synthesize_handbook(
        vault, mode=mode, name=name, sensitivity=sensitivity, today=today
    )
    existed = output_path.exists()
    safe_atomic_write(vault, output_path, body)
    return HandbookResult(
        path=output_path,
        mode=mode,
        sensitivity=sensitivity,
        action="overwritten" if existed else "created",
        redactions_applied=redactions,
    )
