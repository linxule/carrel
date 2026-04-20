from __future__ import annotations

import json

from typer.testing import CliRunner

from carrel import __version__
from carrel.cli.main import app
from carrel.env.platform import Platform
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


def _audit_result(*, liteparse_installed: bool = True) -> AuditResult:
    return AuditResult(
        os="macOS",
        platform=Platform.MACOS,
        arch="arm64",
        hardware_capability=HardwareCapability.HIGH,
        tools=ToolAvailability(
            binaries={"liteparse": BinaryInfo(installed=liteparse_installed, version="1.0.0")},
            api_keys={"groq": ApiKeyStatus(configured=False, env_var="GROQ_API_KEY")},
            mcp_servers=[],
        ),
        tool_matrix=PlatformToolMatrix(
            matrix={"liteparse": {Platform.MACOS: liteparse_installed}}
        ),
    )


def _write_environment(vault, payload: dict) -> None:
    carrel_dir = vault / ".carrel"
    carrel_dir.mkdir(parents=True, exist_ok=True)
    (carrel_dir / "environment.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _profile_payload() -> dict:
    profile = ResearcherProfile(
        version=__version__,
        name="Ada Lovelace",
        field="Mathematics",
        sensitivity="medium",
        cloud_consent=False,
        wiki_enabled=True,
        tools_configured={"liteparse": True},
        automation=AutomationConfig(trust_level=TrustLevel.DELEGATED),
    )
    return profile.model_dump(mode="json")


def test_env_validate_returns_0_for_valid_profile(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _write_environment(vault, _profile_payload())

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "validate", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "valid"
    assert payload["errors"] == []
    assert payload["drift"] == []


def test_env_validate_returns_1_for_invalid_profile(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["sensitivity"] = "invalid"
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "validate", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 1
    body = json.loads(result.stdout)
    assert body["status"] == "invalid"
    assert body["errors"][0]["path"] == "sensitivity"


def test_env_validate_returns_2_for_unknown_extra_key(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["legacy_setting"] = True
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "validate", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 2
    body = json.loads(result.stdout)
    assert any(issue["check"] == "unknown_keys" for issue in body["drift"])


def test_env_validate_returns_2_for_version_mismatch(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["version"] = "0.5.9"
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "validate", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 2
    body = json.loads(result.stdout)
    assert any(issue["check"] == "version" for issue in body["drift"])


def test_env_validate_returns_2_for_marker_mismatch(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    _write_environment(vault, _profile_payload())
    (vault / "CLAUDE.md").write_text(
        "# CLAUDE\n"
        "<!-- carrel:sensitivity -->high<!-- /carrel:sensitivity -->\n",
        encoding="utf-8",
    )

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "validate", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 2
    body = json.loads(result.stdout)
    assert any(issue["check"] == "markers" for issue in body["drift"])
