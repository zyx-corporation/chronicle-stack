"""Federation message CLI surfaces."""

import json
from datetime import datetime
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.federation_message import (
    FederationMessageBox,
    FederationMessageSignatureStatus,
    FederationMessageType,
)
from chronicle.services.federation_message_service import FederationMessageService

federation_app = typer.Typer(help="Federation package/message operations.")
message_app = typer.Typer(help="Federation message creation.")
inbox_app = typer.Typer(help="Federation inbox inspection.")
outbox_app = typer.Typer(help="Federation outbox inspection.")


def _dump_record_summary(record) -> dict:
    envelope = record.envelope.model_dump(mode="json")
    return {
        "message_id": envelope["message_id"],
        "message_type": envelope["message_type"],
        "source_node": envelope["source_node"],
        "target_node": envelope["target_node"],
        "created_at": envelope["created_at"],
        "purpose": envelope["purpose"],
        "object_refs": envelope["object_refs"],
        "signature_status": envelope["signature_status"],
        "preview_only": envelope["preview_only"],
        "auto_apply": envelope["auto_apply"],
        "review_required": envelope["review_required"],
        "retention": envelope["policy"]["retention"],
        "reshare": envelope["policy"]["reshare"],
        "box": record.box.value,
        "stored_at": record.stored_at.isoformat(),
        "preview_summary": record.preview_summary,
        "audit_recorded": record.audit_recorded,
    }


@message_app.command("create")
def federation_message_create_cmd(
    type: Annotated[FederationMessageType, typer.Option("--type")],
    source_node: Annotated[str, typer.Option("--source-node")],
    target_node: Annotated[str, typer.Option("--target-node")],
    purpose: Annotated[str, typer.Option("--purpose")],
    object_ref: Annotated[list[str] | None, typer.Option("--object-ref")] = None,
    retention: Annotated[str, typer.Option("--retention")] = "",
    reshare: Annotated[bool, typer.Option("--reshare/--no-reshare")] = False,
    signature_status: Annotated[
        FederationMessageSignatureStatus,
        typer.Option("--signature-status"),
    ] = FederationMessageSignatureStatus.UNSIGNED,
    expires_at: Annotated[str | None, typer.Option("--expires-at")] = None,
    box: Annotated[FederationMessageBox, typer.Option("--box")] = FederationMessageBox.OUTBOX,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create a preview-only federation message in a local queue."""
    try:
        parsed_expires = datetime.fromisoformat(expires_at) if expires_at else None
        record = FederationMessageService().create_message(
            message_type=type,
            source_node=source_node,
            target_node=target_node,
            purpose=purpose,
            object_refs=object_ref or [],
            retention=retention,
            reshare=reshare,
            signature_status=signature_status,
            expires_at=parsed_expires,
            box=box,
        )
        payload = {
            "message": record.envelope.model_dump(mode="json"),
            "box": record.box.value,
            "stored_at": record.stored_at.isoformat(),
            "preview_summary": record.preview_summary,
            "audit_recorded": record.audit_recorded,
        }
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Federation message stored: {record.envelope.message_id}")
            typer.echo(f"  Box: {record.box.value}")
            typer.echo("  Mode: preview-only; no automatic import or primary-record mutation")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@inbox_app.command("inspect")
def federation_inbox_inspect_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect preview-only inbox messages."""
    try:
        rows = FederationMessageService().inspect_box(FederationMessageBox.INBOX)
        payload = [_dump_record_summary(row) for row in rows]
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            if not payload:
                typer.echo("No federation inbox messages found.")
                return
            for row in payload:
                typer.echo(
                    f"{row['message_id']}  {row['message_type']}  preview_only={row['preview_only']}  audit_recorded={row['audit_recorded']}"
                )
    except ChronicleError as exc:
        handle_error(exc, json_output)


@inbox_app.command("show")
def federation_inbox_show_cmd(
    message_id: Annotated[str, typer.Option("--message")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show one inbox message."""
    try:
        record = FederationMessageService().get_message(FederationMessageBox.INBOX, message_id)
        payload = {
            "record": record.model_dump(mode="json"),
        }
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            typer.echo(f"{record.envelope.message_id} ({record.envelope.message_type.value})")
            typer.echo(record.preview_summary)
    except ChronicleError as exc:
        handle_error(exc, json_output)


@outbox_app.command("inspect")
def federation_outbox_inspect_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Inspect locally created outbox messages."""
    try:
        rows = FederationMessageService().inspect_box(FederationMessageBox.OUTBOX)
        payload = [_dump_record_summary(row) for row in rows]
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            if not payload:
                typer.echo("No federation outbox messages found.")
                return
            for row in payload:
                typer.echo(
                    f"{row['message_id']}  {row['message_type']}  target={row['target_node']}  preview_only={row['preview_only']}"
                )
    except ChronicleError as exc:
        handle_error(exc, json_output)


federation_app.add_typer(message_app, name="message")
federation_app.add_typer(inbox_app, name="inbox")
federation_app.add_typer(outbox_app, name="outbox")
