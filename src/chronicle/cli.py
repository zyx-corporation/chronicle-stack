"""Chronicle CLI — primary interface for Chronicle Core."""

from importlib.metadata import PackageNotFoundError, version as _package_version
from io import UnsupportedOperation
import os
from pathlib import Path
import sys
from typing import Annotated

import typer

from chronicle import __version__
from chronicle.cli_audit import audit_app
from chronicle.cli_ai_index import ai_index_app
from chronicle.cli_context import context_app
from chronicle.cli_graph import graph_app
from chronicle.cli_lifecycle import lifecycle_app
from chronicle.cli_package import package_app
from chronicle.cli_review import review_app
from chronicle.cli_runtime import runtime_app
from chronicle.cli_summary import summary_app
from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.artifact import artifact_app
from chronicle.interfaces.cli.boundary import boundary_app
from chronicle.interfaces.cli.common import handle_error
from chronicle.interfaces.cli.core import register_core_commands
from chronicle.interfaces.cli.decision import decision_app
from chronicle.interfaces.cli.doctor import register_doctor_command
from chronicle.interfaces.cli.export import register_export_command
from chronicle.interfaces.cli.index import index_app
from chronicle.interfaces.cli.injection import injection_app
from chronicle.interfaces.cli.rde import rde_app
from chronicle.ui_server import (
    DEFAULT_UI_HOST,
    DEFAULT_UI_PORT,
    UIAuthMode,
    UIAuthorizationMode,
    build_startup_metadata,
    serve_ui,
    validate_ui_host,
    validate_ui_root,
)
from chronicle.ui_smoke import run_ui_smoke


def _version_callback(value: bool) -> None:
    if value:
        try:
            package_version = _package_version("chronicle-stack")
        except PackageNotFoundError:
            package_version = __version__
        if package_version != __version__:
            package_version = __version__
        typer.echo(f"chronicle {package_version}")
        raise typer.Exit()


app = typer.Typer(
    name="chronicle",
    help=(
        "Chronicle Stack — local-first record of context, artifacts,"
        " decisions, diffs, provenance, and boundary rules."
    ),
    no_args_is_help=True,
)


def _emit_stdout_line(text: str) -> None:
    try:
        os.write(sys.stdout.fileno(), f"{text}\n".encode("utf-8"))
    except (AttributeError, OSError, UnsupportedOperation):
        typer.echo(text)


def _emit_ui_startup_output(*, metadata, enable_ui_mutation: bool, json_output: bool) -> None:
    if json_output:
        _emit_stdout_line(metadata.to_json())
        return
    _emit_stdout_line("Chronicle Stack local UI")
    _emit_stdout_line(f"Root: {metadata.root}")
    _emit_stdout_line(f"Serving: {metadata.url}")
    _emit_stdout_line(f"Bind scope: {metadata.bind_scope}")
    _emit_stdout_line(
        "Mode: mutation enabled for loopback-local review"
        if metadata.mutation_enabled
        else "Mode: read-only, mutation disabled"
    )
    _emit_stdout_line(
        f"Mutation capability flag: {metadata.mutation_capability_flag} (preview intent only)"
    )
    _emit_stdout_line(f"Enable UI mutation: {enable_ui_mutation}")
    _emit_stdout_line(f"Auth: {metadata.auth_mode}; Authorization: {metadata.authorization_mode}")
    _emit_stdout_line(
        "Boundary: no daemon, no external model API, no GraphRAG runtime, no vector DB, no graph DB"
    )
    _emit_stdout_line("Press Ctrl-C to stop.")


@app.callback()
def _root_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    pass


