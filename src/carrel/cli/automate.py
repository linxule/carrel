from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from carrel.cli import emit_carrel_error, resolve_vault
from carrel.cli.output import OutputFormat
from carrel.env.profile import read_profile, write_profile
from carrel.errors import CarrelError
from carrel.models import (
    AutomationConfig,
    AutomationModel,
    AutomationSchedule,
    ResearcherProfile,
    TrustLevel,
)
from carrel.policy.trust import is_allowed, required_trust
from carrel.safe_path import safe_atomic_write, safe_vault_join

app = typer.Typer(help="Configure overnight automation (typed flags only, no prompting)")
console = Console()

# `carrel automate configure` calls into the trust enforcement boundary using
# automation:propose (consultative). The one bootstrap exception is an explicit
# Advisory -> Consultative request: the skill obtains approval, then the runtime
# validates and persists that transition with the rest of the approved config.
AUTOMATE_CONFIGURE_ACTION = "automation:propose"


@app.command("configure")
def configure_command(
    enabled: bool = typer.Option(
        ...,
        "--enabled/--no-enabled",
        help="Turn overnight automation on (--enabled) or off (--no-enabled).",
    ),
    trust_level: TrustLevel = typer.Option(
        ...,
        "--trust-level",
        help="advisory | consultative | delegated | partnership",
    ),
    schedule: AutomationSchedule = typer.Option(
        ...,
        "--schedule",
        help="daily | weekdays | weekly",
    ),
    review_cadence: Literal["monthly", "quarterly", "biannual"] = typer.Option(
        ...,
        "--review-cadence",
        help="monthly | quarterly | biannual",
    ),
    model: AutomationModel = typer.Option(
        AutomationModel.SONNET,
        "--model",
        help="sonnet | opus (default: sonnet)",
    ),
    # Capability booleans — all optional; None means "preserve existing value
    # on the profile." Skills construct typed-flag arg lists per the automation
    # SKILL.md calling pattern; missing flags do not zero out prior choices.
    inbox_processing: bool | None = typer.Option(
        None, "--inbox-processing/--no-inbox-processing"
    ),
    vault_health: bool | None = typer.Option(
        None, "--vault-health/--no-vault-health"
    ),
    cross_linking: bool | None = typer.Option(
        None,
        "--cross-linking/--no-cross-linking",
        help="Maps to AutomationConfig.cross_linking_suggestions.",
    ),
    gap_analysis: bool | None = typer.Option(
        None, "--gap-analysis/--no-gap-analysis"
    ),
    draft_feedback: bool | None = typer.Option(
        None, "--draft-feedback/--no-draft-feedback"
    ),
    reflection_synthesis: bool | None = typer.Option(
        None, "--reflection-synthesis/--no-reflection-synthesis"
    ),
    wiki_maintenance: bool | None = typer.Option(
        None, "--wiki-maintenance/--no-wiki-maintenance"
    ),
    vault: Path | None = typer.Option(None, "--vault"),
    fmt: OutputFormat = typer.Option(OutputFormat.HUMAN, "--format"),
) -> None:
    """Write AutomationConfig into environment.json atomically. Trust-gated."""
    try:
        vault_path = resolve_vault(vault)
        profile = read_profile(vault_path)
        if profile is None:
            raise CarrelError(
                "No environment.json found",
                hint=(
                    f"Expected {vault_path / '.carrel' / 'environment.json'}. "
                    "Run `carrel vault init` or `/carrel-setup` first."
                ),
            )

        # Internal trust gate: persisting automation settings is a
        # consultative proposal-grade action.
        current_trust = profile.automation.trust_level
        advisory_bootstrap = (
            current_trust == TrustLevel.ADVISORY
            and trust_level == TrustLevel.CONSULTATIVE
        )
        if not (
            is_allowed(AUTOMATE_CONFIGURE_ACTION, current_trust)
            or advisory_bootstrap
        ):
            required = required_trust(AUTOMATE_CONFIGURE_ACTION)
            raise CarrelError(
                (
                    f"Action '{AUTOMATE_CONFIGURE_ACTION}' requires trust level "
                    f"'{required.value}'; current is '{current_trust.value}'"
                ),
                hint=(
                    "A fresh advisory profile may transition only to consultative in this "
                    "command, after explicit approval. Higher trust levels require a later, "
                    "separately reviewed transition."
                ),
            )

        # For each capability flag: use the new value if supplied, else
        # preserve what's already on the profile. The CLI is the mechanical
        # writer; only flags the skill explicitly constructs should change.
        existing = profile.automation

        def _resolve(new: bool | None, current: bool) -> bool:
            return current if new is None else new

        new_config = AutomationConfig(
            enabled=enabled,
            inbox_processing=_resolve(inbox_processing, existing.inbox_processing),
            vault_health=_resolve(vault_health, existing.vault_health),
            cross_linking_suggestions=_resolve(
                cross_linking, existing.cross_linking_suggestions
            ),
            gap_analysis=_resolve(gap_analysis, existing.gap_analysis),
            draft_feedback=_resolve(draft_feedback, existing.draft_feedback),
            reflection_synthesis=_resolve(
                reflection_synthesis, existing.reflection_synthesis
            ),
            wiki_maintenance=_resolve(wiki_maintenance, existing.wiki_maintenance),
            trust_level=trust_level,
            model=model,
            schedule=schedule,
            review_cadence=review_cadence,
            last_reviewed=date.today().isoformat(),
        )

        updated_profile = profile.model_copy(update={"automation": new_config})
        _atomic_write_profile(vault_path, updated_profile)

        if fmt == OutputFormat.JSON:
            typer.echo(
                json.dumps(
                    {
                        "vault": str(vault_path),
                        "automation": json.loads(new_config.model_dump_json()),
                    }
                )
            )
            return
        if fmt == OutputFormat.QUIET:
            typer.echo(str(vault_path / ".carrel" / "environment.json"))
            return
        console.print(
            f"Updated automation config in {vault_path / '.carrel' / 'environment.json'}"
        )
        console.print(
            f"  enabled={new_config.enabled} trust={new_config.trust_level.value} "
            f"schedule={new_config.schedule.value} review_cadence={new_config.review_cadence}"
        )
    except CarrelError as error:
        emit_carrel_error(error)


def _atomic_write_profile(vault: Path, profile: ResearcherProfile) -> Path:
    """Atomic profile write via tmp + replace (matches setup_state pattern)."""
    path = safe_vault_join(vault, ".carrel", "environment.json")
    safe_atomic_write(
        vault,
        path,
        profile.model_dump_json(indent=2, by_alias=True),
    )
    return path


# Keep `write_profile` referenced for typing imports & future use.
__all__ = ["app", "write_profile"]
