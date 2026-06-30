from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
from pathlib import Path

from carrel.env.platform import Platform, detect_platform
from carrel.models import (
    ApiKeyStatus,
    AuditResult,
    BinaryInfo,
    HardwareCapability,
    PlatformToolMatrix,
    ToolAvailability,
)

TOOL_CHECKS: dict[str, list[str]] = {
    "git": ["git", "--version"],
    "gh": ["gh", "--version"],
    "node": ["node", "--version"],
    "bun": ["bun", "--version"],
    "python": ["python3", "--version"],
    "uv": ["uv", "--version"],
    "brew": ["brew", "--version"],
    "lit": ["lit", "--version"],
    "coli": ["coli", "--version"],
    "defuddle": ["defuddle", "--version"],
    "gws": ["gws", "--version"],
    "markitdown": ["markitdown", "--help"],
    "ffmpeg": ["ffmpeg", "-version"],
    "pandoc": ["pandoc", "--version"],
}

API_KEY_CHECKS = {
    "mineru": "MINERU_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


async def _run_command(args: list[str], timeout: int = 10, cwd: Path | None = None) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
        )
    except FileNotFoundError:
        return None

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return None

    if proc.returncode != 0:
        return None
    output = stdout.decode().strip() or stderr.decode().strip()
    return output or None


def _parse_version(output: str | None) -> str | None:
    if not output:
        return None
    return output.splitlines()[0].strip()


def _format_bytes(num_bytes: int) -> str:
    gb = num_bytes / 1073741824
    if gb >= 100:
        return f"{gb:.0f}G"
    if gb >= 10:
        return f"{gb:.1f}G"
    return f"{gb:.2f}G"


def _classify_hardware(arch: str, ram_gb: int | None) -> HardwareCapability:
    if arch == "arm64" and ram_gb is not None and ram_gb >= 16:
        return HardwareCapability.HIGH
    if (arch == "arm64" and ram_gb is not None and ram_gb >= 8) or (
        arch != "arm64" and ram_gb is not None and ram_gb >= 16
    ):
        return HardwareCapability.MEDIUM
    return HardwareCapability.LOW


async def _detect_macos_app(bundle_id: str) -> str | None:
    return await _run_command(["mdfind", f"kMDItemCFBundleIdentifier == '{bundle_id}'"])


def _false_platform_map() -> dict[Platform, bool]:
    return {platform_key: False for platform_key in Platform}


def _first_match_path(paths: list[Path]) -> str | None:
    for path in paths:
        if path.exists():
            return str(path)
    return None


def _detect_windows_obsidian_path() -> str | None:
    candidates: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.extend(
            [
                Path(local_app_data) / "Obsidian" / "Obsidian.exe",
                Path(local_app_data) / "Programs" / "Obsidian" / "Obsidian.exe",
                Path(local_app_data) / "Obsidian",
            ]
        )
    program_files = os.environ.get("PROGRAMFILES")
    if program_files:
        candidates.append(Path(program_files) / "Obsidian" / "Obsidian.exe")
    return _first_match_path(candidates)


def _detect_windows_zotero_path() -> str | None:
    candidates: list[Path] = []
    program_files = os.environ.get("PROGRAMFILES")
    if program_files:
        candidates.extend(
            [
                Path(program_files) / "Zotero" / "zotero.exe",
                Path(program_files) / "Zotero",
            ]
        )
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Zotero" / "zotero.exe")
    return _first_match_path(candidates)


def _detect_linux_obsidian_path() -> str | None:
    return shutil.which("obsidian") or _first_match_path([Path.home() / ".config" / "obsidian"])


def _detect_linux_zotero_path() -> str | None:
    return shutil.which("zotero") or _first_match_path([Path.home() / ".zotero"])


def _detect_gui_tool_path(tool: str, current_platform: Platform) -> str | None:
    if current_platform is Platform.MACOS:
        if tool == "obsidian":
            return _first_match_path([Path("/Applications/Obsidian.app")])
        if tool == "zotero":
            return _first_match_path([Path("/Applications/Zotero.app")])
    if tool == "obsidian":
        if current_platform is Platform.WINDOWS:
            return _detect_windows_obsidian_path()
        if current_platform is Platform.LINUX:
            return _detect_linux_obsidian_path()
    if tool == "zotero":
        if current_platform is Platform.WINDOWS:
            return _detect_windows_zotero_path()
        if current_platform is Platform.LINUX:
            return _detect_linux_zotero_path()
    return None


