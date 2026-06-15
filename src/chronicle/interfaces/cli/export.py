"""Export commands for the primary Chronicle CLI."""

import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from chronicle.cli_export import export_profile_cmd
from chronicle.errors import ChronicleError
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.exporters.markdown_exporter import MarkdownExporter
from chronicle.exporters.redaction import RedactionOptions
from chronicle.exporters.yaml_exporter import YamlExporter
from chronicle.interfaces.cli.common import handle_error
from chronicle.services.graph_export_service import GraphExportService


class ExportFormat(StrEnum):
    YAML = "yaml"
    MARKDOWN = "markdown"
    GRAPH_JSON = "graph-json"
    HTML = "html"


def _run_export(
    *,
    format: ExportFormat,
    output: Path | None,
    json_output: bool,
    redact_sensitive: bool,
    exclude_sensitive: bool,
) -> None:
    if redact_sensitive and exclude_sensitive:
        typer.echo("Use either --redact-sensitive or --exclude-sensitive, not both.", err=True)
        raise typer.Exit(code=1)

    redaction = RedactionOptions(
        redact_sensitive=redact_sensitive,
        exclude_sensitive=exclude_sensitive,
    )
    if redaction.enabled and format not in (ExportFormat.YAML, ExportFormat.HTML):
        typer.echo("Redaction-aware export currently supports yaml and html only.", err=True)
        raise typer.Exit(code=1)

    try:
        if format == ExportFormat.YAML:
            content = YamlExporter().export(output=output, redaction=redaction)
        elif format == ExportFormat.GRAPH_JSON:
            graph = GraphExportService().export_graph()
            content = json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, indent=2)
            if output:
                output.write_text(content, encoding="utf-8")
        elif format == ExportFormat.HTML:
            content = HtmlDashboardExporter().export(redaction=redaction)
            if output:
                output.write_text(content, encoding="utf-8")
        else:
            content = MarkdownExporter().export(output=output)

        if output:
            if json_output:
                typer.echo(json.dumps({
                    "output": str(output),
                    "format": format.value,
                    "redact_sensitive": redact_sensitive,
                    "exclude_sensitive": exclude_sensitive,
                }))
            else:
                typer.echo(f"Exported to {output}")
        elif not json_output:
            typer.echo(content)
    except ChronicleError as exc:
        handle_error(exc, json_output)


def register_export_command(app: typer.Typer) -> None:
    """Register primary export command namespace.

    `chronicle export --format ...` remains the compatibility path. The same
    namespace also exposes `chronicle export profile ...` for the auxiliary
    security-aware export profile surface.
    """
    export_app = typer.Typer(
        help="Export Chronicle to YAML, Markdown, Graph JSON, or HTML.",
        no_args_is_help=False,
        invoke_without_command=True,
    )

    @export_app.callback()
    def export_cmd(
        ctx: typer.Context,
        format: Annotated[ExportFormat, typer.Option("--format")] = ExportFormat.YAML,
        output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
        json_output: Annotated[bool, typer.Option("--json")] = False,
        redact_sensitive: Annotated[bool, typer.Option("--redact-sensitive")] = False,
        exclude_sensitive: Annotated[bool, typer.Option("--exclude-sensitive")] = False,
    ) -> None:
        """Export Chronicle to YAML, Markdown, Graph JSON, or HTML."""
        if ctx.invoked_subcommand is not None:
            return
        _run_export(
            format=format,
            output=output,
            json_output=json_output,
            redact_sensitive=redact_sensitive,
            exclude_sensitive=exclude_sensitive,
        )

    export_app.command("profile")(export_profile_cmd)
    app.add_typer(export_app, name="export")
