from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.env.platform import Platform
from carrel.models import (
    ApiKeyStatus,
    AuditResult,
    BinaryInfo,
    HardwareCapability,
    PlatformToolMatrix,
    ToolAvailability,
)

runner = CliRunner()


def test_env_doctor_human_output_includes_platform(monkeypatch) -> None:
    async def fake_audit(project_path=None):  # noqa: ARG001
        return AuditResult(
            os="Windows",
            platform=Platform.WINDOWS,
            arch="x86_64",
            hardware_capability=HardwareCapability.MEDIUM,
            tools=ToolAvailability(
                binaries={"git": BinaryInfo(installed=True, version="git version 2.44.0")},
                api_keys={"gemini": ApiKeyStatus(configured=False, env_var="GEMINI_API_KEY")},
                mcp_servers=[],
            ),
            tool_matrix=PlatformToolMatrix(matrix={"git": {Platform.WINDOWS: True}}),
        )

    monkeypatch.setattr("carrel.cli.env.audit", fake_audit)

    result = runner.invoke(app, ["env", "doctor"])

    assert result.exit_code == 1
    assert "Platform: Windows" in result.output
    assert "git        OK git version 2.44.0" in result.output
