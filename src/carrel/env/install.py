INSTALL_COMMANDS = {
    "liteparse": "brew tap run-llama/liteparse && brew install llamaindex-liteparse",
    "coli": "bun add -g @marswave/coli",
    "markitdown": "uv add markitdown",
    "ffmpeg": "brew install ffmpeg",
    "pandoc": "brew install pandoc",
}


def install_command_for(tool: str) -> str | None:
    return INSTALL_COMMANDS.get(tool)