async def _detect_gui_binary(tool: str, current_platform: Platform) -> BinaryInfo:
    detected_path: str | None = None
    if current_platform is Platform.MACOS:
        bundle_id = "md.obsidian" if tool == "obsidian" else "org.zotero.zotero"
        detected = await _detect_macos_app(bundle_id)
        if detected:
            detected_path = detected.splitlines()[0]
    else:
        detected_path = _detect_gui_tool_path(tool, current_platform)

    return BinaryInfo(installed=detected_path is not None, path=detected_path)


def _read_mcp_servers(project_path: Path | None) -> list[str]:
    if project_path is None:
        return []
    mcp_path = project_path / ".mcp.json"
    if not mcp_path.exists():
        return []
    try:
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return sorted((data.get("mcpServers") or {}).keys())


def populate_tool_matrix(current_platform: Platform) -> PlatformToolMatrix:
    matrix: dict[str, dict[Platform, bool]] = {}
    for tool, args in TOOL_CHECKS.items():
        matrix[tool] = _false_platform_map()
        matrix[tool][current_platform] = shutil.which(args[0]) is not None

    for tool in ("obsidian", "zotero"):
        matrix[tool] = _false_platform_map()
        matrix[tool][current_platform] = _detect_gui_tool_path(tool, current_platform) is not None

    return PlatformToolMatrix(matrix=matrix)


async def audit(project_path: Path | None = None) -> AuditResult:
    """Detect OS, hardware, installed tools, API keys, MCP configs."""

    resolved_project = project_path.expanduser().resolve() if project_path else None
    system_name = platform.system()
    detected_platform = detect_platform()
    os_name = {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}.get(
        system_name, system_name
    )
    arch = platform.machine() or platform.processor() or "unknown"
    arch = "arm64" if arch in {"arm64", "aarch64"} else "x86_64"

    os_version: str | None = None
    ram_gb: int | None = None
    disk_free: str | None = None

    if system_name == "Darwin":
        os_version = await _run_command(["sw_vers", "-productVersion"])
        mem_bytes = await _run_command(["sysctl", "-n", "hw.memsize"])
        if mem_bytes and mem_bytes.isdigit():
            ram_gb = round(int(mem_bytes) / 1073741824)
    else:
        os_version = platform.release()
        if hasattr(os, "sysconf"):
            try:
                page_size = os.sysconf("SC_PAGE_SIZE")
                pages = os.sysconf("SC_PHYS_PAGES")
                ram_gb = round((page_size * pages) / 1073741824)
            except (ValueError, OSError):
                ram_gb = None

    df_target = resolved_project or Path.cwd()
    try:
        usage = shutil.disk_usage(df_target)
        disk_free = _format_bytes(usage.free)
    except (FileNotFoundError, PermissionError, OSError):
        disk_free = None

    binaries: dict[str, BinaryInfo] = {}
    for name, args in TOOL_CHECKS.items():
        tool_path = shutil.which(args[0])
        installed = tool_path is not None
        version = _parse_version(await _run_command(args)) if installed else None
        binaries[name] = BinaryInfo(installed=installed, version=version, path=tool_path)

    binaries["obsidian"] = await _detect_gui_binary("obsidian", detected_platform)
    binaries["zotero"] = await _detect_gui_binary("zotero", detected_platform)

    api_keys = {
        tool: ApiKeyStatus(configured=bool(os.environ.get(env_var)), env_var=env_var)
        for tool, env_var in API_KEY_CHECKS.items()
    }
    hardware = _classify_hardware(arch=arch, ram_gb=ram_gb)
    tool_info = ToolAvailability(
        binaries=binaries, api_keys=api_keys, mcp_servers=_read_mcp_servers(resolved_project)
    )
    tool_matrix = populate_tool_matrix(detected_platform)
    for tool, info in binaries.items():
        if tool not in tool_matrix.matrix:
            tool_matrix.matrix[tool] = _false_platform_map()
        tool_matrix.matrix[tool][detected_platform] = info.installed
    return AuditResult(
        os=os_name,
        platform=detected_platform,
        arch=arch,
        os_version=os_version,
        ram_gb=ram_gb,
        disk_free=disk_free,
        hardware_capability=hardware,
        tools=tool_info,
        tool_matrix=tool_matrix,
    )
