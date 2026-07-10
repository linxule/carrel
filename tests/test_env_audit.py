import json

import pytest

from carrel.env import audit as audit_module
from carrel.env.platform import Platform


@pytest.mark.asyncio
async def test_audit_reports_tools_api_keys_and_mcp_servers_on_macos(tmp_path, monkeypatch) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"markdownify": {}, "vox": {}}}), encoding="utf-8"
    )

    async def fake_run_command(args, timeout=10, cwd=None):  # noqa: ARG001
        mapping = {
            ("sw_vers", "-productVersion"): "14.6",
            ("sysctl", "-n", "hw.memsize"): str(16 * 1073741824),
            ("df", "-h", str(tmp_path)): "Filesystem Size Used Avail Capacity Mounted on\n/dev/disk 100G 40G 60G 40% /",
            ("git", "--version"): "git version 2.44.0",
            ("bun", "--version"): "1.2.19",
            ("uv", "--version"): "uv 0.6.3",
            ("defuddle", "--version"): "defuddle 0.7.0",
            ("gws", "--version"): "gws 0.10.0",
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
        lambda cmd: f"/usr/bin/{cmd}"
        if cmd in {"git", "bun", "uv", "defuddle", "gws", "markitdown"}
        else None,
    )
    monkeypatch.setattr("sys.platform", "darwin")
    monkeypatch.setenv("MINERU_API_KEY", "configured")
    monkeypatch.setenv("MISTRAL_API_KEY", "configured")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "configured")

    result = await audit_module.audit(tmp_path)

    assert result.os == "macOS"
    assert result.platform is Platform.MACOS
    assert result.arch == "arm64"
    assert result.ram_gb == 16
    assert result.hardware_capability.value == "high"
    assert result.tools.binaries["git"].installed is True
    assert result.tools.binaries["bun"].installed is True
    assert result.tools.binaries["uv"].installed is True
    assert result.tools.binaries["defuddle"].installed is True
    assert result.tools.binaries["gws"].installed is True
    assert result.tools.binaries["markitdown"].installed is True
    assert result.tools.binaries["obsidian"].installed is True
    assert result.tools.api_keys["mineru"].configured is True
    assert result.tools.api_keys["mistral"].configured is True
    assert result.tools.api_keys["groq"].configured is False
    assert result.tools.api_keys["gemini"].configured is True
    assert result.tools.mcp_servers == ["markdownify", "vox"]
    assert result.tool_matrix.is_available("git", Platform.MACOS) is True
    assert result.tool_matrix.is_available("git", Platform.WINDOWS) is False


@pytest.mark.asyncio
async def test_audit_detects_windows_obsidian_and_zotero_from_filesystem(tmp_path, monkeypatch) -> None:
    local_app_data = tmp_path / "local"
    program_files = tmp_path / "program-files"
    (local_app_data / "Obsidian").mkdir(parents=True)
    (program_files / "Zotero").mkdir(parents=True)

    async def fake_run_command(args, timeout=10, cwd=None):  # noqa: ARG001
        mapping = {
            ("df", "-h", str(tmp_path)): "Filesystem Size Used Avail Capacity Mounted on\nC: 100G 40G 60G 40% /",
            ("git", "--version"): "git version 2.44.0",
            ("bun", "--version"): "1.2.19",
        }
        return mapping.get(tuple(args))

    monkeypatch.setattr(audit_module, "_run_command", fake_run_command)
    monkeypatch.setattr(audit_module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(audit_module.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(audit_module.platform, "release", lambda: "11")
    monkeypatch.setattr(
        audit_module.os,
        "sysconf",
        lambda name: {"SC_PAGE_SIZE": 4096, "SC_PHYS_PAGES": 2 * 1024 * 1024}[name],
    )
    monkeypatch.setattr(
        audit_module.shutil,
        "which",
        lambda cmd: {
            "git": "C:/Program Files/Git/bin/git.exe",
            "bun": "C:/Users/test/.bun/bin/bun.exe",
        }.get(cmd),
    )
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("PROGRAMFILES", str(program_files))

    result = await audit_module.audit(tmp_path)

    assert result.os == "Windows"
    assert result.platform is Platform.WINDOWS
    assert result.tools.binaries["obsidian"].installed is True
    assert result.tools.binaries["obsidian"].path == str(local_app_data / "Obsidian")
    assert result.tools.binaries["zotero"].installed is True
    assert result.tools.binaries["zotero"].path == str(program_files / "Zotero")
    assert result.tool_matrix.is_available("obsidian", Platform.WINDOWS) is True
    assert result.tool_matrix.is_available("obsidian", Platform.MACOS) is False
    assert result.tool_matrix.is_available("zotero", Platform.WINDOWS) is True


@pytest.mark.asyncio
async def test_audit_detects_linux_obsidian_and_zotero_from_binary_or_config(tmp_path, monkeypatch) -> None:
    home = tmp_path / "home"
    (home / ".config" / "obsidian").mkdir(parents=True)
    (home / ".zotero").mkdir(parents=True)

    async def fake_run_command(args, timeout=10, cwd=None):  # noqa: ARG001
        mapping = {
            ("df", "-h", str(tmp_path)): "Filesystem Size Used Avail Capacity Mounted on\n/dev/root 100G 40G 60G 40% /",
            ("git", "--version"): "git version 2.44.0",
            ("bun", "--version"): "1.2.19",
            ("zotero", "--version"): "Zotero 7.0.0",
        }
        return mapping.get(tuple(args))

    monkeypatch.setattr(audit_module, "_run_command", fake_run_command)
    monkeypatch.setattr(audit_module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(audit_module.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(audit_module.platform, "release", lambda: "6.8.0")
    monkeypatch.setattr(
        audit_module.os,
        "sysconf",
        lambda name: {"SC_PAGE_SIZE": 4096, "SC_PHYS_PAGES": 4 * 1024 * 1024}[name],
    )
    monkeypatch.setattr(
        audit_module.Path,
        "home",
        classmethod(lambda cls: home),
    )
    monkeypatch.setattr(
        audit_module.shutil,
        "which",
        lambda cmd: {
            "git": "/usr/bin/git",
            "bun": "/usr/bin/bun",
            "zotero": "/usr/bin/zotero",
        }.get(cmd),
    )
    monkeypatch.setattr("sys.platform", "linux")

    result = await audit_module.audit(tmp_path)

    assert result.os == "Linux"
    assert result.platform is Platform.LINUX
    assert result.tools.binaries["obsidian"].installed is True
    assert result.tools.binaries["obsidian"].path == str(home / ".config" / "obsidian")
    assert result.tools.binaries["zotero"].installed is True
    assert result.tools.binaries["zotero"].path == "/usr/bin/zotero"
    assert result.tool_matrix.is_available("obsidian", Platform.LINUX) is True
    assert result.tool_matrix.is_available("obsidian", Platform.WINDOWS) is False
    assert result.tool_matrix.is_available("zotero", Platform.LINUX) is True
