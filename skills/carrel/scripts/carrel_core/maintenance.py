from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from .constants import TRUST_ACTIONS, TRUST_LEVELS
from .core import (
    CarrelError,
    current_trust,
    read_profile,
    require_profile,
    safe_atomic_write,
    safe_read_text,
    safe_vault_join,
    slugify,
    trust_allowed,
    write_profile,
)


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


def read_redactions(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        raise CarrelError("Redact list not found", hint=str(path))
    redactions: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        if "->" in value:
            source, replacement = [part.strip() for part in value.split("->", 1)]
            if source:
                redactions.append((source, replacement or "[REDACTED]"))
        else:
            redactions.append((value, "[REDACTED]"))
    return redactions


def apply_redactions(text: str, redactions: list[tuple[str, str]]) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for term, replacement in redactions:
        text, count = re.subn(re.escape(term), replacement, text, flags=re.IGNORECASE)
        counts[term] = counts.get(term, 0) + count
    return text, counts


def cmd_feedback_export(args) -> int:
    terms = read_redactions(args.redact_list)
    meta = safe_vault_join(args.vault, "_meta")
    sources = []
    for folder in ["friction-log", "capability-log", "reflections"]:
        folder_path = safe_vault_join(args.vault, "_meta", folder)
        if folder_path.is_dir():
            for source in sorted(folder_path.glob("*.md")):
                safe_read_text(args.vault, source, encoding="utf-8")
                sources.append(source)
    for flat in ["friction_log.md", "capability-log.md"]:
        flat_path = safe_vault_join(args.vault, "_meta", flat)
        if flat_path.is_file():
            safe_read_text(args.vault, flat_path, encoding="utf-8")
            sources.append(flat_path)
    parts = [f"# Feedback Digest - {date.today().isoformat()}\n"]
    total_counts: dict[str, int] = {term: 0 for term, _ in terms}
    for source in sources:
        parts.append(f"\n## {source.name}\n\n")
        redacted, counts = apply_redactions(safe_read_text(args.vault, source, encoding="utf-8"), terms)
        parts.append(redacted)
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
                "redaction_rules": len(terms),
                "redactions_applied": sum(total_counts.values()),
                "zero_match_terms": zero_match_terms,
            }
        )
    )
    return 0


def cmd_share_generate(args) -> int:
    if ".." in args.name or "/" in args.name or "\\" in args.name:
        raise CarrelError("Invalid collaborator name")
    profile = read_profile(args.vault)
    redactions: list[str] = []
    if args.from_stdin:
        supplied = sys.stdin.read().strip()
        if not supplied:
            raise CarrelError("Empty collaborator handbook received on stdin")
        body = [supplied]
    else:
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
            threads = sorted((args.vault / "notes" / "threads").glob("*.md"))
            if threads:
                body.extend(["", "## Active Threads"])
                for thread in threads:
                    body.append(f"- {thread.name}")
            if args.sensitivity == "medium":
                redactions.append("threads-contents-omitted")
    target = safe_vault_join(args.vault, "_meta", "handbook", f"{date.today().isoformat()}-for-{slugify(args.name)}.md")
    safe_atomic_write(args.vault, target, "\n".join(body).rstrip() + "\n")
    canonical_path = None
    if args.canonical:
        canonical = safe_vault_join(args.vault, "_meta", "lab-handbook.md")
        safe_atomic_write(args.vault, canonical, "\n".join(body).rstrip() + "\n")
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
    profile = require_profile(args.vault)
    required, allowed = trust_allowed("automation:propose", current_trust(args.vault))
    if not allowed:
        raise CarrelError(
            "Automation configuration is not allowed at current trust level",
            hint=f"Requires {required}; update trust through setup or an explicit profile edit.",
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
    pending_decisions = safe_vault_join(args.vault, "_meta", "pending-decisions.md")
    if not pending_decisions.exists():
        safe_atomic_write(args.vault, pending_decisions, "# Pending Decisions\n\nItems deferred from automated processing.\n")
    pending_approvals = safe_vault_join(args.vault, "_meta", "pending-approvals.md")
    if not pending_approvals.exists():
        safe_atomic_write(args.vault, pending_approvals, "# Pending Approvals\n\nProposed actions awaiting researcher approval.\n")
    automation_prompt = safe_vault_join(args.vault, "_meta", "automation-prompt.md")
    if not automation_prompt.exists():
        safe_atomic_write(
            args.vault,
            automation_prompt,
            "\n".join(
                [
                    "# Carrel Automation Prompt",
                    "",
                    "Find the vault root by locating `.carrel/environment.json`.",
                    "Read `.carrel/environment.json` and `.carrel/agent-context.md` before acting.",
                    "Run unattended: do not ask questions; write uncertain items to `_meta/pending-decisions.md`.",
                    "Respect the configured sensitivity, cloud consent, and trust level.",
                ]
            )
            + "\n",
        )
    print(
        json.dumps(
            {
                "path": str(path),
                "automation": automation,
                "pending_decisions": str(pending_decisions),
                "pending_approvals": str(pending_approvals),
                "automation_prompt": str(automation_prompt),
            }
        )
    )
    return 0
