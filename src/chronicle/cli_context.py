"""Auxiliary CLI for model-context dry-run checks."""

import json
from typing import Annotated

import typer

from chronicle.models.context_use import ContextUseSeverity, ContextUseTarget
from chronicle.services.context_use_service import ContextUseService

context_app = typer.Typer(
    name="chronicle-context",
    help="Chronicle Stack model-context dry-run checks.",
    no_args_is_help=True,
)


@context_app.command("check")
def context_check_cmd(
    target: Annotated[ContextUseTarget, typer.Option("--target", help="Target environment: local or external.")],
    purpose: Annotated[str, typer.Option("--purpose", help="Purpose for model-context use.")],
    context_id: Annotated[list[str] | None, typer.Option("--context", help="Context ID to check. Repeatable. If omitted, all contexts are checked.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Dry-run check for using Context records as model context.

    This command does not submit records to any model service.
    """
    report = ContextUseService().check(target=target, purpose=purpose, context_ids=context_id)
    if json_output:
        typer.echo(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        typer.echo("Chronicle Context Use Check")
        typer.echo(f"Status: {report.status.value}")
        typer.echo(f"Target: {report.target.value}")
        typer.echo(f"Purpose: {report.purpose}")
        typer.echo(f"Contexts checked: {report.context_count}")
        typer.echo("")
        for finding in report.findings:
            typer.echo(f"[{finding.severity.value}] {finding.context_id}: {finding.summary}")
            if finding.title:
                typer.echo(f"  Title: {finding.title}")
            if finding.detail:
                typer.echo(f"  Detail: {finding.detail}")
            if finding.recommendation:
                typer.echo(f"  Recommendation: {finding.recommendation}")

    if report.status == ContextUseSeverity.BLOCKED:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    context_app()
