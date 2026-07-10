from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "sensitivity-gate.js"


def _argv_dump_path(tmp_path: Path) -> Path:
    """Where the fake carrel records the argv the hook actually re-invoked it with."""
    return tmp_path / "argv.txt"


def _run_hook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, command: str, explain_output: str):
    if not shutil.which("node"):
        pytest.skip("node is required for hook tests")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_carrel = bin_dir / "carrel"
    argv_dump = shlex.quote(str(_argv_dump_path(tmp_path)))
    # Record every argument the hook passes so tests can prove the tokenizer
    # produced correct argv (e.g. a quoted path arriving as ONE token), then
    # emit the canned --explain payload regardless of args.
    fake_carrel.write_text(
        "#!/bin/sh\n"
        f": > {argv_dump}\n"
        f'for a in "$@"; do printf \'%s\\n\' "$a" >> {argv_dump}; done\n'
        f"printf '%s\\n' {json.dumps(explain_output)}\n",
        encoding="utf-8",
    )
    fake_carrel.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")

    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    return subprocess.run(
        ["node", str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def test_sensitivity_gate_asks_for_mistral_ocr_on_medium_sensitivity(tmp_path, monkeypatch) -> None:
    result = _run_hook(
        tmp_path,
        monkeypatch,
        command="carrel paper convert scan.pdf --tool mistral_ocr",
        explain_output=(
            "PolicyDecision(selected_tool=<ConvertTool.MISTRAL_OCR: 'mistral_ocr'>, "
            "sensitivity=<Sensitivity.MEDIUM: 'medium'>, "
            "rationale='Explicit cloud tool request counts as consent')"
        ),
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "ask"
    assert "medium sensitivity vault" in hook_output["permissionDecisionReason"]


def test_sensitivity_gate_denies_mistral_ocr_when_policy_denies(tmp_path, monkeypatch) -> None:
    result = _run_hook(
        tmp_path,
        monkeypatch,
        command="carrel paper convert scan.pdf --tool mistral_ocr",
        explain_output=(
            "PolicyDecision(selected_tool=None, sensitivity=<Sensitivity.HIGH: 'high'>, "
            "rationale='HIGH sensitivity blocks cloud tools regardless of consent')"
        ),
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["permissionDecision"] == "deny"
    assert "HIGH sensitivity blocks cloud tools" in hook_output["permissionDecisionReason"]


def test_sensitivity_gate_tokenizes_quoted_path_as_single_argv(tmp_path, monkeypatch) -> None:
    """A quoted path with spaces must reach carrel as ONE argv token.

    Whitespace splitting (the old behavior) would shatter
    '/path/with spaces/scan.pdf' into three broken args, the --explain
    subprocess would fail, and the gate would silently pass the cloud
    command through instead of asking.
    """
    result = _run_hook(
        tmp_path,
        monkeypatch,
        command="carrel paper convert '/path/with spaces/scan.pdf' --tool mistral_ocr",
        explain_output=(
            "PolicyDecision(selected_tool=<ConvertTool.MISTRAL_OCR: 'mistral_ocr'>, "
            "sensitivity=<Sensitivity.MEDIUM: 'medium'>, "
            "rationale='Explicit cloud tool request counts as consent')"
        ),
    )

    assert result.returncode == 0
    hook_output = json.loads(result.stdout)["hookSpecificOutput"]
    assert hook_output["permissionDecision"] == "ask"
    # The path survived as a single argument, not three.
    argv = _argv_dump_path(tmp_path).read_text(encoding="utf-8").splitlines()
    assert "/path/with spaces/scan.pdf" in argv
    assert argv[-1] == "--explain"


def test_sensitivity_gate_matches_equals_tool_form(tmp_path, monkeypatch) -> None:
    """`--tool=mistral_ocr` (equals form) must trip the checkpoint too."""
    result = _run_hook(
        tmp_path,
        monkeypatch,
        command="carrel paper convert scan.pdf --tool=mistral_ocr",
        explain_output=(
            "PolicyDecision(selected_tool=<ConvertTool.MISTRAL_OCR: 'mistral_ocr'>, "
            "sensitivity=<Sensitivity.MEDIUM: 'medium'>, "
            "rationale='Explicit cloud tool request counts as consent')"
        ),
    )

    assert result.returncode == 0
    hook_output = json.loads(result.stdout)["hookSpecificOutput"]
    assert hook_output["permissionDecision"] == "ask"
    argv = _argv_dump_path(tmp_path).read_text(encoding="utf-8").splitlines()
    assert "--tool=mistral_ocr" in argv


def test_sensitivity_gate_passes_through_on_tokenizer_uncertainty(tmp_path, monkeypatch) -> None:
    """An unquoted shell operator means the line is more than one carrel call.

    The tokenizer returns null (uncertainty); the hook then fails open — no
    decision emitted, and carrel is never re-invoked.
    """
    result = _run_hook(
        tmp_path,
        monkeypatch,
        command="carrel paper convert scan.pdf --tool mistral_ocr && echo done",
        explain_output=(
            "PolicyDecision(selected_tool=<ConvertTool.MISTRAL_OCR: 'mistral_ocr'>, "
            "sensitivity=<Sensitivity.MEDIUM: 'medium'>, rationale='n/a')"
        ),
    )

    assert result.returncode == 0
    assert result.stdout == ""  # no permission decision — silent pass-through
    assert not _argv_dump_path(tmp_path).exists()  # carrel never re-invoked
