from __future__ import annotations
from datetime import date
from pathlib import Path

from carrel.convert.frontmatter import load_frontmatter, render_frontmatter
from carrel.models import ConvertTool, FileResult
from carrel.safe_path import safe_vault_join
from carrel.source_hash import hash_source
from carrel.vault.organize import paper_dirname


def file_paper(
    content: str,
    metadata: dict,
    vault: Path,
    source_file: Path,
    tool: ConvertTool,
    force: bool = False,
) -> FileResult:
    source_hash = hash_source(source_file)
    dirname = paper_dirname(
        authors=metadata.get("authors"),
        year=str(metadata["year"]) if metadata.get("year") is not None else None,
        title=metadata.get("title"),
        source_filename=source_file.name,
    )
    output_path = safe_vault_join(vault, "papers", dirname, "paper.md")
    payload = {
        "title": metadata.get("title") or source_file.stem,
        "authors": metadata.get("authors"),
        "year": metadata.get("year"),
        "journal": metadata.get("journal"),
        "doi": metadata.get("doi"),
        "source_file": source_file.name,
        "converted": date.today().isoformat(),
        "converter": tool.value,
        "source_hash": source_hash,
        "tags": metadata.get("tags", []),
        "status": metadata.get("status", "unread"),
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
