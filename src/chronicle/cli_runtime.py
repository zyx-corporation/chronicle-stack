"""CLI commands for explicit local runtime actions."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.services.runtime_service import RuntimeService


runtime_app = typer.Typer(help="Explicit local runtime commands.", no_args_is_help=True)


def _dump_json(value: object) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2))


@runtime_app.command("status")
def runtime_status_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show local runtime boundary status."""
    try:
        status = RuntimeService().status()
        if json_output:
            _dump_json(status.model_dump(mode="json"))
            return

        typer.echo("Chronicle Runtime Status")
        typer.echo(f"Provider: {status.provider_kind.value}")
        typer.echo(f"Model: {status.model_name}")
        typer.echo(f"Capabilities: {', '.join(capability.value for capability in status.capabilities)}")
        typer.echo("Boundary: explicit invocation only, no external calls, generated output requires review.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@runtime_app.command("summarize")
def runtime_summarize_cmd(
    text: Annotated[str, typer.Option("--text", help="Source text to summarize locally.")],
    max_sentences: Annotated[int, typer.Option("--max-sentences", min=1, help="Maximum number of sentences to keep.")] = 3,
    record: Annotated[bool, typer.Option("--record", help="Persist the generated summary as an assistant_output event requiring review.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Generate a local placeholder summary with explicit manual invocation."""
    try:
        result = RuntimeService().summarize(text=text, max_sentences=max_sentences, record=record)
        if json_output:
            _dump_json(result.model_dump(mode="json"))
            return

        typer.echo("Chronicle Runtime Summary")
        typer.echo(f"Generated: {result.generated_text}")
        typer.echo(f"Recorded: {result.recorded}")
        if result.event_id:
            typer.echo(f"Event: {result.event_id}")
        typer.echo("Boundary: no LLM, no external runtime, review required before trust.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@runtime_app.command("retrieve-plan")
def runtime_retrieve_plan_cmd(
    query: Annotated[str, typer.Option("--query", help="Query to assemble a local retrieval dry-run plan for.")],
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum hits per surface.")] = 5,
    record: Annotated[bool, typer.Option("--record", help="Persist the retrieval dry-run plan as an assistant_output event requiring review.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Assemble a local dry-run retrieval plan without invoking a model runtime."""
    try:
        plan = RuntimeService().retrieve_plan(query=query, limit=limit, record=record)
        if json_output:
            _dump_json(plan.model_dump(mode="json"))
            return

        typer.echo("Chronicle Runtime Retrieval Plan")
        typer.echo(f"Query: {plan.query}")
        typer.echo(f"Vector hits: {len(plan.vector_hits)}")
        typer.echo(f"Graph hits: {len(plan.graph_hits)}")
        typer.echo(f"Chronicle hits: {len(plan.chronicle_hits)}")
        typer.echo(f"Recorded: {plan.recorded}")
        if plan.event_id:
            typer.echo(f"Event: {plan.event_id}")
        for note in plan.notes:
            typer.echo(f"Note: {note}")
        typer.echo("Boundary: dry-run only, no GraphRAG runtime, no external retrieval service.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


if __name__ == "__main__":
    runtime_app()
