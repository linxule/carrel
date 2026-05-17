from __future__ import annotations

import typer

from carrel.cli.automate import app as automate_app
from carrel.cli.batch import app as batch_app
from carrel.cli.capture import app as capture_app
from carrel.cli.env import app as env_app
from carrel.cli.google import app as google_app
from carrel.cli.migrate import app as migrate_app
from carrel.cli.paper import app as paper_app
from carrel.cli.setup_state import app as setup_state_app
from carrel.cli.trust import app as trust_app
from carrel.cli.transcript import app as transcript_app
from carrel.cli.vault import app as vault_app

app = typer.Typer(help="Carrel -- research environment toolkit")
app.add_typer(automate_app, name="automate")
app.add_typer(batch_app, name="batch")
app.add_typer(capture_app, name="capture")
app.add_typer(google_app, name="google")
app.add_typer(migrate_app, name="migrate")
app.add_typer(paper_app, name="paper")
app.add_typer(setup_state_app, name="setup-state")
app.add_typer(trust_app, name="trust")
app.add_typer(transcript_app, name="transcript")
app.add_typer(vault_app, name="vault")
app.add_typer(env_app, name="env")

__all__ = ["app"]
