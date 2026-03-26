import json

import pytest

from carrel.env import audit as audit_module


@pytest.mark.asyncio
async def test_audit_reports_tools_api_keys_and_mcp_servers(tmp_path, monkeypatch) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"markdownify": {}, "vox": {}}}), encoding="utf-8"
    )

    async def fake_run_command(args, timeout=10, cwd=None):  # noqa: ARG001
        mapping = {
            ("sw_vers", "-productVersion"): "14.6",
            ("sysctl", "-n", "hw.memsize"): str(16 * 1073741824),
            ("df", "-h", str(tmp_path)): "Filesystem Size Used Avail Capacity Mounted on\n/dev/disk 100G 40G 60G 40% /",
            ("git", "--version"): "git version 2.44.0",
            ("uv", "--version"): "uv 0.6.3",
            ("markitdown", "--help"): "usage: markitdown [OPTIONS] FILE",
        }
        return mapping.get(tuple(args))

    async def fake_detect(bundle_id):  # noqa: ARG001
        return "/Applications/Obsidian.app"

    monkeypatch.setattr(audit_module, "_run_command", fake_run_command)
    monkeypatch.setattr(audit_module, "_detect_macos_app", fake_detect)
    monkeypatch.setattr(audit_module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(audit_module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(
        audit_module.shutil,
        "which",
        lambda cmd: f"/usr/bin/{cmd}" if cmd in {"git", "uv", "markitdown"} else None,
    )
    monkeypatch.setenv("MINERU_API_KEY", "configured")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "configured")

    result = await audit_module.audit(tmp_path)

    assert result.os == "macOS"
    assert result.arch == "arm64"
    assert result.ram_gb == 16
    assert result.hardware_capability.value == "high"
    assert result.tools.binaries["git"].installed is True
    assert result.tools.binaries["uv"].installed is True
    assert result.tools.binaries["markitdown"].installed is True
    assert result.tools.binaries["obsidian"].installed is True
    assert result.tools.api_keys["mineru"].configured is True
    assert result.tools.api_keys["groq"].configured is False
    assert result.tools.mcp_servers == ["markdownify", "vox"]
