from enum import Enum
import sys


class Platform(str, Enum):
    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


def detect_platform() -> Platform:
    p = sys.platform
    if p.startswith("darwin"):
        return Platform.MACOS
    if p.startswith("linux"):
        return Platform.LINUX
    if p.startswith("win32") or p == "cygwin":
        return Platform.WINDOWS
    return Platform.UNKNOWN
