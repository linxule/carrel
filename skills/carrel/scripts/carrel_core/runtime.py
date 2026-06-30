from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

VERSION = "0.1.0-skill"

SENSITIVITY = {"high", "medium", "low"}
TRUST_LEVELS = {"advisory", "consultative", "delegated", "partnership"}
TRUST_HIERARCHY = ["advisory", "consultative", "delegated", "partnership"]
TRUST_ACTIONS = {
    "automation:propose": "consultative",
    "automation:execute": "delegated",
    "automation:write-prompt": "delegated",
    "wiki:propose": "consultative",
    "wiki:write": "delegated",
    "vault:move-file": "delegated",
    "vault:reorganize": "partnership",
}
LOCAL_TOOLS = {
    "convert": {"liteparse", "markdownify", "provided"},
    "transcribe": {"coli", "youtube_captions", "provided"},
}
CLOUD_TOOLS = {
    "convert": {"mineru"},
    "transcribe": {"groq", "gemini"},
}

GOOGLE_WORKSPACE_EXPORTS: dict[str, dict[str, tuple[str, str]]] = {
    "document": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/plain", ".txt"),
        "html": ("text/html", ".html"),
    },
    "spreadsheets": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/csv", ".csv"),
        "html": ("text/html", ".html"),
    },
    "presentation": {
        "docx": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        ),
        "pdf": ("application/pdf", ".pdf"),
        "txt": ("text/plain", ".txt"),
    },
}

DOC_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".txt", ".md"}
AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".mp4", ".webm", ".mov", ".ogg", ".flac"}
URL_LIST_EXTENSION = ".txt"

DEFAULT_PROFILE = {
    "version": VERSION,
    "name": None,
    "field": None,
    "sensitivity": "medium",
    "cloud_consent": False,
    "comfort_level": "beginner",
    "wiki_enabled": False,
    "wiki_preference": None,
    "wiki_proposal_deferred_until": None,
    "tools_configured": {},
    "preferences": {},
    "automation": {
        "enabled": False,
        "inbox_processing": True,
        "vault_health": True,
        "cross_linking_suggestions": True,
        "gap_analysis": False,
        "draft_feedback": False,
        "reflection_synthesis": True,
        "wiki_maintenance": False,
        "trust_level": "advisory",
        "model": "sonnet",
        "schedule": "daily",
        "review_cadence": "quarterly",
        "last_reviewed": None,
    },
    "collaborators": None,
    "team_context": None,
    "model_teammates": {},
}

ADAPTER_PROFILE_KEYS = {"claude_code_familiarity"}


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


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    tmp.replace(path)


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


def slugify(value: str, *, fallback: str = "untitled") -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or fallback


def source_hash(source: str | Path) -> str:
    if isinstance(source, Path) and source.exists():
        return hashlib.sha256(source.read_bytes()).hexdigest()
    return hashlib.sha256(str(source).encode("utf-8")).hexdigest()


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
    atomic_write(path, json.dumps(profile, indent=2, sort_keys=True) + "\n")
    return path


def copy_templates(vault: Path, skill_root: Path) -> list[str]:
    source = skill_root / "assets" / "templates"
    copied: list[str] = []
    if not source.exists():
        return copied
    template_dir = safe_vault_join(vault, "_templates")
    template_dir.mkdir(parents=True, exist_ok=True)
    for item in sorted(source.iterdir()):
        if not item.is_file():
            continue
        target = template_dir / item.name
        if target.exists():
            continue
        target.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
        copied.append(item.name)
    return copied


def scaffold_folders(skill_root: Path) -> list[str]:
    scaffold_path = skill_root / "assets" / "templates" / "vault-scaffold.json"
    fallback = [
        "inbox",
        "papers",
        "transcripts",
        "notes",
        "drafts",
        "talks",
        "admin",
        "_meta",
        "_meta/reflections",
        "_meta/local",
        "_templates",
        ".carrel",
    ]
    if not scaffold_path.exists():
        return fallback
    try:
        payload = json.loads(scaffold_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback
    folders = payload.get("folders", [])
    if not isinstance(folders, list):
        return fallback
    paths: list[str] = []
    for item in folders:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.append(item["path"])
    return paths or fallback


def materialize_obsidian_config(vault: Path, skill_root: Path) -> list[str]:
    config_path = skill_root / "assets" / "templates" / "obsidian-config.json"
    written: list[str] = []
    if not config_path.exists():
        return written
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return written
    files = payload.get("files", {})
    if not isinstance(files, dict):
        return written
    obsidian_dir = safe_vault_join(vault, ".obsidian")
    obsidian_dir.mkdir(parents=True, exist_ok=True)
    for filename, value in files.items():
        if "/" in filename or "\\" in filename or filename.startswith("."):
            continue
        target = obsidian_dir / filename
        if target.exists():
            continue
        text = value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True)
        target.write_text(text.rstrip() + "\n", encoding="utf-8")
        written.append(filename)
    return written


