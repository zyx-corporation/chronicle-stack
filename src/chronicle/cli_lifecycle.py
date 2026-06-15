"""CLI for advisory lifecycle marker workflows."""

import json
from typing import Annotated

import typer

from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass, LifecycleVisibility
from chronicle.services.lifecycle_service import LifecycleService


lifecycle_app = typer.Typer(
    name="lifecycle",
    help="Chronicle advisory lifecycle marker workflows.",
    no_args_is_help=True,
)


@lifecycle_app.command("record")
def lifecycle_record_cmd(
    target_id: Annotated[str, typer.Option("--target", help="Target record ID.")],
    action: Annotated[LifecycleAction, typer.Option("--action", help="Lifecycle marker action.")] = LifecycleAction.SEAL,
    target_kind: Annotated[str, typer.Option("--target-kind", help="Target kind, e.g. context or artifact.")] = "unknown",
    actor: Annotated[str, typer.Option("--actor", help="Actor label.")] = "user",
    reason_class: Annotated[LifecycleReasonClass, typer.Option("--reason-class", help="Reason category.")] = LifecycleReasonClass.OTHER,
    reason: Annotated[str, typer.Option("--reason", help="Human-readable reason.")] = "",
    visible_detail_level: Annotated[LifecycleVisibility, typer.Option("--visible-detail-level", help="Advisory visible detail level.")] = LifecycleVisibility.TOMBSTONE_ONLY,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record an advisory lifecycle marker.

    Lifecycle events are metadata for downstream workflows. They do not mutate
    primary records by themselves.
    """
    event = LifecycleService().record(
        action=action,
        target_id=target_id,
        target_kind=target_kind,
        actor=actor,
        reason_class=reason_class,
        reason=reason,
        visible_detail_level=visible_detail_level,
    )
    if json_output:
        typer.echo(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        typer.echo(f"Lifecycle event recorded: {event.lifecycle_id}")
        typer.echo("Boundary: lifecycle markers are advisory metadata, not primary-record mutation.")


@lifecycle_app.command("list")
def lifecycle_list_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List lifecycle marker events."""
    events = LifecycleService().list_events()
    if json_output:
        typer.echo(json.dumps([event.model_dump(mode="json") for event in events], ensure_ascii=False, indent=2))
        return
    if not events:
        typer.echo("No lifecycle events recorded.")
        return
    for event in events:
        typer.echo(f"{event.lifecycle_id}: {event.action.value} {event.target_kind}:{event.target_id}")


@lifecycle_app.command("show")
def lifecycle_show_cmd(
    lifecycle_id: Annotated[str, typer.Option("--id", help="Lifecycle event ID.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show a single lifecycle marker event."""
    events = LifecycleService().list_events()
    for event in events:
        if event.lifecycle_id == lifecycle_id:
            if json_output:
                typer.echo(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))
            else:
                typer.echo(f"Lifecycle: {event.lifecycle_id}")
                typer.echo(f"Action: {event.action.value}")
                typer.echo(f"Target: {event.target_kind}:{event.target_id}")
                typer.echo(f"Reason: {event.reason}")
            return
    typer.echo(f"Lifecycle event not found: {lifecycle_id}", err=True)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    lifecycle_app()
