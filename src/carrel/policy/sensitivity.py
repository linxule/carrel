from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from carrel.models import ConvertTool, Sensitivity, TranscribeTool

PolicyTool = ConvertTool | TranscribeTool
PolicyClass = Literal["convert", "transcribe"]

LOCAL_TOOLS: dict[PolicyClass, set[PolicyTool]] = {
    "convert": {ConvertTool.LITEPARSE, ConvertTool.MARKDOWNIFY, ConvertTool.DEFUDDLE},
    "transcribe": {TranscribeTool.COLI},
}
NETWORK_TOOLS: dict[PolicyClass, set[PolicyTool]] = {
    "convert": set(),
    "transcribe": {TranscribeTool.YOUTUBE_CAPTIONS},
}
CLOUD_TOOLS: dict[PolicyClass, set[PolicyTool]] = {
    "convert": {ConvertTool.MINERU, ConvertTool.MISTRAL_OCR},
    "transcribe": {TranscribeTool.GROQ, TranscribeTool.GEMINI},
}


@dataclass(frozen=True)
class PolicyDecision:
    requested_tool: PolicyTool | None
    selected_tool: PolicyTool | None
    sensitivity: Sensitivity
    cloud_consent: bool
    tool_class: PolicyClass
    local_available: bool
    cloud_available: bool
    rationale: str


def _is_local(tool: PolicyTool, tool_class: PolicyClass) -> bool:
    return tool in LOCAL_TOOLS[tool_class]


def _is_cloud(tool: PolicyTool, tool_class: PolicyClass) -> bool:
    return tool in CLOUD_TOOLS[tool_class]


def _is_network(tool: PolicyTool, tool_class: PolicyClass) -> bool:
    return tool in NETWORK_TOOLS[tool_class]


def _first_available(available_tools: list[PolicyTool], *, tool_class: PolicyClass, locality: str) -> PolicyTool | None:
    if locality == "local":
        candidates = LOCAL_TOOLS[tool_class]
    elif locality == "network":
        candidates = NETWORK_TOOLS[tool_class]
    else:
        candidates = CLOUD_TOOLS[tool_class]
    for tool in available_tools:
        if tool in candidates:
            return tool
    return None


def _decision(
    *,
    requested_tool: PolicyTool | None,
    selected_tool: PolicyTool | None,
    sensitivity: Sensitivity,
    cloud_consent: bool,
    tool_class: PolicyClass,
    local_available: bool,
    cloud_available: bool,
    rationale: str,
) -> PolicyDecision:
    return PolicyDecision(
        requested_tool=requested_tool,
        selected_tool=selected_tool,
        sensitivity=sensitivity,
        cloud_consent=cloud_consent,
        tool_class=tool_class,
        local_available=local_available,
        cloud_available=cloud_available,
        rationale=rationale,
    )


