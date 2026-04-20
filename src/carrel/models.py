from __future__ import annotations

from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Sensitivity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConvertTool(str, Enum):
    LITEPARSE = "liteparse"
    MINERU = "mineru"
    MARKDOWNIFY = "markdownify"
    DEFUDDLE = "defuddle"


class TranscribeTool(str, Enum):
    COLI = "coli"
    GROQ = "groq"
    GEMINI = "gemini"
    YOUTUBE_CAPTIONS = "youtube_captions"


class TrustLevel(str, Enum):
    ADVISORY = "advisory"
    CONSULTATIVE = "consultative"
    DELEGATED = "delegated"
    PARTNERSHIP = "partnership"


class AutomationModel(str, Enum):
    SONNET = "sonnet"
    OPUS = "opus"


class AutomationSchedule(str, Enum):
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"


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


class AutomationConfig(BaseModel):
    enabled: bool = False
    inbox_processing: bool = True
    vault_health: bool = True
    cross_linking_suggestions: bool = True
    gap_analysis: bool = False
    draft_feedback: bool = False
    reflection_synthesis: bool = True
    wiki_maintenance: bool = False
    trust_level: TrustLevel = TrustLevel.ADVISORY
    model: AutomationModel = AutomationModel.SONNET
    schedule: AutomationSchedule = AutomationSchedule.DAILY
    review_cadence: Literal["monthly", "quarterly", "biannual"] = "quarterly"
    last_reviewed: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("last_reviewed")
    @classmethod
    def validate_last_reviewed(cls, value: str | None) -> str | None:
        if value is None:
            return value
        date.fromisoformat(value)
        return value


class SetupState(BaseModel):
    """Tracks /carrel-setup phase progress for resumable setup.

    Written by `carrel vault init` after Phase 4 (initial: last_completed_phase=4).
    Updated by Claude as subsequent phases complete. Marked complete by setting
    `completed_at` to today's ISO date at Phase 9. Read by the session-start hook
    to surface a resume prompt for paused setups.
    """

    last_completed_phase: int = Field(ge=4, le=9)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    completed_at: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")

    @model_validator(mode="after")
    def validate_completion_state(self) -> SetupState:
        is_complete = self.completed_at is not None
        if (self.last_completed_phase == 9) != is_complete:
            raise ValueError(
                "last_completed_phase must be 9 if and only if completed_at is set"
            )
        return self


class ResearcherProfile(BaseModel):
    name: str | None = None
    field: str | None = None
    sensitivity: Sensitivity = Sensitivity.MEDIUM
    cloud_consent: bool = False
    comfort_level: str = "beginner"
    wiki_enabled: bool = False
    wiki_preference: str | None = None
    wiki_proposal_deferred_until: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    tools_configured: dict[str, bool] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)
    claude_code_familiarity: Literal["new", "some", "experienced"] | None = None
    collaborators: bool | None = None
    team_context: str | None = None

    @field_validator("wiki_proposal_deferred_until")
    @classmethod
    def validate_wiki_proposal_deferred_until(cls, value: str | None) -> str | None:
        if value is None:
            return value
        date.fromisoformat(value)
        return value
