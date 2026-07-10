from __future__ import annotations

import json
from enum import Enum

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

console = Console()


class OutputFormat(str, Enum):
    HUMAN = "human"
    JSON = "json"
    QUIET = "quiet"


def print_result(result: BaseModel, fmt: OutputFormat, quiet_field: str = "path") -> None:
    """Print result in requested format."""

    if fmt == OutputFormat.JSON:
        # JSON is a wire format; bypass Rich's wrapping/highlighting entirely.
        typer.echo(result.model_dump_json())
        return
    if fmt == OutputFormat.QUIET:
        if quiet_field:
            data = result.model_dump(mode="json")
            value = data.get(quiet_field)
            if value is not None:
                console.print(value)
        return

    table = Table(show_header=False, box=None)
    for key, value in result.model_dump(mode="json").items():
        table.add_row(str(key), json.dumps(value) if isinstance(value, (dict, list)) else str(value))
    console.print(table)
