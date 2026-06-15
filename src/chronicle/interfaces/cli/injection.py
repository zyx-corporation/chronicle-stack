"""Injection planning commands for the primary Chronicle CLI."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.exporters.injection_plan_report import format_injection_plan
from chronicle.interfaces.cli.common import handle_error
from chronicle.services.injection_service import InjectionPlanService


injection_app = typer.Typer(help="Context injection planning operations.")


@injection_app.command("plan")
def injection_plan_cmd(
    task: Annotated[str, typer.Option("--task", help="Task description for context selection.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    record: Annotated[
        bool,
        typer.Option("--record", help="Persist the plan to chronicle.jsonl."),
    ] = False,
) -> None:
    """Generate a Context Injection Plan for a task."""
    try:
        service = InjectionPlanService()
        plan = service.generate_plan(task)
        event_id = None
        if record:
            event = service.record_plan(plan)
            event_id = event.event_id
        if json_output:
            output = {"plan": plan.model_dump(mode="json"), "recorded": record, "event_id": event_id}
            typer.echo(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            typer.echo(format_injection_plan(plan))
            if record:
                typer.echo(f"\nRecorded as event: {event_id}")
    except ChronicleError as exc:
        handle_error(exc, json_output)
