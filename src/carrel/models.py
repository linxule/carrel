from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Sensitivity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConvertTool(str, Enum):
    LITEPARSE = "liteparse"
    MINERU = "mineru"
    MARKDOWNIFY = "markdownify"


class TranscribeTool(str, Enum):
    COLI = "coli"
    GROQ = "groq"
    GEMINI = "gemini"


class HardwareCapability(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BinaryInfo(BaseModel):
    installed: bool
    version: str | None = None
    path: str | None = None


class ApiKeyStatus(BaseModel):
    configured: bool
    env_var: str


class ToolAvailability(BaseModel):
    binaries: dict[str, BinaryInfo]
    api_keys: dict[str, ApiKeyStatus]
    mcp_servers: list[str]


class ConvertOptions(BaseModel):
    file: Path
    vault: Path
    tool: ConvertTool | None = None
    sensitivity: Sensitivity | None = None
    force: bool = False
    dry_run: bool = False


class ConvertResult(BaseModel):
    path: Path | None
    tool: ConvertTool
    pages: int | None = None
    duration_seconds: float
    skipped: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class TranscribeOptions(BaseModel):
    source: str
    vault: Path
    tool: TranscribeTool | None = None
    sensitivity: Sensitivity | None = None
    kind: str = "recording"
    speakers: int | None = None
    force: bool = False
    dry_run: bool = False
    timeout: int | None = None


class TranscribeResult(BaseModel):
    path: Path | None
    tool: TranscribeTool
    duration_seconds: float
    source_duration: str | None = None
    skipped: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class FileResult(BaseModel):
    path: Path
    action: str
    reason: str | None = None


class ScaffoldResult(BaseModel):
    vault: Path
    profile_path: Path
    created: list[str]
    skipped: list[str]


class AuditResult(BaseModel):
    os: str
    arch: str
    os_version: str | None = None
    ram_gb: int | None = None
    disk_free: str | None = None
    hardware_capability: HardwareCapability
    tools: ToolAvailability


class ResearcherProfile(BaseModel):
    name: str | None = None
    field: str | None = None
    sensitivity: Sensitivity = Sensitivity.MEDIUM
    cloud_consent: bool = False
    comfort_level: str = "beginner"
    tools_configured: dict[str, bool] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
