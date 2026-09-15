"""CLI commands for the explicit local Chronicle API daemon."""

from pathlib import Path
from typing import Annotated

import json
import typer

from chronicle.api.connector_prototypes import (
    ConnectorPrototypeKind,
    ConnectorPrototypeSimulator,
)
from chronicle.api.agent_runtime import default_agent_runtime_contract
from chronicle.api.cloud_authority import (
    default_cloud_authority_model,
    default_cloud_federation_boundary_model,
)
from chronicle.daemon_server import (
    DEFAULT_DAEMON_HOST,
    DEFAULT_DAEMON_PORT,
    build_daemon_startup_metadata,
    serve_daemon,
    run_daemon_smoke,
    validate_daemon_host,
    validate_daemon_root,
)
from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error

daemon_app = typer.Typer(help="Explicit loopback-local Chronicle API daemon.")
prototype_app = typer.Typer(help="Local connector prototype simulator.")
agent_app = typer.Typer(help="Agent runtime contract inspection.")
cloud_app = typer.Typer(help="Chronicle Cloud authority planning inspection.")


@daemon_app.command("start")
def daemon_start_cmd(
    host: Annotated[str, typer.Option("--host", help="Bind host. Loopback only.")] = DEFAULT_DAEMON_HOST,
    port: Annotated[int, typer.Option("--port", help="Bind port for the local API daemon.")] = DEFAULT_DAEMON_PORT,
    root: Annotated[Path, typer.Option("--root", help="Chronicle root. Defaults to current working directory.")] = Path("."),
    token_file: Annotated[
        Path | None,
        typer.Option("--token-file", help="New private token output file; defaults to .chronicle/daemon.token."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print startup metadata as JSON and exit.")] = False,
) -> None:
    """Start the foreground local Chronicle API daemon."""
    try:
        validate_daemon_root(root)
        validate_daemon_host(host)
        metadata = build_daemon_startup_metadata(
            host=host,
            port=port,
            root=root,
            token_file=token_file,
        )
        if json_output:
            typer.echo(metadata.to_json())
            return
        typer.echo("Chronicle API daemon")
        typer.echo(f"Root: {metadata.root}")
        typer.echo(f"Serving: {metadata.url}")
        typer.echo(f"Bind scope: {metadata.bind_scope}")
        typer.echo(f"Auth header: {metadata.auth_header}")
        typer.echo(f"Token file: {metadata.token_file}")
        typer.echo("Mode: read endpoints plus POST /events, POST /diffs, and POST /assertions")
        typer.echo("Boundary: explicit loopback-local daemon; Chronicle JSONL remains authoritative")
        typer.echo("Press Ctrl-C to stop.")
        serve_daemon(host=host, port=port, root=root, token_file=Path(metadata.token_file))
    except ChronicleError as exc:
        handle_error(exc, json_output)


@daemon_app.command("smoke")
def daemon_smoke_cmd(
    root: Annotated[Path, typer.Option("--root", help="Chronicle root. Defaults to current working directory.")] = Path("."),
    host: Annotated[str, typer.Option("--host", help="Bind host metadata to validate. Loopback only.")] = DEFAULT_DAEMON_HOST,
    port: Annotated[int, typer.Option("--port", help="Bind port metadata to validate.")] = DEFAULT_DAEMON_PORT,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run daemon readiness smoke checks without starting a server."""
    try:
        report = run_daemon_smoke(root=root, host=host, port=port)
        if json_output:
            typer.echo(report.to_json())
        else:
            typer.echo("Chronicle daemon smoke")
            typer.echo(f"Root: {report.root}")
            typer.echo("Mode: no server, no browser, no external runtime")
            for check in report.checks:
                status = "PASS" if check.passed else "FAIL"
                typer.echo(f"[{status}] {check.name} - {check.message}")
        if not report.passed:
            raise typer.Exit(code=1)
    except ChronicleError as exc:
        handle_error(exc, json_output)


@prototype_app.command("simulate")
def daemon_prototype_simulate_cmd(
    connector: Annotated[ConnectorPrototypeKind, typer.Option("--connector")],
    title: Annotated[str, typer.Option("--title")],
    body: Annotated[str, typer.Option("--body")],
    idempotency_key: Annotated[str, typer.Option("--idempotency-key")],
    root: Annotated[Path, typer.Option("--root", help="Chronicle root. Defaults to current working directory.")] = Path("."),
    context_id: Annotated[list[str] | None, typer.Option("--context")] = None,
    source_ref: Annotated[str, typer.Option("--source-ref")] = "",
    source_url: Annotated[str | None, typer.Option("--source-url")] = None,
    subject_ref: Annotated[str | None, typer.Option("--subject-ref")] = None,
    commit: Annotated[bool, typer.Option("--commit", help="Submit to local Core services. Default is dry-run.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Simulate a connector prototype without contacting external apps."""
    try:
        validate_daemon_root(root)
        simulation = ConnectorPrototypeSimulator(root).simulate(
            connector=connector,
            title=title,
            body=body,
            idempotency_key=idempotency_key,
            commit=commit,
            context_ids=context_id,
            source_ref=source_ref,
            source_url=source_url,
            subject_ref=subject_ref,
        )
        payload = simulation.model_dump(mode="json")
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"Connector prototype: {payload['connector']}")
        typer.echo(f"Production surface: {payload['production_surface']}")
        typer.echo(f"Request model: {payload['request_model']}")
        typer.echo(f"Committed: {commit}")
        typer.echo("Boundary: simulator only; no external app, credentials, or background sync")
    except ChronicleError as exc:
        handle_error(exc, json_output)


daemon_app.add_typer(prototype_app, name="prototype")


@agent_app.command("contract")
def daemon_agent_contract_cmd(
    runtime_name: Annotated[str, typer.Option("--runtime-name")] = "kazane-compatible-agent",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect the draft agent-runtime API contract."""
    contract = default_agent_runtime_contract(runtime_name)
    payload = contract.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    typer.echo(f"Agent runtime contract: {contract.runtime_name}")
    typer.echo("Boundary: execution layer only; Chronicle remains the preservation mechanism")
    typer.echo("Allowed scopes:")
    for scope in contract.allowed_scopes:
        typer.echo(f"- {scope.value}")


daemon_app.add_typer(agent_app, name="agent")


@cloud_app.command("authority")
def daemon_cloud_authority_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect the draft Chronicle Cloud authority model."""
    model = default_cloud_authority_model()
    payload = model.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    typer.echo("Chronicle Cloud authority model")
    typer.echo(f"Cloud owns Chronicle: {model.cloud_owns_chronicle}")
    typer.echo("Boundary: future service layer only; not cloud AI memory")
    for entry in model.entries:
        typer.echo(f"- {entry.surface.value}: source_authority={entry.can_be_source_authority}")


@cloud_app.command("federation-boundary")
def daemon_cloud_federation_boundary_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect the draft Cloud/Federation relationship boundary."""
    model = default_cloud_federation_boundary_model()
    payload = model.model_dump(mode="json")
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    typer.echo("Chronicle Cloud/Federation boundary")
    typer.echo(f"Cloud bypasses federation consent: {model.cloud_bypasses_federation_consent}")
    typer.echo("Boundary: federation remains the trust/disclosure layer")
    for entry in model.entries:
        owner = "cloud" if entry.belongs_to_cloud else "federation"
        typer.echo(f"- {entry.surface.value}: {owner}")


daemon_app.add_typer(cloud_app, name="cloud")