def cmd_vault_init(args: argparse.Namespace) -> int:
    vault = args.path.expanduser().resolve()
    vault.mkdir(parents=True, exist_ok=True)
    skill_root = Path(__file__).resolve().parents[2]
    for name in scaffold_folders(skill_root):
        safe_vault_join(vault, *name.split("/")).mkdir(parents=True, exist_ok=True)
    for name in ["_meta/mirror", "_meta/handbook"]:
        safe_vault_join(vault, *name.split("/")).mkdir(parents=True, exist_ok=True)
    copied = copy_templates(vault, skill_root)
    obsidian_files = materialize_obsidian_config(vault, skill_root)
    profile_path = vault / ".carrel" / "environment.json"
    if not profile_path.exists():
        write_profile(vault, default_profile())
    context_asset = skill_root / "assets" / "templates" / "agent-context.md"
    context_path = safe_vault_join(vault, ".carrel", "agent-context.md")
    if not context_path.exists():
        context_path.write_text(context_asset.read_text(encoding="utf-8"), encoding="utf-8")
    payload = {
        "vault": str(vault),
        "profile": str(profile_path),
        "context": str(context_path),
        "templates_copied": copied,
        "obsidian_files": obsidian_files,
    }
    print(json.dumps(payload) if args.format == "json" else f"Created vault at {vault}")
    return 0


def validate_profile_payload(payload: dict) -> tuple[list[dict], list[dict]]:
    errors: list[dict] = []
    drift: list[dict] = []
    if not isinstance(payload, dict):
        return ([{"path": "$", "message": "environment.json must be an object"}], drift)
    unknown = sorted(set(payload) - set(DEFAULT_PROFILE) - ADAPTER_PROFILE_KEYS)
    if unknown:
        drift.append(
            {
                "check": "unknown_keys",
                "field": ", ".join(unknown),
                "message": f"Unknown top-level keys: {', '.join(unknown)}",
            }
        )
    sensitivity = payload.get("sensitivity", "medium")
    if sensitivity not in SENSITIVITY:
        errors.append(
            {
                "path": "sensitivity",
                "message": "sensitivity must be high, medium, or low",
            }
        )
    automation = payload.get("automation", {})
    if isinstance(automation, dict):
        trust = automation.get("trust_level", "advisory")
        if trust not in TRUST_LEVELS:
            errors.append(
                {
                    "path": "automation.trust_level",
                    "message": "trust_level is invalid",
                }
            )
    else:
        errors.append({"path": "automation", "message": "automation must be an object"})
    for key in DEFAULT_PROFILE:
        if key not in payload:
            drift.append(
                {
                    "check": "missing_key",
                    "field": key,
                    "message": f"Missing top-level key: {key}",
                }
            )
    return errors, drift


def cmd_env_validate(args: argparse.Namespace) -> int:
    path = args.vault / ".carrel" / "environment.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        payload = {}
    except json.JSONDecodeError as exc:
        result = {
            "status": "invalid",
            "errors": [{"path": "$", "message": f"Invalid JSON: {exc.msg}"}],
            "drift": [],
        }
        print(json.dumps(result))
        return 1
    errors, drift = validate_profile_payload(payload)
    status = "invalid" if errors else "drift" if drift else "valid"
    result = {"status": status, "errors": errors, "drift": drift}
    print(json.dumps(result) if args.format == "json" else status)
    return 1 if errors else 2 if drift else 0


def cmd_env_fix(args: argparse.Namespace) -> int:
    path = args.vault / ".carrel" / "environment.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        payload = {}
    except json.JSONDecodeError as exc:
        raise CarrelError("Invalid environment.json", hint=exc.msg) from exc
    if not isinstance(payload, dict):
        raise CarrelError("Invalid environment.json", hint="Profile must be a JSON object")
    fixed = default_profile()
    fixed.update(
        {
            key: value
            for key, value in payload.items()
            if key in DEFAULT_PROFILE or key in ADAPTER_PROFILE_KEYS
        }
    )
    current_automation = payload.get("automation", {})
    fixed["automation"] = {
        **DEFAULT_PROFILE["automation"],
        **(current_automation if isinstance(current_automation, dict) else {}),
    }
    changed = fixed != payload
    result = {"changed": changed, "path": str(path), "dry_run": args.dry_run}
    if changed and not args.dry_run:
        if path.exists():
            backup = path.with_suffix(".json.bak")
            backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            result["backup"] = str(backup)
        write_profile(args.vault, fixed)
    print(json.dumps(result) if args.format == "json" else ("updated" if changed else "ok"))
    return 0


