"""RDE commands for the primary Chronicle CLI."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.services.rde_service import RdeService


rde_app = typer.Typer(help="RDE Diff Record operations.")


@rde_app.command("record")
def rde_record_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    from_version: Annotated[str, typer.Option("--from")],
    to_version: Annotated[str, typer.Option("--to")],
    summary: Annotated[str, typer.Option("--summary")] = "",
    preserved: Annotated[list[str] | None, typer.Option("--preserved")] = None,
    transformed: Annotated[list[str] | None, typer.Option("--transformed")] = None,
    supplemented: Annotated[list[str] | None, typer.Option("--supplemented")] = None,
    unresolved: Annotated[list[str] | None, typer.Option("--unresolved")] = None,
    risk_items: Annotated[list[str] | None, typer.Option("--deviation-risk")] = None,
    next_update_policy: Annotated[list[str] | None, typer.Option("--next-update-policy")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create an RDE Diff Record."""
    try:
        record = RdeService().record(
            artifact_id=artifact,
            from_version_id=from_version,
            to_version_id=to_version,
            summary=summary,
            preserved=preserved or [],
            transformed=transformed or [],
            supplemented=supplemented or [],
            unresolved=unresolved or [],
            deviation_risks=risk_items or [],
            next_update_policy=next_update_policy or [],
        )
        if json_output:
            typer.echo(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"RDE record created: {record.rde_record_id}")
    except ChronicleError as exc:
        handle_error(exc, json_output)
