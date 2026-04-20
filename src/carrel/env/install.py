import sys


INSTALL_COMMANDS = {
    "liteparse": "brew tap run-llama/liteparse && brew install llamaindex-liteparse",
    "coli": "bun add -g @marswave/coli",
    "defuddle": "bun add -g defuddle",
    "gws": "brew install googleworkspace-cli",
    "markitdown": "uv add markitdown",
    "youtube-transcript-api": "uv add youtube-transcript-api",
    "ffmpeg": "brew install ffmpeg",
    "pandoc": "brew install pandoc",
}

PLATFORM_INSTALL_COMMANDS = {
    "obsidian": {
        "darwin": "brew install --cask obsidian",
        "linux": "Download AppImage from https://obsidian.md/download",
        "win32": "winget install Obsidian.Obsidian",
    },
    "ffmpeg": {
        "darwin": "brew install ffmpeg",
        "linux": "Use your distro package manager, e.g. sudo apt install ffmpeg",
        "win32": "winget install Gyan.FFmpeg",
    },
    "bun": {
        "darwin": "brew install bun",
        "linux": "curl -fsSL https://bun.com/install | bash",
        "win32": "winget install Oven-sh.Bun",
    },
}


def _normalize_platform(platform: str | None) -> str:
    value = (platform or sys.platform).lower()
    if value in {"darwin", "macos", "mac", "osx"}:
        return "darwin"
    if value.startswith("win") or value == "windows":
        return "win32"
    if value.startswith("linux"):
        return "linux"
    return value


def install_command_for(tool: str, platform: str | None = None) -> str | None:
    normalized_platform = _normalize_platform(platform)
    platform_commands = PLATFORM_INSTALL_COMMANDS.get(tool)
    if platform_commands:
        return platform_commands.get(normalized_platform)

    command = INSTALL_COMMANDS.get(tool)
    if command is None:
        return None

    if normalized_platform != "darwin" and command.startswith("brew "):
        return f"{command}  # TODO: spec 007"
    return command


__test__ = {
    "install_command_for": """
    >>> install_command_for("obsidian", "darwin")
    'brew install --cask obsidian'
    >>> install_command_for("obsidian", "win32")
    'winget install Obsidian.Obsidian'
    >>> install_command_for("ffmpeg", "linux")
    'Use your distro package manager, e.g. sudo apt install ffmpeg'
    >>> install_command_for("liteparse", "linux")
    'brew tap run-llama/liteparse && brew install llamaindex-liteparse  # TODO: spec 007'
    """,
}
