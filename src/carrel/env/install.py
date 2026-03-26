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


def install_command_for(tool: str) -> str | None:
    return INSTALL_COMMANDS.get(tool)
