"""Cross-runtime behavioral parity between the two Carrel engines.

Carrel ships the same deterministic operations through two independent
implementations:

* the **typed CLI** (`src/carrel`, typer + pydantic), invoked here in-process
  via typer's ``CliRunner`` — the pattern used across ``tests/test_*_cli.py``;
* the **portable runtime** (`skills/carrel/scripts/carrel.py`, stdlib only),
  invoked by subprocess exactly as ``tests/test_carrel_skill_pack.py`` does
  (copy the skill to a temp dir, run ``[sys.executable, carrel.py, ...]`` with
  ``PYTHONPATH=""`` so no ``carrel`` import can leak in).

The host-split architecture decision (2026-07-10) makes the portable runtime a
**strict subset** of the typed CLI: on every *shared* deterministic surface the
two must agree, while a small, enumerated set of surfaces is deliberately
owned by only one host. Prior tests only checked asset byte-identity and
field-coverage; none ran identical inputs through both engines and compared the
outcomes. This module is that missing drift alarm.

Two kinds of assertion live here:

1. **Parity** — same input, both runtimes, outcomes must match (verdict, exit
   semantics, persisted content, JSON metrics).
2. **Enumerated divergence** — ``vault init`` intentionally differs; the
   difference is pinned to a named allowlist so any *new* unlisted divergence
   fails the test.

Known behavioral mismatches discovered while writing this suite (see the
relevant tests for the precise repro):

* ``reflection append`` seeds a first-of-day file differently (typed scaffolds
  from ``_templates/reflection.md``; portable writes a minimal header). The
  appended timestamped entry itself is identical.
* ``feedback export`` renders a different digest *header* and different
  *inter-section* spacing; the redacted section bodies and JSON metrics match.
* a malformed non-boolean ``cloud_consent`` at *command time* (e.g.
  ``transcript create``) is rejected by both engines, but by different,
  intentional mechanisms: the typed CLI fails closed at profile read
  (``read_profile`` raises before any tool decision runs); the portable
  runtime has no profile-level schema gate at command time and instead
  reads consent with a strict ``is True`` check, so the malformed value is
  simply treated as consent-not-granted and the decision proceeds. See
  ``test_cloud_consent_command_time_parity_never_grants_cloud``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from carrel.cli.main import app
from carrel.env.platform import Platform
from carrel.models import (
    AuditResult,
    HardwareCapability,
    PlatformToolMatrix,
    ResearcherProfile,
    Sensitivity,
    ToolAvailability,
    TranscribeTool,
)
from carrel.policy.sensitivity import select_tool

SKILL_SRC = Path(__file__).resolve().parents[1] / "skills" / "carrel"
runner = CliRunner()


# ---------------------------------------------------------------------------
# Invocation helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def portable_skill(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A single read-only copy of the portable skill for the whole module.

    The runtime sets ``sys.dont_write_bytecode`` and never mutates its own
    directory, so one copy is safe to reuse across cases (vaults are always
    fresh per test). Copying once keeps the suite well under its time budget.
    """

    target = tmp_path_factory.mktemp("portable-skill") / "carrel-skill"
    shutil.copytree(SKILL_SRC, target)
    return target


def _portable(
    skill: Path,
    *args: str,
    input_text: str | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = ""  # force stdlib-only; no carrel package on the path
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(skill / "scripts" / "carrel.py"), *args],
        input=input_text,
        text=True,
        capture_output=True,
        cwd=skill.parent,
        env=env,
        check=False,
        timeout=30,
    )


def _init_typed(vault: Path) -> None:
    result = runner.invoke(app, ["vault", "init", str(vault)])
    assert result.exit_code == 0, result.output


def _init_portable(skill: Path, vault: Path) -> None:
    result = _portable(skill, "vault", "init", str(vault))
    assert result.returncode == 0, result.stderr


