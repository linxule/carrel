from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "carrel"


def _copy_skill(tmp_path: Path) -> Path:
    target = tmp_path / "carrel-skill"
    shutil.copytree(SKILL, target)
    return target


def _run(
    skill: Path,
    *args: str,
    input_text: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = ""
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(skill / "scripts" / "carrel.py"), *args],
        input=input_text,
        text=True,
        capture_output=True,
        cwd=skill.parent,
        env=env,
        check=False,
        timeout=15,
    )


def test_carrel_skill_pack_layout_and_metadata() -> None:
    skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert skill_md.startswith("---\nname: carrel\n")
    assert "description:" in skill_md
    assert len(skill_md.splitlines()) < 500
    openai_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "interface:\n" in openai_yaml
    assert 'default_prompt: "Use $carrel' in openai_yaml
    assert (SKILL / "scripts" / "carrel.py").exists()
    assert (SKILL / "scripts" / "carrel_core" / "runtime.py").exists()
    assert (SKILL / "references" / "contracts" / "vault-contract.md").exists()
    assert (SKILL / "references" / "contracts" / "surface-map.md").exists()
    assert (SKILL / "references" / "contracts" / "host-compatibility.md").exists()
    assert (SKILL / "references" / "contracts" / "external-refresh.json").exists()
    assert (SKILL / "references" / "workflows" / "onboarding.md").exists()
    assert (SKILL / "references" / "workflows" / "ingestion.md").exists()
    assert (SKILL / "assets" / "templates" / "agent-context.md").exists()


def test_carrel_skill_pack_has_no_generated_files() -> None:
    banned = []
    for item in SKILL.rglob("*"):
        if "__pycache__" in item.parts or item.suffix == ".pyc":
            banned.append(str(item.relative_to(SKILL)))
    assert banned == []


def test_carrel_skill_workflow_references_are_routed_and_previewable() -> None:
    skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    workflows = sorted((SKILL / "references" / "workflows").glob("*.md"))
    assert workflows
    for workflow in workflows:
        rel = workflow.relative_to(SKILL).as_posix()
        body = workflow.read_text(encoding="utf-8")
        assert rel in skill_md
        if len(body.splitlines()) > 100:
            assert "## Contents" in body


