from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from .constants import (
    CLOUD_TOOLS,
    DEFAULT_PROFILE,
    LOCAL_TOOLS,
    TRUST_ACTIONS,
    TRUST_HIERARCHY,
    TRUST_LEVELS,
)


class CarrelError(Exception):
    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


def emit_error(error: CarrelError) -> int:
    print(f"Error: {error.message}", file=sys.stderr)
    if error.hint:
        print(f"Hint: {error.hint}", file=sys.stderr)
    return 1


def default_profile() -> dict:
    return json.loads(json.dumps(DEFAULT_PROFILE))


def cloud_consent_granted(profile: dict) -> bool:
    # Only an explicit boolean True counts as consent. A malformed profile
    # value (e.g. the string "false" from hand-edited JSON) is truthy under
    # Python's bool() coercion and must never silently widen egress.
    return profile.get("cloud_consent") is True


def require_asset(path: Path) -> Path:
    if not path.exists():
        raise CarrelError(
            "Skill pack incomplete: assets/templates not found next to "
            f"scripts/: expected {path.resolve(strict=False)}",
            hint="Copy the entire skills/carrel folder, not just scripts/.",
        )
    return path


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    tmp.replace(path)


def assert_safe_write_target(vault: Path, path: Path) -> None:
    root = vault.expanduser().resolve()
    if path.is_symlink():
        raise CarrelError(
            "Path escapes vault root",
            hint=f"Refusing to write through symlink {path}",
        )
    resolved_parent = path.parent.resolve(strict=False)
    try:
        resolved_parent.relative_to(root)
    except ValueError as exc:
        raise CarrelError(
            "Path escapes vault root",
            hint=f"Refusing to write outside {root}",
        ) from exc
    if path.exists() and not path.is_file():
        raise CarrelError(
            "Invalid vault file target",
            hint=f"Expected a regular file: {path}",
        )


def assert_safe_read_target(vault: Path, path: Path) -> None:
    root = vault.expanduser().resolve()
    candidate = path.resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise CarrelError(
            "Path escapes vault root",
            hint=f"Refusing to read outside {root}",
        ) from exc


def safe_atomic_write(vault: Path, path: Path, text: str) -> None:
    assert_safe_write_target(vault, path)
    atomic_write(path, text)


def safe_read_text(vault: Path, path: Path, **kwargs) -> str:
    assert_safe_read_target(vault, path)
    return path.read_text(**kwargs)


def safe_vault_join(vault: Path, *parts: str) -> Path:
    root = vault.expanduser().resolve()
    candidate = root.joinpath(*parts).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise CarrelError(
            "Path escapes vault root",
            hint=f"Refusing to write outside {root}",
        ) from exc
    return candidate


def slugify(value: str, *, fallback: str = "untitled", max_length: int = 80) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    if len(value) > max_length:
        clipped = value[:max_length]
        # Cut at the last hyphen so we don't end mid-word; a single long token
        # with no hyphen in the window is hard-cut. Deterministic either way.
        boundary = clipped.rfind("-")
        value = (clipped[:boundary] if boundary > 0 else clipped).strip("-")
    return value or fallback


def source_hash(source: str | Path) -> str:
    # Intentionally more lenient than src/carrel/source_hash.py's
    # hash_source(): a Path that exists hashes file bytes; anything else
    # (a Path that doesn't exist, a URL string, or an arbitrary identifier
    # string) hashes the text form. This is load-bearing, not an oversight —
    # ingestion.py's --content flows pass bare, non-existent, non-URL source
    # identifiers (e.g. `transcript create recording.m4a --content "..."`)
    # and rely on this falling through to a string hash rather than raising
    # FileNotFoundError the way the full plugin's stricter hash_source() would.
    if isinstance(source, Path) and source.exists():
        digest = hashlib.sha256()
        with source.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    return hashlib.sha256(str(source).encode("utf-8")).hexdigest()


def source_hash_with_content(source: str | Path, content: str | None) -> str:
    # Idempotency hash for an ingested artifact. Without provided content this
    # is exactly source_hash(source). With --content, the provided body is
    # folded in so re-ingesting the same source *identifier* with different
    # content re-writes (a changed transcript/article is a changed artifact),
    # while an identical source+content pair still skips idempotently. Without
    # this, a URL-only or bare-name hash makes every re-run with edited
    # --content silently skip.
    base = source_hash(source)
    if content is None:
        return base
    digest = hashlib.sha256()
    digest.update(base.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(content.encode("utf-8"))
    return digest.hexdigest()


def frontmatter_source_hash(text: str) -> str | None:
    # Read source_hash from the leading `--- ... ---` YAML block only. Line- and
    # block-anchored so a 64-char hash literal appearing in the note *body* can
    # never be mistaken for the frontmatter value (the old `expected in old`
    # substring check did exactly that, producing false "unchanged" skips).
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    block = text if end == -1 else text[:end]
    match = re.search(r'^source_hash:\s*"([^"]*)"\s*$', block, re.MULTILINE)
    return match.group(1) if match else None


def render_frontmatter(metadata: dict, body: str) -> str:
    lines = ["---"]
    for key, value in metadata.items():
        if value is None:
            continue
        text = str(value).replace('"', '\\"')
        lines.append(f'{key}: "{text}"')
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip() + "\n")
    return "\n".join(lines)


