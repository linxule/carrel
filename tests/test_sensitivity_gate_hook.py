from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "sensitivity-gate.js"


def _run_hook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, command: str, explain_output: str):
    if not shutil.which("node"):
        pytest.skip("node is required for hook tests")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_carrel = bin_dir / "carrel"
    fake_carrel.write_text(f"#!/bin/sh\nprintf '%s\\n' {json.dumps(explain_output)}\n", encoding="utf-8")
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
