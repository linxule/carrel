from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from carrel import __version__
from carrel.models import AuditResult, ResearcherProfile
from carrel.env.validation import (
    DriftIssue,
    detect_raw_marker_conflicts,
    format_validation_errors,
    unknown_environment_keys,
)

LEGACY_SENSITIVITY_MAP = {
    "prefer_local": ("medium", False),
    "cautious": ("medium", False),
    "external": ("low", True),
    "permissive": ("low", True),
}


class EnvironmentFixReport(BaseModel):
    status: str
    fixed: list[str]
    deferred: list[str]
    left_alone: list[str]
    dry_run: bool
    backup_path: str | None = None


def _populate_missing_top_level_fields(raw_data: dict[str, Any]) -> list[str]:
    default_profile = ResearcherProfile().model_dump(mode="json", by_alias=True)
    added: list[str] = []
    for field, value in default_profile.items():
        if field == "version":
            continue
        if field not in raw_data:
            raw_data[field] = deepcopy(value)
            added.append(f"Added missing optional field '{field}'")
    if "version" not in raw_data:
        raw_data["version"] = __version__
        added.append("Added missing optional field 'version'")
    return added


def _sync_tools_configured(raw_data: dict[str, Any], audit_result: AuditResult) -> list[str]:
    tools = raw_data.get("tools_configured")
    if not isinstance(tools, dict):
        return []

    changes: list[str] = []
    for tool, configured in sorted(tools.items()):
        actual = audit_result.tool_matrix.is_available(tool, audit_result.platform)
        if configured != actual:
            tools[tool] = actual
            changes.append(
                f"Re-synced tools_configured.{tool} to {str(actual).lower()} on {audit_result.platform.value}"
            )
    return changes


def apply_safe_environment_fixes(
    raw_data: dict[str, Any],
    audit_result: AuditResult,
    vault_path: Path,
    *,
    preserve_unknown: bool,
    dry_run: bool,
) -> tuple[EnvironmentFixReport, ResearcherProfile | None]:
    working = deepcopy(raw_data)
    fixed: list[str] = []
    deferred: list[str] = []
    left_alone: list[str] = []

    claude_path = vault_path / "CLAUDE.md"
    if claude_path.exists():
        for issue in detect_raw_marker_conflicts(
            working,
            claude_path.read_text(encoding="utf-8"),
        ):
            deferred.append(f"{issue.message}. Run /carrel-fix for guided recovery.")

    sensitivity = working.get("sensitivity")
    if isinstance(sensitivity, str):
        normalized = sensitivity.strip().lower()
        if normalized in LEGACY_SENSITIVITY_MAP:
            target_sensitivity, expected_cloud_consent = LEGACY_SENSITIVITY_MAP[normalized]
            current_cloud_consent = working.get("cloud_consent")
            if (
                isinstance(current_cloud_consent, bool)
                and current_cloud_consent != expected_cloud_consent
            ):
                deferred.append(
                    f"Cannot safely fix sensitivity='{sensitivity}' with cloud_consent="
                    f"{str(current_cloud_consent).lower()}. Run /carrel-fix for guided recovery."
                )
            else:
                working["sensitivity"] = target_sensitivity
                working["cloud_consent"] = expected_cloud_consent
                fixed.append(
                    f"Normalized sensitivity '{sensitivity}' to '{target_sensitivity}' "
                    f"and set cloud_consent={str(expected_cloud_consent).lower()}"
                )

    if working.get("version") not in (None, __version__):
        previous_version = working["version"]
        working["version"] = __version__
        fixed.append(f"Bumped version from {previous_version} to {__version__}")

    unknown_keys = unknown_environment_keys(working)
    if unknown_keys:
        if preserve_unknown:
            existing_bucket = working.get("_unknown_keys", {})
            if not isinstance(existing_bucket, dict):
                deferred.append(
                    "Cannot safely preserve unknown keys because _unknown_keys is not an object. "
                    "Run /carrel-fix for guided recovery."
                )
            else:
                for key in unknown_keys:
                    existing_bucket[key] = working.pop(key)
                working["_unknown_keys"] = existing_bucket
                fixed.append(
                    f"Moved orphaned keys to _unknown_keys: {', '.join(unknown_keys)}"
                )
        else:
            for key in unknown_keys:
                working.pop(key)
            fixed.append(f"Removed orphaned keys: {', '.join(unknown_keys)}")

    fixed.extend(_populate_missing_top_level_fields(working))
    fixed.extend(_sync_tools_configured(working, audit_result))

    try:
        profile = ResearcherProfile.model_validate(working)
    except ValidationError as error:
        for issue in format_validation_errors(error):
            deferred.append(
                f"Cannot safely fix {issue.path}: {issue.message}. Run /carrel-fix for guided recovery."
            )
        return (
            EnvironmentFixReport(
                status="deferred",
                fixed=[] if not dry_run else fixed,
                deferred=deferred,
                left_alone=left_alone,
                dry_run=dry_run,
            ),
            None,
        )

    if deferred:
        return (
            EnvironmentFixReport(
                status="deferred",
                fixed=[] if not dry_run else fixed,
                deferred=deferred,
                left_alone=left_alone,
                dry_run=dry_run,
            ),
            profile,
        )

    status = "dry_run" if dry_run and fixed else "noop"
    if fixed and not dry_run:
        status = "fixed"
    elif fixed:
        status = "dry_run"

    return (
        EnvironmentFixReport(
            status=status,
            fixed=fixed,
            deferred=deferred,
            left_alone=left_alone,
            dry_run=dry_run,
        ),
        profile,
    )
