"""Chronicle CLI — primary interface for Chronicle Core."""
# ruff: noqa: E501, I001

import json
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version as _package_version
from pathlib import Path
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.exporters.injection_plan_report import format_injection_plan
from chronicle.exporters.markdown_exporter import MarkdownExporter
from chronicle.exporters.yaml_exporter import YamlExporter
from chronicle.models.artifact import ArtifactType
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.context import ContextScope
from chronicle.models.decision import DecisionType
from chronicle.models.doctor import DoctorSeverity
from chronicle.models.event import Actor, EventType
from chronicle.models.source import SourceProvenance
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.decision_service import DecisionService
from chronicle.services.doctor_service import DoctorService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.injection_service import InjectionPlanService
from chronicle.services.rde_service import RdeService
from chronicle.services.search_service import SearchService


def _version_callback(value: bool) -> None:
    if value:
        try:
            v = _package_version("chronicle-stack")
        except PackageNotFoundError:
            v = "0.0.0+unknown"
        typer.echo(f"chronicle {v}")
        raise typer.Exit()


app = typer.Typer(
    name="chronicle",
    help=(
        "Chronicle Stack — local-first record of context, artifacts,"
        " decisions, diffs, provenance, and boundary rules."
    ),
    no_args_is_help=True,
)
artifact_app = typer.Typer(help="Artifact operations.")
decision_app = typer.Typer(help="Decision operations.")
rde_app = typer.Typer(help="RDE Diff Record operations.")
index_app = typer.Typer(help="Index operations.")
boundary_app = typer.Typer(help="Boundary rule operations.")
injection_app = typer.Typer(help="Context injection planning operations.")
app.add_typer(artifact_app, name="artifact")
app.add_typer(decision_app, name="decision")
app.add_typer(rde_app, name="rde")
app.add_typer(index_app, name="index")
app.add_typer(boundary_app, name="boundary")
app.add_typer(injection_app, name="injection")


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


class ExportFormat(StrEnum):
    YAML = "yaml"
    MARKDOWN = "markdown"
    GRAPH_JSON = "graph-json"
    HTML = "html"


def _handle_error(exc: ChronicleError, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(exc.to_dict(), ensure_ascii=False))
    else:
        typer.echo(str(exc), err=True)
    raise typer.Exit(code=1)


def _source_from_options(
    *,
    source_type: str | None = None,
    source_ref: str | None = None,
    source_tool: str | None = None,
    source_session: str | None = None,
    source_model: str | None = None,
    source_file: str | None = None,
    source_url: str | None = None,
) -> SourceProvenance | None:
    if not any([
        source_type,
        source_ref,
        source_tool,
        source_session,
        source_model,
        source_file,
        source_url,
    ]):
        return None
    return SourceProvenance(
        source_type=source_type or "unknown",
        source_ref=source_ref or "",
        source_tool=source_tool,
        source_session=source_session,
        source_model=source_model,
        source_file=source_file,
        source_url=source_url,
    )


