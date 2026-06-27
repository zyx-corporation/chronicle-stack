"""Artifact commands for the primary Chronicle CLI."""

import json
from pathlib import Path
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error, source_from_options
from chronicle.models.artifact import ArtifactType
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.proposal_service import ProposalService

artifact_app = typer.Typer(help="Artifact operations.")


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
        source = source_from_options(
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
        handle_error(exc, json_output)


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
        handle_error(exc, json_output)


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
        handle_error(exc, json_output)


@artifact_app.command("propose-update")
def artifact_propose_update_cmd(
    artifact: Annotated[str, typer.Option("--artifact")],
    summary: Annotated[str, typer.Option("--summary")] = "",
    file: Annotated[Path | None, typer.Option("--file")] = None,
    content: Annotated[str | None, typer.Option("--content")] = None,
    title: Annotated[str, typer.Option("--title")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record an append-only artifact update proposal."""
    try:
        event = ProposalService().propose_artifact_update(
            artifact_id=artifact,
            summary=summary,
            source_file=file,
            content=content,
            proposed_title=title,
        )
        if json_output:
            typer.echo(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Artifact proposal recorded: {event.event_id}")
            typer.echo("  Review queue target created with needs_review status")
    except ChronicleError as exc:
        handle_error(exc, json_output)


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
        handle_error(exc, json_output)
