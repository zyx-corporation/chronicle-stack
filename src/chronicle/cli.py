"""Chronicle CLI — primary interface for Chronicle Core v0.1."""

import json
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Optional

import typer

from chronicle.errors import ChronicleError
from chronicle.exporters.markdown_exporter import MarkdownExporter
from chronicle.exporters.yaml_exporter import YamlExporter
from chronicle.models.artifact import ArtifactType
from chronicle.models.context import ContextScope
from chronicle.models.decision import DecisionType
from chronicle.models.event import Actor, EventType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.decision_service import DecisionService
from chronicle.services.rde_service import RdeService
from chronicle.services.search_service import SearchService

app = typer.Typer(
    name="chronicle",
    help=(
        "Chronicle Core v0.1 —"
        " record context, artifacts, decisions, and diffs."
    ),
    no_args_is_help=True,
)
artifact_app = typer.Typer(help="Artifact operations.")
decision_app = typer.Typer(help="Decision operations.")
rde_app = typer.Typer(help="RDE Diff Record operations.")
index_app = typer.Typer(help="Index operations.")
app.add_typer(artifact_app, name="artifact")
app.add_typer(decision_app, name="decision")
app.add_typer(rde_app, name="rde")
app.add_typer(index_app, name="index")


class ExportFormat(StrEnum):
    YAML = "yaml"
    MARKDOWN = "markdown"


def _handle_error(exc: ChronicleError, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(exc.to_dict(), ensure_ascii=False))
    else:
        typer.echo(str(exc), err=True)
    raise typer.Exit(code=1)


