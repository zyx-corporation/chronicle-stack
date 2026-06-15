"""Index commands for the primary Chronicle CLI."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.services.chronicle_service import ChronicleService


index_app = typer.Typer(help="Index operations.")


@index_app.command("rebuild")
def index_rebuild_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Rebuild derived indexes from chronicle.jsonl."""
    try:
        service = ChronicleService()
        service.require_initialized()
        service.rebuild_indexes()
        if json_output:
            typer.echo(json.dumps({"status": "ok", "message": "Indexes rebuilt."}))
        else:
            typer.echo("Indexes rebuilt successfully.")
    except ChronicleError as exc:
        handle_error(exc, json_output)
