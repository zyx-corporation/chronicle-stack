"""Auxiliary CLI for security-aware export profiles."""

import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.exporters.redaction import ExportProfile, RedactionOptions
from chronicle.exporters.yaml_exporter import YamlExporter
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.services.audit_service import AuditService

export_app = typer.Typer(
    name="chronicle-export",
    help="Chronicle Stack security-aware export profiles.",
    no_args_is_help=True,
)


@export_app.callback()
def export_root() -> None:
    """Inspect and run security-aware export helpers."""


class ProfileExportFormat(StrEnum):
    YAML = "yaml"
    HTML = "html"


def _record_profile_export_audit(
    *,
    profile: ExportProfile,
    format: ProfileExportFormat,
    output: Path | None,
    redaction: RedactionOptions,
) -> str | None:
    """Record a best-effort audit event for profile export.

    Audit insertion is fail-open with warning for v0.6-beta. The audit
    metadata records operation context only and must not copy exported body
    content.
    """
    try:
        event = AuditService().record(
            operation=AuditOperation.EXPORT,
            actor="chronicle-export",
            purpose=f"security-aware profile export: {profile.value}",
            target_environment=AuditTargetEnvironment.FILE if output else AuditTargetEnvironment.LOCAL,
            result=AuditSeverity.INFO,
            summary=f"Exported {format.value} using {profile.value} profile.",
            metadata={
                "format": format.value,
                "profile": profile.value,
                "redact_sensitive": str(redaction.redact_sensitive).lower(),
                "exclude_sensitive": str(redaction.exclude_sensitive).lower(),
                "output_path": str(output) if output else "",
            },
        )
        return event.audit_id
    except Exception as exc:  # pragma: no cover - defensive fail-open path
        typer.echo(f"Warning: audit insertion failed: {exc}", err=True)
        return None


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

    audit_id = _record_profile_export_audit(
        profile=profile,
        format=format,
        output=output,
        redaction=redaction,
    )

    if output:
        if json_output:
            typer.echo(json.dumps({
                "output": str(output),
                "format": format.value,
                "profile": profile.value,
                "redact_sensitive": redaction.redact_sensitive,
                "exclude_sensitive": redaction.exclude_sensitive,
                "audit_id": audit_id,
            }))
        else:
            typer.echo(f"Exported to {output}")
    elif not json_output:
        typer.echo(content)


if __name__ == "__main__":
    export_app()
