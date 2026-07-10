from __future__ import annotations

import json

from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.models import (
    ApiKeyStatus,
    AuditResult,
    AutomationConfig,
    BinaryInfo,
    HardwareCapability,
    PlatformToolMatrix,
    ResearcherProfile,
    ToolAvailability,
    TrustLevel,
)

runner = CliRunner()


def _write_profile(vault, *, trust_level: TrustLevel = TrustLevel.DELEGATED) -> None:
    carrel_dir = vault / ".carrel"
    carrel_dir.mkdir(parents=True, exist_ok=True)
    profile = ResearcherProfile(
        name="Ada Lovelace",
        field="Mathematics",
        cloud_consent=False,
        wiki_enabled=True,
        tools_configured={"liteparse": True, "coli": True},
        automation=AutomationConfig(trust_level=trust_level),
    )
    (carrel_dir / "environment.json").write_text(
        profile.model_dump_json(indent=2),
        encoding="utf-8",
    )


def _audit_result() -> AuditResult:
    return AuditResult(
        os="macOS",
        platform="macos",
        arch="arm64",
        hardware_capability=HardwareCapability.HIGH,
        tools=ToolAvailability(
            binaries={"liteparse": BinaryInfo(installed=True, version="1.0.0")},
            api_keys={"groq": ApiKeyStatus(configured=False, env_var="GROQ_API_KEY")},
            mcp_servers=["obsidian"],
        ),
        tool_matrix=PlatformToolMatrix(matrix={}),
    )


def test_vault_dashboard_requires_force_to_overwrite(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault)
    dashboard = vault / "_meta" / "my-environment.md"
    dashboard.parent.mkdir(parents=True)
    dashboard.write_text("existing", encoding="utf-8")

    async def fake_audit(project_path):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.vault.audit", fake_audit)

    result = runner.invoke(app, ["vault", "dashboard", "--vault", str(vault)])

    assert result.exit_code == 1
    assert "Dashboard already exists" in result.stderr


def test_vault_dashboard_force_writes_rendered_file(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault)
    (vault / "papers" / "ada1843").mkdir(parents=True)
    (vault / "papers" / "ada1843" / "paper.md").write_text("paper", encoding="utf-8")

    async def fake_audit(project_path):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.vault.audit", fake_audit)

    result = runner.invoke(app, ["vault", "dashboard", "--vault", str(vault), "--force"])

    assert result.exit_code == 0
    content = (vault / "_meta" / "my-environment.md").read_text(encoding="utf-8")
    assert "Ada Lovelace" in content
    assert f"- Vault path: `{vault.resolve()}`" in content
    assert "- Papers: 1" in content


def test_vault_automation_prompt_force_writes_prompt(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault, trust_level=TrustLevel.CONSULTATIVE)

    result = runner.invoke(
        app,
        ["vault", "automation-prompt", "--vault", str(vault), "--force"],
    )

    assert result.exit_code == 0
    content = (vault / "_meta" / "automation-prompt.md").read_text(encoding="utf-8")
    assert "UNATTENDED mode" in content
    assert "- Trust level: `consultative`" in content


def test_vault_automation_prompt_rejects_advisory_trust(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault, trust_level=TrustLevel.ADVISORY)

    result = runner.invoke(
        app,
        ["vault", "automation-prompt", "--vault", str(vault)],
    )

    assert result.exit_code == 1
    assert "automation:write-prompt" in result.stderr
    assert "consultative" in result.stderr
    assert not (vault / "_meta" / "automation-prompt.md").exists()


def test_vault_automation_prompt_rejects_symlinked_meta_directory(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault, trust_level=TrustLevel.CONSULTATIVE)
    outside = tmp_path / "outside-meta"
    outside.mkdir()
    (vault / "_meta").symlink_to(outside, target_is_directory=True)

    result = runner.invoke(
        app,
        ["vault", "automation-prompt", "--vault", str(vault)],
    )

    assert result.exit_code == 1
    assert "Path escapes vault root" in result.stderr
    assert list(outside.iterdir()) == []


def test_vault_check_sync_shows_hint_when_no_markers_exist(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault)
    (vault / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")

    result = runner.invoke(app, ["vault", "check-sync", "--vault", str(vault)])

    assert result.exit_code == 0
    assert (
        "No carrel markers found. Run `carrel vault add-markers` to enable sync checking."
        in result.stdout
    )


def test_vault_check_sync_reports_drift_and_nonzero_exit(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault)
    (vault / "CLAUDE.md").write_text(
        "# CLAUDE\n"
        "<!-- carrel:sensitivity -->high<!-- /carrel:sensitivity -->\n"
        "<!-- carrel:cloud_consent -->true<!-- /carrel:cloud_consent -->\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["vault", "check-sync", "--vault", str(vault), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["drift"] == [
        {"field": "sensitivity", "marker": "high", "profile": "medium"},
        {"field": "cloud_consent", "marker": "true", "profile": "false"},
    ]


def test_vault_add_markers_appends_missing_markers_and_is_idempotent(tmp_path) -> None:
    vault = tmp_path / "vault"
    _write_profile(vault)
    claude = vault / "CLAUDE.md"
    claude.write_text("# CLAUDE\n", encoding="utf-8")

    first = runner.invoke(app, ["vault", "add-markers", "--vault", str(vault)])
    second = runner.invoke(app, ["vault", "add-markers", "--vault", str(vault)])

    assert first.exit_code == 0
    assert second.exit_code == 0
    content = claude.read_text(encoding="utf-8")
    assert "<!-- carrel:sensitivity -->medium<!-- /carrel:sensitivity -->" in content
    assert "<!-- carrel:cloud_consent -->false<!-- /carrel:cloud_consent -->" in content
    assert "<!-- carrel:wiki_enabled -->true<!-- /carrel:wiki_enabled -->" in content
    assert content.count("<!-- carrel:sensitivity -->") == 1