def read_profile(vault: Path) -> dict:
    path = vault / ".carrel" / "environment.json"
    if not path.exists():
        return default_profile()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CarrelError("Invalid environment.json", hint=exc.msg) from exc
    if not isinstance(payload, dict):
        raise CarrelError("Invalid environment.json", hint="Profile must be a JSON object")
    merged = default_profile()
    merged.update(payload)
    automation = payload.get("automation", {})
    if automation is not None and not isinstance(automation, dict):
        raise CarrelError("Invalid environment.json", hint="automation must be an object")
    merged["automation"] = {
        **DEFAULT_PROFILE["automation"],
        **(automation or {}),
    }
    return merged


def require_profile(vault: Path) -> dict:
    path = vault / ".carrel" / "environment.json"
    if not path.exists():
        raise CarrelError("No environment.json found", hint=f"Run vault init {vault}")
    return read_profile(vault)


def write_profile(vault: Path, profile: dict) -> Path:
    path = safe_vault_join(vault, ".carrel", "environment.json")
    safe_atomic_write(vault, path, json.dumps(profile, indent=2, sort_keys=True) + "\n")
    return path


def select_tool(
    tool_class: str,
    requested: str | None,
    available: set[str],
    sensitivity: str,
    cloud_consent: bool,
) -> dict:
    local = LOCAL_TOOLS[tool_class] & available
    cloud = CLOUD_TOOLS[tool_class] & available
    if requested:
        if requested in CLOUD_TOOLS[tool_class] and sensitivity == "high":
            return {"selected_tool": None, "rationale": "HIGH sensitivity blocks cloud tools regardless of consent"}
        if requested in available:
            return {"selected_tool": requested, "rationale": "Explicit tool request honored"}
        return {"selected_tool": None, "rationale": "Requested tool is not available"}
    if local:
        return {"selected_tool": sorted(local)[0], "rationale": "Local tool selected by default"}
    if sensitivity == "high":
        return {"selected_tool": None, "rationale": "HIGH sensitivity requires local; local tool missing; install and retry"}
    if sensitivity == "medium":
        return {
            "selected_tool": None,
            "rationale": (
                "Local tool missing; this stdlib runtime does not execute cloud "
                "tools directly, supply --content or use a host adapter"
            ),
        }
    if cloud_consent and cloud:
        return {"selected_tool": sorted(cloud)[0], "rationale": "No local tool available; cloud consent enabled so routing to cloud"}
    if cloud_consent:
        return {
            "selected_tool": None,
            "rationale": (
                "No local tool available; cloud consent is enabled but no cloud "
                "adapter is available in this runtime (cloud execution requires a "
                "host adapter)"
            ),
        }
    return {"selected_tool": None, "rationale": "Local tool missing; cloud consent is not enabled"}


def available_tools(tool_class: str) -> set[str]:
    tools: set[str] = set()
    if tool_class == "convert":
        if shutil.which("lit"):
            tools.add("liteparse")
        if shutil.which("markitdown"):
            tools.add("markdownify")
    elif tool_class == "transcribe":
        if shutil.which("coli"):
            tools.add("coli")
    return tools


def convert_available_tools(suffix: str, *, explicit_tool: str | None = None) -> set[str]:
    # Suffix-aware convert availability, mirroring src/carrel/convert/router.py.
    # PDFs never fall back to markitdown: only liteparse (local) is offered,
    # plus markdownify when the caller explicitly requested it. Non-PDF
    # documents use markdownify only — liteparse is a PDF parser and must not be
    # selected for a .pptx/.docx. The type-blind available_tools() above stays
    # for callers (policy explain) that only reason about installed binaries.
    detected = available_tools("convert")
    if suffix == ".pdf":
        allowed = {"liteparse"}
        if explicit_tool == "markdownify":
            allowed.add("markdownify")
        return detected & allowed
    return detected & {"markdownify"}


def trust_allowed(action: str, trust_level: str) -> tuple[str, bool]:
    if action not in TRUST_ACTIONS:
        raise CarrelError(
            f"Unknown trust action: {action}",
            hint=f"Valid actions: {', '.join(sorted(TRUST_ACTIONS))}",
        )
    required = TRUST_ACTIONS[action]
    allowed = TRUST_HIERARCHY.index(trust_level) >= TRUST_HIERARCHY.index(required)
    return required, allowed


def current_trust(vault: Path) -> str:
    profile = require_profile(vault)
    automation = profile.get("automation", {})
    trust = automation.get("trust_level", "advisory") if isinstance(automation, dict) else "advisory"
    if trust not in TRUST_LEVELS:
        raise CarrelError("Invalid trust level in environment.json")
    return trust