def _write_env(vault: Path, payload: dict) -> None:
    (vault / ".carrel" / "environment.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _read_env(vault: Path) -> dict:
    return json.loads((vault / ".carrel" / "environment.json").read_text(encoding="utf-8"))


def _valid_profile() -> dict:
    """A schema-complete profile that both engines accept as valid.

    ``version`` is null (no typed version-drift) and ``tools_configured`` is
    empty (no audit-driven tool-drift), so the outcome does not depend on the
    host machine's installed tools.
    """

    return ResearcherProfile().model_dump(mode="json", by_alias=True)


async def _fake_audit(project_path: Path | None = None) -> AuditResult:  # noqa: ARG001
    """Deterministic empty audit for the one env-validate case that runs it.

    ``env validate`` only audits when the profile parses cleanly (the valid
    case). With empty ``tools_configured`` the drift loop is a no-op, but we
    still stub the hardware probe so the test is hermetic and fast.
    """

    return AuditResult(
        os="test",
        platform=Platform.MACOS,
        arch="arm64",
        hardware_capability=HardwareCapability.HIGH,
        tools=ToolAvailability(binaries={}, api_keys={}, mcp_servers=[]),
        tool_matrix=PlatformToolMatrix(matrix={}),
    )


# ---------------------------------------------------------------------------
# env validate
# ---------------------------------------------------------------------------


def test_env_validate_parity_valid(tmp_path, monkeypatch, portable_skill) -> None:
    monkeypatch.setattr("carrel.cli.env.audit", _fake_audit)
    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    (typed_vault / ".carrel").mkdir(parents=True)
    (portable_vault / ".carrel").mkdir(parents=True)
    payload = _valid_profile()
    _write_env(typed_vault, payload)
    _write_env(portable_vault, payload)

    typed = runner.invoke(
        app, ["env", "validate", "--vault", str(typed_vault), "--format", "json"]
    )
    portable = _portable(
        portable_skill, "env", "validate", "--vault", str(portable_vault), "--format", "json"
    )

    assert typed.exit_code == 0
    assert portable.returncode == 0
    assert json.loads(typed.stdout)["status"] == "valid"
    assert json.loads(portable.stdout)["status"] == "valid"


def test_env_validate_parity_invalid_enum(tmp_path, portable_skill) -> None:
    """A bad enum value is rejected by both, citing the same field."""

    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    (typed_vault / ".carrel").mkdir(parents=True)
    (portable_vault / ".carrel").mkdir(parents=True)
    payload = _valid_profile()
    payload["sensitivity"] = "extreme"
    _write_env(typed_vault, payload)
    _write_env(portable_vault, payload)

    typed = runner.invoke(
        app, ["env", "validate", "--vault", str(typed_vault), "--format", "json"]
    )
    portable = _portable(
        portable_skill, "env", "validate", "--vault", str(portable_vault), "--format", "json"
    )

    assert typed.exit_code == 1
    assert portable.returncode == 1
    typed_body = json.loads(typed.stdout)
    portable_body = json.loads(portable.stdout)
    assert typed_body["status"] == "invalid"
    assert portable_body["status"] == "invalid"
    assert "sensitivity" in {issue["path"] for issue in typed_body["errors"]}
    assert "sensitivity" in {issue["path"] for issue in portable_body["errors"]}


def test_env_validate_parity_string_cloud_consent(tmp_path, portable_skill) -> None:
    """A hand-edited string ``cloud_consent`` must be rejected by both engines.

    This is a safety-relevant surface: a malformed consent value must never be
    silently read as a boolean. The portable runtime refuses it in
    ``validate_profile_payload``; the typed model enforces it via the strict
    ``cloud_consent`` field validator in ``src/carrel/models.py`` (added
    2026-07-10 after this parity suite exposed pydantic's lax bool coercion
    accepting "false"/"yes"/"1" strings).
    """

    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    (typed_vault / ".carrel").mkdir(parents=True)
    (portable_vault / ".carrel").mkdir(parents=True)
    payload = _valid_profile()
    payload["cloud_consent"] = "false"
    _write_env(typed_vault, payload)
    _write_env(portable_vault, payload)

    typed = runner.invoke(
        app, ["env", "validate", "--vault", str(typed_vault), "--format", "json"]
    )
    portable = _portable(
        portable_skill, "env", "validate", "--vault", str(portable_vault), "--format", "json"
    )

    typed_body = json.loads(typed.stdout)
    portable_body = json.loads(portable.stdout)
    assert typed.exit_code == 1
    assert portable.returncode == 1
    assert typed_body["status"] == "invalid"
    assert portable_body["status"] == "invalid"
    assert "cloud_consent" in {issue["path"] for issue in typed_body["errors"]}
    assert "cloud_consent" in {issue["path"] for issue in portable_body["errors"]}


# ---------------------------------------------------------------------------
# env fix — cloud_consent asymmetric repair (narrow automatically, never widen)
# ---------------------------------------------------------------------------


def test_env_fix_parity_cloud_consent_false_string_narrows(tmp_path, monkeypatch, portable_skill) -> None:
    """A malformed string "false" is a safe, narrowing repair on both engines.

    ``bool("false")`` is ``True`` in Python, so this could easily have been
    misread as consent; both engines must instead recognize the literal
    string "false" and correct it to the boolean ``False`` — never anything
    that could look like granting consent.
    """

    monkeypatch.setattr("carrel.cli.env.audit", _fake_audit)
    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)
    for vault in (typed_vault, portable_vault):
        payload = _read_env(vault)
        payload["cloud_consent"] = "false"
        _write_env(vault, payload)

    typed = runner.invoke(app, ["env", "fix", "--vault", str(typed_vault), "--format", "json"])
    portable = _portable(
        portable_skill, "env", "fix", "--vault", str(portable_vault), "--format", "json"
    )

    assert typed.exit_code == 0, typed.output
    assert portable.returncode == 0, portable.stderr
    assert _read_env(typed_vault)["cloud_consent"] is False
    assert _read_env(portable_vault)["cloud_consent"] is False

    typed_validate = runner.invoke(
        app, ["env", "validate", "--vault", str(typed_vault), "--format", "json"]
    )
    portable_validate = _portable(
        portable_skill, "env", "validate", "--vault", str(portable_vault), "--format", "json"
    )
    assert typed_validate.exit_code == 0
    assert portable_validate.returncode == 0
    assert json.loads(typed_validate.stdout)["status"] == "valid"
    assert json.loads(portable_validate.stdout)["status"] == "valid"


