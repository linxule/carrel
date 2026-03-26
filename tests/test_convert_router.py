from pathlib import Path

import pytest

from carrel.convert.router import select_convert_tool
from carrel.errors import ToolNotInstalled
from carrel.models import (
    ApiKeyStatus,
    BinaryInfo,
    ConvertTool,
    HardwareCapability,
    Sensitivity,
    ToolAvailability,
)


def make_tools(*, lit: bool = False, mineru_key: bool = False) -> ToolAvailability:
    return ToolAvailability(
        binaries={"lit": BinaryInfo(installed=lit)},
        api_keys={"mineru": ApiKeyStatus(configured=mineru_key, env_var="MINERU_API_KEY")},
        mcp_servers=[],
    )


def test_convert_router_respects_explicit_tool() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.MEDIUM,
        tools=make_tools(),
        explicit_tool=ConvertTool.MINERU,
    )
    assert tool == ConvertTool.MINERU


def test_convert_router_uses_markdownify_for_non_pdf() -> None:
    tool = select_convert_tool(
        file=Path("notes.docx"),
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.MEDIUM,
        tools=make_tools(),
    )
    assert tool == ConvertTool.MARKDOWNIFY


def test_convert_router_prefers_liteparse_for_pdf() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.HIGH,
        tools=make_tools(lit=True),
    )
    assert tool == ConvertTool.LITEPARSE


def test_convert_router_uses_mineru_when_local_missing_and_cloud_allowed() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.MEDIUM,
        tools=make_tools(mineru_key=True),
        cloud_consent=True,
    )
    assert tool == ConvertTool.MINERU


def test_convert_router_errors_when_no_pdf_tool_available() -> None:
    with pytest.raises(ToolNotInstalled) as exc:
        select_convert_tool(
            file=Path("paper.pdf"),
            sensitivity=Sensitivity.MEDIUM,
            hardware=HardwareCapability.MEDIUM,
            tools=make_tools(),
        )
    assert exc.value.hint is not None
