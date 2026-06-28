"""AI boundary commands."""

import json
from datetime import datetime
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.ai_boundary import AiBoundaryPersistencePolicy
from chronicle.services.ai_boundary_service import AiBoundaryService


ai_boundary_app = typer.Typer(help="External AI boundary preview commands.", no_args_is_help=True)


@ai_boundary_app.command("preview")
def ai_boundary_preview_cmd(
    task: Annotated[str, typer.Option("--task", help="Purpose for the external AI handoff.")],
    context: Annotated[list[str] | None, typer.Option("--context", help="Context ID to include. Repeatable.")] = None,
    model: Annotated[str, typer.Option("--model", help="External model or adapter identifier.")] = "external:placeholder",
    runtime_label: Annotated[str, typer.Option("--runtime-label", help="Advisory runtime or adapter label.")] = "external-adapter",
    prompt: Annotated[str | None, typer.Option("--prompt", help="Prompt text to persist only when policy allows.")] = None,
    response: Annotated[str | None, typer.Option("--response", help="Response text to persist only when policy allows.")] = None,
    occurred_at: Annotated[str | None, typer.Option("--occurred-at", help="ISO8601 timestamp for the AI exchange.")] = None,
    persist_prompt: Annotated[bool, typer.Option("--persist-prompt/--no-persist-prompt")] = False,
    persist_response: Annotated[bool, typer.Option("--persist-response/--no-persist-response")] = False,
    persist_model_id: Annotated[bool, typer.Option("--persist-model-id/--no-persist-model-id")] = True,
    persist_runtime: Annotated[bool, typer.Option("--persist-runtime/--no-persist-runtime")] = True,
    persist_timestamp: Annotated[bool, typer.Option("--persist-timestamp/--no-persist-timestamp")] = True,
    record: Annotated[bool, typer.Option("--record", help="Persist the advisory preview as an assistant_output event requiring review.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Build a preview-only external AI boundary report."""
    try:
        parsed_occurred_at = datetime.fromisoformat(occurred_at) if occurred_at else None
        preview = AiBoundaryService().preview(
            task=task,
            model_id=model if persist_model_id else "redacted:model-id",
            context_ids=context or [],
            runtime_label=runtime_label if persist_runtime else "redacted:runtime",
            prompt_text=prompt,
            response_text=response,
            occurred_at=parsed_occurred_at,
            persistence_policy=AiBoundaryPersistencePolicy(
                persist_prompt=persist_prompt,
                persist_response=persist_response,
                persist_model_id=persist_model_id,
                persist_runtime_label=persist_runtime,
                persist_timestamp=persist_timestamp,
            ),
            record=record,
        )
        if json_output:
            typer.echo(json.dumps(preview.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return
        typer.echo("Chronicle AI Boundary Preview")
        typer.echo(f"Task: {preview.task}")
        typer.echo(f"Model: {preview.model_id}")
        typer.echo(f"Included contexts: {len(preview.included_context_ids)}")
        typer.echo(f"Redaction candidates: {len(preview.redaction_candidates)}")
        typer.echo(f"Recorded: {preview.recorded}")
        if preview.event_id:
            typer.echo(f"Event: {preview.event_id}")
        typer.echo("Boundary: preview-only, no external send, no provider lock-in, review required before trust.")
    except (ChronicleError, ValueError) as exc:
        if isinstance(exc, ValueError):
            exc = ChronicleError(
                code="AI_BOUNDARY_TIMESTAMP_INVALID",
                message="`--occurred-at` must be a valid ISO8601 timestamp.",
                hint="Example: 2026-06-28T12:34:56+09:00",
            )
        handle_error(exc, json_output)