@app.command("doctor")
def doctor_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Run read-only health checks for the current Chronicle."""
    report = DoctorService().run()
    if json_output:
        typer.echo(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        typer.echo("Chronicle Doctor")
        typer.echo("")
        typer.echo(f"Status: {report.status.value}")
        if report.chronicle_id:
            typer.echo(f"Chronicle ID: {report.chronicle_id}")
        typer.echo("")
        for check in report.checks:
            typer.echo(f"[{check.severity.value}] {check.check_id}: {check.summary}")
            if check.detail:
                typer.echo(f"  Detail: {check.detail}")
            if check.recommendation:
                typer.echo(f"  Recommendation: {check.recommendation}")

    if report.status == DoctorSeverity.ERROR:
        raise typer.Exit(code=1)


@app.command("init")
def init_cmd(
    title: Annotated[str, typer.Option("--title", help="Chronicle title.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a new Chronicle in the current directory."""
    try:
        metadata = ChronicleService().init(title)
        if json_output:
            typer.echo(json.dumps(metadata.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Chronicle created: {metadata.title}")
            typer.echo(f"  ID: {metadata.chronicle_id}")
            typer.echo("  Path: .chronicle/")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("add-context")
def add_context_cmd(
    title: Annotated[str, typer.Option("--title")],
    summary: Annotated[str, typer.Option("--summary")] = "",
    source_type: Annotated[str, typer.Option("--source-type")] = "conversation",
    scope: Annotated[
        ContextScope,
        typer.Option("--scope", help="Context scope: global, project, session, task, artifact, temporary."),
    ] = ContextScope.PROJECT,
    visibility: Annotated[
        VisibilityHint,
        typer.Option("--visibility", help="Visibility hint: public, private, sensitive, unknown."),
    ] = VisibilityHint.UNKNOWN,
    source_ref: Annotated[str | None, typer.Option("--source-ref")] = None,
    source_tool: Annotated[str | None, typer.Option("--source-tool")] = None,
    source_session: Annotated[str | None, typer.Option("--source-session")] = None,
    source_model: Annotated[str | None, typer.Option("--source-model")] = None,
    source_file: Annotated[str | None, typer.Option("--source-file")] = None,
    source_url: Annotated[str | None, typer.Option("--source-url")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Add a Context to the Chronicle."""
    try:
        source = _source_from_options(
            source_type=source_type,
            source_ref=source_ref,
            source_tool=source_tool,
            source_session=source_session,
            source_model=source_model,
            source_file=source_file,
            source_url=source_url,
        )
        context = ContextService().add_context(
            title=title,
            summary=summary,
            source_type=source_type,
            source_ref=source_ref or "",
            scope=scope,
            visibility_hint=visibility,
            source=source,
        )
        if json_output:
            typer.echo(json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Context added: {context.title} ({context.context_id})")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("record")
def record_cmd(
    type: Annotated[EventType, typer.Option("--type")],
    actor: Annotated[Actor, typer.Option("--actor")],
    summary: Annotated[str, typer.Option("--summary")],
    source_type: Annotated[str | None, typer.Option("--source-type")] = None,
    source_ref: Annotated[str | None, typer.Option("--source-ref")] = None,
    source_tool: Annotated[str | None, typer.Option("--source-tool")] = None,
    source_session: Annotated[str | None, typer.Option("--source-session")] = None,
    source_model: Annotated[str | None, typer.Option("--source-model")] = None,
    source_file: Annotated[str | None, typer.Option("--source-file")] = None,
    source_url: Annotated[str | None, typer.Option("--source-url")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record an arbitrary Chronicle Event."""
    try:
        source = _source_from_options(
            source_type=source_type,
            source_ref=source_ref,
            source_tool=source_tool,
            source_session=source_session,
            source_model=source_model,
            source_file=source_file,
            source_url=source_url,
        )
        event = ChronicleService().record_event(event_type=type, actor=actor, summary=summary, source=source)
        if json_output:
            typer.echo(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Event recorded: {event.event_id} ({event.event_type.value})")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@artifact_app.command("create")
def artifact_create_cmd(
    title: Annotated[str, typer.Option("--title")],
    type: Annotated[ArtifactType, typer.Option("--type")],
    file: Annotated[Path | None, typer.Option("--file")] = None,
    visibility: Annotated[
        VisibilityHint,
        typer.Option("--visibility", help="Visibility hint: public, private, sensitive, unknown."),
    ] = VisibilityHint.UNKNOWN,
    source_type: Annotated[str | None, typer.Option("--source-type")] = None,
    source_ref: Annotated[str | None, typer.Option("--source-ref")] = None,
    source_tool: Annotated[str | None, typer.Option("--source-tool")] = None,
    source_session: Annotated[str | None, typer.Option("--source-session")] = None,
    source_model: Annotated[str | None, typer.Option("--source-model")] = None,
    source_url: Annotated[str | None, typer.Option("--source-url")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a new Artifact."""
    try:
        source = _source_from_options(
            source_type=source_type,
            source_ref=source_ref,
            source_tool=source_tool,
            source_session=source_session,
            source_model=source_model,
            source_url=source_url,
        )
        artifact, version = ArtifactService().create(
            title=title,
            artifact_type=type,
            source_file=file,
            visibility_hint=visibility,
            source=source,
        )
        if json_output:
            typer.echo(json.dumps(
                {
                    "artifact": artifact.model_dump(mode="json"),
                    "version": version.model_dump(mode="json"),
                },
                ensure_ascii=False,
                indent=2,
            ))
        else:
            typer.echo(f"Artifact created: {artifact.title} ({artifact.artifact_id})")
            typer.echo(f"  Version: {version.version_id}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@artifact_app.command("update")
def artifact_update_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    file: Annotated[Path | None, typer.Option("--file")] = None,
    summary: Annotated[str, typer.Option("--summary")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Update an Artifact and create a new Version."""
    try:
        updated, version = ArtifactService().update(
            artifact_id=artifact,
            source_file=file,
            summary=summary,
        )
        if json_output:
            typer.echo(json.dumps(
                {
                    "artifact": updated.model_dump(mode="json"),
                    "version": version.model_dump(mode="json"),
                },
                ensure_ascii=False,
                indent=2,
            ))
        else:
            typer.echo(f"Artifact updated: {updated.title}")
            typer.echo(f"  New version: {version.version_id}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@artifact_app.command("history")
def artifact_history_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show Artifact version history."""
    try:
        art, versions = ArtifactService().history(artifact)
        if json_output:
            typer.echo(json.dumps(
                {
                    "artifact": art.model_dump(mode="json"),
                    "versions": [v.model_dump(mode="json") for v in versions],
                },
                ensure_ascii=False,
                indent=2,
            ))
        else:
            typer.echo(f"Artifact: {art.title}")
            typer.echo("")
            for ver in versions:
                ts = ver.created_at.strftime("%Y-%m-%d %H:%M")
                typer.echo(f"{ver.version_id}  {ts}  {ver.change_summary}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@artifact_app.command("list")
def artifact_list_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """List all Artifacts."""
    try:
        artifacts = ArtifactService().list_artifacts()
        if json_output:
            typer.echo(json.dumps([a.model_dump(mode="json") for a in artifacts], ensure_ascii=False, indent=2))
        else:
            if not artifacts:
                typer.echo("No artifacts found.")
                return
            for art in artifacts:
                typer.echo(f"{art.artifact_id}  {art.title}  ({art.artifact_type.value})")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@decision_app.command("record")
def decision_record_cmd(
    type: Annotated[DecisionType, typer.Option("--type")],
    reason: Annotated[str, typer.Option("--reason")] = "",
    artifact: Annotated[str | None, typer.Option("--artifact")] = None,
    alternative: Annotated[list[str] | None, typer.Option("--alternative")] = None,
    notes: Annotated[str, typer.Option("--notes")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a Decision."""
    try:
        decision = DecisionService().record(
            decision_type=type,
            reason=reason,
            artifact_id=artifact,
            alternatives=alternative,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(decision.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Decision recorded: {decision.decision_id} ({decision.decision_type.value})")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@rde_app.command("record")
def rde_record_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    from_version: Annotated[str, typer.Option("--from")],
    to_version: Annotated[str, typer.Option("--to")],
    summary: Annotated[str, typer.Option("--summary")] = "",
    preserved: Annotated[list[str] | None, typer.Option("--preserved")] = None,
    transformed: Annotated[list[str] | None, typer.Option("--transformed")] = None,
    supplemented: Annotated[list[str] | None, typer.Option("--supplemented")] = None,
    unresolved: Annotated[list[str] | None, typer.Option("--unresolved")] = None,
    deviation_risk: Annotated[list[str] | None, typer.Option("--deviation-risk")] = None,
    next_update_policy: Annotated[list[str] | None, typer.Option("--next-update-policy")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create an RDE Diff Record."""
    try:
        record = RdeService().record(
            artifact_id=artifact,
            from_version_id=from_version,
            to_version_id=to_version,
            summary=summary,
            preserved=preserved or [],
            transformed=transformed or [],
            supplemented=supplemented or [],
            unresolved=unresolved or [],
            deviation_risks=deviation_risk or [],
            next_update_policy=next_update_policy or [],
        )
        if json_output:
            typer.echo(json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"RDE record created: {record.rde_record_id}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("show")
def show_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Show Chronicle overview."""
    try:
        info = ChronicleService().show()
        if json_output:
            typer.echo(json.dumps(
                {
                    "metadata": info["metadata"].model_dump(mode="json"),
                    "event_count": info["event_count"],
                    "artifact_count": info["artifact_count"],
                    "context_count": info["context_count"],
                    "decision_count": info["decision_count"],
                    "corrupt_lines": info["corrupt_lines"],
                },
                ensure_ascii=False,
                indent=2,
            ))
        else:
            meta = info["metadata"]
            typer.echo(f"Chronicle: {meta.title}")
            typer.echo(f"  ID: {meta.chronicle_id}")
            typer.echo(f"  Events: {info['event_count']}")
            typer.echo(f"  Artifacts: {info['artifact_count']}")
            typer.echo(f"  Contexts: {info['context_count']}")
            typer.echo(f"  Decisions: {info['decision_count']}")
            if info["corrupt_lines"]:
                typer.echo(f"  Warning: {info['corrupt_lines']} corrupt JSONL line(s)")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("search")
def search_cmd(
    query: Annotated[str, typer.Argument(help="Search query.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Search events, artifacts, decisions, and contexts."""
    try:
        results = SearchService().search(query)
        if json_output:
            typer.echo(json.dumps(
                [
                    {
                        "kind": r.kind,
                        "identifier": r.identifier,
                        "summary": r.summary,
                        "detail": r.detail,
                    }
                    for r in results
                ],
                ensure_ascii=False,
                indent=2,
            ))
        else:
            if not results:
                typer.echo("No results found.")
                return
            for result in results:
                typer.echo(f"[{result.kind}] {result.identifier}: {result.summary}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("export")
def export_cmd(
    format: Annotated[ExportFormat, typer.Option("--format")] = ExportFormat.YAML,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Export Chronicle to YAML, Markdown, Graph JSON, or HTML."""
    try:
        if format == ExportFormat.YAML:
            content = YamlExporter().export(output=output)
        elif format == ExportFormat.GRAPH_JSON:
            graph = GraphExportService().export_graph()
            content = json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, indent=2)
            if output:
                output.write_text(content, encoding="utf-8")
        elif format == ExportFormat.HTML:
            content = HtmlDashboardExporter().export()
            if output:
                output.write_text(content, encoding="utf-8")
        else:
            content = MarkdownExporter().export(output=output)

        if output:
            if json_output:
                typer.echo(json.dumps({"output": str(output), "format": format.value}))
            else:
                typer.echo(f"Exported to {output}")
        elif not json_output:
            typer.echo(content)
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@index_app.command("rebuild")
def index_rebuild_cmd(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Rebuild derived indexes from chronicle.jsonl."""
    try:
        service = ChronicleService()
        service.require_initialized()
        service.rebuild_indexes()
        if json_output:
            typer.echo(json.dumps({"status": "ok", "message": "Indexes rebuilt."}))
        else:
            typer.echo("Indexes rebuilt successfully.")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


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
        _handle_error(exc, json_output)


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
        _handle_error(exc, json_output)


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
        _handle_error(exc, json_output)


@injection_app.command("plan")
def injection_plan_cmd(
    task: Annotated[str, typer.Option("--task", help="Task description for context selection.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    record: Annotated[
        bool,
        typer.Option("--record", help="Persist the plan to chronicle.jsonl."),
    ] = False,
) -> None:
    """Generate a Context Injection Plan for a task."""
    try:
        service = InjectionPlanService()
        plan = service.generate_plan(task)
        event_id = None
        if record:
            event = service.record_plan(plan)
            event_id = event.event_id
        if json_output:
            output = {"plan": plan.model_dump(mode="json"), "recorded": record, "event_id": event_id}
            typer.echo(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            typer.echo(format_injection_plan(plan))
            if record:
                typer.echo(f"\nRecorded as event: {event_id}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


if __name__ == "__main__":
    app()