def cmd_env_doctor(args: argparse.Namespace) -> int:
    tool_names = [
        "git",
        "node",
        "bun",
        "uv",
        "lit",
        "markitdown",
        "defuddle",
        "coli",
        "gws",
    ]
    binaries = {
        name: {"installed": shutil.which(name) is not None, "path": shutil.which(name)}
        for name in tool_names
    }
    api_keys = {
        "mineru": bool(os.environ.get("MINERU_API_KEY")),
        "groq": bool(os.environ.get("GROQ_API_KEY")),
        "gemini": bool(os.environ.get("GEMINI_API_KEY")),
    }
    payload = {
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "project_path": str(args.project_path.expanduser().resolve()) if args.project_path else None,
        "binaries": binaries,
        "api_keys": api_keys,
        "optional_adapters": {
            "capture": ["defuddle", "markitdown"],
            "convert": ["lit", "markitdown", "mineru"],
            "transcribe": ["coli", "groq", "gemini", "youtube_captions"],
            "google": ["gws"],
        },
    }
    if args.format == "json":
        print(json.dumps(payload))
    else:
        installed = ", ".join(name for name, data in binaries.items() if data["installed"]) or "none"
        print(f"platform: {payload['platform']}\npython: {payload['python']}\ninstalled: {installed}")
    return 0


def select_tool(tool_class: str, requested: str | None, available: set[str], sensitivity: str, cloud_consent: bool) -> dict:
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
        return {"selected_tool": None, "rationale": "Local tool missing; to use cloud, run with an explicit cloud tool"}
    if cloud_consent and cloud:
        return {"selected_tool": sorted(cloud)[0], "rationale": "No local tool available; cloud consent enabled so routing to cloud"}
    return {"selected_tool": None, "rationale": "Local tool missing; cloud consent is not enabled"}


def available_tools(tool_class: str) -> set[str]:
    tools: set[str] = set()
    if tool_class == "convert":
        if shutil.which("lit"):
            tools.add("liteparse")
        if shutil.which("markitdown"):
            tools.add("markdownify")
        if os.environ.get("MINERU_API_KEY"):
            tools.add("mineru")
    elif tool_class == "transcribe":
        if shutil.which("coli"):
            tools.add("coli")
        if shutil.which("youtube-transcript-api"):
            tools.add("youtube_captions")
        if os.environ.get("GROQ_API_KEY"):
            tools.add("groq")
        if os.environ.get("GEMINI_API_KEY"):
            tools.add("gemini")
    return tools


def cmd_policy_explain(args: argparse.Namespace) -> int:
    available = set(args.available_tools.split(",")) if args.available_tools else available_tools(args.tool_class)
    payload = select_tool(
        args.tool_class,
        args.requested_tool,
        available,
        args.sensitivity,
        args.cloud_consent,
    )
    payload.update(
        {
            "tool_class": args.tool_class,
            "requested_tool": args.requested_tool,
            "available_tools": sorted(available),
            "sensitivity": args.sensitivity,
            "cloud_consent": args.cloud_consent,
        }
    )
    print(json.dumps(payload))
    return 0 if payload["selected_tool"] else 1


def write_ingested(path: Path, body: str, metadata: dict, force: bool) -> tuple[str, str | None]:
    existed = path.exists()
    if path.exists() and not force:
        old = path.read_text(encoding="utf-8", errors="replace")
        expected = f'source_hash: "{metadata.get("source_hash")}"'
        if expected in old:
            return "skipped", "source-hash matches; pass --force to overwrite"
        return "skipped", "target exists with a different source-hash; pass --force to overwrite"
    atomic_write(path, render_frontmatter(metadata, body))
    return ("overwritten" if existed else "created"), None


