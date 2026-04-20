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


def environment_field_names() -> set[str]:
    names: set[str] = set()
    for name, field in ResearcherProfile.model_fields.items():
        names.add(name)
        if field.alias:
            names.add(field.alias)
        if field.serialization_alias:
            names.add(field.serialization_alias)
    return names


def unknown_environment_keys(raw_data: dict[str, Any]) -> list[str]:
    return sorted(set(raw_data) - environment_field_names())


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

    unknown_keys = unknown_environment_keys(raw_data)
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


def raw_marker_values(raw_data: dict[str, Any]) -> dict[str, str]:
    automation = raw_data.get("automation") if isinstance(raw_data.get("automation"), dict) else {}
    tools = raw_data.get("tools_configured") if isinstance(raw_data.get("tools_configured"), dict) else {}
    enabled_tools = sorted(tool for tool, enabled in tools.items() if enabled is True)

    values: dict[str, str] = {}
    if isinstance(raw_data.get("sensitivity"), str):
        values["sensitivity"] = raw_data["sensitivity"].strip().lower()
    if isinstance(raw_data.get("cloud_consent"), bool):
        values["cloud_consent"] = str(raw_data["cloud_consent"]).lower()
    if isinstance(automation.get("trust_level"), str):
        values["trust_level"] = automation["trust_level"].strip().lower()
    values["tools_configured"] = ",".join(enabled_tools)
    if isinstance(raw_data.get("wiki_enabled"), bool):
        values["wiki_enabled"] = str(raw_data["wiki_enabled"]).lower()
    return values


def detect_raw_marker_conflicts(
    raw_data: dict[str, Any],
    claude_text: str,
) -> list[DriftIssue]:
    markers = parse_markers(claude_text)
    if not markers:
        return []

    raw_values = raw_marker_values(raw_data)
    conflicts: list[DriftIssue] = []
    for field, marker_value in markers.items():
        raw_value = raw_values.get(field)
        if raw_value is None:
            continue
        if raw_value != marker_value:
            conflicts.append(
                DriftIssue(
                    check="markers",
                    field=field,
                    message=(
                        f"CLAUDE.md marker {field}={marker_value} does not match "
                        f"environment.json {raw_value}"
                    ),
                )
            )
    return conflicts
