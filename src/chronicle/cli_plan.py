"""Operation plan preview commands."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.services.operation_plan_service import OperationPlanService


plan_app = typer.Typer(help="Preview-first operation plan commands.", no_args_is_help=True)


@plan_app.command("artifact-update-preview")
def artifact_update_preview_cmd(
    artifact_id: Annotated[str, typer.Option("--artifact", help="Target artifact ID.")],
    summary: Annotated[str, typer.Option("--summary", help="Proposal summary for the planned update.")],
    content: Annotated[str, typer.Option("--content", help="Proposed replacement content.")],
    proposed_title: Annotated[str, typer.Option("--title", help="Optional proposed artifact title.")] = "",
    source_ref: Annotated[list[str], typer.Option("--source-ref", help="Source record IDs informing the plan.")] = [],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
    record: Annotated[bool, typer.Option("--record", help="Persist the preview-only plan as an assistant_output event.")] = False,
) -> None:
    """Build a preview-only operation plan for an artifact proposal update."""
    try:
        plan = OperationPlanService().build_artifact_update_plan(
            artifact_id=artifact_id,
            summary=summary,
            content=content,
            proposed_title=proposed_title,
            source_refs=source_ref,
        )
        payload = {"plan": plan.model_dump(mode="json")}
        if record:
            payload["event_id"] = OperationPlanService().persist_plan(plan)
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"Plan: {plan.plan_id}")
        typer.echo(f"Operation: {plan.operation}")
        typer.echo(f"Target: {artifact_id}")
        typer.echo("Mode: preview-only; no proposal event recorded")
        if record:
            typer.echo(f"Recorded preview event: {payload['event_id']}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@plan_app.command("artifact-update-proposal")
def artifact_update_proposal_cmd(
    artifact_id: Annotated[str, typer.Option("--artifact", help="Target artifact ID.")],
    summary: Annotated[str, typer.Option("--summary", help="Proposal summary for the update.")],
    content: Annotated[str, typer.Option("--content", help="Proposed replacement content.")],
    proposed_title: Annotated[str, typer.Option("--title", help="Optional proposed artifact title.")] = "",
    source_ref: Annotated[list[str], typer.Option("--source-ref", help="Source record IDs informing the plan.")] = [],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Create a proposal event from a validated artifact update operation plan."""
    try:
        service = OperationPlanService()
        plan = service.build_artifact_update_plan(
            artifact_id=artifact_id,
            summary=summary,
            content=content,
            proposed_title=proposed_title,
            source_refs=source_ref,
        )
        event = service.convert_artifact_update_plan_to_proposal(
            plan=plan,
            summary=summary,
            content=content,
            proposed_title=proposed_title,
        )
        payload = {
            "plan": plan.model_dump(mode="json"),
            "proposal_event_id": event.event_id,
        }
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"Plan: {plan.plan_id}")
        typer.echo(f"Proposal event: {event.event_id}")
        typer.echo("Boundary: preview, review, and apply remain separate")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@plan_app.command("list")
def plan_list_cmd(
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List recorded operation plans."""
    try:
        rows = OperationPlanService().list_plans()
        if json_output:
            typer.echo(
                json.dumps(
                    [
                        {
                            **row,
                            "plan": row["plan"].model_dump(mode="json"),
                        }
                        for row in rows
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        if not rows:
            typer.echo("No operation plans found.")
            return
        for row in rows:
            plan = row["plan"]
            typer.echo(
                f"{plan.plan_id}  {plan.operation}  preview_only={row['preview_only']}  "
                f"converted={row['converted']}  applied={row['applied']}  "
                f"status={row['action_preview_summary']['status']}"
            )
    except ChronicleError as exc:
        handle_error(exc, json_output)


@plan_app.command("show")
def plan_show_cmd(
    plan_id: Annotated[str, typer.Option("--id", help="Recorded operation plan ID.")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Show one recorded operation plan."""
    try:
        row = OperationPlanService().get_plan(plan_id)
        payload = {
            **row,
            "plan": row["plan"].model_dump(mode="json"),
        }
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"{payload['plan']['plan_id']} ({payload['plan']['operation']})")
        typer.echo(payload["summary"])
        typer.echo(f"Status: {payload['action_preview_summary']['status']}")
        typer.echo(f"Next: {payload['action_preview_summary']['next_action_command']}")
        if payload["proposal_event_id"]:
            typer.echo(f"Proposal event: {payload['proposal_event_id']}")
        if payload["applied_event_id"]:
            typer.echo(f"Applied event: {payload['applied_event_id']}")
    except ChronicleError as exc:
        handle_error(exc, json_output)