def test_carrel_skill_runtime_commands_listed_in_skill_parse(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    runtime_section = skill_md.split("## Runtime Boundary", 1)[1].split("## Host Adapters", 1)[0]
    commands = [
        line.removeprefix("- `").removesuffix("`")
        for line in runtime_section.splitlines()
        if line.startswith("- `") and line.endswith("`")
    ]
    assert commands
    for command in commands:
        result = _run(skill, *command.split(), "--help")
        assert result.returncode == 0, (command, result.stderr)


def test_carrel_skill_pack_surface_map_covers_legacy_cli_families() -> None:
    surface_map = (SKILL / "references" / "contracts" / "surface-map.md").read_text(encoding="utf-8")
    for phrase in [
        "vault init",
        "env doctor",
        "env validate",
        "env fix",
        "paper convert",
        "capture url",
        "transcript create",
        "google export",
        "batch convert",
        "batch transcribe",
        "trust check",
        "automate configure",
        "vault new",
        "vault search",
        "vault status",
        "vault organize",
        "vault cheatsheet",
        "vault dashboard",
        "vault automation-prompt",
        "env profile",
        "paper list",
        "transcript list",
        "migrate apply",
        "setup-state advance",
        "vault check-sync",
        "vault add-markers",
        "Slash commands and hooks",
    ]:
        assert phrase in surface_map


def test_carrel_skill_legacy_only_surfaces_are_rejected_by_portable_runtime(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    surface_map = (SKILL / "references" / "contracts" / "surface-map.md").read_text(encoding="utf-8")
    legacy_commands = [
        ("automate", "configure"),
        ("setup-state", "advance"),
        ("migrate", "apply"),
        ("vault", "check-sync"),
        ("vault", "add-markers"),
        ("vault", "new"),
        ("vault", "dashboard"),
        ("paper", "list"),
        ("transcript", "list"),
    ]
    for command in legacy_commands:
        assert " ".join(command) in surface_map
        result = _run(skill, *command, "--help")
        assert result.returncode != 0, command


def test_carrel_skill_runtime_modules_stay_small() -> None:
    modules = sorted((SKILL / "scripts" / "carrel_core").glob("*.py"))
    oversized = {
        module.name: len(module.read_text(encoding="utf-8").splitlines())
        for module in modules
        if module.name != "cli.py" and len(module.read_text(encoding="utf-8").splitlines()) > 400
    }
    assert oversized == {}


def test_carrel_skill_host_compatibility_contract_documents_adapter_boundary() -> None:
    body = (SKILL / "references" / "contracts" / "host-compatibility.md").read_text(encoding="utf-8")
    assert "entire `carrel/` skill folder" in body
    assert "Python 3.10" in body
    assert "python3 <skill-dir>/scripts/carrel.py" in body
    assert "Codex CLI" in body
    assert "Claude Code" in body
    assert "Kimi Code" in body
    assert "Cloud provider calls" in body


def test_carrel_skill_external_help_points_to_source_manifest() -> None:
    skill_body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    body = (SKILL / "references" / "contracts" / "external-help.md").read_text(encoding="utf-8")
    assert "references/contracts/external-help.md" in skill_body
    assert "external-refresh.json" in body
    assert "`sources`" in body
    assert "mistral-ocr" in body
    assert "paddleocr" in body


def test_carrel_skill_onboarding_is_host_neutral_and_script_bounded() -> None:
    skill_body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    body = (SKILL / "references" / "workflows" / "onboarding.md").read_text(encoding="utf-8")
    assert "references/workflows/onboarding.md" in skill_body
    assert "preferences.agent_host" in body
    assert "preferences.agent_experience" in body
    assert ".carrel/agent-context.md" in body
    assert "CLAUDE.md" not in body
    assert "claude_code_familiarity" not in body
    assert "/carrel-" not in body
    assert "vault init" in body
    assert "env validate" in body
    assert "env fix --dry-run" in body


def test_carrel_skill_external_refresh_manifest_is_actionable() -> None:
    manifest_path = SKILL / "references" / "contracts" / "external-refresh.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 2
    assert manifest["last_full_reviewed"] == "2026-06-30"
    assert manifest["refresh_cadence"] == "monthly"
    entries = manifest["entries"]
    required_ids = {
        "liteparse",
        "markitdown",
        "defuddle",
        "coli",
        "gws",
        "mineru",
        "mistral-ocr",
        "paddleocr",
        "groq",
        "gemini",
        "youtube-transcript-api",
        "codex-skills",
        "claude-code-skills",
        "claude-app-desktop",
        "kimi-code-skills",
        "opencode-skills",
        "gemini-cli-skills",
        "obsidian",
        "zotero",
        "vox-openrouter",
        "diagnostic-tools",
    }
    ids = {entry["id"] for entry in entries}
    assert required_ids <= ids
    assert len(ids) == len(entries)

    for entry in entries:
        for field in manifest["entry_required_fields"]:
            assert field in entry, entry["id"]
        date.fromisoformat(entry["last_reviewed"])
        assert entry["sources"], entry["id"]
        assert entry["skill_references"] or entry["repo_references"], entry["id"]
        assert entry["refresh_checks"], entry["id"]
        assert entry["contract_marker"], entry["id"]
        for skill_ref in entry["skill_references"]:
            assert (SKILL / skill_ref).exists(), (
                entry["id"],
                skill_ref,
            )
        for repo_ref in entry["repo_references"]:
            assert (Path(__file__).resolve().parents[1] / repo_ref).exists(), (
                entry["id"],
                repo_ref,
            )

    liteparse = next(entry for entry in entries if entry["id"] == "liteparse")
    assert liteparse["last_reviewed"] == "2026-07-10"
    assert liteparse["observed_version"] == "2.5.0"


def test_carrel_skill_env_doctor_separates_tool_ids_executables_and_candidates(tmp_path) -> None:
    skill = _copy_skill(tmp_path)

    result = _run(skill, "env", "doctor", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["optional_adapters"]["convert"] == [
        "liteparse",
        "markdownify",
        "mineru",
        "mistral_ocr",
    ]
    assert payload["adapter_executables"]["liteparse"] == "lit"
    assert payload["adapter_executables"]["markdownify"] == "markitdown"
    assert payload["tracked_candidates"]["convert"] == ["paddleocr"]


def test_carrel_skill_pack_has_no_required_claude_plugin_dependency() -> None:
    scanned = []
    for root in ["SKILL.md", "references", "scripts"]:
        path = SKILL / root
        files = [path] if path.is_file() else sorted(path.rglob("*"))
        for item in files:
            if item.is_file() and item.suffix in {".md", ".py", ".yaml"}:
                scanned.append(item.read_text(encoding="utf-8"))
    combined = "\n".join(scanned)
    assert ".claude-plugin" not in combined
    assert "CLAUDE_PLUGIN_ROOT" not in combined
    assert "/carrel-" not in combined
    assert "hooks.json" not in combined


def test_carrel_skill_runtime_initializes_portable_vault(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"

    result = _run(skill, "vault", "init", str(vault), "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert Path(payload["profile"]) == vault / ".carrel" / "environment.json"
    assert Path(payload["context"]) == vault / ".carrel" / "agent-context.md"
    assert (vault / "_templates" / "paper.md").exists()
    assert (vault / "reading-progress.base").exists()
    assert payload["bases_created"] == ["reading-progress.base"]
    assert payload["outdated_templates"] == []
    assert payload["unversioned_templates"] == []
    assert not (vault / "_templates" / "reading-progress.base").exists()
    assert not (vault / "_templates" / "paper-tracker.base").exists()
    assert not (vault / "_templates" / "agent-context.md").exists()
    assert not (vault / "_templates" / "vault-scaffold.json").exists()
    assert not (vault / "_templates" / "obsidian-config.json").exists()
    assert (vault / "_meta" / "local").is_dir()
    assert (vault / ".obsidian" / "app.json").exists()
    json.loads((vault / ".obsidian" / "workspace.json").read_text(encoding="utf-8"))
    assert not (vault / "CLAUDE.md").exists()
    profile = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert profile["sensitivity"] == "medium"
    assert profile["cloud_consent"] is False


def test_carrel_skill_runtime_init_uses_validated_profile_and_selected_bases(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    seed = tmp_path / "seed"
    assert _run(skill, "vault", "init", str(seed)).returncode == 0
    profile = json.loads((seed / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    profile.update({"version": "0.9.0", "name": "Ada", "field": "History"})
    profile["_unknown_keys"] = {"recognized-container": "preserved"}
    profile["arbitrary_top_level"] = "discarded like Pydantic extra fields"
    profile["preferences"] = {
        "literature_review": True,
        "interviews": True,
        "dissertation": True,
    }
    profile_file = tmp_path / "profile.json"
    profile_file.write_text(json.dumps(profile), encoding="utf-8")
    vault = tmp_path / "profiled-vault"

    result = _run(
        skill,
        "vault",
        "init",
        str(vault),
        "--profile-file",
        str(profile_file),
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert set(payload["bases_created"]) == {
        "reading-progress.base",
        "paper-tracker.base",
        "interview-tracker.base",
        "writing-tracker.base",
    }
    written = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert written == {key: value for key, value in profile.items() if key != "arbitrary_top_level"}
    assert written["version"] == "0.9.0"
    assert written["_unknown_keys"] == {"recognized-container": "preserved"}
    assert not list((vault / "_templates").glob("*.base"))

    repeated = _run(
        skill,
        "vault",
        "init",
        str(vault),
        "--profile-file",
        str(profile_file),
        "--format",
        "json",
    )
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)["bases_created"] == []


def test_carrel_skill_runtime_init_reuses_profile_and_rejects_conflicts(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0
    profile_path = vault / ".carrel" / "environment.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["preferences"] = {"thesis": True}
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    reused = _run(skill, "vault", "init", str(vault), "--format", "json")
    assert reused.returncode == 0, reused.stderr
    assert (vault / "writing-tracker.base").exists()

    equivalent = {**profile, "version": None, "ignored_extra": True}
    equivalent_file = tmp_path / "equivalent.json"
    equivalent_file.write_text(json.dumps(equivalent), encoding="utf-8")
    equivalent_result = _run(
        skill,
        "vault",
        "init",
        str(vault),
        "--profile-file",
        str(equivalent_file),
    )
    assert equivalent_result.returncode == 0, equivalent_result.stderr
    assert "version" not in json.loads(profile_path.read_text(encoding="utf-8"))
    assert "ignored_extra" not in json.loads(profile_path.read_text(encoding="utf-8"))

    conflicting = {**profile, "name": "Different Researcher"}
    conflict_file = tmp_path / "conflict.json"
    conflict_file.write_text(json.dumps(conflicting), encoding="utf-8")
    before = profile_path.read_text(encoding="utf-8")
    conflict = _run(
        skill,
        "vault",
        "init",
        str(vault),
        "--profile-file",
        str(conflict_file),
    )
    assert conflict.returncode == 1
    assert "conflicts with existing" in conflict.stderr
    assert profile_path.read_text(encoding="utf-8") == before


def test_carrel_skill_runtime_init_validates_profile_before_target_creation(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    invalid_json = tmp_path / "invalid-json.json"
    invalid_json.write_text("{not json", encoding="utf-8")
    invalid_schema = tmp_path / "invalid-schema.json"
    invalid_schema.write_text(json.dumps({"cloud_consent": "yes"}), encoding="utf-8")

    for index, profile_file in enumerate((invalid_json, invalid_schema)):
        vault = tmp_path / f"invalid-vault-{index}"
        result = _run(
            skill,
            "vault",
            "init",
            str(vault),
            "--profile-file",
            str(profile_file),
        )
        assert result.returncode == 1
        assert not vault.exists()


def test_carrel_skill_runtime_init_reports_template_drift_without_overwriting(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0
    reading = vault / "reading-progress.base"
    old_body = reading.read_text(encoding="utf-8").replace(
        "# carrel-template: reading-progress v0.4.0",
        "# carrel-template: reading-progress v0.0.1",
    ).replace(
        "# carrel-template: reading-progress v0.3.0",
        "# carrel-template: reading-progress v0.0.1",
    )
    reading.write_text(old_body, encoding="utf-8")
    custom = vault / "paper-tracker.base"
    custom.write_text("# Researcher-owned custom tracker\n", encoding="utf-8")
    interview_source = skill / "assets" / "templates" / "interview-tracker.base"
    newer = interview_source.read_text(encoding="utf-8").splitlines()
    newer[0] = "# carrel-template: interview-tracker v99.0.0"
    (vault / "interview-tracker.base").write_text("\n".join(newer) + "\n", encoding="utf-8")
    writing_source = skill / "assets" / "templates" / "writing-tracker.base"
    mismatched = writing_source.read_text(encoding="utf-8").splitlines()
    mismatched[0] = mismatched[0].replace("writing-tracker", "different-template")
    (vault / "writing-tracker.base").write_text("\n".join(mismatched) + "\n", encoding="utf-8")

    result = _run(skill, "vault", "init", str(vault), "--format", "json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["outdated_templates"] == ["reading-progress.base"]
    assert payload["unversioned_templates"] == ["paper-tracker.base", "writing-tracker.base"]
    assert reading.read_text(encoding="utf-8") == old_body
    assert custom.read_text(encoding="utf-8") == "# Researcher-owned custom tracker\n"


def test_carrel_skill_runtime_rejects_symlink_write_escape(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / ".carrel" / "agent-context.md").symlink_to(tmp_path / "outside-context.md")

    result = _run(skill, "vault", "init", str(vault), "--format", "json")

    assert result.returncode == 1
    assert "Path escapes vault root" in result.stderr
    assert not (tmp_path / "outside-context.md").exists()
    assert not (vault / "inbox").exists()
    assert not (vault / ".carrel" / "environment.json").exists()


def test_carrel_skill_runtime_init_preflights_tracker_and_scaffold_hazards(tmp_path) -> None:
    skill = _copy_skill(tmp_path)

    tracker_vault = tmp_path / "tracker-vault"
    tracker_vault.mkdir()
    outside_tracker = tmp_path / "outside-tracker.base"
    outside_tracker.write_text("outside stays unchanged\n", encoding="utf-8")
    (tracker_vault / "reading-progress.base").symlink_to(outside_tracker)
    tracker = _run(skill, "vault", "init", str(tracker_vault))
    assert tracker.returncode == 1
    assert "Path escapes vault root" in tracker.stderr
    assert outside_tracker.read_text(encoding="utf-8") == "outside stays unchanged\n"
    assert not (tracker_vault / "inbox").exists()
    assert not (tracker_vault / ".carrel").exists()

    template_vault = tmp_path / "template-vault"
    template_vault.mkdir()
    outside_templates = tmp_path / "outside-templates"
    outside_templates.mkdir()
    (template_vault / "_templates").symlink_to(outside_templates, target_is_directory=True)
    templates = _run(skill, "vault", "init", str(template_vault))
    assert templates.returncode == 1
    assert "Path escapes vault root" in templates.stderr
    assert list(outside_templates.iterdir()) == []
    assert not (template_vault / "inbox").exists()
    assert not (template_vault / ".carrel").exists()

    blocked_vault = tmp_path / "blocked-vault"
    blocked_vault.mkdir()
    (blocked_vault / "papers").write_text("not a directory\n", encoding="utf-8")
    blocked = _run(skill, "vault", "init", str(blocked_vault))
    assert blocked.returncode == 1
    assert "Expected directory" in blocked.stderr
    assert not (blocked_vault / "inbox").exists()
    assert not (blocked_vault / ".carrel").exists()


def test_carrel_skill_runtime_validate_and_fix_environment(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))
    env_path = vault / ".carrel" / "environment.json"
    payload = json.loads(env_path.read_text(encoding="utf-8"))
    payload.pop("comfort_level")
    payload["legacy_setting"] = True
    payload["wiki_enabled"] = True
    payload["collaborators"] = True
    payload["team_context"] = "Lab group"
    payload["model_teammates"] = {"analysis": "active"}
    payload["claude_code_familiarity"] = "some"
    env_path.write_text(json.dumps(payload), encoding="utf-8")

    validate = _run(skill, "env", "validate", "--vault", str(vault), "--format", "json")
    assert validate.returncode == 2
    body = json.loads(validate.stdout)
    assert body["status"] == "drift"
    assert any(item["check"] == "unknown_keys" for item in body["drift"])
    assert any(item["check"] == "missing_key" for item in body["drift"])

    dry_run = _run(skill, "env", "fix", "--vault", str(vault), "--dry-run", "--format", "json")
    assert dry_run.returncode == 0
    assert json.loads(dry_run.stdout)["changed"] is True
    assert "legacy_setting" in env_path.read_text(encoding="utf-8")

    fixed = _run(skill, "env", "fix", "--vault", str(vault), "--format", "json")
    assert fixed.returncode == 0
    fixed_payload = json.loads(env_path.read_text(encoding="utf-8"))
    assert fixed_payload["comfort_level"] == "beginner"
    assert "legacy_setting" not in fixed_payload
    assert fixed_payload["wiki_enabled"] is True
    assert fixed_payload["collaborators"] is True
    assert fixed_payload["team_context"] == "Lab group"
    assert fixed_payload["model_teammates"] == {"analysis": "active"}
    assert "legacy_setting" not in fixed_payload
    # claude_code_familiarity is now a recognized DEFAULT_PROFILE field (matches
    # ResearcherProfile), so env fix preserves it as a top-level value instead
    # of demoting it into _unknown_keys.
    assert fixed_payload["claude_code_familiarity"] == "some"
    assert fixed_payload["_unknown_keys"]["legacy_setting"] is True
    assert "claude_code_familiarity" not in fixed_payload["_unknown_keys"]
    assert (vault / ".carrel" / "environment.json.bak").exists()


def test_carrel_skill_runtime_fix_resets_invalid_enum_values(tmp_path) -> None:
    """env fix must actually repair out-of-domain enum values, not pass them
    through unchanged. Locks the fix for a bug dogfooding found: the
    documented repair loop (validate -> fix --dry-run -> fix -> validate)
    used to complete "successfully" while sensitivity/trust_level stayed
    invalid."""
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))
    env_path = vault / ".carrel" / "environment.json"
    payload = json.loads(env_path.read_text(encoding="utf-8"))
    payload["sensitivity"] = "extreme"
    payload["automation"]["trust_level"] = "omniscient"
    payload["automation"]["model"] = "gpt-5"
    payload["automation"]["schedule"] = "hourly"
    payload["automation"]["review_cadence"] = "never"
    env_path.write_text(json.dumps(payload), encoding="utf-8")

    validate = _run(skill, "env", "validate", "--vault", str(vault), "--format", "json")
    assert validate.returncode == 1
    body = json.loads(validate.stdout)
    assert body["status"] == "invalid"
    error_paths = {item["path"] for item in body["errors"]}
    assert {
        "sensitivity",
        "automation.trust_level",
        "automation.model",
        "automation.schedule",
        "automation.review_cadence",
    } <= error_paths

    fixed = _run(skill, "env", "fix", "--vault", str(vault), "--format", "json")
    assert fixed.returncode == 0, fixed.stderr
    fix_result = json.loads(fixed.stdout)
    assert set(fix_result["reset_invalid_fields"]) == {
        "sensitivity",
        "automation.trust_level",
        "automation.model",
        "automation.schedule",
        "automation.review_cadence",
    }
    fixed_payload = json.loads(env_path.read_text(encoding="utf-8"))
    assert fixed_payload["sensitivity"] == "medium"
    assert fixed_payload["automation"]["trust_level"] == "advisory"
    assert fixed_payload["automation"]["model"] == "sonnet"
    assert fixed_payload["automation"]["schedule"] == "daily"
    assert fixed_payload["automation"]["review_cadence"] == "quarterly"

    revalidate = _run(skill, "env", "validate", "--vault", str(vault), "--format", "json")
    assert revalidate.returncode == 0
    assert json.loads(revalidate.stdout)["status"] == "valid"


def test_carrel_skill_runtime_fix_reports_structurally_invalid_automation(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))
    env_path = vault / ".carrel" / "environment.json"
    payload = json.loads(env_path.read_text(encoding="utf-8"))
    payload["automation"] = "not-an-object"
    env_path.write_text(json.dumps(payload), encoding="utf-8")

    fixed = _run(skill, "env", "fix", "--vault", str(vault), "--format", "json")
    assert fixed.returncode == 0, fixed.stderr
    fix_result = json.loads(fixed.stdout)
    assert "automation" in fix_result["reset_invalid_fields"]
    fixed_payload = json.loads(env_path.read_text(encoding="utf-8"))
    assert isinstance(fixed_payload["automation"], dict)
    assert fixed_payload["automation"]["trust_level"] == "advisory"


def test_carrel_skill_runtime_malformed_cloud_consent_never_grants_cloud_routing(tmp_path) -> None:
    """A hand-edited, non-boolean cloud_consent must fail env validate and
    must never be read as consent by the routing decision.

    `bool("false")` is `True` in Python, so a naive `bool(profile.get(...))`
    read would silently treat this malformed string as consent granted. The
    typed CLI's pydantic model rejects this shape via a strict field
    validator (src/carrel/models.py, added 2026-07-10 — pydantic's default
    lax coercion would otherwise ACCEPT bool-ish strings); the portable
    runtime must match, not coerce it.
    """
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))
    env_path = vault / ".carrel" / "environment.json"
    payload = json.loads(env_path.read_text(encoding="utf-8"))
    payload["cloud_consent"] = "false"
    env_path.write_text(json.dumps(payload), encoding="utf-8")

    validate = _run(skill, "env", "validate", "--vault", str(vault), "--format", "json")
    assert validate.returncode == 1
    body = json.loads(validate.stdout)
    assert body["status"] == "invalid"
    assert any(
        item["path"] == "cloud_consent" and "boolean" in item["message"] for item in body["errors"]
    )

    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    decision = _run(
        skill,
        "transcript",
        "create",
        "recording.m4a",
        "--vault",
        str(vault),
        "--sensitivity",
        "low",
        "--explain",
        env_extra={"PATH": str(empty_bin)},
    )
    assert decision.returncode == 1, decision.stderr
    explain_payload = json.loads(decision.stdout)
    assert explain_payload["selected_tool"] is None
    assert "cloud consent is not enabled" in explain_payload["rationale"]
    assert "cloud consent is enabled" not in explain_payload["rationale"]

    # HONESTY GUARD (2026-07-10): the subprocess assertions above run with an
    # empty PATH, so no cloud tool can be available and `selected_tool is None`
    # is trivially true regardless of consent -- it only proves the rationale
    # wording. The portable runtime's `available_tools()` never surfaces a cloud
    # tool at CLI level (it shutil.which()-detects local binaries only), so
    # faking cloud availability through the CLI is impossible. Drive the
    # portable policy function directly with a cloud tool GENUINELY available to
    # prove the real invariant: a non-consent value (what the malformed
    # cloud_consent reads as) never routes to cloud even when cloud IS reachable.
    #
    # Import from the tmp COPY (never the checked-in skill dir) with bytecode
    # writing disabled and full teardown, so no __pycache__ or stale sys.modules
    # entry leaks (guards test_carrel_skill_pack_has_no_generated_files and
    # peers, and keeps the portable namespace clean for other tests).
    import importlib

    scripts_dir = str(skill / "scripts")
    sys.path.insert(0, scripts_dir)
    prev_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        portable_core = importlib.import_module("carrel_core.core")

        denied = portable_core.select_tool("transcribe", None, {"groq"}, "low", False)
        assert denied["selected_tool"] is None  # cloud reachable, consent=False → blocked
        assert "cloud consent is not enabled" in denied["rationale"]

        # Converse control: flip ONLY consent → cloud is now selected, proving the
        # cloud tool really was available and consent was the deciding gate.
        granted = portable_core.select_tool("transcribe", None, {"groq"}, "low", True)
        assert granted["selected_tool"] == "groq"
    finally:
        sys.dont_write_bytecode = prev_dont_write
        sys.path.remove(scripts_dir)
        for mod in [m for m in sys.modules if m == "carrel_core" or m.startswith("carrel_core.")]:
            del sys.modules[mod]


def test_carrel_skill_default_profile_matches_researcher_profile_schema(tmp_path) -> None:
    """Guard against silent schema drift between the two engines.

    Every `ResearcherProfile` field (by its serialization alias) must have a
    home in the portable `DEFAULT_PROFILE` or be explicitly tolerated via
    `ADAPTER_PROFILE_KEYS` — otherwise a future Pydantic model field addition
    (as happened with `claude_code_familiarity`) silently falls into
    `_unknown_keys` on the portable side, and `env validate`/`env fix` produce
    misleading drift for vaults touched by the full plugin.
    """
    import sys as _sys

    skill = _copy_skill(tmp_path)
    scripts_dir = str(skill / "scripts")
    added = scripts_dir not in _sys.path
    if added:
        _sys.path.insert(0, scripts_dir)
    try:
        from carrel_core.constants import ADAPTER_PROFILE_KEYS, DEFAULT_PROFILE
    finally:
        if added:
            _sys.path.remove(scripts_dir)
        _sys.modules.pop("carrel_core.constants", None)
        _sys.modules.pop("carrel_core", None)

    from carrel.models import ResearcherProfile

    profile_field_names: set[str] = set()
    for name, field in ResearcherProfile.model_fields.items():
        profile_field_names.add(field.serialization_alias or field.alias or name)

    tracked = set(DEFAULT_PROFILE) | ADAPTER_PROFILE_KEYS
    missing = profile_field_names - tracked
    assert missing == set(), (
        f"ResearcherProfile field(s) {sorted(missing)} have no home in the "
        "portable DEFAULT_PROFILE or ADAPTER_PROFILE_KEYS — add them to one "
        "or the other so env validate/env fix stay in sync."
    )


def test_carrel_skill_runtime_ingestion_artifacts_and_idempotency(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    source = tmp_path / "paper.txt"
    source.write_text("A paper body.", encoding="utf-8")
    _run(skill, "vault", "init", str(vault))

    capture = _run(
        skill,
        "capture",
        "url",
        "https://example.com/post",
        "--vault",
        str(vault),
        "--title",
        "Example Article",
        "--content",
        "Captured body.",
    )
    assert capture.returncode == 0, capture.stderr
    captured = vault / "inbox" / "example-article.md"
    assert captured.exists()
    assert 'source_url: "https://example.com/post"' in captured.read_text(encoding="utf-8")

    convert = _run(skill, "convert", "file", str(source), "--vault", str(vault))
    second = _run(skill, "convert", "file", str(source), "--vault", str(vault))
    assert convert.returncode == 0, convert.stderr
    assert json.loads(second.stdout)["action"] == "skipped"
    paper = vault / "papers" / "paper" / "paper.md"
    assert paper.exists()
    assert 'convert_tool: "provided"' in paper.read_text(encoding="utf-8")
    source.write_text("Changed paper body.", encoding="utf-8")
    changed = _run(skill, "convert", "file", str(source), "--vault", str(vault))
    assert changed.returncode == 0, changed.stderr
    changed_payload = json.loads(changed.stdout)
    assert changed_payload["action"] == "skipped"
    assert "different source-hash" in changed_payload["reason"]

    transcript = _run(
        skill,
        "transcript",
        "create",
        "recording.m4a",
        "--vault",
        str(vault),
        "--kind",
        "interview",
        "--content",
        "Transcript body.",
    )
    assert transcript.returncode == 0, transcript.stderr
    transcript_path = Path(json.loads(transcript.stdout)["path"])
    assert transcript_path.exists()
    assert 'kind: "interview"' in transcript_path.read_text(encoding="utf-8")


def test_carrel_skill_runtime_doctor_google_batch_trust_and_automation(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    batch = tmp_path / "batch"
    batch.mkdir()
    (batch / "one.txt").write_text("One body.", encoding="utf-8")
    _run(skill, "vault", "init", str(vault))

    doctor = _run(skill, "env", "doctor", "--format", "json")
    assert doctor.returncode == 0, doctor.stderr
    assert "binaries" in json.loads(doctor.stdout)

    google = _run(
        skill,
        "google",
        "export",
        "https://docs.google.com/document/d/doc123/edit",
        "--vault",
        str(vault),
        "--export-format",
        "txt",
        "--content",
        "Google doc body.",
        "--title",
        "Google Doc",
    )
    assert google.returncode == 0, google.stderr
    assert (vault / "papers" / "google-doc" / "paper.md").exists()

    sweep = _run(skill, "batch", "convert", str(batch), "--vault", str(vault), "--format", "json")
    assert sweep.returncode == 0, sweep.stderr
    assert json.loads(sweep.stdout)[0]["action"] == "converted"

    trust = _run(skill, "trust", "check", "automation:propose", "--vault", str(vault), "--format", "json")
    assert trust.returncode == 1
    assert json.loads(trust.stdout)["required_trust"] == "consultative"

    profile_path = vault / ".carrel" / "environment.json"
    before_jump = profile_path.read_text(encoding="utf-8")
    rejected_jump = _run(
        skill,
        "automation",
        "configure",
        "--vault",
        str(vault),
        "--enabled",
        "true",
        "--trust-level",
        "delegated",
        "--schedule",
        "daily",
        "--review-cadence",
        "quarterly",
    )
    assert rejected_jump.returncode == 1
    assert "transition only to consultative" in rejected_jump.stderr
    assert profile_path.read_text(encoding="utf-8") == before_jump

    bootstrap = _run(
        skill,
        "automation",
        "configure",
        "--vault",
        str(vault),
        "--enabled",
        "false",
        "--trust-level",
        "consultative",
        "--schedule",
        "daily",
        "--review-cadence",
        "quarterly",
    )
    assert bootstrap.returncode == 0, bootstrap.stderr
    assert json.loads(profile_path.read_text(encoding="utf-8"))["automation"][
        "trust_level"
    ] == "consultative"
    assert not (vault / "_meta" / "pending-decisions.md").exists()
    assert not (vault / "_meta" / "pending-approvals.md").exists()
    assert not (vault / "_meta" / "automation-prompt.md").exists()
    approved = _run(
        skill,
        "trust",
        "check",
        "wiki:apply-approved",
        "--vault",
        str(vault),
        "--format",
        "json",
    )
    autonomous = _run(
        skill,
        "trust",
        "check",
        "wiki:write",
        "--vault",
        str(vault),
        "--format",
        "json",
    )
    assert approved.returncode == 0
    assert json.loads(approved.stdout)["required_trust"] == "consultative"
    assert autonomous.returncode == 1

    automation = _run(
        skill,
        "automation",
        "configure",
        "--vault",
        str(vault),
        "--enabled",
        "true",
        "--trust-level",
        "delegated",
        "--schedule",
        "weekdays",
        "--review-cadence",
        "monthly",
        "--gap-analysis",
        "true",
    )
    assert automation.returncode == 0, automation.stderr
    configured = json.loads(automation.stdout)["automation"]
    assert configured["enabled"] is True
    assert configured["schedule"] == "weekdays"
    assert configured["gap_analysis"] is True
    assert configured["last_reviewed"] == date.today().isoformat()
    assert not (vault / "_meta" / "pending-decisions.md").exists()
    assert not (vault / "_meta" / "pending-approvals.md").exists()
    assert not (vault / "_meta" / "automation-prompt.md").exists()
    assert _run(
        skill,
        "trust",
        "check",
        "wiki:apply-approved",
        "--vault",
        str(vault),
    ).returncode == 0
    assert _run(
        skill,
        "trust",
        "check",
        "wiki:write",
        "--vault",
        str(vault),
    ).returncode == 0

    prompt = _run(skill, "vault", "automation-prompt", "--vault", str(vault))
    assert prompt.returncode == 0, prompt.stderr
    assert json.loads(prompt.stdout)["action"] == "created"
    prompt_path = vault / "_meta" / "automation-prompt.md"
    prompt_body = prompt_path.read_text(encoding="utf-8")
    assert "UNATTENDED mode" in prompt_body
    assert "- Trust level: `delegated`" in prompt_body
    assert "**Gap analysis**" in prompt_body
    assert "{{" not in prompt_body
    assert _run(
        skill,
        "vault",
        "automation-prompt",
        "--vault",
        str(vault),
    ).returncode == 1
    forced = _run(
        skill,
        "vault",
        "automation-prompt",
        "--vault",
        str(vault),
        "--force",
    )
    assert forced.returncode == 0, forced.stderr
    assert json.loads(forced.stdout)["action"] == "updated"


def test_carrel_skill_automation_prompt_requires_consultative_trust(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))

    denied = _run(skill, "vault", "automation-prompt", "--vault", str(vault))
    assert denied.returncode == 1
    assert "Requires consultative" in denied.stderr
    assert not (vault / "_meta" / "automation-prompt.md").exists()

    profile_path = vault / ".carrel" / "environment.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["automation"]["trust_level"] = "consultative"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    allowed = _run(skill, "vault", "automation-prompt", "--vault", str(vault))
    assert allowed.returncode == 0, allowed.stderr
    assert (vault / "_meta" / "automation-prompt.md").exists()


def test_carrel_skill_runtime_automation_prompt_rejects_invalid_profile_cleanly(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0
    profile_path = vault / ".carrel" / "environment.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["automation"]["trust_level"] = "invalid"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")

    result = _run(skill, "vault", "automation-prompt", "--vault", str(vault))

    assert result.returncode == 1
    assert "Invalid researcher profile" in result.stderr
    assert "automation.trust_level" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (vault / "_meta" / "automation-prompt.md").exists()

    configure = _run(
        skill,
        "automation",
        "configure",
        "--vault",
        str(vault),
        "--enabled",
        "true",
        "--trust-level",
        "delegated",
        "--schedule",
        "daily",
        "--review-cadence",
        "quarterly",
    )
    assert configure.returncode == 1
    assert "Invalid researcher profile" in configure.stderr
    assert "Traceback" not in configure.stderr
    assert json.loads(profile_path.read_text(encoding="utf-8"))["automation"]["trust_level"] == "invalid"


def test_carrel_skill_runtime_local_markitdown_adapter_is_bounded_and_used(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    source = tmp_path / "paper.docx"
    source.write_text("fake docx", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    adapter = bin_dir / "markitdown"
    adapter.write_text("#!/bin/sh\nprintf 'Converted by adapter\\n'\n", encoding="utf-8")
    adapter.chmod(0o755)
    _run(skill, "vault", "init", str(vault))

    result = _run(
        skill,
        "convert",
        "file",
        str(source),
        "--vault",
        str(vault),
        env_extra={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
    )

    assert result.returncode == 0, result.stderr
    paper = vault / "papers" / "paper" / "paper.md"
    body = paper.read_text(encoding="utf-8")
    assert "Converted by adapter" in body
    assert 'convert_tool: "markdownify"' in body


def test_carrel_skill_runtime_uses_defuddle_parse_for_capture(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    bin_dir = tmp_path / "bin"
    log = tmp_path / "defuddle-argv.txt"
    bin_dir.mkdir()
    adapter = bin_dir / "defuddle"
    adapter.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$DEFUDDLE_LOG\"\nprintf 'Captured by defuddle\\n'\n",
        encoding="utf-8",
    )
    adapter.chmod(0o755)
    _run(skill, "vault", "init", str(vault))

    result = _run(
        skill,
        "capture",
        "url",
        "https://example.com/post",
        "--vault",
        str(vault),
        "--title",
        "Adapter Capture",
        env_extra={
            "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
            "DEFUDDLE_LOG": str(log),
        },
    )

    assert result.returncode == 0, result.stderr
    assert log.read_text(encoding="utf-8").splitlines() == [
        "parse",
        "https://example.com/post",
        "--markdown",
    ]
    assert "Captured by defuddle" in (vault / "inbox" / "adapter-capture.md").read_text(encoding="utf-8")


def test_carrel_skill_runtime_maintenance_artifacts(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))
    meta = vault / "_meta"
    (meta / "friction-log").mkdir()
    (meta / "friction-log" / "2026-01-01.md").write_text(
        "Alice at Acme Lab hit a problem.",
        encoding="utf-8",
    )
    (meta / "friction_log.md").write_text(
        "Alice reported legacy flat log trouble.",
        encoding="utf-8",
    )
    redact = tmp_path / "redact.txt"
    redact.write_text("Alice -> Researcher\nAcme Lab\n", encoding="utf-8")

    reflection = _run(
        skill,
        "reflection",
        "append",
        "--vault",
        str(vault),
        input_text="Session felt productive.",
    )
    mirror = _run(
        skill,
        "mirror",
        "write",
        "--vault",
        str(vault),
        input_text="# Mirror\n\nPattern synthesis.",
    )
    feedback = _run(skill, "feedback", "export", "--vault", str(vault), "--redact-list", str(redact))
    approved_handbook = "  # Approved Handbook\n\nUse this lab process.\n\n"
    (vault / ".carrel" / "environment.json").write_text("{broken json", encoding="utf-8")
    share = _run(
        skill,
        "share",
        "generate",
        "--vault",
        str(vault),
        "--for",
        "New RA",
        "--sensitivity",
        "high",
        "--from-stdin",
        "--canonical",
        input_text=approved_handbook,
    )

    assert reflection.returncode == 0, reflection.stderr
    assert mirror.returncode == 0, mirror.stderr
    assert feedback.returncode == 0, feedback.stderr
    assert share.returncode == 0, share.stderr
    assert (meta / "reflections" / f"reflection-{date.today().isoformat()}.md").exists()
    assert (meta / "mirror" / f"{date.today().strftime('%Y-%m')}.md").exists()
    digest = meta / f"feedback-digest-{date.today().isoformat()}.md"
    assert digest.exists()
    assert "Alice" not in digest.read_text(encoding="utf-8")
    assert "Researcher" in digest.read_text(encoding="utf-8")
    assert "Acme Lab" not in digest.read_text(encoding="utf-8")
    assert "legacy flat log trouble" in digest.read_text(encoding="utf-8")
    handbook = Path(json.loads(share.stdout)["path"])
    assert handbook.exists()
    assert handbook.read_text(encoding="utf-8") == approved_handbook
    canonical = Path(json.loads(share.stdout)["canonical_path"])
    assert canonical == meta / "lab-handbook.md"
    assert canonical.read_text(encoding="utf-8") == handbook.read_text(encoding="utf-8")


def test_carrel_skill_runtime_share_rejects_names_without_slug_characters(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0

    for name in ("   ", "😀✨"):
        result = _run(
            skill,
            "share",
            "generate",
            "--vault",
            str(vault),
            "--for",
            name,
            "--from-stdin",
            input_text="# Approved\n",
        )
        assert result.returncode == 1
        assert "Traceback" not in result.stderr
    assert list((vault / "_meta" / "handbook").iterdir()) == []


def test_carrel_skill_runtime_share_preflights_canonical_target(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0
    canonical = vault / "_meta" / "lab-handbook.md"
    canonical.mkdir()

    result = _run(
        skill,
        "share",
        "generate",
        "--vault",
        str(vault),
        "--for",
        "New RA",
        "--sensitivity",
        "high",
        "--from-stdin",
        "--canonical",
        input_text="# Approved handbook\n",
    )

    assert result.returncode == 1
    assert "Invalid vault file target" in result.stderr
    assert canonical.is_dir()
    assert list((vault / "_meta" / "handbook").iterdir()) == []


def test_carrel_skill_runtime_feedback_mapping_grammar_and_metrics(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0
    profile_path = vault / ".carrel" / "environment.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["name"] = "Alice Smith"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    friction = vault / "_meta" / "friction_log.md"
    friction.write_text(
        "ALICE SMITH met Acme Lab and Acme. Token token exposed a SECRET. LongPerson joined.\n",
        encoding="utf-8",
    )
    redact = tmp_path / "redact.txt"
    redact.write_text(
        "# literal replacement rules\n"
        "Acme -> Company\n"
        "Acme Lab → Institution\n"
        "Token -> \\1\\vault\n"
        "LongPerson -> Acme\n"
        "Secret\n"
        "Never Seen\n",
        encoding="utf-8",
    )

    result = _run(
        skill,
        "feedback",
        "export",
        "--vault",
        str(vault),
        "--redact-list",
        str(redact),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    digest = Path(payload["path"]).read_text(encoding="utf-8")
    assert "Alice Smith" not in digest
    assert "Researcher met Institution and Company" in digest
    assert "\\1\\vault \\1\\vault" in digest
    assert "Acme joined" in digest
    assert "Company joined" not in digest
    assert "SECRET" not in digest
    assert "[REDACTED]" in digest
    assert payload["redaction_rules"] == 7
    assert payload["redacted_terms"] == 7
    assert payload["redactions_applied"] == 7
    assert payload["zero_match_terms"] == ["Never Seen"]


def test_carrel_skill_runtime_feedback_rejects_empty_mapping_source(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0
    redact = tmp_path / "redact.txt"
    redact.write_text("# comment\n  → replacement\n", encoding="utf-8")

    result = _run(
        skill,
        "feedback",
        "export",
        "--vault",
        str(vault),
        "--redact-list",
        str(redact),
    )

    assert result.returncode == 1
    assert "Line 2" in result.stderr
    assert not (vault / "_meta" / f"feedback-digest-{date.today().isoformat()}.md").exists()


def test_carrel_skill_runtime_feedback_redacts_heading_and_unicode_i_variants(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    assert _run(skill, "vault", "init", str(vault)).returncode == 0
    source = vault / "_meta" / "reflections" / "x.md"
    source.write_text("i İ ı I\n", encoding="utf-8")
    redact = tmp_path / "redact.txt"
    redact.write_text("x.md\ni -> X\n", encoding="utf-8")

    result = _run(
        skill,
        "feedback",
        "export",
        "--vault",
        str(vault),
        "--redact-list",
        str(redact),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    body = Path(payload["path"]).read_text(encoding="utf-8")
    # Headings carry the vault-relative path (same-basename collision fix), but
    # only the basename is redacted — the fixed structural directory prefix
    # (friction-log/capability-log/reflections) is left intact, so a rule cannot
    # eat characters inside a path component. Here "x.md" -> [REDACTED] while the
    # "i" in "reflections" is NOT touched. Total = 4 body "i" + 1 basename "x.md".
    assert "## _meta/reflections/[REDACTED]" in body
    assert "X X X X" in body
    assert payload["redacted_terms"] == 5
    assert payload["redactions_applied"] == 5
    assert payload["zero_match_terms"] == []


def test_carrel_skill_runtime_feedback_rejects_symlinked_sources(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leak.md").write_text("outside secret", encoding="utf-8")
    _run(skill, "vault", "init", str(vault))
    reflections = vault / "_meta" / "reflections"
    reflections.rmdir()
    reflections.symlink_to(outside)
    redact = tmp_path / "redact.txt"
    redact.write_text("secret\n", encoding="utf-8")

    result = _run(skill, "feedback", "export", "--vault", str(vault), "--redact-list", str(redact))

    assert result.returncode == 1
    assert "Path escapes vault root" in result.stderr


def test_carrel_skill_runtime_policy_blocks_high_sensitivity_cloud(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))
    result = _run(
        skill,
        "policy",
        "explain",
        "--tool-class",
        "convert",
        "--requested-tool",
        "mineru",
        "--available-tools",
        "mineru",
        "--sensitivity",
        "high",
        "--cloud-consent",
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["selected_tool"] is None
    assert "HIGH sensitivity blocks cloud tools" in payload["rationale"]

    mistral = _run(
        skill,
        "policy",
        "explain",
        "--tool-class",
        "convert",
        "--requested-tool",
        "mistral_ocr",
        "--available-tools",
        "mistral_ocr",
        "--sensitivity",
        "high",
        "--cloud-consent",
    )
    assert mistral.returncode == 1
    payload = json.loads(mistral.stdout)
    assert payload["selected_tool"] is None
    assert "HIGH sensitivity blocks cloud tools" in payload["rationale"]

    transcript = _run(
        skill,
        "transcript",
        "create",
        "recording.m4a",
        "--vault",
        str(vault),
        "--tool",
        "groq",
        "--sensitivity",
        "high",
        "--content",
        "Transcript body.",
    )
    assert transcript.returncode == 1
    assert "HIGH sensitivity blocks cloud tools" in transcript.stderr

    google = _run(
        skill,
        "google",
        "export",
        "https://docs.google.com/document/d/doc123/edit",
        "--vault",
        str(vault),
        "--sensitivity",
        "high",
    )
    assert google.returncode == 1
    assert "HIGH sensitivity blocks Google Workspace export" in google.stderr


def test_carrel_skill_runtime_batch_transcribe_rejects_leading_dash_source(tmp_path) -> None:
    """A dash-prefixed source from a URL-list file must not reach adapter argv.

    `batch transcribe` builds sources from a `.txt` URL-list file, bypassing
    argparse's own dash-prefix parsing entirely, so adapters.py must reject
    the value itself before invoking the coli subprocess.
    """
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "coli-ran.txt"
    adapter = bin_dir / "coli"
    adapter.write_text(f"#!/bin/sh\ntouch '{marker}'\nprintf 'should not run\\n'\n", encoding="utf-8")
    adapter.chmod(0o755)
    _run(skill, "vault", "init", str(vault))
    folder = tmp_path / "audio"
    folder.mkdir()
    (folder / "urls.txt").write_text("-evil-flag\n", encoding="utf-8")

    result = _run(
        skill,
        "batch",
        "transcribe",
        str(folder),
        "--vault",
        str(vault),
        "--tool",
        "coli",
        "--format",
        "json",
        env_extra={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"},
    )

    assert result.returncode == 1, result.stdout
    outcomes = json.loads(result.stdout)
    assert outcomes[0]["action"] == "failed"
    assert "starts with '-'" in outcomes[0]["detail"]
    assert not marker.exists()


def test_carrel_skill_runtime_adapters_reject_leading_dash_values(tmp_path) -> None:
    """Both adapter argv builders (capture URL, coli source) reject '-' prefixes."""
    import sys as _sys

    skill = _copy_skill(tmp_path)
    scripts_dir = str(skill / "scripts")
    added = scripts_dir not in _sys.path
    if added:
        _sys.path.insert(0, scripts_dir)
    try:
        from carrel_core.adapters import capture_url_with_adapter, transcribe_with_adapter
        from carrel_core.core import CarrelError

        messages = []
        try:
            capture_url_with_adapter("-evil")
        except CarrelError as error:
            messages.append(error.message)
        try:
            transcribe_with_adapter("-evil", "coli")
        except CarrelError as error:
            messages.append(error.message)
    finally:
        if added:
            _sys.path.remove(scripts_dir)
        _sys.modules.pop("carrel_core.adapters", None)
        _sys.modules.pop("carrel_core.core", None)
        _sys.modules.pop("carrel_core", None)

    assert len(messages) == 2
    assert all("starts with '-'" in message for message in messages)


def test_carrel_skill_runtime_does_not_write_bytecode_cache(tmp_path) -> None:
    """sys.dont_write_bytecode in carrel.py must keep a copied skill dir clean.

    Regression guard for test_carrel_skill_pack_has_no_generated_files, which
    would otherwise fail the next time someone runs the runtime manually
    against the checked-in skill folder instead of a copy.
    """
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"

    result = _run(skill, "vault", "init", str(vault))

    assert result.returncode == 0, result.stderr
    assert list(skill.rglob("__pycache__")) == []


def _dry_run_target(output: str) -> str:
    return output.strip().rsplit(" -> ", 1)[-1]


def test_carrel_skill_runtime_youtube_sources_slug_by_video_id_not_watch(tmp_path) -> None:
    """Distinct YouTube videos must produce distinct targets.

    The old slug derived from the URL path stem, so every
    ``youtube.com/watch?v=<id>`` collided on the literal ``watch`` — the second
    video silently skipped, and ``--force`` overwrote the first (data loss).
    The slug now keys on the extracted video id.
    """
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))

    first = _run(
        skill, "transcript", "create",
        "https://www.youtube.com/watch?v=AAA111aaa11", "--vault", str(vault), "--dry-run",
    )
    second = _run(
        skill, "transcript", "create",
        "https://youtu.be/BBB222bbb22", "--vault", str(vault), "--dry-run",
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    first_target = _dry_run_target(first.stdout)
    second_target = _dry_run_target(second.stdout)
    assert first_target != second_target
    assert "youtube-aaa111aaa11" in first_target
    assert "youtube-bbb222bbb22" in second_target

    # Same collision guard for capture (no --title -> URL-derived slug).
    cap_first = _run(
        skill, "capture", "url",
        "https://www.youtube.com/watch?v=AAA111aaa11", "--vault", str(vault), "--dry-run",
    )
    cap_second = _run(
        skill, "capture", "url",
        "https://www.youtube.com/watch?v=BBB222bbb22", "--vault", str(vault), "--dry-run",
    )
    assert _dry_run_target(cap_first.stdout) != _dry_run_target(cap_second.stdout)
    assert "youtube-aaa111aaa11" in _dry_run_target(cap_first.stdout)


def test_carrel_skill_runtime_youtube_url_without_id_errors_not_collides(tmp_path) -> None:
    """A YouTube URL with no extractable video id is an actionable error, not a
    colliding ``playlist``/``watch`` slug."""
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))

    for command in (
        ("transcript", "create", "https://www.youtube.com/playlist?list=PL999"),
        ("capture", "url", "https://www.youtube.com/playlist?list=PL999"),
    ):
        result = _run(skill, *command, "--vault", str(vault), "--dry-run")
        assert result.returncode == 1, result.stdout
        assert "video id" in result.stderr.lower()
        assert "Traceback" not in result.stderr


def test_carrel_skill_runtime_provided_content_change_is_not_a_false_skip(tmp_path) -> None:
    """With --content, changing the body must be detected as a different
    source-hash. The old URL-only hash silently skipped edited content."""
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))
    url = "https://example.com/post"
    common = ["capture", "url", url, "--vault", str(vault), "--title", "Note"]

    created = _run(skill, *common, "--content", "First body.")
    assert json.loads(created.stdout)["action"] == "created"

    same = _run(skill, *common, "--content", "First body.")
    same_payload = json.loads(same.stdout)
    assert same_payload["action"] == "skipped"
    assert "source-hash matches" in same_payload["reason"]

    changed = _run(skill, *common, "--content", "Second body.")
    changed_payload = json.loads(changed.stdout)
    assert changed_payload["action"] == "skipped"
    assert "different source-hash" in changed_payload["reason"]

    forced = _run(skill, *common, "--content", "Second body.", "--force")
    assert json.loads(forced.stdout)["action"] == "overwritten"


def test_carrel_skill_runtime_frontmatter_hash_scan_ignores_body(tmp_path) -> None:
    """The idempotency check reads source_hash from the frontmatter block only.

    A 64-char hash literal in the note body must never be mistaken for the
    frontmatter value (the old substring check did exactly that)."""
    import sys as _sys

    skill = _copy_skill(tmp_path)
    scripts_dir = str(skill / "scripts")
    added = scripts_dir not in _sys.path
    if added:
        _sys.path.insert(0, scripts_dir)
    try:
        from carrel_core.core import frontmatter_source_hash, render_frontmatter

        real = "a" * 64
        decoy = "b" * 64
        note = render_frontmatter(
            {"source_hash": real}, f'Body mentions source_hash: "{decoy}"\n'
        )
        assert frontmatter_source_hash(note) == real
        assert frontmatter_source_hash("no frontmatter here") is None
    finally:
        if added:
            _sys.path.remove(scripts_dir)
        _sys.modules.pop("carrel_core.core", None)
        _sys.modules.pop("carrel_core", None)


def test_carrel_skill_runtime_pdf_never_falls_back_to_markitdown(tmp_path) -> None:
    """A PDF with no liteparse must error, never silently route to markitdown."""
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    source = tmp_path / "scan.pdf"
    source.write_text("fake pdf", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "markitdown-ran.txt"
    adapter = bin_dir / "markitdown"
    adapter.write_text(f"#!/bin/sh\ntouch '{marker}'\nprintf 'converted\\n'\n", encoding="utf-8")
    adapter.chmod(0o755)
    _run(skill, "vault", "init", str(vault))

    result = _run(
        skill, "convert", "file", str(source), "--vault", str(vault),
        env_extra={"PATH": str(bin_dir)},
    )

    assert result.returncode == 1
    assert not marker.exists()
    assert "liteparse" in (result.stderr + result.stdout).lower()
    assert not (vault / "papers" / "scan" / "paper.md").exists()


def test_carrel_skill_runtime_non_pdf_never_routes_to_liteparse(tmp_path) -> None:
    """liteparse is a PDF parser; a .pptx must never be routed to it."""
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    source = tmp_path / "deck.pptx"
    source.write_text("fake pptx", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "lit-ran.txt"
    adapter = bin_dir / "lit"
    adapter.write_text(f"#!/bin/sh\ntouch '{marker}'\nprintf 'parsed\\n'\n", encoding="utf-8")
    adapter.chmod(0o755)
    _run(skill, "vault", "init", str(vault))

    result = _run(
        skill, "convert", "file", str(source), "--vault", str(vault),
        env_extra={"PATH": str(bin_dir)},
    )

    assert result.returncode == 1
    assert not marker.exists()
    assert not (vault / "papers" / "deck" / "paper.md").exists()


def test_carrel_skill_runtime_google_export_lists_supported_formats_on_mismatch(tmp_path) -> None:
    """A presentation has no html export; the error lists the formats it does
    support rather than failing opaquely."""
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    _run(skill, "vault", "init", str(vault))

    result = _run(
        skill, "google", "export",
        "https://docs.google.com/presentation/d/deck123/edit",
        "--vault", str(vault), "--export-format", "html", "--content", "Body.",
    )

    assert result.returncode == 1
    assert "presentation" in result.stderr
    assert "html" in result.stderr
    for supported in ("docx", "pdf", "txt"):
        assert supported in result.stderr
    assert list((vault / "papers").iterdir()) == []
