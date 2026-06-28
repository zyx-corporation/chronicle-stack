"""Meaningful reaction CLI commands."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.reaction import ChronicleReactionType
from chronicle.services.reaction_service import ReactionService


reaction_app = typer.Typer(help="Meaningful reaction operations.", no_args_is_help=True)


@reaction_app.command("record")
def reaction_record_cmd(
    type: Annotated[ChronicleReactionType, typer.Option("--type")],
    target_object: Annotated[str, typer.Option("--target-object")],
    summary: Annotated[str, typer.Option("--summary")],
    created_by: Annotated[str, typer.Option("--created-by")] = "user",
    detail: Annotated[str, typer.Option("--detail")] = "",
    source_object: Annotated[str | None, typer.Option("--source-object")] = None,
    context: Annotated[str | None, typer.Option("--context")] = None,
    artifact: Annotated[str | None, typer.Option("--artifact")] = None,
    decision: Annotated[str | None, typer.Option("--decision")] = None,
    related_object: Annotated[list[str] | None, typer.Option("--related-object")] = None,
    metadata: Annotated[list[str] | None, typer.Option("--metadata", help="Repeatable key=value metadata.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a meaningful relation-oriented reaction."""
    try:
        parsed_metadata: dict[str, str] = {}
        for item in metadata or []:
            if "=" not in item:
                raise typer.BadParameter("Expected key=value for --metadata.")
            key, value = item.split("=", 1)
            parsed_metadata[key] = value
        record = ReactionService().record(
            reaction_type=type,
            created_by=created_by,
            target_object_id=target_object,
            summary=summary,
            detail=detail,
            source_object_id=source_object,
            target_context_id=context,
            target_artifact_id=artifact,
            target_decision_id=decision,
            related_object_ids=related_object or [],
            metadata=parsed_metadata,
        )
        if json_output:
            typer.echo(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return
        typer.echo(f"Chronicle reaction recorded: {record.reaction_id} ({record.reaction_type.value})")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@reaction_app.command("list")
def reaction_list_cmd(
    type: Annotated[ChronicleReactionType | None, typer.Option("--type")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List meaningful reactions."""
    try:
        rows = ReactionService().list_reactions()
        if type is not None:
            rows = [row for row in rows if row.reaction_type == type]
        if json_output:
            typer.echo(json.dumps([row.model_dump(mode="json") for row in rows], ensure_ascii=False, indent=2))
            return
        if not rows:
            typer.echo("No chronicle reactions found.")
            return
        for row in rows:
            typer.echo(f"{row.reaction_id}  {row.reaction_type.value}  {row.target_object_id}  {row.summary}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@reaction_app.command("show")
def reaction_show_cmd(
    reaction_id: Annotated[str, typer.Option("--id")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show one meaningful reaction."""
    try:
        record = ReactionService().get(reaction_id)
        if json_output:
            typer.echo(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return
        typer.echo(f"{record.reaction_id} ({record.reaction_type.value})")
        typer.echo(record.summary)
    except ChronicleError as exc:
        handle_error(exc, json_output)

