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
    openai_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "interface:\n" in openai_yaml
    assert 'default_prompt: "Use $carrel' in openai_yaml
    assert (SKILL / "scripts" / "carrel.py").exists()
    assert (SKILL / "scripts" / "carrel_core" / "runtime.py").exists()
    assert (SKILL / "references" / "contracts" / "vault-contract.md").exists()
    assert (SKILL / "references" / "contracts" / "surface-map.md").exists()
    assert (SKILL / "references" / "contracts" / "host-compatibility.md").exists()
    assert (SKILL / "references" / "workflows" / "ingestion.md").exists()
    assert (SKILL / "assets" / "templates" / "agent-context.md").exists()


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


def test_carrel_skill_runtime_rejects_symlink_write_escape(tmp_path) -> None:
    skill = _copy_skill(tmp_path)
    vault = tmp_path / "vault"
    (vault / ".carrel").mkdir(parents=True)
    (vault / ".carrel" / "agent-context.md").symlink_to(tmp_path / "outside-context.md")

    result = _run(skill, "vault", "init", str(vault), "--format", "json")

    assert result.returncode == 1
    assert "Path escapes vault root" in result.stderr
    assert not (tmp_path / "outside-context.md").exists()


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
    assert "claude_code_familiarity" not in fixed_payload
    assert fixed_payload["_unknown_keys"]["legacy_setting"] is True
    assert fixed_payload["_unknown_keys"]["claude_code_familiarity"] == "some"
    assert (vault / ".carrel" / "environment.json.bak").exists()


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
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["automation"]["trust_level"] = "delegated"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
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
    redact.write_text("Alice\nAcme Lab\n", encoding="utf-8")

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
    assert "legacy flat log trouble" in digest.read_text(encoding="utf-8")
    handbook = Path(json.loads(share.stdout)["path"])
    assert handbook.exists()
    assert "researcher-field-omitted" in share.stdout


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