def test_env_fix_parity_cloud_consent_true_string_defers(tmp_path, monkeypatch, portable_skill) -> None:
    """A malformed string "true" cannot be safely auto-repaired on either engine.

    Converting "true" to the boolean ``True`` would *widen* consent
    automatically — that decision belongs to a human, not `env fix --safe`.
    Both engines must defer and leave the file on disk untouched.
    """

    monkeypatch.setattr("carrel.cli.env.audit", _fake_audit)
    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)
    for vault in (typed_vault, portable_vault):
        payload = _read_env(vault)
        payload["cloud_consent"] = "true"
        _write_env(vault, payload)
    typed_before = (typed_vault / ".carrel" / "environment.json").read_text(encoding="utf-8")
    portable_before = (portable_vault / ".carrel" / "environment.json").read_text(encoding="utf-8")

    typed = runner.invoke(app, ["env", "fix", "--vault", str(typed_vault), "--format", "json"])
    portable = _portable(
        portable_skill, "env", "fix", "--vault", str(portable_vault), "--format", "json"
    )

    assert typed.exit_code == 2, typed.output
    assert portable.returncode == 2, portable.stderr
    assert json.loads(typed.stdout)["deferred"]
    assert json.loads(portable.stdout)["deferred"]
    # Untouched on disk -- no partial fix, no widening.
    assert (typed_vault / ".carrel" / "environment.json").read_text(encoding="utf-8") == typed_before
    assert (
        portable_vault / ".carrel" / "environment.json"
    ).read_text(encoding="utf-8") == portable_before
    assert not (typed_vault / ".carrel" / "environment.json.bak").exists()
    assert not (portable_vault / ".carrel" / "environment.json.bak").exists()


# ---------------------------------------------------------------------------
# cloud_consent at command time — same safety outcome, different mechanism
# ---------------------------------------------------------------------------


