import pytest

from carrel.errors import CarrelError
from carrel.models import (
    ApiKeyStatus,
    BinaryInfo,
    HardwareCapability,
    Sensitivity,
    ToolAvailability,
    TranscribeTool,
)
from carrel.transcribe.router import select_transcribe_tool


def make_tools(*, coli: bool = False, groq_key: bool = False, gemini_key: bool = False) -> ToolAvailability:
    return ToolAvailability(
        binaries={"coli": BinaryInfo(installed=coli)},
        api_keys={
            "groq": ApiKeyStatus(configured=groq_key, env_var="GROQ_API_KEY"),
            "gemini": ApiKeyStatus(configured=gemini_key, env_var="GEMINI_API_KEY"),
        },
        mcp_servers=[],
    )


def test_transcribe_router_respects_explicit_tool() -> None:
    tool = select_transcribe_tool(
        source="audio.wav",
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.MEDIUM,
        tools=make_tools(),
        explicit_tool=TranscribeTool.GROQ,
    )
    assert tool == TranscribeTool.GROQ


def test_transcribe_router_prefers_youtube_captions_over_gemini_by_default() -> None:
    tool = select_transcribe_tool(
        source="https://www.youtube.com/watch?v=abc123",
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.HIGH,
        tools=make_tools(gemini_key=True),
        cloud_consent=True,
    )
    assert tool == TranscribeTool.YOUTUBE_CAPTIONS


def test_transcribe_router_falls_back_to_local_youtube_captions() -> None:
    tool = select_transcribe_tool(
        source="https://youtu.be/abc123",
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.MEDIUM,
        tools=make_tools(),
    )
    assert tool == TranscribeTool.YOUTUBE_CAPTIONS


def test_transcribe_router_prefers_coli_for_audio_files() -> None:
    tool = select_transcribe_tool(
        source="recording.m4a",
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.MEDIUM,
        tools=make_tools(coli=True),
    )
    assert tool == TranscribeTool.COLI


def test_transcribe_router_uses_groq_when_low_sensitivity_allows_cloud_fallback() -> None:
    tool = select_transcribe_tool(
        source="recording.m4a",
        sensitivity=Sensitivity.LOW,
        hardware=HardwareCapability.LOW,
        tools=make_tools(groq_key=True),
        cloud_consent=True,
    )
    assert tool == TranscribeTool.GROQ


def test_transcribe_router_errors_for_medium_sensitivity_without_explicit_cloud_override() -> None:
    with pytest.raises(CarrelError) as exc:
        select_transcribe_tool(
            source="recording.m4a",
            sensitivity=Sensitivity.MEDIUM,
            hardware=HardwareCapability.MEDIUM,
            tools=make_tools(groq_key=True),
            cloud_consent=True,
        )
    assert exc.value.message == "Local tool missing; to use cloud, run with `--tool <cloud>`"
    assert exc.value.hint is not None


def test_transcribe_router_rejects_gemini_for_local_file() -> None:
    with pytest.raises(CarrelError, match="only works with YouTube URLs"):
        select_transcribe_tool(
            source="interview.m4a",
            sensitivity=Sensitivity.MEDIUM,
            hardware=HardwareCapability.MEDIUM,
            tools=make_tools(gemini_key=True),
            explicit_tool=TranscribeTool.GEMINI,
        )


def test_transcribe_router_rejects_youtube_captions_for_local_file() -> None:
    with pytest.raises(CarrelError, match="only works with YouTube URLs"):
        select_transcribe_tool(
            source="/path/to/lecture.wav",
            sensitivity=Sensitivity.MEDIUM,
            hardware=HardwareCapability.MEDIUM,
            tools=make_tools(),
            explicit_tool=TranscribeTool.YOUTUBE_CAPTIONS,
        )


def test_transcribe_router_rejects_groq_for_youtube_url() -> None:
    with pytest.raises(CarrelError, match="only works with local audio files"):
        select_transcribe_tool(
            source="https://www.youtube.com/watch?v=abc123",
            sensitivity=Sensitivity.MEDIUM,
            hardware=HardwareCapability.MEDIUM,
            tools=make_tools(groq_key=True),
            explicit_tool=TranscribeTool.GROQ,
        )


def test_transcribe_router_rejects_coli_for_youtube_url() -> None:
    with pytest.raises(CarrelError, match="only works with local audio files"):
        select_transcribe_tool(
            source="https://youtu.be/abc123",
            sensitivity=Sensitivity.MEDIUM,
            hardware=HardwareCapability.MEDIUM,
            tools=make_tools(coli=True),
            explicit_tool=TranscribeTool.COLI,
        )


def test_transcribe_router_allows_gemini_for_youtube_url() -> None:
    tool = select_transcribe_tool(
        source="https://www.youtube.com/watch?v=test123",
        sensitivity=Sensitivity.MEDIUM,
        hardware=HardwareCapability.MEDIUM,
        tools=make_tools(gemini_key=True),
        explicit_tool=TranscribeTool.GEMINI,
    )
    assert tool == TranscribeTool.GEMINI
