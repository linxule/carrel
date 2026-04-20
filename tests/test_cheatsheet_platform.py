from pathlib import Path

from carrel.env.platform import Platform
from carrel.models import ResearcherProfile
from carrel.vault.templates import render_cheat_sheet


def test_render_cheat_sheet_uses_macos_install_commands() -> None:
    profile = ResearcherProfile(tools_configured={"obsidian": True, "gws": True})

    rendered = render_cheat_sheet(Path("/tmp/research"), profile, Platform.MACOS)

    assert "- Install: `brew install --cask obsidian`" in rendered
    assert "- Install: `npm install -g @googleworkspace/cli`" in rendered


def test_render_cheat_sheet_uses_windows_install_commands() -> None:
    profile = ResearcherProfile(tools_configured={"obsidian": True, "ffmpeg": True})

    rendered = render_cheat_sheet(Path("/tmp/research"), profile, Platform.WINDOWS)

    assert "- Install: `winget install Obsidian.Obsidian`" in rendered
    assert "- Install: `winget install Gyan.FFmpeg`" in rendered
