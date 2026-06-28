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


@rde_app.command("draft")
def rde_draft_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    from_version: Annotated[str, typer.Option("--from")],
    to_version: Annotated[str, typer.Option("--to")],
    summary: Annotated[str, typer.Option("--summary")] = "",
    mode: Annotated[str, typer.Option("--mode")] = "manual",
    ai_summary: Annotated[str, typer.Option("--ai-summary")] = "",
    ai_response: Annotated[str | None, typer.Option("--ai-response")] = None,
    ai_model: Annotated[str | None, typer.Option("--ai-model")] = None,
    runtime_label: Annotated[str | None, typer.Option("--runtime-label")] = None,
    interpretation: Annotated[str | None, typer.Option("--interpretation")] = None,
    preserved: Annotated[list[str] | None, typer.Option("--preserved")] = None,
    transformed: Annotated[list[str] | None, typer.Option("--transformed")] = None,
    supplemented: Annotated[list[str] | None, typer.Option("--supplemented")] = None,
    unresolved: Annotated[list[str] | None, typer.Option("--unresolved")] = None,
    risk_items: Annotated[list[str] | None, typer.Option("--deviation-risk")] = None,
    next_update_policy: Annotated[list[str] | None, typer.Option("--next-update-policy")] = None,
    record: Annotated[bool, typer.Option("--record")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Prepare an RDE draft memo, optionally persisting the linked RDE record."""
    try:
        memo = RdeService().draft(
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
            mode=mode,
            ai_summary=ai_summary,
            ai_response=ai_response,
            ai_model=ai_model,
            runtime_label=runtime_label,
            interpretation=interpretation,
            record=record,
        )
        if json_output:
            typer.echo(json.dumps(memo.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return
        typer.echo("Chronicle RDE Draft")
        typer.echo(f"Mode: {memo.mode}")
        typer.echo(f"Artifact: {memo.artifact_id}")
        typer.echo(f"Linked delta object: {memo.linked_delta_object_id or 'obj_delta_<pending>'}")
        if memo.linked_hypothesis_object_id:
            typer.echo(f"Hypothesis object: {memo.linked_hypothesis_object_id}")
        if memo.recorded_rde_id:
            typer.echo(f"RDE record: {memo.recorded_rde_id}")
        typer.echo("Boundary: AI response remains separate, interpretation stays hypothesis-oriented, review required.")
    except ChronicleError as exc:
        handle_error(exc, json_output)