def test_cloud_consent_command_time_parity_never_grants_cloud(tmp_path, portable_skill) -> None:
    """A malformed non-bool cloud_consent must never grant cloud at command time.

    This is the intended-contract case documented at the top of this module:
    both engines refuse to treat the malformed value as consent, but they get
    there by different, deliberate mechanisms.

    * typed CLI: ``read_profile`` (src/carrel/env/profile.py) raises
      CarrelError for any schema violation, so the whole command fails
      closed *before* a tool decision is ever computed -- nonzero exit, no
      decision exists to inspect.
    * portable runtime: there is no profile-level schema gate at command
      time. ``cloud_consent_granted()`` (carrel_core/core.py) reads the raw
      value with a strict ``is True`` check, so the malformed string is read
      as consent-not-granted and the (safe) decision proceeds normally.
    """

    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)
    for vault in (typed_vault, portable_vault):
        payload = _read_env(vault)
        payload["cloud_consent"] = "true"  # malformed: string, not boolean
        _write_env(vault, payload)

    typed = runner.invoke(
        app,
        ["transcript", "create", "recording.m4a", "--vault", str(typed_vault), "--explain"],
    )

    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    portable = _portable(
        portable_skill,
        "transcript",
        "create",
        "recording.m4a",
        "--vault",
        str(portable_vault),
        "--sensitivity",
        "low",
        "--explain",
        env_extra={"PATH": str(empty_bin)},
    )

    # typed: fails closed at profile read -- no tool decision is ever made.
    # (The failure is deliberately generic -- read_profile rejects the whole
    # payload on ANY schema violation, not specifically cloud_consent -- so
    # assert on the parse-failure message and the diagnostic-path hint, not
    # on a field name that happens not to appear in this generic error.)
    assert typed.exit_code == 1, typed.output
    assert "Could not parse" in typed.output
    assert "env validate" in typed.output
    assert "env fix --safe" in typed.output

    # portable: a decision IS made, but the malformed value never reads as
    # consent -- no local tool (empty PATH) + low sensitivity would only
    # route to cloud if consent were (mis)read as granted.
    assert portable.returncode == 1, portable.stderr
    portable_payload = json.loads(portable.stdout)
    assert portable_payload["selected_tool"] is None
    assert "cloud consent is not enabled" in portable_payload["rationale"]
    assert "cloud consent is enabled" not in portable_payload["rationale"]

    # HONESTY GUARD (2026-07-10): the assertions above run with an empty PATH,
    # so *no* cloud tool can be available and `selected_tool is None` is
    # trivially true regardless of consent. That proves the rationale wording,
    # not the safety property. Drive the typed policy function directly with a
    # cloud tool GENUINELY available to prove the actual invariant: a
    # non-consent value (what a malformed cloud_consent reads as) never routes
    # to cloud even when cloud IS reachable.
    cloud_available = [TranscribeTool.GROQ]  # cloud tool present, no local tool
    denied = select_tool(
        requested_tool=None,
        available_tools=cloud_available,
        sensitivity=Sensitivity.LOW,
        cloud_consent=False,  # malformed non-bool reads as not-consented
        tool_class="transcribe",
    )
    assert denied.cloud_available is True  # the cloud tool really was available
    assert denied.selected_tool is None  # ...and consent=False still blocked it

    # Converse control: the ONLY thing changed is consent, and now cloud IS
    # selected -- proving the None above was caused by consent, not by the
    # cloud tool secretly being unavailable.
    granted = select_tool(
        requested_tool=None,
        available_tools=cloud_available,
        sensitivity=Sensitivity.LOW,
        cloud_consent=True,
        tool_class="transcribe",
    )
    assert granted.selected_tool == TranscribeTool.GROQ


# ---------------------------------------------------------------------------
# vault init — enumerated divergence (drift alarm)
# ---------------------------------------------------------------------------

# These files are created by exactly one runtime **by contract** (host-split,
# 2026-07-10). This list is the drift alarm: a NEW divergence that is not
# listed here fails `test_vault_init_tree_parity`, forcing a deliberate
# decision about whether it is intended.
#
# Typed-only — surfaces owned by the full Claude Code plugin / setup flow:
#   CLAUDE.md                 Claude-adapter marker file; portable writes
#                             .carrel/agent-context.md instead (surface-map:
#                             "vault check-sync/add-markers → Claude adapter only").
#   .carrel/setup-state.json  plugin/host resumable-setup state (surface-map:
#                             "setup-state ... → Host adapter setup flow only").
#   _meta/cheat_sheet.md      judgment-heavy synthesis the portable runtime
#   _meta/my-environment.md   defers to the agent (surface-map "Agent Workflows":
#                             vault cheatsheet / vault dashboard).
#   _meta/capability-log.md   tracker stubs the full plugin seeds at init;
#   _meta/friction_log.md     portable leaves creation to the agent.
TYPED_ONLY_INIT_FILES = frozenset(
    {
        "CLAUDE.md",
        ".carrel/setup-state.json",
        "_meta/cheat_sheet.md",
        "_meta/my-environment.md",
        "_meta/capability-log.md",
        "_meta/friction_log.md",
    }
)