def capture_content(url: str, args: argparse.Namespace) -> tuple[str, dict, str]:
    if args.content:
        return args.content, {"title": args.title or urlparse(url).netloc, "domain": urlparse(url).netloc}, "provided"
    for tool, command in [("defuddle", "defuddle"), ("markitdown", "markitdown")]:
        if shutil.which(command):
            proc = subprocess.run([command, url], text=True, capture_output=True, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout, {"title": args.title or urlparse(url).netloc, "domain": urlparse(url).netloc}, tool
    raise CarrelError("No capture adapter available", hint="Install defuddle/markitdown or pass --content.")


def cmd_capture_url(args: argparse.Namespace) -> int:
    vault = args.vault.expanduser().resolve()
    url = args.url
    title = args.title or Path(urlparse(url).path).stem or urlparse(url).netloc
    target = safe_vault_join(vault, "inbox", f"{slugify(title)}.md")
    if args.dry_run:
        print(f"Would capture {url} -> {target}")
        return 0
    body, metadata, tool = capture_content(url, args)
    metadata.update(
        {
            "title": metadata.get("title") or title,
            "source_url": url,
            "capture_tool": tool,
            "source_hash": source_hash(url),
        }
    )
    action, reason = write_ingested(target, body, metadata, args.force)
    print(json.dumps({"path": str(target), "action": action, "reason": reason}))
    return 0


def cmd_convert_file(args: argparse.Namespace) -> int:
    vault = args.vault.expanduser().resolve()
    file_path = args.file.expanduser().resolve()
    profile = read_profile(vault)
    available = available_tools("convert")
    if file_path.suffix.lower() in {".txt", ".md"} or args.content:
        available.add("provided")
    sensitivity = args.sensitivity or profile.get("sensitivity", "medium")
    if not args.tool and (file_path.suffix.lower() in {".txt", ".md"} or args.content):
        decision = {"selected_tool": "provided", "rationale": "Bundled runtime can read provided/plain text directly"}
    else:
        decision = select_tool(
            "convert",
            args.tool,
            available,
            sensitivity,
            bool(profile.get("cloud_consent")),
        )
    if args.explain:
        print(json.dumps(decision))
        return 0 if decision["selected_tool"] else 1
    if args.tool and not decision["selected_tool"]:
        raise CarrelError("Requested conversion tool is not allowed", hint=decision["rationale"])
    if not decision["selected_tool"] and not args.content:
        raise CarrelError("No conversion tool selected", hint=decision["rationale"])
    if args.dry_run:
        print(f"Would convert {file_path} -> papers/{slugify(file_path.stem)}/paper.md")
        return 0
    if args.content:
        body = args.content
    elif file_path.suffix.lower() in {".txt", ".md"}:
        body = file_path.read_text(encoding="utf-8")
    else:
        raise CarrelError("Adapter execution not available in stdlib runtime", hint="Pass --content or install/use a host adapter.")
    target = safe_vault_join(vault, "papers", slugify(file_path.stem), "paper.md")
    metadata = {
        "title": file_path.stem,
        "source": str(file_path),
        "convert_tool": decision["selected_tool"] or "provided",
        "source_hash": source_hash(file_path),
    }
    action, reason = write_ingested(target, body, metadata, args.force)
    print(json.dumps({"path": str(target), "action": action, "reason": reason}))
    return 0


def cmd_transcript_create(args: argparse.Namespace) -> int:
    vault = args.vault.expanduser().resolve()
    source = args.source
    profile = read_profile(vault)
    available = available_tools("transcribe")
    if args.content:
        available.add("provided")
    sensitivity = args.sensitivity or profile.get("sensitivity", "medium")
    if not args.tool and args.content:
        decision = {"selected_tool": "provided", "rationale": "Bundled runtime can file provided transcript text directly"}
    else:
        decision = select_tool(
            "transcribe",
            args.tool,
            available,
            sensitivity,
            bool(profile.get("cloud_consent")),
        )
    if args.explain:
        payload = dict(decision)
        payload.update(
            {
                "tool_class": "transcribe",
                "requested_tool": args.tool,
                "available_tools": sorted(available),
                "sensitivity": sensitivity,
            }
        )
        print(json.dumps(payload))
        return 0 if decision["selected_tool"] else 1
    slug = slugify(Path(urlparse(source).path).stem or Path(source).stem or "recording")
    target = safe_vault_join(vault, "transcripts", f"{date.today().isoformat()}-{args.kind}-{slug}.md")
    if args.dry_run:
        print(f"Would transcribe {source} -> {target}")
        return 0
    if args.tool and not decision["selected_tool"]:
        raise CarrelError("Requested transcription tool is not allowed", hint=decision["rationale"])
    if not decision["selected_tool"] and not args.content:
        raise CarrelError("No transcription tool selected", hint=decision["rationale"])
    if not args.content:
        raise CarrelError("Adapter execution not available in stdlib runtime", hint="Pass --content or install/use a host adapter.")
    source_path = Path(source).expanduser()
    source_for_hash: str | Path = source_path if source_path.exists() else source
    metadata = {
        "source": source,
        "kind": args.kind,
        "transcribe_tool": decision["selected_tool"] or "provided",
        "source_hash": source_hash(source_for_hash),
    }
    action, reason = write_ingested(target, args.content, metadata, args.force)
    print(json.dumps({"path": str(target), "action": action, "reason": reason}))
    return 0


def parse_google_workspace_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "docs.google.com":
        raise CarrelError(
            "Unsupported Google Workspace URL",
            hint="Use a docs.google.com/document, spreadsheets, or presentation URL.",
        )
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[1] != "d":
        raise CarrelError(
            "Unsupported Google Workspace URL",
            hint="Expected docs.google.com/<kind>/d/<id>/edit.",
        )
    kind = parts[0]
    if kind not in GOOGLE_WORKSPACE_EXPORTS:
        raise CarrelError(
            "Unsupported Google Workspace file type",
            hint="Supported kinds: document, spreadsheets, presentation.",
        )
    return kind, parts[2]


def google_export_target(vault: Path, url: str, export_format: str) -> tuple[str, str, Path]:
    kind, file_id = parse_google_workspace_url(url)
    try:
        mime_type, suffix = GOOGLE_WORKSPACE_EXPORTS[kind][export_format]
    except KeyError as exc:
        raise CarrelError(
            "Unsupported export format",
            hint=f"{kind} files do not support --export-format {export_format}.",
        ) from exc
    target = safe_vault_join(vault, ".carrel", "exports", f"{file_id}{suffix}")
    return file_id, mime_type, target


def cmd_google_export(args: argparse.Namespace) -> int:
    vault = args.vault.expanduser().resolve()
    profile = read_profile(vault)
    sensitivity = args.sensitivity or profile.get("sensitivity", "medium")
    if sensitivity == "high" and not args.content:
        raise CarrelError(
            "HIGH sensitivity blocks Google Workspace export",
            hint="Export locally yourself and pass --content, or lower sensitivity explicitly.",
        )
    file_id, mime_type, export_path = google_export_target(vault, args.url, args.export_format)
    available = available_tools("convert")
    if args.content:
        available.add("provided")
    if not args.tool and args.content:
        decision = {"selected_tool": "provided", "rationale": "Bundled runtime can file provided export text directly"}
    else:
        decision = select_tool(
            "convert",
            args.tool,
            available,
            sensitivity,
            bool(profile.get("cloud_consent")),
        )
    if args.explain:
        payload = dict(decision)
        payload.update(
            {
                "google_file_id": file_id,
                "export_path": str(export_path),
                "export_mime_type": mime_type,
                "available_tools": sorted(available),
            }
        )
        print(json.dumps(payload))
        return 0 if payload["selected_tool"] else 1
    if args.tool and not decision["selected_tool"]:
        raise CarrelError("Requested conversion tool is not allowed", hint=decision["rationale"])
    if args.dry_run:
        print(json.dumps({"action": "would-export", "export_path": str(export_path)}))
        return 0
    if args.content:
        atomic_write(export_path, args.content)
        body = args.content
    else:
        gws = shutil.which("gws")
        if not gws:
            raise CarrelError("No Google export adapter available", hint="Install gws/authenticate it or pass --content.")
        export_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                gws,
                "drive",
                "files",
                "export",
                "--params",
                json.dumps({"fileId": file_id, "mimeType": mime_type}),
                "-o",
                str(export_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise CarrelError("gws export failed", hint=proc.stderr.strip() or "Check auth and file permissions.")
        if export_path.suffix.lower() in {".txt", ".csv", ".html", ".md"}:
            body = export_path.read_text(encoding="utf-8", errors="replace")
        else:
            raise CarrelError("Adapter execution not available in stdlib runtime", hint="Export as txt/html or pass --content.")
    target = safe_vault_join(vault, "papers", slugify(args.title or file_id), "paper.md")
    metadata = {
        "title": args.title or file_id,
        "source_url": args.url,
        "google_file_id": file_id,
        "export_format": args.export_format,
        "convert_tool": decision["selected_tool"] or "provided",
        "source_hash": source_hash(args.url),
    }
    action, reason = write_ingested(target, body, metadata, args.force)
    if not args.keep_export and export_path.exists():
        export_path.unlink()
    print(json.dumps({"path": str(target), "exported_file": str(export_path), "action": action, "reason": reason}))
    return 0


def append_pending_decision(vault: Path, body: str) -> None:
    target = safe_vault_join(vault, "_meta", "pending-decisions.md")
    header = "# Pending Decisions\n\n"
    row = f"- [ ] **{date.today().isoformat()}**: {body}\n"
    existing = target.read_text(encoding="utf-8") if target.exists() else header
    if row in existing:
        return
    atomic_write(target, existing.rstrip() + "\n" + row)


def enumerate_files(folder: Path, extensions: set[str], *, include_url_lists: bool = False) -> list[Path]:
    if not folder.exists():
        raise CarrelError("Batch folder not found", hint=str(folder))
    if not folder.is_dir():
        raise CarrelError("Batch target is not a folder", hint="Pass a directory.")
    files: list[Path] = []
    for path in sorted(folder.iterdir()):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in extensions or (include_url_lists and suffix == URL_LIST_EXTENSION):
            files.append(path)
    return files


def cmd_batch_convert(args: argparse.Namespace) -> int:
    outcomes: list[dict] = []
    for file_path in enumerate_files(args.folder.expanduser(), DOC_EXTENSIONS):
        ns = argparse.Namespace(
            file=file_path,
            vault=args.vault,
            tool=args.tool,
            sensitivity=args.sensitivity,
            content=None,
            dry_run=args.dry_run,
            explain=args.explain,
            force=args.force,
        )
        try:
            child_out = io.StringIO()
            with contextlib.redirect_stdout(child_out):
                code = cmd_convert_file(ns)
            outcomes.append(
                {
                    "file": str(file_path),
                    "action": "converted" if code == 0 else "failed",
                    "detail": child_out.getvalue().strip() or "ok",
                }
            )
        except CarrelError as error:
            action = "deferred" if args.unattended else "failed"
            if args.unattended:
                append_pending_decision(args.vault, f"`{file_path.name}` - convert failed: {error.message}")
            outcomes.append({"file": str(file_path), "action": action, "detail": error.message})
            if not args.unattended:
                continue
    print(json.dumps(outcomes) if args.format == "json" else "\n".join(item["file"] for item in outcomes))
    return 0 if all(item["action"] in {"converted", "deferred"} for item in outcomes) else 1


def read_urls(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def cmd_batch_transcribe(args: argparse.Namespace) -> int:
    outcomes: list[dict] = []
    for file_path in enumerate_files(args.folder.expanduser(), AUDIO_EXTENSIONS, include_url_lists=True):
        sources = read_urls(file_path) if file_path.suffix.lower() == URL_LIST_EXTENSION else [str(file_path)]
        if not sources:
            if args.unattended:
                append_pending_decision(args.vault, f"`{file_path.name}` - URL list is empty")
            outcomes.append({"file": str(file_path), "action": "deferred" if args.unattended else "failed", "detail": "empty URL list"})
            continue
        for source in sources:
            ns = argparse.Namespace(
                source=source,
                vault=args.vault,
                kind=args.kind,
                tool=args.tool,
                sensitivity=args.sensitivity,
                content=args.content,
                dry_run=args.dry_run,
                explain=args.explain,
                force=args.force,
            )
            try:
                child_out = io.StringIO()
                with contextlib.redirect_stdout(child_out):
                    code = cmd_transcript_create(ns)
                outcomes.append(
                    {
                        "file": str(file_path),
                        "source": source,
                        "action": "transcribed" if code == 0 else "failed",
                        "detail": child_out.getvalue().strip() or "ok",
                    }
                )
            except CarrelError as error:
                action = "deferred" if args.unattended else "failed"
                if args.unattended:
                    append_pending_decision(args.vault, f"`{source}` - transcribe failed: {error.message}")
                outcomes.append({"file": str(file_path), "source": source, "action": action, "detail": error.message})
    print(json.dumps(outcomes) if args.format == "json" else "\n".join(item["file"] for item in outcomes))
    return 0 if all(item["action"] in {"transcribed", "deferred"} for item in outcomes) else 1


def cmd_reflection_append(args: argparse.Namespace) -> int:
    body = sys.stdin.read().rstrip()
    if not body:
        raise CarrelError("Empty reflection body received on stdin")
    target = safe_vault_join(args.vault, "_meta", "reflections", f"reflection-{date.today().isoformat()}.md")
    existed = target.exists()
    previous = target.read_text(encoding="utf-8") if target.exists() else f"# Reflection - {date.today().isoformat()}\n"
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    atomic_write(target, f"{previous.rstrip()}\n\n## {stamp}\n\n{body}\n")
    print(json.dumps({"path": str(target), "action": "appended" if existed else "created"}))
    return 0


def cmd_mirror_write(args: argparse.Namespace) -> int:
    body = sys.stdin.read()
    if not body.strip():
        raise CarrelError("Empty mirror body received on stdin")
    target = safe_vault_join(args.vault, "_meta", "mirror", f"{date.today().strftime('%Y-%m')}.md")
    existed = target.exists()
    new_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == new_hash and not args.force:
        print(json.dumps({"path": str(target), "action": "skipped"}))
        return 0
    atomic_write(target, body)
    print(json.dumps({"path": str(target), "action": "updated" if existed else "created"}))
    return 0


def read_redactions(path: Path) -> list[str]:
    if not path.exists():
        raise CarrelError("Redact list not found", hint=str(path))
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def apply_redactions(text: str, terms: list[str]) -> str:
    for term in terms:
        text = re.sub(re.escape(term), "[REDACTED]", text, flags=re.IGNORECASE)
    return text


def cmd_feedback_export(args: argparse.Namespace) -> int:
    terms = read_redactions(args.redact_list)
    meta = args.vault / "_meta"
    sources = []
    for folder in ["friction-log", "capability-log", "reflections"]:
        sources.extend(sorted((meta / folder).glob("*.md")))
    parts = [f"# Feedback Digest - {date.today().isoformat()}\n"]
    for source in sources:
        parts.append(f"\n## {source.name}\n\n")
        parts.append(apply_redactions(source.read_text(encoding="utf-8"), terms))
    target = safe_vault_join(args.vault, "_meta", f"feedback-digest-{date.today().isoformat()}.md")
    atomic_write(target, "\n".join(parts).rstrip() + "\n")
    print(json.dumps({"path": str(target), "sources": [str(path) for path in sources], "redacted_terms": len(terms)}))
    return 0


def cmd_share_generate(args: argparse.Namespace) -> int:
    if ".." in args.name or "/" in args.name or "\\" in args.name:
        raise CarrelError("Invalid collaborator name")
    profile = read_profile(args.vault)
    redactions: list[str] = []
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
    if args.sensitivity != "high":
        threads = sorted((args.vault / "notes" / "threads").glob("*.md"))
        if threads:
            body.extend(["", "## Active Threads"])
            for thread in threads:
                body.append(f"- {thread.name}")
        if args.sensitivity == "medium":
            redactions.append("threads-contents-omitted")
    target = safe_vault_join(args.vault, "_meta", "handbook", f"{date.today().isoformat()}-for-{slugify(args.name)}.md")
    atomic_write(target, "\n".join(body).rstrip() + "\n")
    print(json.dumps({"path": str(target), "sensitivity": args.sensitivity, "redactions_applied": redactions}))
    return 0


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


def cmd_trust_check(args: argparse.Namespace) -> int:
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
        print(
            f"Action '{args.action}' requires trust level '{required}'; current is '{trust}'",
            file=sys.stderr,
        )
    return 0 if allowed else 1


def cmd_trust_list(args: argparse.Namespace) -> int:
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


def cmd_trust_show(args: argparse.Namespace) -> int:
    trust = current_trust(args.vault)
    if args.format == "json":
        print(json.dumps({"trust_level": trust}))
    else:
        print(f"trust_level: {trust}")
    return 0


def cmd_automation_configure(args: argparse.Namespace) -> int:
    profile = require_profile(args.vault)
    required, allowed = trust_allowed("automation:write-prompt", current_trust(args.vault))
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="carrel.py")
    sub = parser.add_subparsers(dest="group", required=True)

    vault = sub.add_parser("vault")
    vault_sub = vault.add_subparsers(dest="command", required=True)
    vault_init = vault_sub.add_parser("init")
    vault_init.add_argument("path", type=Path)
    vault_init.add_argument("--format", choices=["human", "json"], default="human")
    vault_init.set_defaults(func=cmd_vault_init)

    env = sub.add_parser("env")
    env_sub = env.add_subparsers(dest="command", required=True)
    env_validate = env_sub.add_parser("validate")
    env_validate.add_argument("--vault", type=Path, required=True)
    env_validate.add_argument("--format", choices=["human", "json"], default="human")
    env_validate.set_defaults(func=cmd_env_validate)
    env_fix = env_sub.add_parser("fix")
    env_fix.add_argument("--vault", type=Path, required=True)
    env_fix.add_argument("--dry-run", action="store_true")
    env_fix.add_argument("--format", choices=["human", "json"], default="human")
    env_fix.set_defaults(func=cmd_env_fix)
    env_doctor = env_sub.add_parser("doctor")
    env_doctor.add_argument("--project-path", type=Path)
    env_doctor.add_argument("--format", choices=["human", "json"], default="human")
    env_doctor.set_defaults(func=cmd_env_doctor)

    policy = sub.add_parser("policy")
    policy_sub = policy.add_subparsers(dest="command", required=True)
    explain = policy_sub.add_parser("explain")
    explain.add_argument("--tool-class", choices=["convert", "transcribe"], required=True)
    explain.add_argument("--requested-tool")
    explain.add_argument("--available-tools", default="")
    explain.add_argument("--sensitivity", choices=sorted(SENSITIVITY), default="medium")
    explain.add_argument("--cloud-consent", action="store_true")
    explain.set_defaults(func=cmd_policy_explain)

    capture = sub.add_parser("capture")
    capture_sub = capture.add_subparsers(dest="command", required=True)
    capture_url = capture_sub.add_parser("url")
    capture_url.add_argument("url")
    capture_url.add_argument("--vault", type=Path, required=True)
    capture_url.add_argument("--title")
    capture_url.add_argument("--content")
    capture_url.add_argument("--dry-run", action="store_true")
    capture_url.add_argument("--force", action="store_true")
    capture_url.set_defaults(func=cmd_capture_url)

    convert = sub.add_parser("convert")
    convert_sub = convert.add_subparsers(dest="command", required=True)
    convert_file = convert_sub.add_parser("file")
    convert_file.add_argument("file", type=Path)
    convert_file.add_argument("--vault", type=Path, required=True)
    convert_file.add_argument("--tool")
    convert_file.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    convert_file.add_argument("--content")
    convert_file.add_argument("--dry-run", action="store_true")
    convert_file.add_argument("--explain", action="store_true")
    convert_file.add_argument("--force", action="store_true")
    convert_file.set_defaults(func=cmd_convert_file)

    google = sub.add_parser("google")
    google_sub = google.add_subparsers(dest="command", required=True)
    google_export = google_sub.add_parser("export")
    google_export.add_argument("url")
    google_export.add_argument("--vault", type=Path, required=True)
    google_export.add_argument("--export-format", choices=["docx", "pdf", "txt", "html"], default="docx")
    google_export.add_argument("--keep-export", action="store_true")
    google_export.add_argument("--tool")
    google_export.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    google_export.add_argument("--content")
    google_export.add_argument("--title")
    google_export.add_argument("--dry-run", action="store_true")
    google_export.add_argument("--explain", action="store_true")
    google_export.add_argument("--force", action="store_true")
    google_export.set_defaults(func=cmd_google_export)

    batch = sub.add_parser("batch")
    batch_sub = batch.add_subparsers(dest="command", required=True)
    batch_convert = batch_sub.add_parser("convert")
    batch_convert.add_argument("folder", type=Path)
    batch_convert.add_argument("--vault", type=Path, required=True)
    batch_convert.add_argument("--unattended", action="store_true")
    batch_convert.add_argument("--tool")
    batch_convert.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    batch_convert.add_argument("--dry-run", action="store_true")
    batch_convert.add_argument("--explain", action="store_true")
    batch_convert.add_argument("--force", action="store_true")
    batch_convert.add_argument("--format", choices=["human", "json"], default="human")
    batch_convert.set_defaults(func=cmd_batch_convert)
    batch_transcribe = batch_sub.add_parser("transcribe")
    batch_transcribe.add_argument("folder", type=Path)
    batch_transcribe.add_argument("--vault", type=Path, required=True)
    batch_transcribe.add_argument("--unattended", action="store_true")
    batch_transcribe.add_argument("--kind", default="recording")
    batch_transcribe.add_argument("--tool")
    batch_transcribe.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    batch_transcribe.add_argument("--content")
    batch_transcribe.add_argument("--dry-run", action="store_true")
    batch_transcribe.add_argument("--explain", action="store_true")
    batch_transcribe.add_argument("--force", action="store_true")
    batch_transcribe.add_argument("--format", choices=["human", "json"], default="human")
    batch_transcribe.set_defaults(func=cmd_batch_transcribe)

    transcript = sub.add_parser("transcript")
    transcript_sub = transcript.add_subparsers(dest="command", required=True)
    transcript_create = transcript_sub.add_parser("create")
    transcript_create.add_argument("source")
    transcript_create.add_argument("--vault", type=Path, required=True)
    transcript_create.add_argument("--kind", default="recording")
    transcript_create.add_argument("--tool")
    transcript_create.add_argument("--sensitivity", choices=sorted(SENSITIVITY))
    transcript_create.add_argument("--content")
    transcript_create.add_argument("--dry-run", action="store_true")
    transcript_create.add_argument("--explain", action="store_true")
    transcript_create.add_argument("--force", action="store_true")
    transcript_create.set_defaults(func=cmd_transcript_create)

    reflection = sub.add_parser("reflection")
    reflection_sub = reflection.add_subparsers(dest="command", required=True)
    reflection_append = reflection_sub.add_parser("append")
    reflection_append.add_argument("--vault", type=Path, required=True)
    reflection_append.set_defaults(func=cmd_reflection_append)

    mirror = sub.add_parser("mirror")
    mirror_sub = mirror.add_subparsers(dest="command", required=True)
    mirror_write = mirror_sub.add_parser("write")
    mirror_write.add_argument("--vault", type=Path, required=True)
    mirror_write.add_argument("--force", action="store_true")
    mirror_write.set_defaults(func=cmd_mirror_write)

    feedback = sub.add_parser("feedback")
    feedback_sub = feedback.add_subparsers(dest="command", required=True)
    feedback_export = feedback_sub.add_parser("export")
    feedback_export.add_argument("--vault", type=Path, required=True)
    feedback_export.add_argument("--redact-list", type=Path, required=True)
    feedback_export.set_defaults(func=cmd_feedback_export)

    share = sub.add_parser("share")
    share_sub = share.add_subparsers(dest="command", required=True)
    share_generate = share_sub.add_parser("generate")
    share_generate.add_argument("--vault", type=Path, required=True)
    share_generate.add_argument("--for", dest="name", required=True)
    share_generate.add_argument("--sensitivity", choices=sorted(SENSITIVITY), default="medium")
    share_generate.add_argument("--mode", choices=["quick", "full"], default="quick")
    share_generate.set_defaults(func=cmd_share_generate)

    trust = sub.add_parser("trust")
    trust_sub = trust.add_subparsers(dest="command", required=True)
    trust_check = trust_sub.add_parser("check")
    trust_check.add_argument("action")
    trust_check.add_argument("--vault", type=Path, required=True)
    trust_check.add_argument("--trust-level", choices=sorted(TRUST_LEVELS))
    trust_check.add_argument("--format", choices=["human", "json"], default="human")
    trust_check.set_defaults(func=cmd_trust_check)
    trust_list = trust_sub.add_parser("list")
    trust_list.add_argument("--vault", type=Path, required=True)
    trust_list.add_argument("--trust-level", choices=sorted(TRUST_LEVELS))
    trust_list.add_argument("--format", choices=["human", "json"], default="human")
    trust_list.set_defaults(func=cmd_trust_list)
    trust_show = trust_sub.add_parser("show")
    trust_show.add_argument("--vault", type=Path, required=True)
    trust_show.add_argument("--format", choices=["human", "json"], default="human")
    trust_show.set_defaults(func=cmd_trust_show)

    automation = sub.add_parser("automation")
    automation_sub = automation.add_subparsers(dest="command", required=True)
    automation_configure = automation_sub.add_parser("configure")
    automation_configure.add_argument("--vault", type=Path, required=True)
    automation_configure.add_argument("--enabled", choices=["true", "false"], required=True)
    automation_configure.add_argument("--trust-level", choices=sorted(TRUST_LEVELS), required=True)
    automation_configure.add_argument("--schedule", choices=["daily", "weekdays", "weekly"], required=True)
    automation_configure.add_argument("--review-cadence", choices=["monthly", "quarterly", "biannual"], required=True)
    automation_configure.add_argument("--model", choices=["sonnet", "opus"], default="sonnet")
    automation_configure.add_argument("--inbox-processing", choices=["true", "false"])
    automation_configure.add_argument("--vault-health", choices=["true", "false"])
    automation_configure.add_argument("--cross-linking", choices=["true", "false"])
    automation_configure.add_argument("--gap-analysis", choices=["true", "false"])
    automation_configure.add_argument("--draft-feedback", choices=["true", "false"])
    automation_configure.add_argument("--reflection-synthesis", choices=["true", "false"])
    automation_configure.add_argument("--wiki-maintenance", choices=["true", "false"])
    automation_configure.set_defaults(func=cmd_automation_configure)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CarrelError as error:
        return emit_error(error)
