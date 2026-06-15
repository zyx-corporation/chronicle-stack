"""CLI for local audit event workflows."""

import json
from typing import Annotated

import typer

from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.services.audit_service import AuditService


audit_app = typer.Typer(
    name="audit",
    help="Chronicle local audit event workflows.",
    no_args_is_help=True,
)


@audit_app.command("record")
def audit_record_cmd(
    operation: Annotated[AuditOperation, typer.Option("--operation", help="Audited operation.")] = AuditOperation.EXPORT,
    actor: Annotated[str, typer.Option("--actor", help="Actor label.")] = "user",
    purpose: Annotated[str, typer.Option("--purpose", help="Purpose for this audited operation.")] = "",
    target: Annotated[AuditTargetEnvironment, typer.Option("--target", help="Target environment.")] = AuditTargetEnvironment.LOCAL,
    result: Annotated[AuditSeverity, typer.Option("--result", help="Audit result severity.")] = AuditSeverity.INFO,
    summary: Annotated[str, typer.Option("--summary", help="Short audit summary.")] = "",
    record_id: Annotated[list[str] | None, typer.Option("--record", help="Referenced Chronicle record ID. Repeatable.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a local audit event.

    Audit events improve traceability. They are not enforcement or
    certification mechanisms.
    """
    event = AuditService().record(
        operation=operation,
        actor=actor,
        purpose=purpose,
        target_environment=target,
        referenced_records=record_id or [],
        result=result,
        summary=summary,
    )
    if json_output:
        typer.echo(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        typer.echo(f"Audit event recorded: {event.audit_id}")
        typer.echo("Boundary: audit events are traceability metadata, not enforcement.")


@audit_app.command("list")
def audit_list_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List local audit events."""
    events = AuditService().list_events()
    if json_output:
        typer.echo(json.dumps([event.model_dump(mode="json") for event in events], ensure_ascii=False, indent=2))
        return
    if not events:
        typer.echo("No audit events recorded.")
        return
    for event in events:
        typer.echo(f"{event.audit_id}: {event.operation.value} [{event.result.value}] {event.summary}")


@audit_app.command("show")
def audit_show_cmd(
    audit_id: Annotated[str, typer.Option("--id", help="Audit event ID.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show a single audit event."""
    events = AuditService().list_events()
    for event in events:
        if event.audit_id == audit_id:
            if json_output:
                typer.echo(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))
            else:
                typer.echo(f"Audit: {event.audit_id}")
                typer.echo(f"Operation: {event.operation.value}")
                typer.echo(f"Result: {event.result.value}")
                typer.echo(f"Purpose: {event.purpose}")
                typer.echo(f"Summary: {event.summary}")
            return
    typer.echo(f"Audit event not found: {audit_id}", err=True)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    audit_app()