# Portable-only — the host-neutral setup companion plus templates the portable
# runtime ships for the agent to fill (the typed CLI generates the finished
# artifact at init instead, or writes it lazily at first use):
#   .carrel/agent-context.md         portable setup-state companion (host-split).
#   _templates/automation-prompt.md  shipped as templates; typed renders the
#   _templates/dashboard.md          finished _meta/ artifact on demand.
#   _templates/my-environment.md     (typed writes _meta/my-environment.md).
PORTABLE_ONLY_INIT_FILES = frozenset(
    {
        ".carrel/agent-context.md",
        "_templates/automation-prompt.md",
        "_templates/dashboard.md",
        "_templates/my-environment.md",
    }
)


def _relative_files(root: Path) -> set[str]:
    return {item.relative_to(root).as_posix() for item in root.rglob("*") if item.is_file()}


def test_vault_init_tree_parity(tmp_path, portable_skill) -> None:
    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)

    typed_files = _relative_files(typed_vault)
    portable_files = _relative_files(portable_vault)

    # The symmetric difference must be exactly the enumerated host-split
    # allowlist. A new, unlisted divergence is the drift alarm firing.
    assert typed_files - portable_files == TYPED_ONLY_INIT_FILES
    assert portable_files - typed_files == PORTABLE_ONLY_INIT_FILES

    # The shared core both engines must always scaffold identically.
    shared = typed_files & portable_files
    assert {
        ".carrel/environment.json",
        "reading-progress.base",
        "_templates/paper.md",
        "_templates/reflection.md",
        ".obsidian/app.json",
        ".obsidian/workspace.json",
    } <= shared


def test_vault_init_environment_json_is_cross_runtime_equal(tmp_path, portable_skill) -> None:
    """The shared profile is byte-equal in meaning and each validates on both.

    Serialization differs only in key order (typed preserves model field order;
    portable sorts), so we compare the parsed objects, and cross-validate each
    engine's output against the *other* engine.
    """

    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)

    typed_env = _read_env(typed_vault)
    portable_env = _read_env(portable_vault)
    # The only intended difference: the typed CLI serializes ``version: null``,
    # while the portable runtime deliberately never writes the shared
    # ``version`` key at all — it tracks the full Claude Code plugin's semver,
    # and the portable pack must not stamp a value that would look like a plugin
    # version to the full plugin's drift/migration checks. See
    # skills/carrel/scripts/carrel_core/constants.py (ADAPTER_PROFILE_KEYS / VERSION).
    assert "version" not in portable_env
    assert typed_env.get("version") is None
    assert {k: v for k, v in typed_env.items() if k != "version"} == portable_env

    # portable-produced profile through the typed validator, and vice versa.
    typed_on_portable = runner.invoke(
        app, ["env", "validate", "--vault", str(portable_vault), "--format", "json"]
    )
    portable_on_typed = _portable(
        portable_skill, "env", "validate", "--vault", str(typed_vault), "--format", "json"
    )
    assert json.loads(typed_on_portable.stdout)["status"] == "valid"
    assert json.loads(portable_on_typed.stdout)["status"] == "valid"


# ---------------------------------------------------------------------------
# trust check
# ---------------------------------------------------------------------------


def _set_trust(vault: Path, level: str) -> None:
    payload = _read_env(vault)
    payload["automation"]["trust_level"] = level
    _write_env(vault, payload)


@pytest.mark.parametrize(
    ("action", "trust_level"),
    [
        ("automation:propose", "advisory"),      # below required -> deny
        ("automation:propose", "consultative"),  # at required -> allow
        ("wiki:write", "consultative"),          # below required -> deny
        ("wiki:write", "delegated"),             # at required -> allow
    ],
)
def test_trust_check_parity(tmp_path, portable_skill, action, trust_level) -> None:
    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)
    _set_trust(typed_vault, trust_level)
    _set_trust(portable_vault, trust_level)

    typed = runner.invoke(
        app, ["trust", "check", action, "--vault", str(typed_vault), "--format", "json"]
    )
    portable = _portable(
        portable_skill, "trust", "check", action, "--vault", str(portable_vault), "--format", "json"
    )

    # Allow/deny verdict must match (exit 0 = allowed, exit 1 = denied).
    assert typed.exit_code == portable.returncode
    # The portable runtime always emits JSON; assert the required trust level.
    portable_body = json.loads(portable.stdout)
    # The typed CLI emits JSON only when allowed (it raises before echoing on
    # deny), so compare required_trust only where both provide it.
    if typed.exit_code == 0:
        assert json.loads(typed.stdout)["required_trust"] == portable_body["required_trust"]


