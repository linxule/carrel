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
    return profile.model_dump(mode="json", by_alias=True)


def test_env_fix_normalizes_legacy_sensitivity(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["sensitivity"] = "cautious"
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0
    fixed_payload = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert fixed_payload["sensitivity"] == "medium"
    assert fixed_payload["cloud_consent"] is False


def test_env_fix_bumps_version(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["version"] = "0.5.9"
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0
    fixed_payload = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert fixed_payload["version"] == __version__


def test_env_fix_populates_missing_optional_fields(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = {"name": "Ada Lovelace", "sensitivity": "medium"}
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0
    fixed_payload = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert fixed_payload["version"] == __version__
    assert fixed_payload["cloud_consent"] is False
    assert fixed_payload["automation"]["trust_level"] == "advisory"


def test_env_fix_resyncs_tools_configured(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["tools_configured"]["liteparse"] = True
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result(liteparse_installed=False)

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0
    fixed_payload = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert fixed_payload["tools_configured"]["liteparse"] is False


def test_env_fix_preserves_unknown_keys_under_bucket(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["legacy_setting"] = {"enabled": True}
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0
    fixed_payload = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert "legacy_setting" not in fixed_payload
    assert fixed_payload["_unknown_keys"]["legacy_setting"] == {"enabled": True}


def test_env_fix_returns_nonzero_for_ambiguous_legacy_sensitivity(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["sensitivity"] = "external"
    payload["cloud_consent"] = False
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault)])

    assert result.exit_code == 2
    assert "Cannot safely fix sensitivity='external'" in result.output


def test_env_fix_narrows_string_false_cloud_consent(tmp_path, monkeypatch) -> None:
    """A hand-edited string "false" is a safe, narrowing repair.

    `bool("false")` is `True` in Python, so this exact typo is the one case
    worth auto-repairing: it can only ever narrow consent to `False`, never
    widen it.
    """
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["cloud_consent"] = "false"
    _write_environment(vault, payload)

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0, result.output
    fixed_payload = json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))
    assert fixed_payload["cloud_consent"] is False


def test_env_fix_defers_string_true_cloud_consent(tmp_path, monkeypatch) -> None:
    """A hand-edited string "true" must never be auto-repaired to `True`.

    Converting it would widen consent automatically; only a human editing
    the file directly may do that, so `env fix --safe` must defer and leave
    the file untouched.
    """
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["cloud_consent"] = "true"
    _write_environment(vault, payload)
    original_text = (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 2, result.output
    body = json.loads(result.stdout)
    assert any("cloud_consent" in item for item in body["deferred"])
    assert (vault / ".carrel" / "environment.json").read_text(encoding="utf-8") == original_text
    assert not (vault / ".carrel" / "environment.json.bak").exists()


def test_env_fix_creates_backup_before_change(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["version"] = "0.5.9"
    _write_environment(vault, payload)
    original_text = (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "fix", "--vault", str(vault), "--format", "json"])

    assert result.exit_code == 0
    backup_path = vault / ".carrel" / "environment.json.bak"
    assert backup_path.exists()
    assert backup_path.read_text(encoding="utf-8") == original_text


def test_env_fix_dry_run_makes_no_changes(tmp_path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    payload = _profile_payload()
    payload["version"] = "0.5.9"
    _write_environment(vault, payload)
    original_text = (vault / ".carrel" / "environment.json").read_text(encoding="utf-8")

    async def fake_audit(project_path=None):  # noqa: ARG001
        return _audit_result()

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(
        app,
        ["env", "fix", "--vault", str(vault), "--dry-run", "--format", "json"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "dry_run"
    assert (vault / ".carrel" / "environment.json").read_text(encoding="utf-8") == original_text
    assert not (vault / ".carrel" / "environment.json.bak").exists()
