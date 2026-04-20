from __future__ import annotations
from datetime import date
from pathlib import Path

from carrel.convert.frontmatter import load_frontmatter, render_frontmatter
from carrel.models import FileResult, TranscribeTool
from carrel.safe_path import safe_vault_join
from carrel.source_hash import hash_source
from carrel.vault.organize import transcript_filename


def file_transcript(
    content: str,
    metadata: dict,
    vault: Path,
    source: str,
    tool: TranscribeTool,
    kind: str = "recording",
    force: bool = False,
) -> FileResult:
    source_hash = hash_source(source)
    output_path = safe_vault_join(
        vault,
        "transcripts",
        transcript_filename(
            source=source,
            date=date.today().isoformat(),
            kind=kind,
            title=metadata.get("title"),
        ),
    )
    payload = {
        "title": metadata.get("title"),
        "date": metadata.get("date") or date.today().isoformat(),
        "duration": metadata.get("duration"),
        "participants": metadata.get("participants"),
        "project": metadata.get("project"),
        "source_file": source,
        "transcribed": date.today().isoformat(),
        "transcriber": tool.value,
        "kind": kind,
        "source_hash": source_hash,
    }

    if output_path.exists():
        existing, _ = load_frontmatter(output_path)
        existing_hash = existing.get("source_hash")
        if existing_hash == source_hash:
            return FileResult(path=output_path, action="skipped", reason="already converted")
        if not force:
            return FileResult(
                path=output_path,
                action="skipped",
                reason="source changed -- pass --force to re-convert",
            )
        action = "overwritten"
    else:
        action = "created"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_frontmatter(content=content, metadata=payload), encoding="utf-8")
    return FileResult(path=output_path, action=action)