@app.command("init")
def init_cmd(
    title: Annotated[str, typer.Option("--title", help="Chronicle title.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a new Chronicle in the current directory."""
    try:
        service = ChronicleService()
        metadata = service.init(title)
        if json_output:
            typer.echo(
                json.dumps(
                    metadata.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                )
            )
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
    source_type: Annotated[
        str, typer.Option("--source-type")
    ] = "conversation",
    scope: Annotated[
        ContextScope, typer.Option("--scope", help="Context scope: global, project, session, task, artifact, temporary.")
    ] = ContextScope.PROJECT,
    visibility: Annotated[
        VisibilityHint, typer.Option("--visibility", help="Visibility hint: public, private, sensitive, unknown.")
    ] = VisibilityHint.UNKNOWN,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Add a Context to the Chronicle."""
    try:
        service = ContextService()
        context = service.add_context(
            title=title,
            summary=summary,
            source_type=source_type,
            scope=scope,
            visibility_hint=visibility,
        )
        if json_output:
            typer.echo(
                json.dumps(
                    context.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            typer.echo(
                f"Context added: {context.title} ({context.context_id})"
            )
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("record")
def record_cmd(
    type: Annotated[EventType, typer.Option("--type")],
    actor: Annotated[Actor, typer.Option("--actor")],
    summary: Annotated[str, typer.Option("--summary")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record an arbitrary Chronicle Event."""
    try:
        service = ChronicleService()
        event = service.record_event(
            event_type=type, actor=actor, summary=summary
        )
        if json_output:
            typer.echo(
                json.dumps(
                    event.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            typer.echo(
                f"Event recorded: {event.event_id}"
                f" ({event.event_type.value})"
            )
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@artifact_app.command("create")
def artifact_create_cmd(
    title: Annotated[str, typer.Option("--title")],
    type: Annotated[ArtifactType, typer.Option("--type")],
    file: Annotated[Optional[Path], typer.Option("--file")] = None,
    visibility: Annotated[
        VisibilityHint, typer.Option("--visibility", help="Visibility hint: public, private, sensitive, unknown.")
    ] = VisibilityHint.UNKNOWN,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a new Artifact."""
    try:
        service = ArtifactService()
        artifact, version = service.create(
            title=title, artifact_type=type, source_file=file, visibility_hint=visibility
        )
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "artifact": artifact.model_dump(mode="json"),
                        "version": version.model_dump(mode="json"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            typer.echo(
                f"Artifact created: {artifact.title}"
                f" ({artifact.artifact_id})"
            )
            typer.echo(f"  Version: {version.version_id}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@artifact_app.command("update")
def artifact_update_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    file: Annotated[Optional[Path], typer.Option("--file")] = None,
    summary: Annotated[str, typer.Option("--summary")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Update an Artifact and create a new Version."""
    try:
        service = ArtifactService()
        updated, version = service.update(
            artifact_id=artifact, source_file=file, summary=summary
        )
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "artifact": updated.model_dump(mode="json"),
                        "version": version.model_dump(mode="json"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
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
        service = ArtifactService()
        art, versions = service.history(artifact)
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "artifact": art.model_dump(mode="json"),
                        "versions": [
                            v.model_dump(mode="json") for v in versions
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            typer.echo(f"Artifact: {art.title}")
            typer.echo("")
            for ver in versions:
                ts = ver.created_at.strftime("%Y-%m-%d %H:%M")
                typer.echo(
                    f"{ver.version_id}  {ts}  {ver.change_summary}"
                )
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@artifact_app.command("list")
def artifact_list_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List all Artifacts."""
    try:
        service = ArtifactService()
        artifacts = service.list_artifacts()
        if json_output:
            typer.echo(
                json.dumps(
                    [a.model_dump(mode="json") for a in artifacts],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            if not artifacts:
                typer.echo("No artifacts found.")
                return
            for art in artifacts:
                typer.echo(
                    f"{art.artifact_id}  {art.title}"
                    f"  ({art.artifact_type.value})"
                )
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@decision_app.command("record")
def decision_record_cmd(
    type: Annotated[DecisionType, typer.Option("--type")],
    reason: Annotated[str, typer.Option("--reason")] = "",
    artifact: Annotated[
        Optional[str], typer.Option("--artifact")
    ] = None,
    alternative: Annotated[
        Optional[list[str]], typer.Option("--alternative")
    ] = None,
    notes: Annotated[str, typer.Option("--notes")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a Decision."""
    try:
        service = DecisionService()
        decision = service.record(
            decision_type=type,
            reason=reason,
            artifact_id=artifact,
            alternatives=alternative,
            notes=notes,
        )
        if json_output:
            typer.echo(
                json.dumps(
                    decision.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            typer.echo(
                f"Decision recorded: {decision.decision_id}"
                f" ({decision.decision_type.value})"
            )
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@rde_app.command("record")
def rde_record_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    from_version: Annotated[str, typer.Option("--from")],
    to_version: Annotated[str, typer.Option("--to")],
    summary: Annotated[str, typer.Option("--summary")] = "",
    preserved: Annotated[Optional[list[str]], typer.Option("--preserved")] = None,
    transformed: Annotated[Optional[list[str]], typer.Option("--transformed")] = None,
    supplemented: Annotated[Optional[list[str]], typer.Option("--supplemented")] = None,
    unresolved: Annotated[Optional[list[str]], typer.Option("--unresolved")] = None,
    deviation_risk: Annotated[Optional[list[str]], typer.Option("--deviation-risk")] = None,
    next_update_policy: Annotated[Optional[list[str]], typer.Option("--next-update-policy")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create an RDE Diff Record."""
    try:
        service = RdeService()
        record = service.record(
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
            typer.echo(
                json.dumps(
                    record.model_dump(mode="json"),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            typer.echo(f"RDE record created: {record.rde_record_id}")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("show")
def show_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show Chronicle overview."""
    try:
        service = ChronicleService()
        info = service.show()
        if json_output:
            typer.echo(
                json.dumps(
                    {
                        "metadata": info["metadata"].model_dump(
                            mode="json"
                        ),
                        "event_count": info["event_count"],
                        "artifact_count": info["artifact_count"],
                        "context_count": info["context_count"],
                        "decision_count": info["decision_count"],
                        "corrupt_lines": info["corrupt_lines"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            meta = info["metadata"]
            typer.echo(f"Chronicle: {meta.title}")
            typer.echo(f"  ID: {meta.chronicle_id}")
            typer.echo(f"  Events: {info['event_count']}")
            typer.echo(f"  Artifacts: {info['artifact_count']}")
            typer.echo(f"  Contexts: {info['context_count']}")
            typer.echo(f"  Decisions: {info['decision_count']}")
            if info["corrupt_lines"]:
                typer.echo(
                    f"  Warning: {info['corrupt_lines']}"
                    " corrupt JSONL line(s)"
                )
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("search")
def search_cmd(
    query: Annotated[str, typer.Argument(help="Search query.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Search events, artifacts, decisions, and contexts."""
    try:
        service = SearchService()
        results = service.search(query)
        if json_output:
            typer.echo(
                json.dumps(
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
                )
            )
        else:
            if not results:
                typer.echo("No results found.")
                return
            for result in results:
                typer.echo(
                    f"[{result.kind}] {result.identifier}:"
                    f" {result.summary}"
                )
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@app.command("export")
def export_cmd(
    format: Annotated[
        ExportFormat, typer.Option("--format")
    ] = ExportFormat.YAML,
    output: Annotated[
        Optional[Path], typer.Option("--output", "-o")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Export Chronicle to YAML or Markdown."""
    try:
        if format == ExportFormat.YAML:
            content = YamlExporter().export(output=output)
        else:
            content = MarkdownExporter().export(output=output)

        if output:
            if json_output:
                typer.echo(
                    json.dumps(
                        {"output": str(output), "format": format.value}
                    )
                )
            else:
                typer.echo(f"Exported to {output}")
        elif not json_output:
            typer.echo(content)
    except ChronicleError as exc:
        _handle_error(exc, json_output)


@index_app.command("rebuild")
def index_rebuild_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Rebuild derived indexes from chronicle.jsonl."""
    try:
        service = ChronicleService()
        service.require_initialized()
        service.rebuild_indexes()
        if json_output:
            typer.echo(
                json.dumps({"status": "ok", "message": "Indexes rebuilt."})
            )
        else:
            typer.echo("Indexes rebuilt successfully.")
    except ChronicleError as exc:
        _handle_error(exc, json_output)


if __name__ == "__main__":
    app()
