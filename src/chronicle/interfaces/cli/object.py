"""Chronicle object commands."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.models.chronicle_object import (
    ChronicleObjectAiInvolvement,
    ChronicleObjectLifecycle,
    ChronicleObjectLifecycleState,
    ChronicleObjectType,
)
from chronicle.models.visibility import VisibilityHint
from chronicle.services.chronicle_object_service import ChronicleObjectService

object_app = typer.Typer(help="Chronicle object operations.")


@object_app.command("record")
def object_record_cmd(
    type: Annotated[ChronicleObjectType, typer.Option("--type")],
    summary: Annotated[str, typer.Option("--summary")],
    created_by: Annotated[str, typer.Option("--created-by")] = "user",
    detail: Annotated[str, typer.Option("--detail")] = "",
    visibility: Annotated[VisibilityHint, typer.Option("--visibility")] = VisibilityHint.UNKNOWN,
    origin_question: Annotated[str | None, typer.Option("--origin-question")] = None,
    artifact: Annotated[str | None, typer.Option("--artifact")] = None,
    context: Annotated[str | None, typer.Option("--context")] = None,
    decision: Annotated[str | None, typer.Option("--decision")] = None,
    rde: Annotated[str | None, typer.Option("--rde")] = None,
    evidence: Annotated[list[str] | None, typer.Option("--evidence")] = None,
    related_object: Annotated[list[str] | None, typer.Option("--related-object")] = None,
    ai_involved: Annotated[bool, typer.Option("--ai-involved/--ai-not-involved")] = False,
    ai_model: Annotated[list[str] | None, typer.Option("--ai-model")] = None,
    lifecycle_state: Annotated[
        ChronicleObjectLifecycleState,
        typer.Option("--lifecycle-state"),
    ] = ChronicleObjectLifecycleState.ACTIVE,
    retention: Annotated[str | None, typer.Option("--retention")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record an explicit Chronicle object event."""
    try:
        record = ChronicleObjectService().record(
            object_type=type,
            summary=summary,
            created_by=created_by,
            detail=detail,
            visibility_hint=visibility,
            origin_question_id=origin_question,
            artifact_id=artifact,
            context_id=context,
            decision_id=decision,
            rde_record_id=rde,
            evidence=evidence or [],
            related_object_ids=related_object or [],
            ai_involvement=ChronicleObjectAiInvolvement(
                involved=ai_involved or bool(ai_model),
                models=ai_model or [],
            ),
            lifecycle=ChronicleObjectLifecycle(state=lifecycle_state, retention=retention),
        )
        if json_output:
            typer.echo(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Chronicle object recorded: {record.object_id} ({record.object_type.value})")
    except ChronicleError as exc:
        from chronicle.interfaces.cli.common import handle_error

        handle_error(exc, json_output)


@object_app.command("list")
def object_list_cmd(
    type: Annotated[ChronicleObjectType | None, typer.Option("--type")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List Chronicle objects."""
    try:
        rows = ChronicleObjectService().list_objects()
        if type is not None:
            rows = [row for row in rows if row.object_type == type]
        if json_output:
            typer.echo(json.dumps([row.model_dump(mode="json") for row in rows], ensure_ascii=False, indent=2))
        else:
            if not rows:
                typer.echo("No chronicle objects found.")
                return
            for row in rows:
                typer.echo(f"{row.object_id}  {row.object_type.value}  {row.summary}")
    except ChronicleError as exc:
        from chronicle.interfaces.cli.common import handle_error

        handle_error(exc, json_output)


@object_app.command("show")
def object_show_cmd(
    object_id: Annotated[str, typer.Option("--id")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show one Chronicle object."""
    try:
        record = ChronicleObjectService().get(object_id)
        if json_output:
            typer.echo(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"{record.object_id} ({record.object_type.value})")
            typer.echo(record.summary)
    except ChronicleError as exc:
        from chronicle.interfaces.cli.common import handle_error

        handle_error(exc, json_output)
