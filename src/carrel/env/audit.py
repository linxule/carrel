from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
from pathlib import Path

from carrel.models import (
    ApiKeyStatus,
    AuditResult,
    BinaryInfo,
    HardwareCapability,
    ToolAvailability,
)

TOOL_CHECKS: dict[str, list[str]] = {
    "git": ["git", "--version"],
    "gh": ["gh", "--version"],
    "node": ["node", "--version"],
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


async def audit(project_path: Path | None = None) -> AuditResult:
    """Detect OS, hardware, installed tools, API keys, MCP configs."""

    resolved_project = project_path.expanduser().resolve() if project_path else None
    system_name = platform.system()
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
    df_output = await _run_command(["df", "-h", str(df_target)])
    if df_output:
        last_line = df_output.splitlines()[-1].split()
        if len(last_line) >= 4:
            disk_free = last_line[3]

    binaries: dict[str, BinaryInfo] = {}
    for name, args in TOOL_CHECKS.items():
        tool_path = shutil.which(args[0])
        installed = tool_path is not None
        version = _parse_version(await _run_command(args)) if installed else None
        binaries[name] = BinaryInfo(installed=installed, version=version, path=tool_path)

    if system_name == "Darwin":
        obsidian_path = await _detect_macos_app("md.obsidian")
        zotero_path = await _detect_macos_app("org.zotero.zotero")
        binaries["obsidian"] = BinaryInfo(
            installed=bool(obsidian_path),
            path=obsidian_path.splitlines()[0] if obsidian_path else None,
        )
        binaries["zotero"] = BinaryInfo(
            installed=bool(zotero_path),
            path=zotero_path.splitlines()[0] if zotero_path else None,
        )
    else:
        binaries["obsidian"] = BinaryInfo(
            installed=shutil.which("obsidian") is not None, path=shutil.which("obsidian")
        )
        binaries["zotero"] = BinaryInfo(
            installed=shutil.which("zotero") is not None, path=shutil.which("zotero")
        )

    api_keys = {
        tool: ApiKeyStatus(configured=bool(os.environ.get(env_var)), env_var=env_var)
        for tool, env_var in API_KEY_CHECKS.items()
    }
    hardware = _classify_hardware(arch=arch, ram_gb=ram_gb)
    tool_info = ToolAvailability(
        binaries=binaries, api_keys=api_keys, mcp_servers=_read_mcp_servers(resolved_project)
    )
    return AuditResult(
        os=os_name,
        arch=arch,
        os_version=os_version,
        ram_gb=ram_gb,
        disk_free=disk_free,
        hardware_capability=hardware,
        tools=tool_info,
    )
