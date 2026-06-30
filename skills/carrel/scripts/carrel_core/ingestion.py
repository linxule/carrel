from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from .constants import (
    AUDIO_EXTENSIONS,
    DOC_EXTENSIONS,
    GOOGLE_WORKSPACE_EXPORTS,
    SENSITIVITY,
    URL_LIST_EXTENSION,
)
from .core import (
    CarrelError,
    atomic_write,
    available_tools,
    read_profile,
    render_frontmatter,
    safe_vault_join,
    select_tool,
    slugify,
    source_hash,
)


def cmd_policy_explain(args) -> int:
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


def capture_content(url: str, args) -> tuple[str, dict, str]:
    if args.content:
        return args.content, {"title": args.title or urlparse(url).netloc, "domain": urlparse(url).netloc}, "provided"
    for tool, command in [("defuddle", "defuddle"), ("markitdown", "markitdown")]:
        if shutil.which(command):
            proc = subprocess.run([command, url], text=True, capture_output=True, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout, {"title": args.title or urlparse(url).netloc, "domain": urlparse(url).netloc}, tool
    raise CarrelError("No capture adapter available", hint="Install defuddle/markitdown or pass --content.")


def cmd_capture_url(args) -> int:
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


def cmd_convert_file(args) -> int:
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
        decision = select_tool("convert", args.tool, available, sensitivity, bool(profile.get("cloud_consent")))
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


def cmd_transcript_create(args) -> int:
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
        decision = select_tool("transcribe", args.tool, available, sensitivity, bool(profile.get("cloud_consent")))
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
        raise CarrelError("Unsupported Google Workspace URL", hint="Use a docs.google.com/document, spreadsheets, or presentation URL.")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[1] != "d":
        raise CarrelError("Unsupported Google Workspace URL", hint="Expected docs.google.com/<kind>/d/<id>/edit.")
    kind = parts[0]
    if kind not in GOOGLE_WORKSPACE_EXPORTS:
        raise CarrelError("Unsupported Google Workspace file type", hint="Supported kinds: document, spreadsheets, presentation.")
    return kind, parts[2]


def google_export_target(vault: Path, url: str, export_format: str) -> tuple[str, str, Path]:
    kind, file_id = parse_google_workspace_url(url)
    try:
        mime_type, suffix = GOOGLE_WORKSPACE_EXPORTS[kind][export_format]
    except KeyError as exc:
        raise CarrelError("Unsupported export format", hint=f"{kind} files do not support --export-format {export_format}.") from exc
    target = safe_vault_join(vault, ".carrel", "exports", f"{file_id}{suffix}")
    return file_id, mime_type, target


def cmd_google_export(args) -> int:
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
        decision = select_tool("convert", args.tool, available, sensitivity, bool(profile.get("cloud_consent")))
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


def cmd_batch_convert(args) -> int:
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
            outcomes.append({"file": str(file_path), "action": "converted" if code == 0 else "failed", "detail": child_out.getvalue().strip() or "ok"})
        except CarrelError as error:
            action = "deferred" if args.unattended else "failed"
            if args.unattended:
                append_pending_decision(args.vault, f"`{file_path.name}` - convert failed: {error.message}")
            outcomes.append({"file": str(file_path), "action": action, "detail": error.message})
    print(json.dumps(outcomes) if args.format == "json" else "\n".join(item["file"] for item in outcomes))
    return 0 if all(item["action"] in {"converted", "deferred"} for item in outcomes) else 1


def read_urls(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def cmd_batch_transcribe(args) -> int:
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
