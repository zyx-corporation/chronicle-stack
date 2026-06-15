"""Decision commands for the primary Chronicle CLI."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.decision import DecisionType
from chronicle.services.decision_service import DecisionService


decision_app = typer.Typer(help="Decision operations.")


@decision_app.command("record")
def decision_record_cmd(
    type: Annotated[DecisionType, typer.Option("--type")],
    reason: Annotated[str, typer.Option("--reason")] = "",
    artifact: Annotated[str | None, typer.Option("--artifact")] = None,
    alternative: Annotated[list[str] | None, typer.Option("--alternative")] = None,
    notes: Annotated[str, typer.Option("--notes")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a Decision."""
    try:
        decision = DecisionService().record(
            decision_type=type,
            reason=reason,
            artifact_id=artifact,
            alternatives=alternative,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(decision.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Decision recorded: {decision.decision_id} ({decision.decision_type.value})")
    except ChronicleError as exc:
        handle_error(exc, json_output)
