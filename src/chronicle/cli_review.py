"""CLI commands for append-only review workflow actions."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.review import ReviewerIdentityKind
from chronicle.services.review_service import ReviewService


review_app = typer.Typer(help="Append-only review workflow commands.", no_args_is_help=True)


def _dump_json(value: object) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2))


@review_app.command("queue")
def review_queue_cmd(
    include_resolved: Annotated[bool, typer.Option("--include-resolved", help="Include already approved or rejected targets.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List review targets derived from needs-review events."""
    try:
        rows = ReviewService().queue(include_resolved=include_resolved)
        if json_output:
            _dump_json([row.model_dump(mode="json") for row in rows])
            return
        typer.echo("Chronicle Review Queue")
        typer.echo(f"Pending targets: {len(rows)}")
        for row in rows:
            typer.echo(f"- {row.target_event_id} [{row.review_kind}] {row.target_summary}")
            if row.latest_disposition is not None:
                typer.echo(f"  Latest: {row.latest_disposition.value} by {row.latest_reviewer}")
        typer.echo("Boundary: append-only CLI review, UI mutation remains disabled.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@review_app.command("approve")
def review_approve_cmd(
    event_id: Annotated[str, typer.Option("--event", help="Target event requiring review.")],
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer identity label.")],
    reviewer_kind: Annotated[
        ReviewerIdentityKind,
        typer.Option("--reviewer-kind", help="Structured reviewer identity kind."),
    ] = ReviewerIdentityKind.USER_DECLARED,
    session_label: Annotated[str | None, typer.Option("--session", help="Optional local session label.")] = None,
    note: Annotated[str | None, typer.Option("--note", help="Optional review note.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record an approval as an append-only reviewer event."""
    _emit_decision(
        "approve",
        event_id=event_id,
        reviewer=reviewer,
        reviewer_kind=reviewer_kind,
        session_label=session_label,
        note=note,
        json_output=json_output,
    )


@review_app.command("reject")
def review_reject_cmd(
    event_id: Annotated[str, typer.Option("--event", help="Target event requiring review.")],
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer identity label.")],
    reviewer_kind: Annotated[
        ReviewerIdentityKind,
        typer.Option("--reviewer-kind", help="Structured reviewer identity kind."),
    ] = ReviewerIdentityKind.USER_DECLARED,
    session_label: Annotated[str | None, typer.Option("--session", help="Optional local session label.")] = None,
    note: Annotated[str | None, typer.Option("--note", help="Optional review note.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a rejection as an append-only reviewer event."""
    _emit_decision(
        "reject",
        event_id=event_id,
        reviewer=reviewer,
        reviewer_kind=reviewer_kind,
        session_label=session_label,
        note=note,
        json_output=json_output,
    )


@review_app.command("request-changes")
def review_request_changes_cmd(
    event_id: Annotated[str, typer.Option("--event", help="Target event requiring review.")],
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer identity label.")],
    reviewer_kind: Annotated[
        ReviewerIdentityKind,
        typer.Option("--reviewer-kind", help="Structured reviewer identity kind."),
    ] = ReviewerIdentityKind.USER_DECLARED,
    session_label: Annotated[str | None, typer.Option("--session", help="Optional local session label.")] = None,
    note: Annotated[str | None, typer.Option("--note", help="Optional review note.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a request-for-changes as an append-only reviewer event."""
    _emit_decision(
        "request_changes",
        event_id=event_id,
        reviewer=reviewer,
        reviewer_kind=reviewer_kind,
        session_label=session_label,
        note=note,
        json_output=json_output,
    )


def _emit_decision(
    action: str,
    *,
    event_id: str,
    reviewer: str,
    reviewer_kind: ReviewerIdentityKind,
    session_label: str | None,
    note: str | None,
    json_output: bool,
) -> None:
    try:
        service = ReviewService()
        if action == "approve":
            result = service.approve(
                event_id=event_id,
                reviewer=reviewer,
                reviewer_kind=reviewer_kind,
                session_label=session_label,
                note=note,
            )
        elif action == "reject":
            result = service.reject(
                event_id=event_id,
                reviewer=reviewer,
                reviewer_kind=reviewer_kind,
                session_label=session_label,
                note=note,
            )
        else:
            result = service.request_changes(
                event_id=event_id,
                reviewer=reviewer,
                reviewer_kind=reviewer_kind,
                session_label=session_label,
                note=note,
            )
        if json_output:
            _dump_json(result.model_dump(mode="json"))
            return
        typer.echo(f"Review recorded: {result.review_event_id}")
        typer.echo(f"Target: {result.target_event_id}")
        typer.echo(f"Disposition: {result.disposition.value}")
        typer.echo(f"Reviewer: {result.reviewer}")
        typer.echo(f"Reviewer kind: {result.reviewer_identity.kind.value}")
        if result.note:
            typer.echo(f"Note: {result.note}")
        typer.echo("Boundary: append-only review event recorded; original target event remains unchanged.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


if __name__ == "__main__":
    review_app()
