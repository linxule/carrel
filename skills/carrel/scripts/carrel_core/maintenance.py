from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

from .constants import TRUST_ACTIONS
from .core import (
    CarrelError,
    assert_safe_write_target,
    current_trust,
    read_profile,
    require_asset,
    require_profile,
    safe_atomic_write,
    safe_read_text,
    safe_vault_join,
    trust_allowed,
    write_profile,
)
from .redaction import apply_redactions, normalize_redactions, read_redactions
from .vault_setup import normalize_profile

AUTOMATION_CAPABILITIES = {
    "inbox_processing": (
        "Inbox processing",
        "Process new inbox items conservatively; defer judgment calls to `_meta/pending-decisions.md`.",
    ),
    "vault_health": (
        "Vault health",
        "Check for broken links, orphaned notes, and stale drafts before writing the morning brief.",
    ),
    "cross_linking_suggestions": (
        "Cross-linking suggestions",
        "Surface high-confidence links between recent notes and write them to `_meta/suggestions/`.",
    ),
    "gap_analysis": ("Gap analysis", "Flag gaps as suggestions, not conclusions."),
    "draft_feedback": ("Draft feedback", "Give structural feedback without rewriting the researcher's voice."),
    "reflection_synthesis": ("Reflection synthesis", "Synthesize reflections when enough new material exists."),
    "wiki_maintenance": ("Wiki maintenance", "Maintain the field map and log every change in the brief."),
}
AUTOMATION_TRUST_RULES = {
    "advisory": (
        "Never modify research content. Write only operational suggestions and briefs under `_meta/`."
    ),
    "consultative": "Write suggestions and proposed actions, but never execute them without approval.",
    "delegated": "You may file new items following the vault conventions. Never reorganize existing files.",
    "partnership": (
        "You may file new items and reorganize existing files within the vault epistemology. "
        "Log every action with revert instructions."
    ),
}
def cmd_reflection_append(args) -> int:
    body = sys.stdin.read().rstrip()
    if not body:
        raise CarrelError("Empty reflection body received on stdin")
    target = safe_vault_join(args.vault, "_meta", "reflections", f"reflection-{date.today().isoformat()}.md")
    existed = target.exists()
    previous = safe_read_text(args.vault, target, encoding="utf-8") if target.exists() else f"# Reflection - {date.today().isoformat()}\n"
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    safe_atomic_write(args.vault, target, f"{previous.rstrip()}\n\n## {stamp}\n\n{body}\n")
    print(json.dumps({"path": str(target), "action": "appended" if existed else "created"}))
    return 0

def cmd_mirror_write(args) -> int:
    body = sys.stdin.read()
    if not body.strip():
        raise CarrelError("Empty mirror body received on stdin")
    target = safe_vault_join(args.vault, "_meta", "mirror", f"{date.today().strftime('%Y-%m')}.md")
    existed = target.exists()
    new_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if target.exists() and hashlib.sha256(safe_read_text(args.vault, target, encoding="utf-8").encode("utf-8")).hexdigest() == new_hash and not args.force:
        print(json.dumps({"path": str(target), "action": "skipped"}))
        return 0
    safe_atomic_write(args.vault, target, body)
    print(json.dumps({"path": str(target), "action": "updated" if existed else "created"}))
    return 0

# Fixed structural sweep-dir names, used both to sweep and to compute the
# never-redacted heading prefix (don't hardcode the list twice).
FEEDBACK_SWEEP_DIRS = ["friction-log", "capability-log", "reflections"]


def _feedback_structural_prefix(rel: Path) -> tuple[str, str]:
    """(structural prefix, redactable tail) — mirrors exporter._split_structural_prefix.

    ``_meta`` plus the fixed sweep-dir name (when present) is never redacted;
    user-named subdirectories and the basename are the redactable tail.
    """

    parts = rel.parts
    prefix_len = 1  # "_meta"
    if len(parts) > 2 and parts[1] in FEEDBACK_SWEEP_DIRS:
        prefix_len = 2
    return "/".join(parts[:prefix_len]), "/".join(parts[prefix_len:])


