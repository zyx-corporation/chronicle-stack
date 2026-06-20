"""CLI commands for explicit local runtime actions."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.runtime_service import RuntimeService


runtime_app = typer.Typer(help="Explicit local runtime commands.", no_args_is_help=True)
runtime_config_app = typer.Typer(help="Stored runtime provider configuration.", no_args_is_help=True)


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
        typer.echo(
            "Configured provider contract: "
            f"{status.configured_provider_kind.value} / {status.configured_model_name}"
        )
        typer.echo(f"Capabilities: {', '.join(capability.value for capability in status.capabilities)}")
        typer.echo("Boundary: explicit invocation only, no external calls, generated output requires review.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@runtime_app.command("summarize")
def runtime_summarize_cmd(
    text: Annotated[str, typer.Option("--text", help="Source text to summarize locally.")],
    max_sentences: Annotated[int, typer.Option("--max-sentences", min=1, help="Maximum number of sentences to keep.")] = 3,
    record: Annotated[bool, typer.Option("--record", help="Persist the generated summary as an assistant_output event requiring review.")] = False,
    draft_title: Annotated[str | None, typer.Option("--draft-title", help="Also persist the generated summary as a pending-review summary job with this title.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Generate a local placeholder summary with explicit manual invocation."""
    try:
        result = RuntimeService().summarize(
            text=text,
            max_sentences=max_sentences,
            record=record,
            draft_title=draft_title,
        )
        if json_output:
            _dump_json(result.model_dump(mode="json"))
            return

        typer.echo("Chronicle Runtime Summary")
        typer.echo(f"Generated: {result.generated_text}")
        typer.echo(f"Recorded: {result.recorded}")
        if result.event_id:
            typer.echo(f"Event: {result.event_id}")
        if result.draft_summary_job_id:
            typer.echo(f"Draft summary job: {result.draft_summary_job_id}")
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


@runtime_config_app.command("show")
def runtime_config_show_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show stored runtime provider configuration without invoking it."""
    try:
        state = RuntimeConfigService().show()
        if json_output:
            _dump_json(state.model_dump(mode="json"))
            return

        typer.echo("Chronicle Runtime Config")
        typer.echo(f"Source: {state.source}")
        typer.echo(f"Provider kind: {state.config.provider_kind.value}")
        typer.echo(f"Provider name: {state.config.provider_name}")
        typer.echo(f"Model: {state.config.model_name}")
        if state.config.base_url:
            typer.echo(f"Base URL: {state.config.base_url}")
        if state.config.api_key_env:
            typer.echo(f"API key env: {state.config.api_key_env}")
        typer.echo(f"Allow network: {state.config.allow_network}")
        typer.echo(f"Allow external context: {state.config.allow_external_context}")
        for warning in state.warnings:
            typer.echo(f"Warning: {warning}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@runtime_config_app.command("set-local")
def runtime_config_set_local_cmd(
    model_name: Annotated[str, typer.Option("--model", help="Configured model name for the local provider contract.")] = "local-placeholder",
    provider_name: Annotated[str, typer.Option("--provider-name", help="Configured provider display name.")] = "local-placeholder",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Persist a local-only runtime provider contract."""
    try:
        state = RuntimeConfigService().set_local(model_name=model_name, provider_name=provider_name)
        if json_output:
            _dump_json(state.model_dump(mode="json"))
            return

        typer.echo("Stored local runtime provider contract.")
        typer.echo(f"Provider: {state.config.provider_name}")
        typer.echo(f"Model: {state.config.model_name}")
        typer.echo("Boundary: configuration only, no model invocation performed.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@runtime_config_app.command("set-http")
def runtime_config_set_http_cmd(
    base_url: Annotated[str, typer.Option("--base-url", help="Configured HTTP runtime base URL.")] ,
    model_name: Annotated[str, typer.Option("--model", help="Configured model name for the HTTP provider contract.")] ,
    api_key_env: Annotated[str, typer.Option("--api-key-env", help="Environment variable name that would hold the API key.")] ,
    provider_name: Annotated[str, typer.Option("--provider-name", help="Configured provider display name.")] = "http-manual",
    allow_network: Annotated[bool, typer.Option("--allow-network", help="Persist downstream network intent in the stored contract only.")] = False,
    allow_external_context: Annotated[bool, typer.Option("--allow-external-context", help="Persist downstream external-context intent in the stored contract only.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Persist an HTTP provider contract without invoking any network runtime."""
    try:
        state = RuntimeConfigService().set_http(
            base_url=base_url,
            model_name=model_name,
            api_key_env=api_key_env,
            provider_name=provider_name,
            allow_network=allow_network,
            allow_external_context=allow_external_context,
        )
        if json_output:
            _dump_json(state.model_dump(mode="json"))
            return

        typer.echo("Stored HTTP runtime provider contract.")
        typer.echo(f"Provider: {state.config.provider_name}")
        typer.echo(f"Model: {state.config.model_name}")
        typer.echo(f"Base URL: {state.config.base_url}")
        typer.echo("Boundary: configuration only, no network request performed.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@runtime_config_app.command("disable")
def runtime_config_disable_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Persist a disabled runtime provider contract."""
    try:
        state = RuntimeConfigService().disable()
        if json_output:
            _dump_json(state.model_dump(mode="json"))
            return

        typer.echo("Stored disabled runtime provider contract.")
        typer.echo("Boundary: configuration only, runtime remains disabled until reconfigured.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


runtime_app.add_typer(runtime_config_app, name="config")


if __name__ == "__main__":
    runtime_app()
