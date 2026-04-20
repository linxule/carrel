from carrel.env.platform import Platform
from carrel.models import PlatformToolMatrix


def test_platform_tool_matrix_round_trips_with_platform_keys() -> None:
    matrix = PlatformToolMatrix.model_validate(
        {"matrix": {"ffmpeg": {"macos": True, "linux": False, "windows": True}}}
    )

    assert matrix.matrix["ffmpeg"][Platform.MACOS] is True
    assert matrix.matrix["ffmpeg"][Platform.LINUX] is False
    assert matrix.matrix["ffmpeg"][Platform.WINDOWS] is True


def test_platform_tool_matrix_missing_tool_returns_false() -> None:
    matrix = PlatformToolMatrix(matrix={"bun": {Platform.MACOS: True}})

    assert matrix.is_available("missing", Platform.MACOS) is False


def test_platform_tool_matrix_missing_platform_returns_false() -> None:
    matrix = PlatformToolMatrix(matrix={"bun": {Platform.MACOS: True}})

    assert matrix.is_available("bun", Platform.WINDOWS) is False
