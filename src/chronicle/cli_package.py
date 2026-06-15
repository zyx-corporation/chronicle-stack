"""Auxiliary CLI for controlled integration packages."""

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from chronicle.models.integration_package import IntegrationPackageRecord, IntegrationTargetEnvironment
from chronicle.services.integration_package_service import IntegrationPackageService

package_app = typer.Typer(
    name="chronicle-package",
    help="Chronicle Stack controlled integration package contracts.",
    no_args_is_help=True,
)


def _record_summary(record: IntegrationPackageRecord) -> dict[str, Any]:
    """Return a package record summary without body content."""
    return {
        "record_id": record.record_id,
        "record_kind": record.record_kind,
        "title": record.title,
        "classification_layer": record.classification_layer,
        "sensitivity": record.sensitivity,
        "allowed_operations": record.allowed_operations,
        "content_boundary": record.content_boundary.value,
        "has_content": record.content is not None,
        "warnings": record.warnings,
        "metadata": record.metadata,
    }


@package_app.command("context")
def context_package_cmd(
    purpose: Annotated[str, typer.Option("--purpose", help="Purpose for building the package.")],
    target: Annotated[IntegrationTargetEnvironment, typer.Option("--target", help="Target environment: local or external.")] = IntegrationTargetEnvironment.LOCAL,
    context_id: Annotated[list[str] | None, typer.Option("--context", help="Context ID to include. Repeatable. If omitted, all contexts are included.")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    persist: Annotated[bool, typer.Option("--persist", help="Persist the package under .chronicle/packages.")] = False,
) -> None:
    """Build a controlled context package.

    This command does not call models, graph databases, vector databases, or
    external runtimes.
    """
    service = IntegrationPackageService()
    package = service.build_context_package(
        purpose=purpose,
        target_environment=target,
        context_ids=context_id,
    )
    if persist:
        package_dir = service.save_package(package)
        typer.echo(f"Package persisted: {package.manifest.package_id}")
        typer.echo(f"  Path: {package_dir}")
        return

    payload = json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if output:
        output.write_text(payload, encoding="utf-8")
        typer.echo(f"Package written to {output}")
    else:
        typer.echo(payload)


@package_app.command("list")
def list_packages_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List persisted integration packages."""
    manifests = IntegrationPackageService().list_package_manifests()
    if json_output:
        typer.echo(json.dumps([manifest.model_dump(mode="json") for manifest in manifests], ensure_ascii=False, indent=2))
        return

    if not manifests:
        typer.echo("No persisted packages found.")
        return

    for manifest in manifests:
        typer.echo(
            f"{manifest.package_id}  {manifest.package_kind.value}  "
            f"{manifest.output_classification}  {len(manifest.referenced_records)} record(s)"
        )


@package_app.command("show")
def show_package_cmd(
    package: Annotated[str, typer.Option("--package", help="Package ID to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show a persisted package manifest."""
    manifest = IntegrationPackageService().load_package_manifest(package)
    if json_output:
        typer.echo(json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return

    typer.echo(f"Package: {manifest.package_id}")
    typer.echo(f"  Kind: {manifest.package_kind.value}")
    typer.echo(f"  Purpose: {manifest.purpose}")
    typer.echo(f"  Target: {manifest.target_environment.value}")
    typer.echo(f"  Output classification: {manifest.output_classification}")
    typer.echo(f"  Referenced records: {len(manifest.referenced_records)}")
    if manifest.warnings:
        typer.echo(f"  Warnings: {', '.join(manifest.warnings)}")


@package_app.command("records")
def package_records_cmd(
    package: Annotated[str, typer.Option("--package", help="Package ID to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show persisted package record summaries without body content."""
    records = IntegrationPackageService().load_package_records(package)
    summaries = [_record_summary(record) for record in records]
    if json_output:
        typer.echo(json.dumps(summaries, ensure_ascii=False, indent=2))
        return

    if not summaries:
        typer.echo("No records found.")
        return

    for summary in summaries:
        typer.echo(
            f"{summary['record_id']}  {summary['record_kind']}  "
            f"{summary['content_boundary']}  has_content={summary['has_content']}"
        )
        if summary["warnings"]:
            typer.echo(f"  Warnings: {', '.join(summary['warnings'])}")


if __name__ == "__main__":
    package_app()
