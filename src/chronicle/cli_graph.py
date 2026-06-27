"""CLI commands for read-only graph export inspection."""

import json
from collections import Counter
from typing import Annotated

import typer

from chronicle.services.graph_export_service import GraphExportService


graph_app = typer.Typer(help="Read-only graph export inspection commands.")


def _dump_json(value: object) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, indent=2))


@graph_app.command("summary")
def graph_summary_cmd(
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show a summary of the derived graph export."""
    graph = GraphExportService().export_graph()
    node_counts = Counter(node.node_type for node in graph.nodes)
    edge_counts = Counter(edge.edge_type for edge in graph.edges)
    payload = {
        "schema_version": graph.schema_version,
        "contract_version": (
            graph.export_contract.contract_version if graph.export_contract is not None else None
        ),
        "chronicle_id": graph.chronicle_id,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "node_types": dict(sorted(node_counts.items())),
        "edge_types": dict(sorted(edge_counts.items())),
        "incremental_mode": (
            graph.export_contract.incremental_mode if graph.export_contract is not None else None
        ),
        "incremental_expectations": (
            graph.export_contract.incremental_expectations if graph.export_contract is not None else []
        ),
    }
    if json_output:
        _dump_json(payload)
        return

    typer.echo("Graph Summary")
    typer.echo(f"Chronicle ID: {graph.chronicle_id}")
    if graph.export_contract is not None:
        typer.echo(f"Contract: {graph.export_contract.contract_version} ({graph.export_contract.export_family})")
    typer.echo(f"Nodes: {len(graph.nodes)}")
    typer.echo(f"Edges: {len(graph.edges)}")
    typer.echo("")
    typer.echo("Node types:")
    for node_type, count in payload["node_types"].items():
        typer.echo(f"  {node_type}: {count}")
    typer.echo("")
    typer.echo("Edge types:")
    for edge_type, count in payload["edge_types"].items():
        typer.echo(f"  {edge_type}: {count}")


@graph_app.command("nodes")
def graph_nodes_cmd(
    type: Annotated[str | None, typer.Option("--type", help="Filter by node_type.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List derived graph nodes."""
    graph = GraphExportService().export_graph()
    nodes = [node for node in graph.nodes if type is None or node.node_type == type]
    if json_output:
        _dump_json([node.model_dump(mode="json") for node in nodes])
        return

    if not nodes:
        typer.echo("No graph nodes found.")
        return
    for node in nodes:
        title = f" — {node.title}" if node.title else ""
        typer.echo(f"{node.node_id}  {node.node_type}  {node.source_id}{title}")


@graph_app.command("edges")
def graph_edges_cmd(
    type: Annotated[str | None, typer.Option("--type", help="Filter by edge_type.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List derived graph edges."""
    graph = GraphExportService().export_graph()
    edges = [edge for edge in graph.edges if type is None or edge.edge_type == type]
    if json_output:
        _dump_json([edge.model_dump(mode="json") for edge in edges])
        return

    if not edges:
        typer.echo("No graph edges found.")
        return
    for edge in edges:
        typer.echo(f"{edge.edge_id}  {edge.edge_type}  {edge.from_node_id} -> {edge.to_node_id}")
