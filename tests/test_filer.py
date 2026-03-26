from pathlib import Path

import frontmatter

from carrel.convert.filer import file_paper
from carrel.models import ConvertTool, TranscribeTool
from carrel.transcribe.filer import file_transcript


def test_file_paper_idempotency_and_force(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / "papers").mkdir(parents=True)
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"first-version")

    first = file_paper(
        content="# Paper",
        metadata={"title": "Identity Construction", "authors": "Kevin Corley and Dennis Gioia", "year": "2004"},
        vault=vault,
        source_file=source,
        tool=ConvertTool.LITEPARSE,
    )
    assert first.action == "created"
    stored = frontmatter.load(first.path)
    assert stored["source_hash"]

    second = file_paper(
        content="# Paper",
        metadata={"title": "Identity Construction", "authors": "Kevin Corley and Dennis Gioia", "year": "2004"},
        vault=vault,
        source_file=source,
        tool=ConvertTool.LITEPARSE,
    )
    assert second.action == "skipped"
    assert second.reason == "already converted"

    source.write_bytes(b"second-version")
    third = file_paper(
        content="# Updated",
        metadata={"title": "Identity Construction", "authors": "Kevin Corley and Dennis Gioia", "year": "2004"},
        vault=vault,
        source_file=source,
        tool=ConvertTool.LITEPARSE,
    )
    assert third.action == "skipped"
    assert third.reason == "source changed -- pass --force to re-convert"

    fourth = file_paper(
        content="# Updated",
        metadata={"title": "Identity Construction", "authors": "Kevin Corley and Dennis Gioia", "year": "2004"},
        vault=vault,
        source_file=source,
        tool=ConvertTool.LITEPARSE,
        force=True,
    )
    assert fourth.action == "overwritten"


def test_file_transcript_idempotency_and_force(tmp_path) -> None:
    vault = tmp_path / "vault"
    (vault / "transcripts").mkdir(parents=True)
    source = tmp_path / "meeting.m4a"
    source.write_bytes(b"meeting-audio")

    first = file_transcript(
        content="Transcript body",
        metadata={"title": "Weekly Lab Meeting"},
        vault=vault,
        source=str(source),
        tool=TranscribeTool.COLI,
        kind="meeting",
    )
    assert first.action == "created"
    assert first.path.name.endswith(".md")

    second = file_transcript(
        content="Transcript body",
        metadata={"title": "Weekly Lab Meeting"},
        vault=vault,
        source=str(source),
        tool=TranscribeTool.COLI,
        kind="meeting",
    )
    assert second.action == "skipped"
    assert second.reason == "already converted"

    source.write_bytes(b"updated-meeting-audio")
    third = file_transcript(
        content="Transcript body",
        metadata={"title": "Weekly Lab Meeting"},
        vault=vault,
        source=str(source),
        tool=TranscribeTool.COLI,
        kind="meeting",
    )
    assert third.action == "skipped"

    fourth = file_transcript(
        content="Transcript body",
        metadata={"title": "Weekly Lab Meeting"},
        vault=vault,
        source=str(source),
        tool=TranscribeTool.COLI,
        kind="meeting",
        force=True,
    )
    assert fourth.action == "overwritten"
