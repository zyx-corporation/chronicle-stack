"""AI runtime CLI boundary.

The runtime command group exposes configuration/status metadata only. It does
not invoke LLMs, embedding providers, vector DBs, graph DBs, GraphRAG runtimes,
or external services.
"""

import json
from typing import Annotated

import typer

from chronicle.models.runtime import disabled_runtime_status

runtime_app = typer.Typer(
    name="runtime",
    help="AI runtime boundary and status commands.",
    no_args_is_help=True,
)


@runtime_app.command("status")
def runtime_status_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show AI runtime status without invoking any provider."""

    report = disabled_runtime_status()
    if json_output:
        typer.echo(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    typer.echo("Chronicle AI Runtime Status")
    typer.echo(f"Status: {report.status.value}")
    typer.echo(f"Provider: {report.config.provider_kind.value}")
    typer.echo(f"Provider name: {report.config.provider_name}")
    typer.echo(f"Capabilities: {', '.join(cap.value for cap in report.config.capabilities) or 'none'}")
    typer.echo("Boundary:")
    typer.echo(f"  explicit invocation required: {report.boundary.explicit_invocation_required}")
    typer.echo(f"  network calls by default: {report.boundary.network_calls_default}")
    typer.echo(f"  model calls by default: {report.boundary.model_calls_default}")
    typer.echo(f"  vector DB by default: {report.boundary.vector_db_default}")
    typer.echo(f"  graph DB by default: {report.boundary.graph_db_default}")
    typer.echo(f"  generated output requires review: {report.boundary.generated_output_requires_review}")
    typer.echo(f"  indexes are derived surfaces: {report.boundary.indexes_are_derived}")
    if report.warnings:
        typer.echo("Warnings:")
        for warning in report.warnings:
            typer.echo(f"  - {warning}")


if __name__ == "__main__":
    runtime_app()
