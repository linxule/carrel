from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "check-environment.js"


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    carrel_dir = vault / ".carrel"
    carrel_dir.mkdir(parents=True)
    (carrel_dir / "environment.json").write_text(
        json.dumps({"name": "Ada", "sensitivity": "medium", "cloud_consent": False, "tools_configured": {}}),
        encoding="utf-8",
    )
    (carrel_dir / "plugin-state.json").write_text("{}", encoding="utf-8")
    return vault


def _run_hook(vault: Path, monkeypatch: pytest.MonkeyPatch, *, path_dirs: list[Path]) -> subprocess.CompletedProcess:
    if not shutil.which("node"):
        pytest.skip("node is required for hook tests")
    node_dir = str(Path(shutil.which("node")).parent)
    path_value = os.pathsep.join([*(str(p) for p in path_dirs), node_dir])
    monkeypatch.setenv("PATH", path_value)
    return subprocess.run(
        ["node", str(HOOK)],
        cwd=vault,
        text=True,
        capture_output=True,
        check=False,
    )


def test_missing_carrel_binary_prints_actionable_hint(tmp_path, monkeypatch) -> None:
    vault = _make_vault(tmp_path)
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()

    result = _run_hook(vault, monkeypatch, path_dirs=[empty_bin])

    assert result.returncode == 0
    assert "Carrel CLI not found" in result.stdout
    assert "uv tool install git+https://github.com/linxule/carrel.git" in result.stdout

    state = json.loads((vault / ".carrel" / "plugin-state.json").read_text(encoding="utf-8"))
    assert "last_validated_at" in state


def test_missing_carrel_binary_hint_is_throttled_within_24h(tmp_path, monkeypatch) -> None:
    vault = _make_vault(tmp_path)
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()

    first = _run_hook(vault, monkeypatch, path_dirs=[empty_bin])
    assert "Carrel CLI not found" in first.stdout

    second = _run_hook(vault, monkeypatch, path_dirs=[empty_bin])
    assert "Carrel CLI not found" not in second.stdout


def test_env_validate_drift_exit_code_still_surfaces(tmp_path, monkeypatch) -> None:
    vault = _make_vault(tmp_path)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_carrel = fake_bin / "carrel"
    fake_carrel.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    fake_carrel.chmod(0o755)

    result = _run_hook(vault, monkeypatch, path_dirs=[fake_bin])

    assert result.returncode == 0
    assert "Environment drift detected" in result.stdout


def _sh() -> list[Path]:
    # Fake `carrel` scripts below shell out to `sleep`; include real system
    # bin dirs so that resolves, on top of the fake carrel's own dir.
    return [Path("/bin"), Path("/usr/bin")]


def test_slow_carrel_within_new_timeout_still_completes(tmp_path, monkeypatch) -> None:
    # Regression guard for the timeout bump (1000ms -> 3000ms): a cold start
    # slower than the old timeout must not be killed under the new one.
    if not (Path("/bin/sleep").exists() or Path("/usr/bin/sleep").exists()):
        pytest.skip("sleep is required for this test")
    vault = _make_vault(tmp_path)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_carrel = fake_bin / "carrel"
    fake_carrel.write_text("#!/bin/sh\nsleep 1.5\nexit 2\n", encoding="utf-8")
    fake_carrel.chmod(0o755)

    result = _run_hook(vault, monkeypatch, path_dirs=[fake_bin, *_sh()])

    assert result.returncode == 0
    assert "Environment drift detected" in result.stdout
    assert "ETIMEDOUT" not in result.stderr


def test_carrel_timeout_still_stamps_throttle_and_logs_reason(tmp_path, monkeypatch) -> None:
    # A carrel invocation slower than the 3000ms timeout must be killed, but
    # the hook still (a) exits 0 non-blocking, (b) stamps last_validated_at so
    # a chronically slow machine isn't re-checked every session, and (c) logs
    # the ETIMEDOUT reason.
    if not (Path("/bin/sleep").exists() or Path("/usr/bin/sleep").exists()):
        pytest.skip("sleep is required for this test")
    vault = _make_vault(tmp_path)
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_carrel = fake_bin / "carrel"
    fake_carrel.write_text("#!/bin/sh\nsleep 5\n", encoding="utf-8")
    fake_carrel.chmod(0o755)

    result = _run_hook(vault, monkeypatch, path_dirs=[fake_bin, *_sh()])

    assert result.returncode == 0
    assert "ETIMEDOUT" in result.stderr

    state = json.loads((vault / ".carrel" / "plugin-state.json").read_text(encoding="utf-8"))
    assert "last_validated_at" in state