# ---------------------------------------------------------------------------
# reflection append / vault reflect-log
# ---------------------------------------------------------------------------


def _last_entry(text: str) -> str:
    """The final ``## <timestamp>`` section with its timestamp masked.

    Both runtimes append ``## <UTC timestamp>\\n\\n<body>\\n`` as the last
    section. We normalize the timestamp (wall-clock, so never byte-equal) and
    deliberately drop everything before it: the first-of-day *seed* legitimately
    differs (typed scaffolds from _templates/reflection.md; portable writes a
    minimal header). The appended entry is the shared surface.
    """

    entry = text.rsplit("\n## ", 1)[-1]
    return re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC", "<TS>", entry)


def test_reflection_append_parity(tmp_path, portable_skill) -> None:
    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)
    # A body with no "## " so the last-section split is unambiguous.
    prose = "Session felt productive."

    typed = runner.invoke(
        app,
        ["vault", "reflect-log", "--append", "--from-stdin", "--vault", str(typed_vault)],
        input=prose,
    )
    portable = _portable(
        portable_skill, "reflection", "append", "--vault", str(portable_vault), input_text=prose
    )
    assert typed.exit_code == 0, typed.output
    assert portable.returncode == 0, portable.stderr

    typed_files = sorted((typed_vault / "_meta" / "reflections").glob("*.md"))
    portable_files = sorted((portable_vault / "_meta" / "reflections").glob("*.md"))
    assert len(typed_files) == 1
    assert len(portable_files) == 1
    # Same dated filename pattern.
    assert typed_files[0].name == portable_files[0].name
    assert re.fullmatch(r"reflection-\d{4}-\d{2}-\d{2}\.md", typed_files[0].name)
    # The appended entry (timestamp masked) is identical across runtimes.
    typed_entry = _last_entry(typed_files[0].read_text(encoding="utf-8"))
    portable_entry = _last_entry(portable_files[0].read_text(encoding="utf-8"))
    assert typed_entry == portable_entry
    assert typed_entry == f"<TS>\n\n{prose}\n"


# ---------------------------------------------------------------------------
# mirror write / vault mirror
# ---------------------------------------------------------------------------


def test_mirror_write_parity(tmp_path, portable_skill) -> None:
    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)
    body = "# Mirror\n\nPattern synthesis of the researcher.\n"

    typed = runner.invoke(
        app,
        ["vault", "mirror", "--write", "--from-stdin", "--vault", str(typed_vault)],
        input=body,
    )
    portable = _portable(
        portable_skill, "mirror", "write", "--vault", str(portable_vault), input_text=body
    )
    assert typed.exit_code == 0, typed.output
    assert portable.returncode == 0, portable.stderr

    typed_files = sorted((typed_vault / "_meta" / "mirror").glob("*.md"))
    portable_files = sorted((portable_vault / "_meta" / "mirror").glob("*.md"))
    assert len(typed_files) == 1
    assert len(portable_files) == 1
    # Same monthly filename and byte-identical content (verbatim, no header/stamp).
    assert typed_files[0].name == portable_files[0].name
    assert re.fullmatch(r"\d{4}-\d{2}\.md", typed_files[0].name)
    assert typed_files[0].read_text(encoding="utf-8") == body
    assert portable_files[0].read_text(encoding="utf-8") == body


# ---------------------------------------------------------------------------
# feedback export
# ---------------------------------------------------------------------------


