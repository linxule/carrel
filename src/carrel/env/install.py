from __future__ import annotations

from carrel.env.platform import Platform, detect_platform


INSTALLS: dict[str, dict[Platform, str | None]] = {
    "liteparse": {
        Platform.MACOS: "bun add -g @llamaindex/liteparse",
        Platform.LINUX: "bun add -g @llamaindex/liteparse",
        Platform.WINDOWS: "bun add -g @llamaindex/liteparse",
    },
    "gws": {
        Platform.MACOS: "npm install -g @googleworkspace/cli",
        Platform.LINUX: "npm install -g @googleworkspace/cli",
        Platform.WINDOWS: "npm install -g @googleworkspace/cli",
    },
    "obsidian": {
        Platform.MACOS: "brew install --cask obsidian",
        Platform.LINUX: "Download AppImage from https://obsidian.md",
        Platform.WINDOWS: "winget install Obsidian.Obsidian",
    },
    "ffmpeg": {
        Platform.MACOS: "brew install ffmpeg",
        Platform.LINUX: "apt install -y ffmpeg  # or dnf install ffmpeg on Fedora",
        Platform.WINDOWS: "winget install Gyan.FFmpeg",
    },
    "coli": {
        Platform.MACOS: "bun add -g @marswave/coli",
        Platform.LINUX: "bun add -g @marswave/coli",
        Platform.WINDOWS: "bun add -g @marswave/coli",
    },
    "defuddle": {
        Platform.MACOS: "bun add -g defuddle",
        Platform.LINUX: "bun add -g defuddle",
        Platform.WINDOWS: "bun add -g defuddle",
    },
    "bun": {
        Platform.MACOS: "curl -fsSL https://bun.sh/install | bash",
        Platform.LINUX: "curl -fsSL https://bun.sh/install | bash",
        Platform.WINDOWS: 'powershell -c "irm https://bun.sh/install.ps1 | iex"',
    },
    "zotero": {
        Platform.MACOS: "brew install --cask zotero",
        Platform.LINUX: "Download from https://www.zotero.org/download/",
        Platform.WINDOWS: "winget install Zotero.Zotero",
    },
    "markitdown": {
        Platform.MACOS: "uv add markitdown",
        Platform.LINUX: "uv add markitdown",
        Platform.WINDOWS: "uv add markitdown",
    },
    "youtube-transcript-api": {
        Platform.MACOS: "uv add youtube-transcript-api",
        Platform.LINUX: "uv add youtube-transcript-api",
        Platform.WINDOWS: "uv add youtube-transcript-api",
    },
    "pandoc": {
        Platform.MACOS: "brew install pandoc",
        Platform.LINUX: "apt install -y pandoc  # or dnf install pandoc on Fedora",
        Platform.WINDOWS: "winget install JohnMacFarlane.Pandoc",
    },
}


def _coerce_platform(platform: Platform | str | None) -> Platform:
    if platform is None:
        return detect_platform()
    if isinstance(platform, Platform):
        return platform

    value = platform.lower()
    if value in {"darwin", "macos", "mac", "osx"}:
        return Platform.MACOS
    if value.startswith("win") or value in {"windows", "cygwin"}:
        return Platform.WINDOWS
    if value.startswith("linux"):
        return Platform.LINUX
    return Platform.UNKNOWN


def install_command(tool: str, platform: Platform | None = None) -> str | None:
    resolved_platform = detect_platform() if platform is None else platform
    return INSTALLS.get(tool, {}).get(resolved_platform)


def install_command_for(tool: str, platform: Platform | str | None = None) -> str | None:
    return install_command(tool, _coerce_platform(platform))
