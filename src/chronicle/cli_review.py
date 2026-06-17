"""Review workflow CLI."""

import json
from typing import Annotated

import typer

from chronicle.models.review import ReviewAction
from chronicle.services.review_service import ReviewService

review_app = typer.Typer(
    name="review",
    help="Local review workflow commands.",
    no_args_is_help=True,
)


@review_app.command("queue")
def review_queue_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List generated/prepared outputs waiting for review."""

    jobs = ReviewService().list_review_queue()
    if json_output:
        typer.echo(json.dumps([job.model_dump(mode="json") for job in jobs], ensure_ascii=False, indent=2))
        return
    if not jobs:
        typer.echo("Review queue is empty.")
        return
    for job in jobs:
        typer.echo(f"{job.summary_job_id}: {job.title} [{job.status.value}]")


@review_app.command("decisions")
def review_decisions_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List recorded review decisions."""

    decisions = ReviewService().list_decisions()
    if json_output:
        typer.echo(json.dumps([decision.model_dump(mode="json") for decision in decisions], ensure_ascii=False, indent=2))
        return
    if not decisions:
        typer.echo("No review decisions found.")
        return
    for decision in decisions:
        typer.echo(f"{decision.review_id}: {decision.action.value} {decision.target_id} -> {decision.resulting_status.value}")


def _print_decision(decision, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(decision.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return
    typer.echo(f"Review decision: {decision.review_id}")
    typer.echo(f"Target: {decision.target_type.value}:{decision.target_id}")
    typer.echo(f"Action: {decision.action.value}")
    typer.echo(f"Resulting status: {decision.resulting_status.value}")
    if decision.reason:
        typer.echo(f"Reason: {decision.reason}")
    typer.echo("Boundary: review records a local decision; it is not correctness proof or security certification.")


@review_app.command("approve")
def review_approve_cmd(
    summary_job_id: Annotated[str, typer.Option("--id", help="Summary job ID.")],
    reason: Annotated[str, typer.Option("--reason", help="Optional approval reason.")] = "",
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer label.")] = "reviewer",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Approve a summary job."""

    decision = ReviewService().decide_summary_job(summary_job_id, ReviewAction.APPROVE, reason=reason, reviewer=reviewer)
    _print_decision(decision, json_output)


@review_app.command("reject")
def review_reject_cmd(
    summary_job_id: Annotated[str, typer.Option("--id", help="Summary job ID.")],
    reason: Annotated[str, typer.Option("--reason", help="Rejection reason.")],
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer label.")] = "reviewer",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Reject a summary job."""

    decision = ReviewService().decide_summary_job(summary_job_id, ReviewAction.REJECT, reason=reason, reviewer=reviewer)
    _print_decision(decision, json_output)


@review_app.command("request-changes")
def review_request_changes_cmd(
    summary_job_id: Annotated[str, typer.Option("--id", help="Summary job ID.")],
    reason: Annotated[str, typer.Option("--reason", help="Requested changes.")],
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer label.")] = "reviewer",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Request changes for a summary job."""

    decision = ReviewService().decide_summary_job(summary_job_id, ReviewAction.REQUEST_CHANGES, reason=reason, reviewer=reviewer)
    _print_decision(decision, json_output)


if __name__ == "__main__":
    review_app()
