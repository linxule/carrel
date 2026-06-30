import pytest

from carrel.env.install import INSTALLS, install_command, install_command_for
from carrel.env.platform import Platform


@pytest.mark.parametrize(
    ("platform", "tool", "expected"),
    [
        (Platform.MACOS, "liteparse", "npm install -g @llamaindex/liteparse"),
        (Platform.LINUX, "liteparse", "npm install -g @llamaindex/liteparse"),
        (Platform.WINDOWS, "liteparse", "npm install -g @llamaindex/liteparse"),
        (Platform.MACOS, "gws", "npm install -g @googleworkspace/cli"),
        (Platform.LINUX, "gws", "npm install -g @googleworkspace/cli"),
        (Platform.WINDOWS, "gws", "npm install -g @googleworkspace/cli"),
        (Platform.MACOS, "obsidian", "brew install --cask obsidian"),
        (Platform.LINUX, "obsidian", "Download AppImage from https://obsidian.md"),
        (Platform.WINDOWS, "obsidian", "winget install Obsidian.Obsidian"),
        (Platform.MACOS, "ffmpeg", "brew install ffmpeg"),
        (Platform.LINUX, "ffmpeg", "apt install -y ffmpeg  # or dnf install ffmpeg on Fedora"),
        (Platform.WINDOWS, "ffmpeg", "winget install Gyan.FFmpeg"),
        (Platform.MACOS, "coli", "npm install -g @marswave/coli"),
        (Platform.LINUX, "coli", "npm install -g @marswave/coli"),
        (Platform.WINDOWS, "coli", "npm install -g @marswave/coli"),
        (Platform.MACOS, "defuddle", "npm install -g defuddle"),
        (Platform.LINUX, "defuddle", "npm install -g defuddle"),
        (Platform.WINDOWS, "defuddle", "npm install -g defuddle"),
        (Platform.MACOS, "bun", "curl -fsSL https://bun.sh/install | bash"),
        (Platform.LINUX, "bun", "curl -fsSL https://bun.sh/install | bash"),
        (Platform.WINDOWS, "bun", 'powershell -c "irm https://bun.sh/install.ps1 | iex"'),
        (Platform.MACOS, "zotero", "brew install --cask zotero"),
        (Platform.LINUX, "zotero", "Download from https://www.zotero.org/download/"),
        (Platform.WINDOWS, "zotero", "winget install Zotero.Zotero"),
    ],
)
def test_install_command_matrix(tool: str, platform: Platform, expected: str) -> None:
    assert install_command(tool, platform) == expected
    assert install_command_for(tool, platform) == expected


def test_install_command_for_accepts_legacy_platform_strings() -> None:
    assert install_command_for("obsidian", "darwin") == "brew install --cask obsidian"
    assert install_command_for("obsidian", "linux") == "Download AppImage from https://obsidian.md"
    assert install_command_for("obsidian", "win32") == "winget install Obsidian.Obsidian"


def test_install_command_unknown_tool_returns_none() -> None:
    assert install_command("missing", Platform.MACOS) is None
    assert install_command_for("missing", "linux") is None


def test_install_table_is_platform_keyed_for_every_tool() -> None:
    for platform_commands in INSTALLS.values():
        assert set(platform_commands) == {Platform.MACOS, Platform.LINUX, Platform.WINDOWS}