@app.command("ui")
def ui_cmd(
    host: Annotated[str, typer.Option("--host", help="Bind host. Defaults to loopback only.")] = DEFAULT_UI_HOST,
    port: Annotated[int, typer.Option("--port", help="Bind port for the local UI.")] = DEFAULT_UI_PORT,
    root: Annotated[Path, typer.Option("--root", help="Chronicle root. Defaults to current working directory.")] = Path("."),
    open_browser: Annotated[bool, typer.Option("--open", help="Open the local UI in the default browser.")] = False,
    mutation_capability_flag: Annotated[
        bool,
        typer.Option(
            "--mutation-capability-flag",
            help="Record preview intent for future GUI mutation work without enabling any write route.",
        ),
    ] = False,
    enable_ui_mutation: Annotated[
        bool,
        typer.Option(
            "--enable-ui-mutation",
            help="Enable loopback-local GUI review mutation when auth/authorization gates are configured.",
        ),
    ] = False,
    auth_mode: Annotated[
        str,
        typer.Option("--auth-mode", help="UI boundary auth-mode placeholder metadata."),
    ] = UIAuthMode.NOT_ENABLED,
    authorization_mode: Annotated[
        str,
        typer.Option("--authorization-mode", help="UI boundary authorization-mode placeholder metadata."),
    ] = UIAuthorizationMode.NOT_ENABLED,
    json_output: Annotated[bool, typer.Option("--json", help="Print startup metadata as JSON and exit.")] = False,
) -> None:
    """Start an explicit foreground read-only local web UI."""
    try:
        validate_ui_root(root)
        validate_ui_host(host)
        metadata = build_startup_metadata(
            host=host,
            port=port,
            root=root,
            mutation_capability_flag=mutation_capability_flag,
            enable_ui_mutation=enable_ui_mutation,
            auth_mode=auth_mode,
            authorization_mode=authorization_mode,
        )
        _emit_ui_startup_output(
            metadata=metadata,
            enable_ui_mutation=enable_ui_mutation,
            json_output=json_output,
        )
        sys.stdout.flush()
        sys.stderr.flush()
        if json_output:
            return
        serve_ui(
            host=host,
            port=port,
            root=root,
            open_browser=open_browser,
            mutation_capability_flag=mutation_capability_flag,
            enable_ui_mutation=enable_ui_mutation,
            auth_mode=auth_mode,
            authorization_mode=authorization_mode,
        )
    except ChronicleError as exc:
        handle_error(exc, json_output)


@app.command("ui-smoke")
def ui_smoke_cmd(
    root: Annotated[Path, typer.Option("--root", help="Chronicle root. Defaults to current working directory.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable smoke report.")] = False,
) -> None:
    """Run read-only local UI smoke checks without starting a server."""
    try:
        validate_ui_root(root)
        report = run_ui_smoke(root)
        if json_output:
            typer.echo(report.to_json())
        else:
            typer.echo("Chronicle UI smoke")
            typer.echo(f"Root: {report.root}")
            typer.echo("Mode: read-only, no server, no browser, no external runtime")
            for check in report.checks:
                status = "PASS" if check.passed else "FAIL"
                typer.echo(f"[{status}] {check.name} - {check.message}")
        if not report.passed:
            raise typer.Exit(code=1)
    except ChronicleError as exc:
        handle_error(exc, json_output)


register_core_commands(app)
register_doctor_command(app)
register_export_command(app)

app.add_typer(artifact_app, name="artifact")
app.add_typer(decision_app, name="decision")
app.add_typer(rde_app, name="rde")
app.add_typer(index_app, name="index")
app.add_typer(boundary_app, name="boundary")
app.add_typer(injection_app, name="injection")
app.add_typer(package_app, name="package")
app.add_typer(context_app, name="context")
app.add_typer(audit_app, name="audit")
app.add_typer(lifecycle_app, name="lifecycle")
app.add_typer(graph_app, name="graph")
app.add_typer(ai_index_app, name="ai-index")
app.add_typer(runtime_app, name="runtime")
app.add_typer(summary_app, name="summary")
app.add_typer(review_app, name="review")


def main() -> None:
    """Console-script entrypoint."""
    app()


if __name__ == "__main__":
    main()