def cmd_feedback_export(args) -> int:
    terms = read_redactions(args.redact_list)
    profile = read_profile(args.vault)
    researcher_name = profile.get("name")
    if (
        isinstance(researcher_name, str)
        and researcher_name.strip()
        and not any(term.casefold() == researcher_name.strip().casefold() for term, _, _ in terms)
    ):
        terms.append((researcher_name.strip(), "Researcher", True))  # whole-word auto rule
    terms = normalize_redactions(terms)
    vault_root = args.vault.expanduser().resolve()
    candidates = []
    for folder in FEEDBACK_SWEEP_DIRS:
        folder_path = safe_vault_join(args.vault, "_meta", folder)
        if folder_path.is_dir():
            candidates.extend(sorted(folder_path.glob("*.md")))
    for flat in ["friction_log.md", "capability-log.md"]:
        flat_path = safe_vault_join(args.vault, "_meta", flat)
        if flat_path.is_file():
            candidates.append(flat_path)
    parts = [f"# Feedback Digest - {date.today().isoformat()}\n"]
    total_counts: dict[str, int] = {term: 0 for term, _, _ in terms}
    sources = []
    unreadable = []  # dropped from the digest and every count, not silently covered
    for source in candidates:
        try:
            body = safe_read_text(args.vault, source, encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            unreadable.append(source)
            continue
        sources.append(source)
        # Redact the tail (user-named subdirs + basename) and body, never the
        # fixed structural prefix (`_meta/<sweep-dir>/`): a rule must not eat
        # characters inside a fixed component, yet a codename in a user-named
        # nested dir must still be redacted, not leaked.
        prefix, tail = _feedback_structural_prefix(source.relative_to(vault_root))
        redacted_tail, tail_counts = apply_redactions(tail, terms)
        redacted_body, body_counts = apply_redactions(body.rstrip(), terms)
        section = f"## {prefix}/{redacted_tail}\n\n{redacted_body}".rstrip()
        parts.append(f"\n{section}\n")
        for counts in (tail_counts, body_counts):
            for term, count in counts.items():
                total_counts[term] = total_counts.get(term, 0) + count
    zero_match_terms = [term for term, count in total_counts.items() if count == 0]
    target = safe_vault_join(args.vault, "_meta", f"feedback-digest-{date.today().isoformat()}.md")
    safe_atomic_write(args.vault, target, "\n".join(parts).rstrip() + "\n")
    print(
        json.dumps(
            {
                "path": str(target),
                "sources": [str(path) for path in sources],
                "unreadable_sources": [str(path) for path in unreadable],
                "redacted_terms": sum(total_counts.values()),
                "redaction_rules": len(terms),
                "redactions_applied": sum(total_counts.values()),
                "zero_match_terms": zero_match_terms,
            }
        )
    )
    return 0


def collaborator_slug(name: str) -> str:
    if not name or not name.strip():
        raise CarrelError("Collaborator name is required")
    if ".." in name or "/" in name or "\\" in name:
        raise CarrelError("Invalid collaborator name")
    # NFKD-transliterate accents before stripping so "José" -> "jose", not "Jos".
    decomposed = unicodedata.normalize("NFKD", name.strip())
    slug = decomposed.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise CarrelError("Collaborator name has no usable characters")
    return slug


def cmd_share_generate(args) -> int:
    name_slug = collaborator_slug(args.name)
    redactions: list[str] = []
    if args.from_stdin:
        rendered = sys.stdin.read()
        if not rendered.strip():
            raise CarrelError("Empty collaborator handbook received on stdin")
    else:
        profile = read_profile(args.vault)
        if args.sensitivity == "high":
            researcher = "Researcher details omitted for high sensitivity."
            redactions.extend(["researcher-field-omitted", "threads-section-omitted"])
        else:
            researcher = f"Researcher: {profile.get('name') or 'Researcher'}\nField: {profile.get('field') or 'unspecified'}"
        body = [
            f"# Collaborator Handbook for {args.name}",
            "",
            researcher,
            "",
            "## Vault Layout",
            "- papers/",
            "- notes/",
            "- transcripts/",
            "- _meta/",
        ]
        if args.mode == "full" and args.sensitivity != "high":
            friction = []
            for source in [
                safe_vault_join(args.vault, "_meta", "friction_log.md"),
                *sorted(safe_vault_join(args.vault, "_meta", "friction-log").glob("*.md")),
            ]:
                if source.is_file():
                    text = safe_read_text(args.vault, source, encoding="utf-8")
                    friction.append(text[:400].rstrip())
            if friction:
                body.extend(["", "## Friction & Workarounds"])
                body.extend(friction)
                if args.sensitivity == "medium":
                    redactions.append("friction-excerpt-truncated")
        elif args.mode == "full":
            redactions.append("friction-log-omitted")
        if args.sensitivity != "high":
            threads = sorted(safe_vault_join(args.vault, "notes", "threads").glob("*.md"))
            if threads:
                body.extend(["", "## Active Threads"])
                for thread in threads:
                    body.append(f"- {thread.name}")
            if args.sensitivity == "medium":
                redactions.append("threads-contents-omitted")
        rendered = "\n".join(body).rstrip() + "\n"
    target = safe_vault_join(
        args.vault,
        "_meta",
        "handbook",
        f"{date.today().isoformat()}-for-{name_slug}.md",
    )
    canonical = safe_vault_join(args.vault, "_meta", "lab-handbook.md") if args.canonical else None
    assert_safe_write_target(args.vault, target)
    if canonical is not None:
        assert_safe_write_target(args.vault, canonical)
    safe_atomic_write(args.vault, target, rendered)
    canonical_path = None
    if canonical is not None:
        safe_atomic_write(args.vault, canonical, rendered)
        canonical_path = str(canonical)
    print(json.dumps({"path": str(target), "canonical_path": canonical_path, "sensitivity": args.sensitivity, "redactions_applied": redactions}))
    return 0


def cmd_trust_check(args) -> int:
    trust = args.trust_level or current_trust(args.vault)
    required, allowed = trust_allowed(args.action, trust)
    payload = {
        "action": args.action,
        "required_trust": required,
        "trust_level": trust,
        "allowed": allowed,
    }
    if args.format == "json":
        print(json.dumps(payload))
    elif allowed:
        print(f"allowed: {args.action}")
    else:
        print(f"Action '{args.action}' requires trust level '{required}'; current is '{trust}'", file=sys.stderr)
    return 0 if allowed else 1


def cmd_trust_list(args) -> int:
    trust = args.trust_level or current_trust(args.vault)
    payload = {}
    for action in sorted(TRUST_ACTIONS):
        required, allowed = trust_allowed(action, trust)
        payload[action] = {"required_trust": required, "allowed": allowed}
    if args.format == "json":
        print(json.dumps(payload))
    else:
        for action, item in payload.items():
            marker = "yes" if item["allowed"] else "no"
            print(f"{action}: {marker} (requires {item['required_trust']})")
    return 0


def cmd_trust_show(args) -> int:
    trust = current_trust(args.vault)
    if args.format == "json":
        print(json.dumps({"trust_level": trust}))
    else:
        print(f"trust_level: {trust}")
    return 0


def cmd_automation_configure(args) -> int:
    profile = normalize_profile(require_profile(args.vault))
    current_trust = profile["automation"]["trust_level"]
    required, allowed = trust_allowed("automation:propose", current_trust)
    bootstrap = current_trust == "advisory" and args.trust_level == "consultative"
    if not (allowed or bootstrap):
        raise CarrelError(
            "Automation configuration is not allowed at current trust level",
            hint=(
                f"Requires {required}. A fresh advisory profile may transition only to "
                "consultative here after explicit approval."
            ),
        )
    automation = dict(profile.get("automation", {}))
    automation["enabled"] = args.enabled == "true"
    automation["trust_level"] = args.trust_level
    automation["schedule"] = args.schedule
    automation["review_cadence"] = args.review_cadence
    automation["model"] = args.model
    automation["last_reviewed"] = date.today().isoformat()
    optional_flags = {
        "inbox_processing": args.inbox_processing,
        "vault_health": args.vault_health,
        "cross_linking_suggestions": args.cross_linking,
        "gap_analysis": args.gap_analysis,
        "draft_feedback": args.draft_feedback,
        "reflection_synthesis": args.reflection_synthesis,
        "wiki_maintenance": args.wiki_maintenance,
    }
    for key, value in optional_flags.items():
        if value is not None:
            automation[key] = value == "true"
    profile["automation"] = automation
    path = write_profile(args.vault, profile)
    print(json.dumps({"path": str(path), "automation": automation}))
    return 0


def _render_automation_prompt(profile: dict) -> str:
    automation = profile["automation"]
    enabled = [
        f"- **{label}**: {instruction}"
        for field, (label, instruction) in AUTOMATION_CAPABILITIES.items()
        if automation.get(field)
    ]
    capability_block = "\n".join(enabled) or (
        "- No automation capabilities are enabled. Stop after confirming that the vault is idle."
    )
    skill_root = Path(__file__).resolve().parents[2]
    template_path = require_asset(skill_root / "assets" / "templates" / "automation-prompt.md")
    template = template_path.read_text(encoding="utf-8")
    return (
        template.replace("{{researcher_name}}", profile.get("name") or "this researcher")
        .replace("{{researcher_field}}", profile.get("field") or "Unknown")
        .replace("{{sensitivity}}", profile["sensitivity"])
        .replace("{{cloud_consent}}", str(profile["cloud_consent"]).lower())
        .replace("{{trust_level}}", automation["trust_level"])
        .replace("{{trust_unlocks}}", AUTOMATION_TRUST_RULES[automation["trust_level"]])
        .replace("{{schedule}}", automation["schedule"])
        .replace("{{model}}", automation["model"])
        .replace("{{enabled_capabilities}}", capability_block)
    )


def cmd_vault_automation_prompt(args) -> int:
    profile = normalize_profile(require_profile(args.vault))
    required, allowed = trust_allowed(
        "automation:write-prompt",
        profile["automation"]["trust_level"],
    )
    if not allowed:
        raise CarrelError(
            "Automation prompt generation is not allowed at current trust level",
            hint=f"Requires {required}; approve automation configuration first.",
        )
    target = safe_vault_join(args.vault, "_meta", "automation-prompt.md")
    existed = target.exists()
    if existed and not args.force:
        raise CarrelError(
            "Automation prompt already exists",
            hint=f"{target} exists; pass --force to overwrite.",
        )
    safe_atomic_write(args.vault, target, _render_automation_prompt(profile))
    print(json.dumps({"path": str(target), "action": "updated" if existed else "created"}))
    return 0
