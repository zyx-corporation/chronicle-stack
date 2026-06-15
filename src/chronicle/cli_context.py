"""Auxiliary CLI for model-context dry-run checks and context metadata workflows."""

import json
from typing import Annotated

import typer

from chronicle.models.classification import ClassificationLayer, Sensitivity
from chronicle.models.context_use import ContextUseSeverity, ContextUseTarget
from chronicle.services.context_service import ContextService
from chronicle.services.context_use_service import ContextUseService

context_app = typer.Typer(
    name="chronicle-context",
    help="Chronicle Stack model-context dry-run checks and context metadata workflows.",
    no_args_is_help=True,
)

classification_app = typer.Typer(
    help="Advisory Context classification metadata workflows.",
    no_args_is_help=True,
)


def _parse_layer(value: str) -> ClassificationLayer:
    try:
        return ClassificationLayer(int(value))
    except ValueError:
        normalized = value.upper()
        if normalized in ClassificationLayer.__members__:
            return ClassificationLayer[normalized]
    raise typer.BadParameter("layer must be one of 0,1,2,3,4 or PUBLIC,SHAREABLE,INTERNAL,SENSITIVE_CONTEXT,RESTRICTED_SECRET")


def _parse_sensitivity(value: str) -> Sensitivity:
    normalized = value.lower()
    for sensitivity in Sensitivity:
        if sensitivity.value == normalized or sensitivity.name.lower() == normalized:
            return sensitivity
    raise typer.BadParameter("sensitivity must be public, shareable, internal, sensitive, restricted, or unknown")


@context_app.command("check")
def context_check_cmd(
    target: Annotated[ContextUseTarget, typer.Option("--target", help="Target environment: local or external.")],
    purpose: Annotated[str, typer.Option("--purpose", help="Purpose for model-context use.")],
    context_id: Annotated[list[str] | None, typer.Option("--context", help="Context ID to check. Repeatable. If omitted, all contexts are checked.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False
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


@classification_app.command("missing")
def classification_missing_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List Context records without advisory classification metadata."""
    contexts = ContextService().list_missing_classification()
    if json_output:
        typer.echo(json.dumps([context.model_dump(mode="json") for context in contexts], ensure_ascii=False, indent=2))
        return
    if not contexts:
        typer.echo("All Context records have classification metadata.")
        return
    for context in contexts:
        typer.echo(f"{context.context_id}: {context.title}")


@classification_app.command("show")
def classification_show_cmd(
    context_id: Annotated[str, typer.Option("--context", help="Context ID to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show advisory classification metadata for a Context record."""
    context = ContextService().get_context(context_id)
    payload = context.classification.model_dump(mode="json") if context.classification else None
    if json_output:
        typer.echo(json.dumps({"context_id": context.context_id, "classification": payload}, ensure_ascii=False, indent=2))
        return
    typer.echo(f"Context: {context.context_id}")
    typer.echo(f"Title: {context.title}")
    if context.classification is None:
        typer.echo("Classification: missing")
        return
    typer.echo(f"Layer: {context.classification.layer.name} ({context.classification.layer.value})")
    typer.echo(f"Sensitivity: {context.classification.sensitivity.value}")
    if context.classification.owner:
        typer.echo(f"Owner: {context.classification.owner}")


@classification_app.command("set")
def classification_set_cmd(
    context_id: Annotated[str, typer.Option("--context", help="Context ID to classify.")],
    layer: Annotated[str, typer.Option("--layer", help="Layer: 0-4 or enum name.")] = "internal",
    sensitivity: Annotated[str, typer.Option("--sensitivity", help="Sensitivity label.")] = "internal",
    owner: Annotated[str, typer.Option("--owner", help="Optional owner label.")] = "",
    reason: Annotated[str, typer.Option("--reason", help="Optional classification reason.")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Attach advisory classification metadata to a Context record.

    This records a new Context snapshot with the same context_id. It does not
    implement access control or external policy enforcement.
    """
    context = ContextService().classify_context(
        context_id=context_id,
        layer=_parse_layer(layer),
        sensitivity=_parse_sensitivity(sensitivity),
        owner=owner,
        reason=reason,
    )
    if json_output:
        typer.echo(json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        typer.echo(f"Context classified: {context.context_id}")
        typer.echo("Boundary: classification metadata is advisory, not access control.")


context_app.add_typer(classification_app, name="classification")


if __name__ == "__main__":
    context_app()
