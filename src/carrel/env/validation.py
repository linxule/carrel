from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from carrel import __version__
from carrel.models import AuditResult, ResearcherProfile
from carrel.vault.markers import parse_markers
from carrel.vault.sync import compare_markers


class ValidationIssue(BaseModel):
    path: str
    message: str
    type: str


class DriftIssue(BaseModel):
    check: str
    message: str
    field: str | None = None


class EnvironmentValidationReport(BaseModel):
    status: str
    errors: list[ValidationIssue]
    drift: list[DriftIssue]


def load_environment_payload(path: Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    try:
        raw_data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [
            ValidationIssue(
                path="$",
                message=f"Invalid JSON: {error.msg}",
                type="json_invalid",
            )
        ]
    if not isinstance(raw_data, dict):
        return None, [
            ValidationIssue(
                path="$",
                message="environment.json must contain a JSON object",
                type="model_type",
            )
        ]
    return raw_data, []


def validate_environment_payload(path: Path) -> tuple[ResearcherProfile | None, list[ValidationIssue]]:
    try:
        profile = ResearcherProfile.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as error:
        return None, format_validation_errors(error)
    return profile, []


def format_validation_errors(error: ValidationError) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for item in error.errors():
        loc = item.get("loc", ())
        path = ".".join(str(part) for part in loc) or "$"
        issues.append(
            ValidationIssue(
                path=path,
                message=item.get("msg", "Invalid value"),
                type=item.get("type", "validation_error"),
            )
        )
    return issues


def detect_environment_drift(
    vault_path: Path,
    raw_data: dict[str, Any],
    profile: ResearcherProfile,
    audit_result: AuditResult,
) -> list[DriftIssue]:
    drift: list[DriftIssue] = []

    unknown_keys = sorted(set(raw_data) - set(ResearcherProfile.model_fields))
    if unknown_keys:
        drift.append(
            DriftIssue(
                check="unknown_keys",
                field=", ".join(unknown_keys),
                message=f"Unknown top-level keys: {', '.join(unknown_keys)}",
            )
        )

    version = raw_data.get("version")
    if version is not None and version != __version__:
        drift.append(
            DriftIssue(
                check="version",
                field="version",
                message=f"environment.json version is {version}; current plugin version is {__version__}",
            )
        )

    for tool, configured in sorted(profile.tools_configured.items()):
        actual = audit_result.tool_matrix.is_available(tool, audit_result.platform)
        if configured != actual:
            drift.append(
                DriftIssue(
                    check="tools_configured",
                    field=f"tools_configured.{tool}",
                    message=(
                        f"tools_configured.{tool}={str(configured).lower()} but audit reports "
                        f"{str(actual).lower()} on {audit_result.platform.value}"
                    ),
                )
            )

    claude_path = vault_path / "CLAUDE.md"
    if claude_path.exists():
        markers = parse_markers(claude_path.read_text(encoding="utf-8"))
        for item in compare_markers(profile, markers):
            drift.append(
                DriftIssue(
                    check="markers",
                    field=item["field"],
                    message=(
                        f"CLAUDE.md marker {item['field']}={item['marker']} does not match "
                        f"environment.json {item['profile']}"
                    ),
                )
            )

    return drift


def report_status(errors: list[ValidationIssue], drift: list[DriftIssue]) -> str:
    if errors:
        return "invalid"
    if drift:
        return "drift"
    return "valid"
