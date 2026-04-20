from carrel.vault.organize import paper_dirname, sort_inbox, transcript_filename


def test_paper_dirname_fallbacks() -> None:
    assert paper_dirname("Kevin Corley and Dennis Gioia", "2004", "Identity Construction") == "corley-gioia-2004"
    assert paper_dirname("Kevin Corley and Dennis Gioia", None, "Identity Construction in Organizations") == "corley-gioia-identity-construction-organizations"
    assert paper_dirname(None, None, "Identity Construction in Organizations") == "identity-construction-in-organizations"
    assert paper_dirname(None, None, None, "original-filename.pdf") == "original-filename"


def test_transcript_filename_fallbacks() -> None:
    assert transcript_filename("interview-P001.m4a", "2026-03-26", kind="interview") == "interview-p001.md"
    assert transcript_filename("meeting.m4a", "2026-03-26", kind="meeting") == "meeting.md"
    assert transcript_filename("random.wav", "2026-03-26") == "recording-random.md"
    assert transcript_filename("https://youtube.com/watch?v=abc123", "2026-03-26") == "youtube-abc123.md"
    assert transcript_filename(
        "https://youtube.com/watch?v=abc123",
        "2026-03-26",
        title="Video Title Slug",
    ) == "video-title-slug.md"


def test_sort_inbox_suggests_destinations(tmp_path) -> None:
    vault = tmp_path / "vault"
    inbox = vault / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "paper.pdf").write_text("pdf", encoding="utf-8")
    (inbox / "meeting.m4a").write_text("audio", encoding="utf-8")
    (inbox / "idea.md").write_text("idea", encoding="utf-8")

    suggestions = sort_inbox(vault)
    by_source = {suggestion["source"].split("/")[-1]: suggestion for suggestion in suggestions}

    assert len(suggestions) == 3
    assert by_source["meeting.m4a"]["destination"].endswith("transcripts/recording-meeting.md")
    assert by_source["paper.pdf"]["destination"].endswith("papers/paper/paper.md")
    assert by_source["idea.md"]["destination"].endswith("notes/idea.md")
