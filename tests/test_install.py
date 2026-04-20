import pytest

from carrel.env.install import install_command_for


@pytest.mark.parametrize(
    ("tool", "platform", "expected"),
    [
        ("obsidian", "darwin", "brew install --cask obsidian"),
        ("obsidian", "win32", "winget install Obsidian.Obsidian"),
        ("ffmpeg", "linux", "Use your distro package manager, e.g. sudo apt install ffmpeg"),
        ("bun", "windows", "winget install Oven-sh.Bun"),
    ],
)
def test_install_command_for_platform_specific_tools(tool: str, platform: str, expected: str) -> None:
    assert install_command_for(tool, platform) == expected


@pytest.mark.parametrize("platform", ["linux", "win32"])
def test_install_command_for_adds_brew_fallback_for_non_darwin_platforms(platform: str) -> None:
    assert (
        install_command_for("liteparse", platform)
        == "brew tap run-llama/liteparse && brew install llamaindex-liteparse  # TODO: spec 007"
    )
