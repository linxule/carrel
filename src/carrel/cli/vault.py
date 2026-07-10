from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from carrel.cli import emit_carrel_error, normalize_path, resolve_vault
from carrel.cli.output import OutputFormat, print_result
from carrel.env.audit import audit
from carrel.env.platform import detect_platform
from carrel.env.profile import read_profile
from carrel.errors import CarrelError
from carrel.feedback.exporter import export_feedback
from carrel.models import FileResult, Sensitivity
from carrel.policy.trust import is_allowed, required_trust
from carrel.safe_path import assert_safe_write_target, safe_atomic_write, safe_vault_join
from carrel.share.synthesizer import slug_name, validate_mode, write_handbook
from carrel.vault.automation_prompt import render_automation_prompt
from carrel.vault.dashboard import collect_activity_stats, render_dashboard
from carrel.vault.markers import ensure_markers, parse_markers
from carrel.vault.organize import sort_inbox
from carrel.vault.scaffold import load_profile_file, scaffold_vault
from carrel.vault.sync import compare_markers, marker_values
from carrel.vault.templates import read_template, render_cheat_sheet

app = typer.Typer(help="Vault setup and management")
console = Console()


def _safe_slug(name: str) -> str:
    if ".." in name or "/" in name or "\\" in name:
        raise CarrelError(
            "Invalid note name",
            hint="Path traversal is not allowed. Use a note name, not a path.",
        )
    normalized = (
        name.lower().replace(" ", "_").replace("/", "").replace("\\", "").replace(".", "")
    )
    normalized = normalized.strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    if not normalized:
        raise CarrelError(
            "Invalid note name",
            hint="Use letters, numbers, or spaces so Carrel can create a safe filename.",
        )
    return normalized


def _require_profile(vault_path: Path):
    profile_path = safe_vault_join(vault_path, ".carrel", "environment.json")
    if not profile_path.exists():
        raise CarrelError(
            "No ResearcherProfile found",
            hint=f"Expected {profile_path}. Run `carrel vault init` first.",
        )
    profile = read_profile(vault_path)
    if profile is None:
        raise CarrelError(
            "No ResearcherProfile found",
            hint=f"Expected {profile_path}. Run `carrel vault init` first.",
        )
    return profile


def _atomic_write(vault: Path, path: Path, content: str) -> None:
    safe_atomic_write(vault, path, content)


def _render_drift_table(drifts: list[dict[str, str]]) -> None:
    table = Table()
    table.add_column("Field")
    table.add_column("CLAUDE.md")
    table.add_column("environment.json")
    for drift in drifts:
        table.add_row(drift["field"], drift["marker"], drift["profile"])
    console.print(table)


