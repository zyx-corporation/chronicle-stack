"""Trust model CLI surfaces."""

import json
from datetime import datetime
from typing import Annotated

import typer

from chronicle.errors import ChronicleError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.trust import TrustLevel
from chronicle.services.trust_service import TrustService

trust_app = typer.Typer(help="Node trust model operations.")
node_app = typer.Typer(help="Node profile operations.")


@node_app.command("add")
def trust_node_add_cmd(
    node_id: Annotated[str, typer.Option("--node-id")],
    subject_id: Annotated[str, typer.Option("--subject-id")],
    display_name: Annotated[str, typer.Option("--display-name")] = "",
    public_key_ref: Annotated[str, typer.Option("--public-key-ref")] = "",
    key_rotation_ref: Annotated[str, typer.Option("--key-rotation-ref")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        profile = TrustService().add_node_profile(
            node_id=node_id,
            subject_id=subject_id,
            display_name=display_name,
            public_key_ref=public_key_ref,
            key_rotation_ref=key_rotation_ref,
        )
        if json_output:
            typer.echo(json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Trust node profile stored: {profile.node_id}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@node_app.command("list")
def trust_node_list_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        rows = TrustService().list_node_profiles()
        if json_output:
            typer.echo(json.dumps([row.model_dump(mode="json") for row in rows], ensure_ascii=False, indent=2))
        else:
            if not rows:
                typer.echo("No trust node profiles found.")
                return
            for row in rows:
                typer.echo(f"{row.node_id}  subject={row.subject_id}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@trust_app.command("assert")
def trust_assert_cmd(
    target_node: Annotated[str, typer.Option("--target-node")],
    domain: Annotated[str, typer.Option("--domain")],
    purpose: Annotated[str, typer.Option("--purpose")],
    level: Annotated[TrustLevel, typer.Option("--level")],
    target_subject_id: Annotated[str, typer.Option("--target-subject-id")] = "",
    capability: Annotated[list[str] | None, typer.Option("--capability")] = None,
    context_scope: Annotated[str, typer.Option("--context-scope")] = "",
    expires_at: Annotated[str | None, typer.Option("--expires-at")] = None,
    delegated_actor: Annotated[list[str] | None, typer.Option("--delegated-actor")] = None,
    ai_proxy: Annotated[list[str] | None, typer.Option("--ai-proxy")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        relation = TrustService().assert_relation(
            target_node=target_node,
            target_subject_id=target_subject_id,
            domain=domain,
            purpose=purpose,
            level=level,
            capabilities=capability or [],
            context_scope=context_scope,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            delegated_actor_metadata=_pairs_to_dict(delegated_actor or []),
            ai_proxy_generation_metadata=_pairs_to_dict(ai_proxy or []),
        )
        if json_output:
            typer.echo(json.dumps(relation.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Trust relation asserted: {relation.relation_id}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@trust_app.command("withdraw")
def trust_withdraw_cmd(
    relation_id: Annotated[str, typer.Option("--relation")],
    reason: Annotated[str, typer.Option("--reason")],
    delegated_actor: Annotated[list[str] | None, typer.Option("--delegated-actor")] = None,
    ai_proxy: Annotated[list[str] | None, typer.Option("--ai-proxy")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        relation = TrustService().withdraw_relation(
            relation_id=relation_id,
            reason=reason,
            delegated_actor_metadata=_pairs_to_dict(delegated_actor or []),
            ai_proxy_generation_metadata=_pairs_to_dict(ai_proxy or []),
        )
        if json_output:
            typer.echo(json.dumps(relation.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo(f"Trust relation withdrawn: {relation.relation_id}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@trust_app.command("list")
def trust_list_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        rows = TrustService().list_relations()
        if json_output:
            typer.echo(json.dumps([row.model_dump(mode="json") for row in rows], ensure_ascii=False, indent=2))
        else:
            if not rows:
                typer.echo("No trust relations found.")
                return
            for row in rows:
                typer.echo(
                    f"{row.relation_id}  {row.target_node}  level={row.level.value}  domain={row.domain}  status={row.status.value}"
                )
    except ChronicleError as exc:
        handle_error(exc, json_output)


trust_app.add_typer(node_app, name="node")


def _pairs_to_dict(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        result[key] = value
    return result
