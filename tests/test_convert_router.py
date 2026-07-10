from pathlib import Path

import pytest

from carrel.convert.router import select_convert_tool
from carrel.errors import CarrelError
from carrel.models import (
    ApiKeyStatus,
    BinaryInfo,
    ConvertTool,
    Sensitivity,
    ToolAvailability,
)


def make_tools(
    *,
    lit: bool = False,
    mineru_key: bool = False,
    mistral_key: bool = False,
) -> ToolAvailability:
    return ToolAvailability(
        binaries={"lit": BinaryInfo(installed=lit)},
        api_keys={
            "mineru": ApiKeyStatus(configured=mineru_key, env_var="MINERU_API_KEY"),
            "mistral": ApiKeyStatus(configured=mistral_key, env_var="MISTRAL_API_KEY"),
        },
        mcp_servers=[],
    )


def test_convert_router_respects_explicit_tool() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.MEDIUM,
        tools=make_tools(mineru_key=True),
        explicit_tool=ConvertTool.MINERU,
    )
    assert tool == ConvertTool.MINERU


def test_convert_router_uses_markdownify_for_non_pdf() -> None:
    tool = select_convert_tool(
        file=Path("notes.docx"),
        sensitivity=Sensitivity.MEDIUM,
        tools=make_tools(),
    )
    assert tool == ConvertTool.MARKDOWNIFY


def test_convert_router_prefers_liteparse_for_pdf() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.MEDIUM,
        tools=make_tools(lit=True),
    )
    assert tool == ConvertTool.LITEPARSE


def test_convert_router_uses_mineru_when_low_sensitivity_allows_cloud_fallback() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.LOW,
        tools=make_tools(mineru_key=True),
        cloud_consent=True,
    )
    assert tool == ConvertTool.MINERU


def test_convert_router_uses_mistral_ocr_when_low_sensitivity_allows_cloud_fallback() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.LOW,
        tools=make_tools(mistral_key=True),
        cloud_consent=True,
    )
    assert tool == ConvertTool.MISTRAL_OCR


def test_convert_router_honors_explicit_mistral_ocr_request() -> None:
    tool = select_convert_tool(
        file=Path("paper.pdf"),
        sensitivity=Sensitivity.MEDIUM,
        tools=make_tools(lit=True, mistral_key=True),
        explicit_tool=ConvertTool.MISTRAL_OCR,
    )
    assert tool == ConvertTool.MISTRAL_OCR


def test_convert_router_rejects_explicit_mistral_ocr_without_api_key() -> None:
    with pytest.raises(CarrelError) as exc:
        select_convert_tool(
            file=Path("paper.pdf"),
            sensitivity=Sensitivity.MEDIUM,
            tools=make_tools(lit=True),
            explicit_tool=ConvertTool.MISTRAL_OCR,
        )
    assert exc.value.message == "Requested cloud tool is not available; configure credentials and retry"
    assert exc.value.hint == "Configure MISTRAL_API_KEY or choose an available local tool."


def test_convert_router_errors_when_medium_sensitivity_needs_explicit_cloud_override() -> None:
    with pytest.raises(CarrelError) as exc:
        select_convert_tool(
            file=Path("paper.pdf"),
            sensitivity=Sensitivity.MEDIUM,
            tools=make_tools(mineru_key=True),
            cloud_consent=True,
        )
    assert exc.value.message == "Local tool missing; to use cloud, run with `--tool <cloud>`"
    assert exc.value.hint is not None


def test_convert_router_rejects_defuddle_for_files() -> None:
    with pytest.raises(CarrelError, match="defuddle is for web capture"):
        select_convert_tool(
            file=Path("paper.pdf"),
            sensitivity=Sensitivity.MEDIUM,
            tools=make_tools(lit=True),
            explicit_tool=ConvertTool.DEFUDDLE,
        )


def test_convert_router_rejects_defuddle_for_non_pdf_too() -> None:
    with pytest.raises(CarrelError, match="defuddle is for web capture"):
        select_convert_tool(
            file=Path("notes.docx"),
            sensitivity=Sensitivity.MEDIUM,
            tools=make_tools(),
            explicit_tool=ConvertTool.DEFUDDLE,
        )


def test_convert_router_honors_explicit_mineru_for_non_pdf_document() -> None:
    # MinerU supports Office docs; an explicit request with the key set must route
    # to MinerU rather than fail 'configure credentials' (regression, spec wave A).
    tool = select_convert_tool(
        file=Path("notes.docx"),
        sensitivity=Sensitivity.MEDIUM,
        tools=make_tools(mineru_key=True),
        explicit_tool=ConvertTool.MINERU,
    )
    assert tool == ConvertTool.MINERU


def test_convert_router_honors_explicit_mistral_ocr_for_non_pdf_image() -> None:
    tool = select_convert_tool(
        file=Path("scan.png"),
        sensitivity=Sensitivity.MEDIUM,
        tools=make_tools(mistral_key=True),
        explicit_tool=ConvertTool.MISTRAL_OCR,
    )
    assert tool == ConvertTool.MISTRAL_OCR


def test_convert_router_non_pdf_default_stays_local_first() -> None:
    # Default (non-explicit) routing for a non-PDF is unchanged: local markdownify,
    # even when a cloud key is configured.
    tool = select_convert_tool(
        file=Path("notes.docx"),
        sensitivity=Sensitivity.MEDIUM,
        tools=make_tools(mineru_key=True),
    )
    assert tool == ConvertTool.MARKDOWNIFY


def test_convert_router_rejects_explicit_mineru_for_unsupported_suffix() -> None:
    with pytest.raises(CarrelError) as exc:
        select_convert_tool(
            file=Path("notes.txt"),
            sensitivity=Sensitivity.MEDIUM,
            tools=make_tools(mineru_key=True),
            explicit_tool=ConvertTool.MINERU,
        )
    assert "does not support" in exc.value.message
    assert "markdownify" in (exc.value.hint or "")


def test_convert_router_blocks_explicit_mineru_at_high_sensitivity_with_sensitivity_hint() -> None:
    with pytest.raises(CarrelError) as exc:
        select_convert_tool(
            file=Path("paper.pdf"),
            sensitivity=Sensitivity.HIGH,
            tools=make_tools(lit=True, mineru_key=True),
            explicit_tool=ConvertTool.MINERU,
        )
    # mineru key IS configured; the block is a sensitivity policy, so the hint must
    # not tell the user to configure credentials.
    assert exc.value.message == "HIGH sensitivity blocks cloud tools regardless of consent"
    assert "MINERU_API_KEY" not in (exc.value.hint or "")
    assert "sensitivity" in (exc.value.hint or "").lower()
