"""Boundary rule commands for the primary Chronicle CLI."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService


boundary_app = typer.Typer(help="Boundary rule operations.")


@boundary_app.command("add")
def boundary_add_cmd(
    type: Annotated[BoundaryRuleType, typer.Option("--type", help="Rule type: include, exclude, warn.")],
    field: Annotated[BoundaryConditionField, typer.Option("--field", help="Field to evaluate.")],
    operator: Annotated[
        BoundaryOperator,
        typer.Option("--operator", help="Operator: equals, not_equals, in, contains."),
    ],
    value: Annotated[list[str], typer.Option("--value", help="Value(s) to match.")],
    reason: Annotated[str, typer.Option("--reason")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Add a Context Boundary Rule."""
    try:
        val = value[0] if len(value) == 1 else value
        rule = BoundaryService().add_rule(
            rule_type=type,
            field=field,
            operator=operator,
            value=val,
            reason=reason,
        )
        if json_output:
            typer.echo(json.dumps(rule.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Boundary rule added: {rule.rule_id} ({rule.rule_type.value})")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@boundary_app.command("list")
def boundary_list_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List all Boundary Rules."""
    try:
        rules = BoundaryService().list_rules()
        if json_output:
            typer.echo(json.dumps([r.model_dump(mode="json") for r in rules], ensure_ascii=False, indent=2))
        else:
            if not rules:
                typer.echo("No boundary rules found.")
                return
            for rule in rules:
                val = rule.value if isinstance(rule.value, str) else ", ".join(rule.value)
                typer.echo(
                    f"{rule.rule_id}  {rule.rule_type.value}  "
                    f"{rule.field.value} {rule.operator.value} {val}"
                )
    except ChronicleError as exc:
        handle_error(exc, json_output)


@boundary_app.command("check")
def boundary_check_cmd(
    context: Annotated[str, typer.Option("--context", help="Context ID to evaluate.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Evaluate Boundary Rules against a Context."""
    try:
        chronicle = ChronicleService()
        chronicle.require_initialized()
        contexts = chronicle.index.load_contexts()
        if context not in contexts:
            typer.echo(f"Context not found: {context}", err=True)
            raise typer.Exit(code=1)
        results = BoundaryService().evaluate_context(contexts[context])
        if json_output:
            typer.echo(json.dumps([r.model_dump(mode="json") for r in results], ensure_ascii=False, indent=2))
        else:
            matched = [r for r in results if r.matched]
            if not matched:
                typer.echo("No boundary rules matched.")
                return
            for result in matched:
                typer.echo(f"[{result.rule_type.value}] {result.rule_id}: {result.reason}")
    except ChronicleError as exc:
        handle_error(exc, json_output)
