"""Auxiliary CLI for controlled integration packages."""

import json
from pathlib import Path
from typing import Annotated

import typer

from chronicle.models.integration_package import IntegrationTargetEnvironment
from chronicle.services.integration_package_service import IntegrationPackageService

package_app = typer.Typer(
    name="chronicle-package",
    help="Chronicle Stack controlled integration package contracts.",
    no_args_is_help=True,
)


@package_app.command("context")
def context_package_cmd(
    purpose: Annotated[str, typer.Option("--purpose", help="Purpose for building the package.")],
    target: Annotated[IntegrationTargetEnvironment, typer.Option("--target", help="Target environment: local or external.")] = IntegrationTargetEnvironment.LOCAL,
    context_id: Annotated[list[str] | None, typer.Option("--context", help="Context ID to include. Repeatable. If omitted, all contexts are included.")] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    """Build a controlled context package.

    This command does not call models, graph databases, vector databases, or
    external runtimes.
    """
    package = IntegrationPackageService().build_context_package(
        purpose=purpose,
        target_environment=target,
        context_ids=context_id,
    )
    payload = json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if output:
        output.write_text(payload, encoding="utf-8")
        typer.echo(f"Package written to {output}")
    else:
        typer.echo(payload)


if __name__ == "__main__":
    package_app()
