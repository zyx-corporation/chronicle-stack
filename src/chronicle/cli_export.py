"""Auxiliary CLI for security-aware export profiles."""

import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.exporters.redaction import ExportProfile, RedactionOptions
from chronicle.exporters.yaml_exporter import YamlExporter

export_app = typer.Typer(
    name="chronicle-export",
    help="Chronicle Stack security-aware export profiles.",
    no_args_is_help=True,
)


class ProfileExportFormat(StrEnum):
    YAML = "yaml"
    HTML = "html"


@export_app.command("profile")
def export_profile_cmd(
    profile: Annotated[ExportProfile, typer.Option("--profile", help="Security-aware export profile.")],
    format: Annotated[ProfileExportFormat, typer.Option("--format")] = ProfileExportFormat.YAML,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Export Chronicle using a security-aware profile.

    This command does not mutate primary Chronicle records.
    """
    redaction = RedactionOptions.from_profile(profile)
    if format == ProfileExportFormat.YAML:
        content = YamlExporter().export(output=output, redaction=redaction)
    else:
        content = HtmlDashboardExporter().export(redaction=redaction)
        if output:
            output.write_text(content, encoding="utf-8")

    if output:
        if json_output:
            typer.echo(json.dumps({
                "output": str(output),
                "format": format.value,
                "profile": profile.value,
                "redact_sensitive": redaction.redact_sensitive,
                "exclude_sensitive": redaction.exclude_sensitive,
            }))
        else:
            typer.echo(f"Exported to {output}")
    elif not json_output:
        typer.echo(content)


if __name__ == "__main__":
    export_app()