def select_tool(
    requested_tool: PolicyTool | None,
    available_tools: list[PolicyTool],
    sensitivity: Sensitivity,
    cloud_consent: bool,
    tool_class: PolicyClass,
) -> PolicyDecision:
    local_tool = _first_available(available_tools, tool_class=tool_class, locality="local")
    network_tool = _first_available(available_tools, tool_class=tool_class, locality="network")
    cloud_tool = _first_available(available_tools, tool_class=tool_class, locality="cloud")
    local_available = local_tool is not None
    cloud_available = cloud_tool is not None

    if requested_tool is not None:
        if _is_network(requested_tool, tool_class):
            # A caption fetch egresses no vault data (only the public video URL),
            # so an explicit request is honored at every sensitivity level. At HIGH
            # the default routing still refuses (below); this is the researcher's
            # deliberate override, recorded in the rationale.
            if requested_tool not in available_tools:
                return _decision(
                    requested_tool=requested_tool,
                    selected_tool=None,
                    sensitivity=sensitivity,
                    cloud_consent=cloud_consent,
                    tool_class=tool_class,
                    local_available=local_available,
                    cloud_available=cloud_available,
                    rationale="Requested caption tool is not available; install it and retry",
                )
            if sensitivity == Sensitivity.HIGH:
                return _decision(
                    requested_tool=requested_tool,
                    selected_tool=requested_tool,
                    sensitivity=sensitivity,
                    cloud_consent=cloud_consent,
                    tool_class=tool_class,
                    local_available=local_available,
                    cloud_available=cloud_available,
                    rationale="HIGH sensitivity: explicit researcher override for public caption fetch",
                )
            return _decision(
                requested_tool=requested_tool,
                selected_tool=requested_tool,
                sensitivity=sensitivity,
                cloud_consent=cloud_consent,
                tool_class=tool_class,
                local_available=local_available,
                cloud_available=cloud_available,
                rationale="public caption fetch, no vault data egresses",
            )

        if _is_cloud(requested_tool, tool_class):
            if sensitivity == Sensitivity.HIGH:
                return _decision(
                    requested_tool=requested_tool,
                    selected_tool=None,
                    sensitivity=sensitivity,
                    cloud_consent=cloud_consent,
                    tool_class=tool_class,
                    local_available=local_available,
                    cloud_available=cloud_available,
                    rationale="HIGH sensitivity blocks cloud tools regardless of consent",
                )
            if requested_tool not in available_tools:
                return _decision(
                    requested_tool=requested_tool,
                    selected_tool=None,
                    sensitivity=sensitivity,
                    cloud_consent=cloud_consent,
                    tool_class=tool_class,
                    local_available=local_available,
                    cloud_available=cloud_available,
                    rationale="Requested cloud tool is not available; configure credentials and retry",
                )
            return _decision(
                requested_tool=requested_tool,
                selected_tool=requested_tool,
                sensitivity=sensitivity,
                cloud_consent=cloud_consent,
                tool_class=tool_class,
                local_available=local_available,
                cloud_available=cloud_available,
                rationale="Explicit cloud tool request counts as consent",
            )

        if local_available and requested_tool in available_tools:
            return _decision(
                requested_tool=requested_tool,
                selected_tool=requested_tool,
                sensitivity=sensitivity,
                cloud_consent=cloud_consent,
                tool_class=tool_class,
                local_available=local_available,
                cloud_available=cloud_available,
                rationale="Requested local tool is available; preference honored",
            )

        if sensitivity == Sensitivity.HIGH:
            return _decision(
                requested_tool=requested_tool,
                selected_tool=None,
                sensitivity=sensitivity,
                cloud_consent=cloud_consent,
                tool_class=tool_class,
                local_available=local_available,
                cloud_available=cloud_available,
                rationale="HIGH sensitivity requires local; local tool missing; install and retry",
            )
        if sensitivity == Sensitivity.MEDIUM:
            return _decision(
                requested_tool=requested_tool,
                selected_tool=None,
                sensitivity=sensitivity,
                cloud_consent=cloud_consent,
                tool_class=tool_class,
                local_available=local_available,
                cloud_available=cloud_available,
                rationale="Local tool missing; to use cloud, run with `--tool <cloud>`",
            )
        if cloud_consent and cloud_tool is not None:
            return _decision(
                requested_tool=requested_tool,
                selected_tool=cloud_tool,
                sensitivity=sensitivity,
                cloud_consent=cloud_consent,
                tool_class=tool_class,
                local_available=local_available,
                cloud_available=cloud_available,
                rationale="Requested local tool unavailable; cloud consent enabled so routing to cloud",
            )
        return _decision(
            requested_tool=requested_tool,
            selected_tool=None,
            sensitivity=sensitivity,
            cloud_consent=cloud_consent,
            tool_class=tool_class,
            local_available=local_available,
            cloud_available=cloud_available,
            rationale="Local tool missing; to use cloud, set cloud_consent=True or run with `--tool <cloud>`",
        )

    if local_tool is not None:
        return _decision(
            requested_tool=requested_tool,
            selected_tool=local_tool,
            sensitivity=sensitivity,
            cloud_consent=cloud_consent,
            tool_class=tool_class,
            local_available=local_available,
            cloud_available=cloud_available,
            rationale="Local tool selected by default",
        )

    if network_tool is not None:
        if sensitivity == Sensitivity.HIGH:
            return _decision(
                requested_tool=requested_tool,
                selected_tool=None,
                sensitivity=sensitivity,
                cloud_consent=cloud_consent,
                tool_class=tool_class,
                local_available=local_available,
                cloud_available=cloud_available,
                rationale="HIGH sensitivity blocks automatic caption fetches; pass --tool youtube_captions to override for public captions",
            )
        return _decision(
            requested_tool=requested_tool,
            selected_tool=network_tool,
            sensitivity=sensitivity,
            cloud_consent=cloud_consent,
            tool_class=tool_class,
            local_available=local_available,
            cloud_available=cloud_available,
            rationale="Caption fetch selected by default; public captions, no vault data egresses",
        )

    if sensitivity == Sensitivity.HIGH:
        return _decision(
            requested_tool=requested_tool,
            selected_tool=None,
            sensitivity=sensitivity,
            cloud_consent=cloud_consent,
            tool_class=tool_class,
            local_available=local_available,
            cloud_available=cloud_available,
            rationale="HIGH sensitivity requires local; local tool missing; install and retry",
        )
    if sensitivity == Sensitivity.MEDIUM:
        return _decision(
            requested_tool=requested_tool,
            selected_tool=None,
            sensitivity=sensitivity,
            cloud_consent=cloud_consent,
            tool_class=tool_class,
            local_available=local_available,
            cloud_available=cloud_available,
            rationale="Local tool missing; to use cloud, run with `--tool <cloud>`",
        )
    if cloud_consent and cloud_tool is not None:
        return _decision(
            requested_tool=requested_tool,
            selected_tool=cloud_tool,
            sensitivity=sensitivity,
            cloud_consent=cloud_consent,
            tool_class=tool_class,
            local_available=local_available,
            cloud_available=cloud_available,
            rationale="No local tool available; cloud consent enabled so routing to cloud",
        )
    return _decision(
        requested_tool=requested_tool,
        selected_tool=None,
        sensitivity=sensitivity,
        cloud_consent=cloud_consent,
        tool_class=tool_class,
        local_available=local_available,
        cloud_available=cloud_available,
        rationale="Local tool missing; to use cloud, set cloud_consent=True or run with `--tool <cloud>`",
    )
