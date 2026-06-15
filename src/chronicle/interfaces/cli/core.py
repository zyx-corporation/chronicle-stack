"""Core root commands for the primary Chronicle CLI."""

import json
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error, source_from_options
from chronicle.models.context import ContextScope
from chronicle.models.event import Actor, EventType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.search_service import SearchService


def register_core_commands(app: typer.Typer) -> None:
    """Register root-level core commands."""

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
            handle_error(exc, json_output)

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
            source = source_from_options(
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
            handle_error(exc, json_output)

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
            source = source_from_options(
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
            handle_error(exc, json_output)

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
            handle_error(exc, json_output)

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
            handle_error(exc, json_output)
