from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
BASE_NAMES = {
    "interview-tracker.base",
    "paper-tracker.base",
    "reading-progress.base",
    "writing-tracker.base",
}


def _load_base(path: Path) -> tuple[str, dict]:
    text = path.read_text(encoding="utf-8")
    payload = yaml.safe_load(text)
    assert isinstance(payload, dict), path
    return text, payload


def test_shipped_bases_use_current_schema_and_match_portable_assets() -> None:
    for name in BASE_NAMES:
        root_path = ROOT / "templates" / name
        portable_path = SKILLS / "carrel" / "assets" / "templates" / name
        text, payload = _load_base(root_path)

        assert portable_path.read_bytes() == root_path.read_bytes(), name
        assert text.splitlines()[0].endswith("v0.4.0"), name
        assert isinstance(payload["filters"], (str, dict)), name
        assert isinstance(payload["formulas"], dict), name
        assert isinstance(payload["properties"], dict), name
        assert isinstance(payload["summaries"], dict), name
        assert isinstance(payload["views"], list) and payload["views"], name
        assert "filter" not in payload, name
        assert "sort" not in payload, name

        defined_formulas = set(payload["formulas"])
        referenced_formulas = {
            match.removeprefix("formula.")
            for match in re.findall(r"formula\.[A-Za-z0-9_]+", text)
        }
        assert referenced_formulas <= defined_formulas, name

        for view in payload["views"]:
            assert isinstance(view.get("order"), list) and view["order"], (name, view)
            assert "filter" not in view, (name, view["name"])
            assert "group" not in view, (name, view["name"])
            if "filters" in view:
                assert isinstance(view["filters"], (str, dict)), (name, view["name"])
            if "groupBy" in view:
                assert set(view["groupBy"]) == {"property", "direction"}, (name, view["name"])
            for sort in view.get("sort", []):
                assert sort["direction"] in {"ASC", "DESC"}, (name, view["name"])


def test_base_semantics_cover_dates_and_hyphenated_properties_safely() -> None:
    interview = (ROOT / "templates" / "interview-tracker.base").read_text(encoding="utf-8")
    writing = (ROOT / "templates" / "writing-tracker.base").read_text(encoding="utf-8")

    assert 'displayName: "Transcribed on"' in interview
    assert 'note["follow-up"]' in interview
    assert 'note["due-date"]' in writing
    assert 'date(note["due-date"])' in writing
    assert 'note["blockers"]' in writing


def test_canvas_reference_example_conforms_to_json_canvas_contract() -> None:
    path = SKILLS / "research-partner" / "references" / "concept-mapping.md"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```json\n(.*?)\n```", text, flags=re.DOTALL)
    assert match
    canvas = json.loads(match.group(1))

    node_ids = [node["id"] for node in canvas["nodes"]]
    edge_ids = [edge["id"] for edge in canvas["edges"]]
    assert len(set(node_ids + edge_ids)) == len(node_ids) + len(edge_ids)
    assert all(re.fullmatch(r"[0-9a-f]{16}", item) for item in node_ids + edge_ids)
    assert {node["type"] for node in canvas["nodes"]} >= {"text", "file", "link"}
    assert all(edge["fromNode"] in node_ids and edge["toNode"] in node_ids for edge in canvas["edges"])
    assert "A group label is optional" in text


def test_wiki_docs_define_approved_batch_provenance_and_quality_contracts() -> None:
    skill = (SKILLS / "knowledge-wiki" / "SKILL.md").read_text(encoding="utf-8")
    protocol = (SKILLS / "knowledge-wiki" / "references" / "wiki-protocol.md").read_text(
        encoding="utf-8"
    )
    portable = (SKILLS / "carrel" / "references" / "workflows" / "field-map.md").read_text(
        encoding="utf-8"
    )
    combined = "\n".join((skill, protocol, portable))

    for token in (
        "wiki:propose",
        "wiki:apply-approved",
        "wiki:write",
        "source_digests",
        "confidence: high | medium | low",
        "contested: true",
        "contradictions:",
        "^[papers/",
        "single-source",
        "source drift",
    ):
        assert token in combined
    assert "A direct request does not bypass" in skill
    assert "separate `raw/` layer" in skill
    assert "does not import Hermes' separate `raw/` layer" in skill


def test_external_refresh_manifest_v2_dates_only_refreshed_contracts() -> None:
    path = SKILLS / "carrel" / "references" / "contracts" / "external-refresh.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = {entry["id"]: entry for entry in manifest["entries"]}

    assert manifest["manifest_version"] == 2
    assert manifest["last_full_reviewed"] == "2026-06-30"
    assert "last_reviewed" in manifest["entry_required_fields"]
    assert entries["liteparse"]["observed_version"] == "2.5.0"
    assert entries["liteparse"]["last_reviewed"] == "2026-07-10"
    assert entries["claude-app-desktop"]["last_reviewed"] == "2026-07-10"
    assert entries["obsidian"]["last_reviewed"] == "2026-07-10"
    assert all(date.fromisoformat(entry["last_reviewed"]) <= date(2026, 7, 10) for entry in entries.values())
    assert all(
        entry["last_reviewed"] == "2026-06-30"
        for key, entry in entries.items()
        if key not in {"liteparse", "claude-app-desktop", "obsidian"}
    )
    assert "npm install -g @llamaindex/liteparse" in entries["liteparse"]["refresh_checks"][0]
    assert any("schedule-recurring-tasks" in source for source in entries["claude-app-desktop"]["sources"])


