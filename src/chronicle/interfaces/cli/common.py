"""Shared helpers for Chronicle CLI adapters."""

import json

import typer

from chronicle.errors import ChronicleError
from chronicle.models.source import SourceProvenance


def handle_error(exc: ChronicleError, json_output: bool) -> None:
    """Render a ChronicleError and exit with failure."""
    if json_output:
        typer.echo(json.dumps(exc.to_dict(), ensure_ascii=False))
    else:
        typer.echo(str(exc), err=True)
    raise typer.Exit(code=1)


def source_from_options(
    *,
    source_type: str | None = None,
    source_ref: str | None = None,
    source_tool: str | None = None,
    source_session: str | None = None,
    source_model: str | None = None,
    source_file: str | None = None,
    source_url: str | None = None,
) -> SourceProvenance | None:
    """Build SourceProvenance from optional CLI source fields."""
    if not any([
        source_type,
        source_ref,
        source_tool,
        source_session,
        source_model,
        source_file,
        source_url,
    ]):
        return None
    return SourceProvenance(
        source_type=source_type or "unknown",
        source_ref=source_ref or "",
        source_tool=source_tool,
        source_session=source_session,
        source_model=source_model,
        source_file=source_file,
        source_url=source_url,
    )
