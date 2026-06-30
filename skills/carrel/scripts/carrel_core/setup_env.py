from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from .constants import ADAPTER_PROFILE_KEYS, DEFAULT_PROFILE, SENSITIVITY, TRUST_LEVELS
from .core import CarrelError, default_profile, safe_atomic_write, safe_vault_join, write_profile


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
        if item.name in {"agent-context.md", "vault-scaffold.json", "obsidian-config.json"}:
            continue
        if item.suffix not in {".md", ".base"}:
            continue
        target = template_dir / item.name
        if target.is_symlink():
            raise CarrelError("Path escapes vault root", hint=f"Refusing template symlink {target}")
        if target.exists():
            continue
        safe_atomic_write(vault, target, item.read_text(encoding="utf-8"))
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
    paths = [
        item["path"]
        for item in folders
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]
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
        if target.is_symlink():
            raise CarrelError("Path escapes vault root", hint=f"Refusing Obsidian symlink {target}")
        if target.exists():
            continue
        text = value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True)
        safe_atomic_write(vault, target, text.rstrip() + "\n")
        written.append(filename)
    return written


def cmd_vault_init(args) -> int:
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
    if context_path.is_symlink():
        raise CarrelError("Path escapes vault root", hint=f"Refusing context symlink {context_path}")
    if not context_path.exists():
        safe_atomic_write(vault, context_path, context_asset.read_text(encoding="utf-8"))
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
        errors.append({"path": "sensitivity", "message": "sensitivity must be high, medium, or low"})
    automation = payload.get("automation", {})
    if isinstance(automation, dict):
        trust = automation.get("trust_level", "advisory")
        if trust not in TRUST_LEVELS:
            errors.append({"path": "automation.trust_level", "message": "trust_level is invalid"})
    else:
        errors.append({"path": "automation", "message": "automation must be an object"})
    for key in DEFAULT_PROFILE:
        if key not in payload:
            drift.append({"check": "missing_key", "field": key, "message": f"Missing top-level key: {key}"})
    return errors, drift


def cmd_env_validate(args) -> int:
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


def cmd_env_fix(args) -> int:
    path = args.vault / ".carrel" / "environment.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        payload = {}
    except json.JSONDecodeError as exc:
        raise CarrelError("Invalid environment.json", hint=exc.msg) from exc
    if not isinstance(payload, dict):
        raise CarrelError("Invalid environment.json", hint="Profile must be a JSON object")
    unknown_keys = {
        key: value
        for key, value in payload.items()
        if key not in DEFAULT_PROFILE and key not in ADAPTER_PROFILE_KEYS
    }
    existing_unknown = payload.get("_unknown_keys", {})
    if isinstance(existing_unknown, dict):
        unknown_keys = {**existing_unknown, **unknown_keys}
    fixed = default_profile()
    fixed.update(
        {
            key: value
            for key, value in payload.items()
            if key in DEFAULT_PROFILE or key in ADAPTER_PROFILE_KEYS
        }
    )
    fixed["_unknown_keys"] = unknown_keys
    current_automation = payload.get("automation", {})
    fixed["automation"] = {
        **DEFAULT_PROFILE["automation"],
        **(current_automation if isinstance(current_automation, dict) else {}),
    }
    changed = fixed != payload
    result = {"changed": changed, "path": str(path), "dry_run": args.dry_run}
    if changed and not args.dry_run:
        if path.exists():
            backup = safe_vault_join(args.vault, ".carrel", "environment.json.bak")
            safe_atomic_write(args.vault, backup, path.read_text(encoding="utf-8"))
            result["backup"] = str(backup)
        write_profile(args.vault, fixed)
    print(json.dumps(result) if args.format == "json" else ("updated" if changed else "ok"))
    return 0


def cmd_env_doctor(args) -> int:
    tool_names = ["git", "node", "bun", "uv", "lit", "markitdown", "defuddle", "coli", "gws"]
    binaries = {
        name: {"installed": shutil.which(name) is not None, "path": shutil.which(name)}
        for name in tool_names
    }
    payload = {
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "project_path": str(args.project_path.expanduser().resolve()) if args.project_path else None,
        "binaries": binaries,
        "api_keys": {
            "mineru": bool(os.environ.get("MINERU_API_KEY")),
            "mistral": bool(os.environ.get("MISTRAL_API_KEY")),
            "groq": bool(os.environ.get("GROQ_API_KEY")),
            "gemini": bool(os.environ.get("GEMINI_API_KEY")),
        },
        "optional_adapters": {
            "capture": ["defuddle", "markitdown"],
            "convert": ["lit", "markitdown", "mineru", "mistral_ocr", "paddleocr"],
            "transcribe": ["coli", "groq", "gemini"],
            "google": ["gws"],
        },
    }
    if args.format == "json":
        print(json.dumps(payload))
    else:
        installed = ", ".join(name for name, data in binaries.items() if data["installed"]) or "none"
        print(f"platform: {payload['platform']}\npython: {payload['python']}\ninstalled: {installed}")
    return 0
