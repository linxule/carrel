class CarrelError(Exception):
    """Base error with actionable hint."""

    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint
        super().__init__(message)


class ToolNotInstalled(CarrelError):
    def __init__(self, tool: str, install_command: str):
        super().__init__(f"{tool} is not installed", hint=f"Install it: {install_command}")


class ToolNotConfigured(CarrelError):
    def __init__(self, tool: str, missing: str):
        super().__init__(
            f"{tool} is not configured: {missing}",
            hint=f"Set {missing} in your environment or pass --tool to use a local alternative",
        )


class VaultNotFound(CarrelError):
    def __init__(self):
        super().__init__(
            "No vault found",
            hint="Run: carrel vault init ~/Documents/Research\n"
            "Or set CARREL_VAULT environment variable\n"
            "Or pass --vault /path/to/vault",
        )


class ConversionError(CarrelError):
    pass


class TranscriptionError(CarrelError):
    pass
