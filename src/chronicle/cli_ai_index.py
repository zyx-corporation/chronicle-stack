"""CLI commands for local placeholder vector and graph index contracts."""

import json
from collections import Counter
from typing import Annotated

import typer

from chronicle.errors import ChronicleError, InvalidMetadataOptionError
from chronicle.interfaces.cli.common import handle_error
from chronicle.models.ai_index import AiIndexStatus, GraphIndexStatus
from chronicle.services.graph_index_service import GraphIndexService
from chronicle.services.vector_index_service import VectorIndexService


ai_index_app = typer.Typer(
    help="Local file-backed placeholder vector and graph index operations.",
    no_args_is_help=True,
)
vector_app = typer.Typer(help="Placeholder vector index operations.")
graph_app = typer.Typer(help="Placeholder graph index operations.")
ai_index_app.add_typer(vector_app, name="vector")
ai_index_app.add_typer(graph_app, name="graph")


def _dump_json(value: object) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2))


def _parse_key_values(values: list[str], option_name: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        key, separator, raw_value = value.partition("=")
        if not separator or not key:
            raise InvalidMetadataOptionError(option_name, value)
        parsed[key] = raw_value
    return parsed


def _status_payload() -> AiIndexStatus:
    vector_service = VectorIndexService()
    vector_status = vector_service.status()
    graph_service = GraphIndexService()
    graph_snapshot = graph_service.snapshot()
    return AiIndexStatus(
        vector=vector_status,
        graph=GraphIndexStatus(
            path=str(graph_service.paths.graph_index_file),
            node_count=len(graph_snapshot.nodes),
            edge_count=len(graph_snapshot.edges),
            external_call_made=False,
        ),
    )


@ai_index_app.command("status")
def ai_index_status_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show local placeholder ai-index status and boundaries."""
    try:
        payload = _status_payload()
        if json_output:
            _dump_json(payload.model_dump(mode="json"))
            return

        typer.echo("Chronicle AI Index Status")
        typer.echo(f"Vector path: {payload.vector.path}")
        typer.echo(f"Vector entries: {payload.vector.entry_count}")
        typer.echo(f"Graph path: {payload.graph.path}")
        typer.echo(f"Graph nodes: {payload.graph.node_count}")
        typer.echo(f"Graph edges: {payload.graph.edge_count}")
        typer.echo("Boundary: local file-backed placeholder derived surfaces only.")
        typer.echo("Boundary: no LLM, no embeddings, no vector DB, no graph DB, no GraphRAG runtime.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@vector_app.command("add")
def vector_add_cmd(
    record: Annotated[str, typer.Option("--record", help="Chronicle record ID to anchor the index entry.")],
    text: Annotated[str, typer.Option("--text", help="Text to index locally.")],
    type: Annotated[str, typer.Option("--type", help="Record type label for the placeholder entry.")] = "event",
    metadata: Annotated[list[str], typer.Option("--metadata", help="Repeatable metadata key=value pairs.")] = [],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Add or replace a local placeholder vector index entry."""
    try:
        entry = VectorIndexService().add_entry(
            record_id=record,
            text=text,
            record_type=type,
            metadata=_parse_key_values(metadata, "metadata"),
        )
        if json_output:
            _dump_json(entry.model_dump(mode="json"))
            return

        typer.echo(f"Vector index entry stored for {entry.record_id}")
        typer.echo(f"Type: {entry.record_type}")
        typer.echo(f"Embedding provider: {entry.embedding_provider}")
        typer.echo("Boundary: external_call_made=false")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@vector_app.command("search")
def vector_search_cmd(
    query: Annotated[str, typer.Option("--query", help="Local placeholder search query.")],
    limit: Annotated[int, typer.Option("--limit", min=1, help="Maximum number of results.")] = 5,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Search local placeholder vector entries with token overlap and substring scoring."""
    try:
        results = VectorIndexService().search(query=query, limit=limit)
        if json_output:
            _dump_json([result.model_dump(mode="json") for result in results])
            return

        if not results:
            typer.echo("No vector index matches found.")
            return
        for result in results:
            typer.echo(f"{result.record_id}  {result.record_type}  score={result.score}")
            typer.echo(f"  {result.text}")
        typer.echo("Boundary: assistive placeholder search only, not correctness proof.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@graph_app.command("add-node")
def graph_add_node_cmd(
    id: Annotated[str, typer.Option("--id", help="Chronicle record ID to anchor the graph node.")],
    label: Annotated[list[str], typer.Option("--label", help="Repeatable graph labels.")] = [],
    property: Annotated[list[str], typer.Option("--property", help="Repeatable property key=value pairs.")] = [],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Add or update a local placeholder graph node."""
    try:
        node = GraphIndexService().add_node(
            node_id=id,
            labels=label,
            properties=_parse_key_values(property, "property"),
        )
        if json_output:
            _dump_json(node.model_dump(mode="json"))
            return

        typer.echo(f"Graph node stored: {node.node_id}")
        typer.echo(f"Labels: {', '.join(node.labels) if node.labels else '(none)'}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@graph_app.command("add-edge")
def graph_add_edge_cmd(
    source: Annotated[str, typer.Option("--source", help="Source Chronicle record ID.")],
    target: Annotated[str, typer.Option("--target", help="Target Chronicle record ID.")],
    relation: Annotated[str, typer.Option("--relation", help="Edge relation label.")],
    property: Annotated[list[str], typer.Option("--property", help="Repeatable property key=value pairs.")] = [],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Add or replace a local placeholder graph edge."""
    try:
        edge = GraphIndexService().add_edge(
            source_id=source,
            target_id=target,
            relation=relation,
            properties=_parse_key_values(property, "property"),
        )
        if json_output:
            _dump_json(edge.model_dump(mode="json"))
            return

        typer.echo(f"Graph edge stored: {edge.source_id} -[{edge.relation}]-> {edge.target_id}")
    except ChronicleError as exc:
        handle_error(exc, json_output)


@graph_app.command("neighbors")
def graph_neighbors_cmd(
    id: Annotated[str, typer.Option("--id", help="Node ID to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List adjacent placeholder graph nodes and edges."""
    try:
        result = GraphIndexService().neighbors(node_id=id)
        if json_output:
            _dump_json(result.model_dump(mode="json"))
            return

        typer.echo(f"Graph neighbors for {result.node_id}")
        typer.echo(f"Outgoing: {len(result.outgoing)}")
        typer.echo(f"Incoming: {len(result.incoming)}")
        label_counts = Counter(label for node in result.neighbors for label in node.labels)
        if result.neighbors:
            typer.echo("Neighbors:")
            for node in result.neighbors:
                labels = ",".join(node.labels) if node.labels else "-"
                typer.echo(f"  {node.node_id} [{labels}]")
        else:
            typer.echo("Neighbors: (none)")
        if label_counts:
            typer.echo(f"Neighbor labels: {dict(sorted(label_counts.items()))}")
        typer.echo("Boundary: local adjacency only, not a graph DB or GraphRAG runtime.")
    except ChronicleError as exc:
        handle_error(exc, json_output)


if __name__ == "__main__":
    ai_index_app()