def test_capability_registry_records_current_upstream_review_pins() -> None:
    text = (SKILLS / "self-improve" / "references" / "capability-registry.md").read_text(
        encoding="utf-8"
    )
    assert "a1dc48e68138490d522c04cbf5822214c6eb1202" in text
    assert "9b736ba8da230341054cc668bedc0bcb041baa98" in text
    assert "llm-wiki` v2.1.0" in text
    assert "8e3f9537db21b49ebe796f7b5a6ff489028fe1fb" in text
    assert text.count("2026-10-10") >= 4
    assert "Hermes `raw/` source layer and `WIKI_PATH`" in text


def test_skill_frontmatter_names_size_and_references_are_portable() -> None:
    skill_paths = sorted(SKILLS.glob("*/SKILL.md"))
    assert len(skill_paths) == 14

    for path in skill_paths:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert len(lines) < 500, (path, len(lines))
        match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert match, path
        frontmatter = yaml.safe_load(match.group(1))
        # Host-split (2026-07-10): the portable `carrel` pack is the standalone
        # engine for non-plugin hosts, so it carries the agentskills.io spec
        # fields `license` + `compatibility` on top of the plugin baseline; the
        # 13 plugin skills stay strict {name, description}.
        if path.parent.name == "carrel":
            assert set(frontmatter) == {"name", "description", "license", "compatibility"}, path
        else:
            assert set(frontmatter) == {"name", "description"}, path
        assert frontmatter["name"] == path.parent.name, path

        for ref in re.findall(r"`((?:skills/)?(?:[A-Za-z0-9_-]+/)*references/[A-Za-z0-9_./-]+\.md)`", text):
            candidates = [path.parent / ref, SKILLS / ref, ROOT / ref]
            assert any(target.is_file() for target in candidates), (path, ref)


def test_active_skill_docs_reject_stale_command_and_product_claims() -> None:
    active_paths = [
        ROOT / "README.md",
        ROOT / "CLAUDE.md",
        *(ROOT / "commands").rglob("*.md"),
        *(ROOT / "docs").rglob("*.md"),
        *SKILLS.rglob("*.md"),
    ]
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in active_paths)
    automation = (SKILLS / "automation" / "SKILL.md").read_text(encoding="utf-8")
    vault_ops = (SKILLS / "vault-ops" / "SKILL.md").read_text(encoding="utf-8")
    transcribe = (SKILLS / "transcribe" / "SKILL.md").read_text(encoding="utf-8")

    assert "carrel vault new <name> --template <template>" in vault_ops
    assert "carrel vault new <template> <name>" not in corpus
    assert "plain transcript text" in transcribe
    assert "gives word-level timestamps" not in corpus
    assert "carrel automate configure --enabled true" not in automation
    assert "configure --enabled <bool>" not in corpus
    assert "--mode interactive" not in corpus
    assert "Schedule tab" not in corpus
    assert "New local task" not in corpus
    assert "$3-8/month" not in corpus
    assert "279 tests" not in corpus
    assert "13 skills" not in corpus
    assert "Carrel v0.4 runs" not in corpus
    assert "v0.3.0" not in corpus
    assert "references/cowork-scheduling-guide.md" in automation
    assert not (SKILLS / "automation" / "references" / "desktop-scheduling-guide.md").exists()
    reflection = (SKILLS / "session-reflection" / "SKILL.md").read_text(encoding="utf-8")
    assert "environment.json` → `researcher_name" not in reflection


def test_automation_prompt_assets_create_pending_files_only_for_real_items() -> None:
    paths = [
        ROOT / "templates" / "automation-prompt.md",
        SKILLS / "carrel" / "assets" / "templates" / "automation-prompt.md",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "only when an actual ambiguous item is deferred" in text, path
        assert "only when proposing a concrete action" in text, path
        assert "never execute the proposal unattended" in text, path


def test_collaborator_and_feedback_skills_match_current_cli_contracts() -> None:
    collaborator = (SKILLS / "collaborator-onboarding" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    reflection = (SKILLS / "session-reflection" / "SKILL.md").read_text(encoding="utf-8")

    assert "--mode full" in collaborator
    assert "--from-stdin" in collaborator
    assert "--canonical" in collaborator
    assert "--mode interactive" not in collaborator
    assert "does not read vault sources, synthesize prose, or sanitize" in collaborator
    assert "environment.json` → `name`" in reflection
    assert "preferences.institution" in reflection
    assert "original -> replacement" in reflection
    assert "researcher_name" not in reflection