def test_feedback_export_parity(tmp_path, portable_skill) -> None:
    """Identical sources + redact list -> identical redactions and metrics.

    The vaults are normalized to an identical source set first: the typed init
    pre-seeds ``_meta/capability-log.md``/``friction_log.md`` while the portable
    init does not, so without this cleanup the digests would differ purely from
    vault state, not the redaction algorithm. A single source file also avoids
    the (separately noted) inter-section spacing divergence.
    """

    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)

    fixture = "ALICE SMITH met Acme Lab. Token exposed a SECRET. LongPerson joined.\n"
    for vault in (typed_vault, portable_vault):
        (vault / "_meta" / "capability-log.md").unlink(missing_ok=True)
        (vault / "_meta" / "friction_log.md").write_text(fixture, encoding="utf-8")
        payload = _read_env(vault)
        payload["name"] = "Alice Smith"  # exercises the auto-added name redaction
        _write_env(vault, payload)

    redact = tmp_path / "redact.txt"
    redact.write_text(
        "Acme Lab -> Institution\nToken -> Tok\nSecret\nNeverSeen\n", encoding="utf-8"
    )

    typed = runner.invoke(
        app,
        ["vault", "feedback", "export", "--redact-list", str(redact),
         "--vault", str(typed_vault), "--format", "json"],
    )
    portable = _portable(
        portable_skill, "feedback", "export", "--vault", str(portable_vault),
        "--redact-list", str(redact),
    )
    assert typed.exit_code == 0, typed.output
    assert portable.returncode == 0, portable.stderr

    typed_body = json.loads(typed.stdout)
    portable_body = json.loads(portable.stdout)

    # JSON metrics must match exactly.
    for key in ("redacted_terms", "redaction_rules", "redactions_applied", "zero_match_terms"):
        assert typed_body[key] == portable_body[key], key

    # Same source set (relative to each vault).
    typed_sources = {str(Path(s).relative_to(typed_vault)) for s in typed_body["sources"]}
    portable_sources = {str(Path(s).relative_to(portable_vault)) for s in portable_body["sources"]}
    assert typed_sources == portable_sources == {"_meta/friction_log.md"}

    # Section headings now use the vault-relative path (`## _meta/friction_log.md`,
    # not the bare `## friction_log.md`) so same-basename files in different
    # `_meta` subdirectories stay distinct (review finding; both runtimes mirror
    # it — exporter.py and carrel_core/maintenance.py). Assert the relative-path
    # form explicitly on each side so a regression to bare basenames is caught
    # directly, not only via the byte-identity check below.
    typed_digest = Path(typed_body["path"]).read_text(encoding="utf-8")
    portable_digest = Path(portable_body["path"]).read_text(encoding="utf-8")
    assert "## _meta/friction_log.md" in typed_digest
    assert "## _meta/friction_log.md" in portable_digest
    assert "## friction_log.md\n" not in typed_digest  # not the collision-prone basename
    assert "## friction_log.md\n" not in portable_digest

    # The redacted section (everything from the first "## " header — heading and
    # body) is byte-identical across runtimes; only the top-level digest header
    # (`# Feedback Digest — <date>`) differs by contract.
    def _sections(digest: str) -> str:
        return digest[digest.find("## ") :]

    assert _sections(typed_digest) == _sections(portable_digest)


# ---------------------------------------------------------------------------
# automation configure
# ---------------------------------------------------------------------------


def test_automation_configure_parity(tmp_path, portable_skill) -> None:
    """Equivalent configure invocations persist an identical automation block.

    Both engines gate on ``automation:propose`` (consultative) but allow the
    one advisory -> consultative bootstrap, so a fresh vault can be configured.
    The grammars differ (typed ``--enabled`` boolean flag vs portable
    ``--enabled true``); the persisted ``automation`` object must be equal.

    INTENDED CONTRACT (decision 2026-07-10, advisory bootstrap): pinning the
    Advisory->Consultative self-transition here is deliberate, not an accident
    of the current code — the skill's interview-approval flow is the approval of
    record and no on-disk artifact gates it. Both runtimes must agree on exactly
    that one exception. See src/carrel/cli/automate.py.
    """

    typed_vault = tmp_path / "typed"
    portable_vault = tmp_path / "portable"
    _init_typed(typed_vault)
    _init_portable(portable_skill, portable_vault)

    typed = runner.invoke(
        app,
        ["automate", "configure", "--enabled", "--trust-level", "consultative",
         "--schedule", "daily", "--review-cadence", "quarterly", "--gap-analysis",
         "--vault", str(typed_vault), "--format", "json"],
    )
    portable = _portable(
        portable_skill, "automation", "configure", "--vault", str(portable_vault),
        "--enabled", "true", "--trust-level", "consultative", "--schedule", "daily",
        "--review-cadence", "quarterly", "--gap-analysis", "true",
    )
    assert typed.exit_code == 0, typed.output
    assert portable.returncode == 0, portable.stderr

    typed_automation = _read_env(typed_vault)["automation"]
    portable_automation = _read_env(portable_vault)["automation"]
    assert typed_automation == portable_automation
    # Sanity: the configured values actually landed.
    assert typed_automation["enabled"] is True
    assert typed_automation["trust_level"] == "consultative"
    assert typed_automation["gap_analysis"] is True
