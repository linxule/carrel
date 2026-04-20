from carrel.env.platform import Platform, detect_platform


def test_detect_platform_maps_darwin(monkeypatch) -> None:
    monkeypatch.setattr("sys.platform", "darwin")
    assert detect_platform() is Platform.MACOS


def test_detect_platform_maps_linux(monkeypatch) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    assert detect_platform() is Platform.LINUX


def test_detect_platform_maps_win32(monkeypatch) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    assert detect_platform() is Platform.WINDOWS


def test_detect_platform_maps_cygwin(monkeypatch) -> None:
    monkeypatch.setattr("sys.platform", "cygwin")
    assert detect_platform() is Platform.WINDOWS


def test_detect_platform_maps_unknown(monkeypatch) -> None:
    monkeypatch.setattr("sys.platform", "plan9")
    assert detect_platform() is Platform.UNKNOWN
