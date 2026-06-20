"""Summary job CLI.

Summary commands create and inspect local draft summary jobs. They do not invoke
LLMs, embeddings, vector DBs, graph DBs, GraphRAG runtimes, or external services.
"""

import json
from typing import Annotated

import typer

from chronicle.models.summary_job import SummarySourceRef
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.summary_job_service import SummaryJobService

summary_app = typer.Typer(
    name="summary",
    help="Local summary draft job workflows.",
    no_args_is_help=True,
)


def _parse_source_ref(value: str) -> SummarySourceRef:
    if ":" in value:
        record_type, record_id = value.split(":", 1)
        return SummarySourceRef(record_id=record_id, record_type=record_type)
    return SummarySourceRef(record_id=value)


@summary_app.command("create")
def summary_create_cmd(
    title: Annotated[str, typer.Option("--title", help="Summary title.")],
    text: Annotated[str, typer.Option("--text", help="Draft summary text. No model call is made.")],
    source: Annotated[list[str] | None, typer.Option("--source", help="Source reference, e.g. event:evt_x or ctx_x. Repeatable.")] = None,
    prompt: Annotated[str, typer.Option("--prompt", help="Prompt/provenance note. No model call is made.")] = "",
    tag: Annotated[list[str] | None, typer.Option("--tag", help="Optional tag. Repeatable.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a local summary draft job without invoking an AI runtime."""

    source_refs = [_parse_source_ref(item) for item in (source or [])]
    job = SummaryJobService().create_manual_draft(
        title=title,
        summary_text=text,
        source_refs=source_refs,
        prompt=prompt,
        tags=tag or [],
    )
    if json_output:
        typer.echo(json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    typer.echo(f"Summary job created: {job.summary_job_id}")
    typer.echo(f"Artifact: {job.artifact_id}")
    typer.echo(f"Status: {job.status.value}")
    typer.echo("Boundary: no AI runtime, model API, vector DB, graph DB, or GraphRAG runtime was invoked.")
    typer.echo("Review: generated or prepared summaries remain drafts until reviewed.")


@summary_app.command("list")
def summary_list_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List local summary draft jobs."""

    jobs = SummaryJobService().list_jobs()
    if json_output:
        typer.echo(json.dumps([job.model_dump(mode="json") for job in jobs], ensure_ascii=False, indent=2))
        return

    if not jobs:
        typer.echo("No summary jobs found.")
        return
    for job in jobs:
        typer.echo(f"{job.summary_job_id}: {job.title} [{job.status.value}]")


@summary_app.command("show")
def summary_show_cmd(
    summary_job_id: Annotated[str, typer.Option("--id", help="Summary job ID.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show a local summary draft job."""

    job = SummaryJobService().get(summary_job_id)
    if json_output:
        typer.echo(json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    typer.echo(f"Summary job: {job.summary_job_id}")
    typer.echo(f"Title: {job.title}")
    typer.echo(f"Status: {job.status.value}")
    typer.echo(f"Artifact: {job.artifact_id}")
    typer.echo(f"External call made: {job.provenance.external_call_made}")
    typer.echo("Sources:")
    for ref in job.source_refs:
        typer.echo(f"  - {ref.record_type}:{ref.record_id}")


@summary_app.command("run")
def summary_run_cmd(
    summary_job_id: Annotated[str, typer.Option("--id", help="Source summary job ID.")],
    max_sentences: Annotated[int, typer.Option("--max-sentences", min=1, help="Maximum number of sentences to keep.")] = 3,
    draft_title: Annotated[str | None, typer.Option("--draft-title", help="Override title for the generated runtime-backed draft summary job.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Re-run a local draft through the explicit manual runtime boundary."""

    source_job = SummaryJobService().get(summary_job_id)
    result = RuntimeService().summarize(
        text=source_job.summary_text,
        max_sentences=max_sentences,
        draft_title=draft_title or f"Runtime Draft: {source_job.title}",
        source_refs=source_job.source_refs,
        tags=["summary-run", summary_job_id],
        prompt=source_job.provenance.prompt or f"summary run from {summary_job_id}",
        operator="summary-run",
    )
    if json_output:
        typer.echo(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    typer.echo("Summary job re-run through explicit runtime boundary")
    typer.echo(f"Source summary job: {summary_job_id}")
    typer.echo(f"Generated: {result.generated_text}")
    if result.draft_summary_job_id:
        typer.echo(f"Draft summary job: {result.draft_summary_job_id}")
    typer.echo("Boundary: explicit manual runtime only, no external model API, review remains required.")


@summary_app.command("invoke-plan")
def summary_invoke_plan_cmd(
    summary_job_id: Annotated[str, typer.Option("--id", help="Source summary job ID.")],
    operation: Annotated[str, typer.Option("--operation", help="Planned provider operation name.")] = "summarize",
    record: Annotated[bool, typer.Option("--record", help="Persist the invocation dry-run plan as an assistant_output event requiring review.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a provider invocation dry-run plan from an existing summary draft."""

    source_job = SummaryJobService().get(summary_job_id)
    result = RuntimeService().invocation_plan_from_summary(
        summary_job_id=source_job.summary_job_id,
        summary_title=source_job.title,
        summary_text=source_job.summary_text,
        prompt=source_job.provenance.prompt,
        source_ref_count=len(source_job.source_refs),
        operation=operation,
        record=record,
    )
    if json_output:
        typer.echo(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    typer.echo("Summary job invocation plan created through explicit runtime boundary")
    typer.echo(f"Source summary job: {summary_job_id}")
    typer.echo(f"Operation: {result.operation}")
    typer.echo(f"Invocation ready: {result.invocation_ready}")
    if result.blocking_reasons:
        typer.echo(f"Blocking reasons: {', '.join(result.blocking_reasons)}")
    if result.event_id:
        typer.echo(f"Event: {result.event_id}")
    typer.echo("Boundary: dry-run contract only, no provider execution, review remains required.")


if __name__ == "__main__":
    summary_app()