@app.command("init")
def init_command(
    path: Path = typer.Argument(...),
    profile_file: Path | None = typer.Option(
        None,
        "--profile-file",
        help="Validated ResearcherProfile JSON to use for profile-driven scaffolding.",
    ),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        profile = load_profile_file(profile_file) if profile_file is not None else None
        result = scaffold_vault(normalize_path(path), profile=profile)
        if fmt == OutputFormat.HUMAN:
            console.print(f"Created vault at {result.vault}")
            console.print(f"  profile: {result.profile_path}")
            console.print(f"  created: {len(result.created)}")
            console.print(f"  skipped: {len(result.skipped)}")
            console.print(f"  outdated templates: {len(result.outdated_templates)}")
            console.print(f"  unversioned templates: {len(result.unversioned_templates)}")
        else:
            print_result(result, fmt, quiet_field="vault")
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("new")
def new_command(
    name: str = typer.Argument(...),
    template: str = typer.Option("meeting", "--template"),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        mapping = {
            "paper-notes": vault_path / "notes",
            "meeting": vault_path / "notes",
            "reflection": vault_path / "_meta" / "reflections",
            "daily": vault_path / "notes",
        }
        template_name = f"{template}.md"
        body = read_template(template_name).replace("{{date}}", date.today().isoformat())
        target_dir = mapping.get(template, vault_path / "notes")
        target = target_dir / f"{_safe_slug(name)}.md"
        if target.exists():
            result = FileResult(path=target, action="skipped", reason="already exists")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            result = FileResult(path=target, action="created")
        print_result(result, fmt)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("search")
def search_command(
    query: str = typer.Argument(...),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        matches = []
        for path in sorted(vault_path.rglob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if query.lower() in text.lower():
                matches.append(str(path))
        if fmt == OutputFormat.JSON:
            console.print(json.dumps(matches))
        else:
            for match in matches:
                console.print(match)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("status")
def status_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        counts = {
            "papers": len(list((vault_path / "papers").glob("*/paper.md"))),
            "notes": len(list((vault_path / "notes").glob("*.md"))),
            "transcripts": len(list((vault_path / "transcripts").glob("*.md"))),
            "inbox": len(list((vault_path / "inbox").glob("*"))),
        }
        if fmt == OutputFormat.QUIET:
            typer.echo(str(vault_path))
            return
        if fmt == OutputFormat.JSON:
            console.print(json.dumps({"vault": str(vault_path), **counts}))
            return
        console.print(f"Vault: {vault_path}")
        for name, count in counts.items():
            console.print(f"  {name}/ {count} files")
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("organize")
def organize_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        suggestions = sort_inbox(vault_path)
        if fmt == OutputFormat.JSON:
            console.print(json.dumps(suggestions))
            return
        for suggestion in suggestions:
            if fmt == OutputFormat.QUIET:
                console.print(suggestion["destination"])
            else:
                console.print(f'{suggestion["source"]} -> {suggestion["destination"]}')
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("cheatsheet")
def cheatsheet_command(
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing cheat sheet"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Regenerate _meta/cheat_sheet.md from the current ResearcherProfile."""
    try:
        vault_path = resolve_vault(vault)
        profile_path = vault_path / ".carrel" / "environment.json"
        if not profile_path.exists():
            raise CarrelError(
                "No ResearcherProfile found",
                hint=f"Expected {profile_path}. Run `carrel vault init` first.",
            )
        profile = read_profile(vault_path)
        if profile is None:
            raise CarrelError(
                "No ResearcherProfile found",
                hint=f"Expected {profile_path}. Run `carrel vault init` first.",
            )
        cheat_sheet = vault_path / "_meta" / "cheat_sheet.md"
        existed = cheat_sheet.exists()
        if existed and not force:
            result = FileResult(
                path=cheat_sheet,
                action="skipped",
                reason="cheat sheet already exists; pass --force to overwrite",
            )
        else:
            cheat_sheet.parent.mkdir(parents=True, exist_ok=True)
            try:
                cheat_sheet_platform = asyncio.run(audit(vault_path)).platform
            except Exception:
                cheat_sheet_platform = detect_platform()
            cheat_sheet.write_text(
                render_cheat_sheet(vault_path, profile, cheat_sheet_platform),
                encoding="utf-8",
            )
            result = FileResult(path=cheat_sheet, action="updated" if existed else "created")
        print_result(result, fmt)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("dashboard")
def dashboard_command(
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing dashboard"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        dashboard_path = vault_path / "_meta" / "my-environment.md"
        existed = dashboard_path.exists()
        if existed and not force:
            raise CarrelError(
                "Dashboard already exists",
                hint=f"{dashboard_path} exists; pass --force to overwrite.",
            )

        audit_result = asyncio.run(audit(vault_path))
        activity = collect_activity_stats(vault_path)
        content = render_dashboard(profile, audit_result, activity).replace(
            "`(set by CLI at write time)`",
            f"`{vault_path}`",
        )
        _atomic_write(vault_path, dashboard_path, content)
        print_result(
            FileResult(path=dashboard_path, action="updated" if existed else "created"),
            fmt,
        )
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("automation-prompt")
def automation_prompt_command(
    vault: Path | None = typer.Option(None, "--vault"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing prompt"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        action = "automation:write-prompt"
        if not is_allowed(action, profile.automation.trust_level):
            required = required_trust(action)
            raise CarrelError(
                f"Action '{action}' requires trust level '{required.value}'",
                hint=(
                    f"Current trust is '{profile.automation.trust_level.value}'. "
                    "Approve automation configuration before generating its prompt."
                ),
            )
        prompt_path = safe_vault_join(vault_path, "_meta", "automation-prompt.md")
        existed = prompt_path.exists()
        if existed and not force:
            raise CarrelError(
                "Automation prompt already exists",
                hint=f"{prompt_path} exists; pass --force to overwrite.",
            )

        _atomic_write(
            vault_path,
            prompt_path,
            render_automation_prompt(profile, profile.automation),
        )
        print_result(
            FileResult(path=prompt_path, action="updated" if existed else "created"),
            fmt,
        )
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("check-sync")
def check_sync_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        claude_path = vault_path / "CLAUDE.md"
        if not claude_path.exists():
            raise CarrelError(
                "No CLAUDE.md found",
                hint=f"Expected {claude_path}. Run `/carrel-setup` or create it first.",
            )

        markers = parse_markers(claude_path.read_text(encoding="utf-8"))
        if not markers:
            if fmt != OutputFormat.QUIET:
                console.print(
                    "No carrel markers found. Run `carrel vault add-markers` to enable sync checking."
                )
            raise typer.Exit(code=0)

        drifts = compare_markers(profile, markers)

        if fmt == OutputFormat.JSON:
            console.print(json.dumps({"drift": drifts, "ok": not drifts}))
        elif fmt == OutputFormat.HUMAN:
            if drifts:
                console.print("Profile drift detected between CLAUDE.md markers and environment.json.")
                _render_drift_table(drifts)
            else:
                console.print("No profile drift detected.")

        raise typer.Exit(code=1 if drifts else 0)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("add-markers")
def add_markers_command(
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    try:
        vault_path = resolve_vault(vault)
        profile = _require_profile(vault_path)
        claude_path = vault_path / "CLAUDE.md"
        if not claude_path.exists():
            raise CarrelError(
                "No CLAUDE.md found",
                hint=f"Expected {claude_path}. Run `/carrel-setup` or create it first.",
            )

        original = claude_path.read_text(encoding="utf-8")
        updated = ensure_markers(original, marker_values(profile))
        action = "updated" if updated != original else "skipped"
        if updated != original:
            _atomic_write(vault_path, claude_path, updated)
        print_result(
            FileResult(
                path=claude_path,
                action=action,
                reason=None if action == "updated" else "all markers already present",
            ),
            fmt,
        )
    except CarrelError as error:
        emit_carrel_error(error)


# ---------------------------------------------------------------------------
# v0.9.0 (spec 014) — feedback export, mirror, reflect-log, share generate
# ---------------------------------------------------------------------------

feedback_app = typer.Typer(help="Feedback digest export")
app.add_typer(feedback_app, name="feedback")

share_app = typer.Typer(help="Generate vault handbooks for collaborators")
app.add_typer(share_app, name="share")


@feedback_app.command("export")
def feedback_export_command(
    redact_list: Path = typer.Option(
        ...,
        "--redact-list",
        help="Path to a text file with one redaction term per line.",
    ),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Write an anonymized feedback digest to _meta/feedback-digest-<YYYY-MM-DD>.md."""
    try:
        vault_path = resolve_vault(vault)
        today = date.today().isoformat()
        # Flat file in _meta/ (matches legacy /carrel-feedback convention and
        # the session-reflection skill contract). Earlier (pre-fix) v0.9.0 builds
        # used _meta/feedback-export/<date>.md — researchers upgrading from a
        # very early v0.9.0 RC should move existing files manually.
        output_path = safe_vault_join(
            vault_path, "_meta", f"feedback-digest-{today}.md"
        )
        result = export_feedback(
            vault=vault_path,
            redact_list=normalize_path(redact_list),
            output_path=output_path,
            today=today,
        )
        if fmt == OutputFormat.JSON:
            typer.echo(
                json.dumps(
                    {
                        "path": str(result.path),
                        "action": result.action,
                        "sources": [str(s) for s in result.sources],
                        "redacted_terms": result.redacted_terms,
                        "redaction_rules": result.redaction_rules,
                        "redactions_applied": result.redactions_applied,
                        "zero_match_terms": result.zero_match_terms,
                    }
                )
            )
            return
        if fmt == OutputFormat.QUIET:
            typer.echo(str(result.path))
            return
        console.print(
            f"{result.action.capitalize()} {result.path} "
            f"(sources={len(result.sources)}, redactions={result.redacted_terms})"
        )
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("mirror")
def mirror_command(
    write: bool = typer.Option(
        False, "--write", help="Persist the mirror to _meta/mirror/<YYYY-MM>.md."
    ),
    from_stdin: bool = typer.Option(
        False,
        "--from-stdin",
        help="Read the mirror body from stdin (required with --write).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite even when the existing file's source-hash matches.",
    ),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Persist a researcher self-portrait synthesis to the dated mirror file."""
    try:
        vault_path = resolve_vault(vault)
        if not write:
            raise CarrelError(
                "Mirror persistence requires --write",
                hint="The CLI persists; synthesis stays in the skill. Pass --write --from-stdin.",
            )
        if not from_stdin:
            raise CarrelError(
                "Reading from stdin requires --from-stdin",
                hint="Pipe the mirror synthesis: cat mirror.md | carrel vault mirror --write --from-stdin",
            )
        body = sys.stdin.read()
        if not body.strip():
            raise CarrelError(
                "Empty mirror body received on stdin",
                hint="Pipe a non-empty synthesis. Use --force only to overwrite an existing file.",
            )
        # Monthly filename — same month re-runs update the existing portrait
        # rather than creating one file per day. Matches the research-partner
        # skill's idempotency contract ("re-runs in the same month update the
        # existing file rather than duplicating").
        month = date.today().strftime("%Y-%m")
        output_path = safe_vault_join(vault_path, "_meta", "mirror", f"{month}.md")
        new_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        existed = output_path.exists()
        action = "created"
        if existed:
            existing_hash = hashlib.sha256(
                output_path.read_bytes()
            ).hexdigest()
            if existing_hash == new_hash and not force:
                action = "skipped"
                print_result(
                    FileResult(
                        path=output_path,
                        action=action,
                        reason="source-hash matches; pass --force to overwrite",
                    ),
                    fmt,
                )
                return
            action = "overwritten"
        _atomic_write(vault_path, output_path, body)
        print_result(FileResult(path=output_path, action=action), fmt)
    except CarrelError as error:
        emit_carrel_error(error)


@app.command("reflect-log")
def reflect_log_command(
    append: bool = typer.Option(
        False, "--append", help="Append a reflection entry to today's reflect-log."
    ),
    from_stdin: bool = typer.Option(
        False,
        "--from-stdin",
        help="Read the reflection body from stdin (required with --append).",
    ),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Atomically append a reflection to _meta/reflections/reflection-<YYYY-MM-DD>.md."""
    try:
        vault_path = resolve_vault(vault)
        if not append:
            raise CarrelError(
                "Reflection persistence requires --append",
                hint="Reflect-log is append-only. Pass --append --from-stdin.",
            )
        if not from_stdin:
            raise CarrelError(
                "Reading from stdin requires --from-stdin",
                hint="Pipe the reflection: cat reflection.md | carrel vault reflect-log --append --from-stdin",
            )
        body = sys.stdin.read().rstrip()
        if not body:
            raise CarrelError(
                "Empty reflection body received on stdin",
                hint="Pipe a non-empty reflection.",
            )
        today = date.today().isoformat()
        # Matches legacy /carrel-reflect convention and the session-reflection
        # skill contract: _meta/reflections/reflection-<date>.md. Mirror's
        # synthesis and feedback-digest export both read from this path.
        output_path = safe_vault_join(
            vault_path, "_meta", "reflections", f"reflection-{today}.md"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        existed = output_path.exists()
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = f"\n## {timestamp}\n\n{body}\n"
        if not existed:
            # First write of the day: seed from the vault's reflection template
            # if present, else use a minimal header. Template path matches
            # `carrel vault init` output (`_templates/reflection.md`).
            template_path = vault_path / "_templates" / "reflection.md"
            if template_path.is_file():
                try:
                    seed = template_path.read_text(encoding="utf-8").rstrip()
                except (OSError, UnicodeDecodeError):
                    seed = f"# Reflection — {today}"
            else:
                seed = f"# Reflection — {today}"
            entry = f"{seed}\n{entry}"
        # Atomic append: read-modify-write through a tmp file so a crash mid-write
        # cannot leave a half-truncated reflect-log.
        previous = output_path.read_text(encoding="utf-8") if existed else ""
        _atomic_write(vault_path, output_path, previous + entry)
        print_result(
            FileResult(
                path=output_path,
                action="appended" if existed else "created",
            ),
            fmt,
        )
    except CarrelError as error:
        emit_carrel_error(error)


@share_app.command("generate")
def share_generate_command(
    mode: str = typer.Option(
        ...,
        "--mode",
        help="quick | full (skill picks; quick = defaults, full = synthesized handbook).",
    ),
    name: str = typer.Option(..., "--for", help="Collaborator name (slug-safe)."),
    sensitivity: Sensitivity = typer.Option(
        ...,
        "--sensitivity",
        help="low | medium | high — controls redaction depth.",
    ),
    vault: Path | None = typer.Option(None, "--vault"),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Print what would be written + redactions, do not persist.",
    ),
    from_stdin: bool = typer.Option(
        False,
        "--from-stdin",
        help="Persist an approved handbook body from stdin without reading vault sources.",
    ),
    canonical: bool = typer.Option(
        False,
        "--canonical",
        help="Also write the approved body to _meta/lab-handbook.md.",
    ),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Write _meta/handbook/<YYYY-MM-DD>-for-<name>.md from the vault state."""
    try:
        vault_path = resolve_vault(vault)
        collaborator_slug = slug_name(name)
        validate_mode(mode)
        today = date.today().isoformat()
        output_path = safe_vault_join(
            vault_path,
            "_meta",
            "handbook",
            f"{today}-for-{collaborator_slug}.md",
        )
        canonical_path = (
            safe_vault_join(vault_path, "_meta", "lab-handbook.md") if canonical else None
        )
        supplied_body: str | None = None
        if from_stdin:
            supplied_body = sys.stdin.read()
            if not supplied_body.strip():
                raise CarrelError(
                    "Empty collaborator handbook received on stdin",
                    hint="Pipe the approved non-empty handbook body with --from-stdin.",
                )
        if explain:
            if supplied_body is not None:
                body = supplied_body
                redactions: list[str] = []
            else:
                from carrel.share.synthesizer import synthesize_handbook

                body, redactions = synthesize_handbook(
                    vault_path,
                    mode=mode,
                    name=name,
                    sensitivity=sensitivity,
                    today=today,
                )
            payload = {
                "would_write": str(output_path),
                "canonical_would_write": str(canonical_path) if canonical_path else None,
                "mode": mode,
                "sensitivity": sensitivity.value,
                "from_stdin": from_stdin,
                "redactions_applied": redactions,
                "bytes": len(body.encode("utf-8")),
            }
            if fmt == OutputFormat.JSON:
                typer.echo(json.dumps(payload))
            else:
                typer.echo(json.dumps(payload, indent=2))
            return
        assert_safe_write_target(vault_path, output_path)
        if canonical_path is not None:
            assert_safe_write_target(vault_path, canonical_path)
        if supplied_body is not None:
            existed = output_path.exists()
            _atomic_write(vault_path, output_path, supplied_body)
            if canonical_path is not None:
                _atomic_write(vault_path, canonical_path, supplied_body)
            payload = {
                "path": str(output_path),
                "canonical_path": str(canonical_path) if canonical_path else None,
                "action": "overwritten" if existed else "created",
                "mode": mode,
                "sensitivity": sensitivity.value,
                "redactions_applied": [],
            }
            if fmt == OutputFormat.JSON:
                typer.echo(json.dumps(payload))
            elif fmt == OutputFormat.QUIET:
                typer.echo(str(output_path))
            else:
                console.print(
                    f"{payload['action'].capitalize()} {output_path} "
                    f"(mode={mode}, sensitivity={sensitivity.value}, redactions=0)"
                )
            return
        result = write_handbook(
            vault_path,
            mode=mode,
            name=name,
            sensitivity=sensitivity,
            output_path=output_path,
            today=today,
        )
        if canonical_path is not None:
            _atomic_write(
                vault_path,
                canonical_path,
                result.path.read_text(encoding="utf-8"),
            )
        if fmt == OutputFormat.JSON:
            typer.echo(
                json.dumps(
                    {
                        "path": str(result.path),
                        "canonical_path": str(canonical_path) if canonical_path else None,
                        "action": result.action,
                        "mode": result.mode,
                        "sensitivity": result.sensitivity.value,
                        "redactions_applied": result.redactions_applied,
                    }
                )
            )
            return
        if fmt == OutputFormat.QUIET:
            typer.echo(str(result.path))
            return
        console.print(
            f"{result.action.capitalize()} {result.path} "
            f"(mode={result.mode}, sensitivity={result.sensitivity.value}, "
            f"redactions={len(result.redactions_applied)})"
        )
    except CarrelError as error:
        emit_carrel_error(error)
