"""Deterministic graph export service (v0.3).

Builds a graph-json view from Chronicle records.  No graph database,
no vector database, no embeddings, no LLM calls.
"""

from datetime import datetime, timezone
from pathlib import Path

from chronicle.models.graph import GraphEdge, GraphExport, GraphNode
from chronicle.services.chronicle_service import ChronicleService


def _nid(prefix: str, source_id: str) -> str:
    return f"n_{prefix}_{source_id}"


def _eid(prefix: str, from_id: str, to_id: str) -> str:
    return f"e_{prefix}_{from_id}_{to_id}"


class GraphExportService:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def export_graph(self) -> GraphExport:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, versions = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        boundary_rules = self.chronicle.index.load_boundary_rules()

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        cid = metadata.chronicle_id

        # Chronicle node
        chr_nid = _nid("chronicle", cid)
        nodes.append(GraphNode(
            node_id=chr_nid, node_type="chronicle", source_id=cid,
            title=metadata.title,
        ))

        for event in events:
            evt_nid = _nid("event", event.event_id)
            nodes.append(GraphNode(
                node_id=evt_nid, node_type="event", source_id=event.event_id,
                title=event.summary, summary=event.event_type.value,
            ))
            edges.append(GraphEdge(
                edge_id=_eid("chronicle_has_event", chr_nid, evt_nid),
                edge_type="chronicle_has_event", from_node_id=chr_nid, to_node_id=evt_nid,
            ))

            # Event → X edges based on payload
            if event.artifact_id:
                art_nid = _nid("artifact", event.artifact_id)
                edges.append(GraphEdge(
                    edge_id=_eid("event_artifact", evt_nid, art_nid),
                    edge_type="event_creates_artifact" if event.event_type.value == "artifact_created"
                    else "event_updates_artifact",
                    from_node_id=evt_nid, to_node_id=art_nid,
                ))
            if event.decision_id:
                dec_nid = _nid("decision", event.decision_id)
                edges.append(GraphEdge(
                    edge_id=_eid("event_records_decision", evt_nid, dec_nid),
                    edge_type="event_records_decision", from_node_id=evt_nid, to_node_id=dec_nid,
                ))
            if event.rde_record_id:
                rde_nid = _nid("rde_diff_record", event.rde_record_id)
                edges.append(GraphEdge(
                    edge_id=_eid("event_records_rde", evt_nid, rde_nid),
                    edge_type="event_records_rde", from_node_id=evt_nid, to_node_id=rde_nid,
                ))
            if event.event_type.value == "injection_plan_recorded" and "injection_plan" in event.payload:
                ip = event.payload["injection_plan"]
                ip_id = ip["plan_id"]
                ip_nid = _nid("injection_plan", ip_id)
                edges.append(GraphEdge(
                    edge_id=_eid("event_records_injection_plan", evt_nid, ip_nid),
                    edge_type="event_records_injection_plan", from_node_id=evt_nid, to_node_id=ip_nid,
                ))

        # Context nodes
        for ctx in contexts.values():
            ctx_nid = _nid("context", ctx.context_id)
            nodes.append(GraphNode(
                node_id=ctx_nid, node_type="context", source_id=ctx.context_id,
                title=ctx.title, summary=ctx.summary,
                metadata={"scope": ctx.scope.value, "visibility": ctx.visibility_hint.value},
            ))
            if ctx.source:
                src_nid = _nid("source_provenance", ctx.context_id)
                nodes.append(GraphNode(
                    node_id=src_nid, node_type="source_provenance", source_id=ctx.context_id,
                    title=ctx.source.source_type,
                    metadata={"tool": ctx.source.source_tool or "", "session": ctx.source.source_session or ""},
                ))
                edges.append(GraphEdge(
                    edge_id=_eid("context_has_source", ctx_nid, src_nid),
                    edge_type="context_has_source", from_node_id=ctx_nid, to_node_id=src_nid,
                ))

        # Artifact nodes
        for art in artifacts.values():
            art_nid = _nid("artifact", art.artifact_id)
            nodes.append(GraphNode(
                node_id=art_nid, node_type="artifact", source_id=art.artifact_id,
                title=art.title, summary=art.artifact_type.value,
                metadata={"visibility": art.visibility_hint.value},
            ))
            for ver in versions.get(art.artifact_id, []):
                ver_nid = _nid("artifact_version", ver.version_id)
                nodes.append(GraphNode(
                    node_id=ver_nid, node_type="artifact_version", source_id=ver.version_id,
                    title=ver.change_summary,
                    metadata={"source_event_id": ver.source_event_id},
                ))
                edges.append(GraphEdge(
                    edge_id=_eid("artifact_has_version", art_nid, ver_nid),
                    edge_type="artifact_has_version", from_node_id=art_nid, to_node_id=ver_nid,
                ))
                edges.append(GraphEdge(
                    edge_id=_eid("version_source_event", ver_nid, _nid("event", ver.source_event_id)),
                    edge_type="artifact_version_source_event",
                    from_node_id=ver_nid, to_node_id=_nid("event", ver.source_event_id),
                ))

        # Decision nodes
        for dec in decisions.values():
            dec_nid = _nid("decision", dec.decision_id)
            nodes.append(GraphNode(
                node_id=dec_nid, node_type="decision", source_id=dec.decision_id,
                title=dec.reason or dec.decision_type.value,
                metadata={"decision_type": dec.decision_type.value, "event_id": dec.event_id or ""},
            ))
            if dec.event_id:
                edges.append(GraphEdge(
                    edge_id=_eid("decision_source_event", dec_nid, _nid("event", dec.event_id)),
                    edge_type="decision_source_event",
                    from_node_id=dec_nid, to_node_id=_nid("event", dec.event_id),
                ))

        # BoundaryRule nodes
        for rule in boundary_rules.values():
            br_nid = _nid("boundary_rule", rule.rule_id)
            val = rule.value if isinstance(rule.value, str) else ", ".join(rule.value)
            nodes.append(GraphNode(
                node_id=br_nid, node_type="boundary_rule", source_id=rule.rule_id,
                title=rule.reason or f"{rule.rule_type.value} {rule.field.value} {rule.operator.value} {val}",
                metadata={"rule_type": rule.rule_type.value, "field": rule.field.value, "operator": rule.operator.value},
            ))

        # Recorded InjectionPlan nodes and edges
        for event in events:
            if event.event_type.value == "injection_plan_recorded" and "injection_plan" in event.payload:
                ip = event.payload["injection_plan"]
                ip_id = ip["plan_id"]
                ip_nid = _nid("injection_plan", ip_id)
                nodes.append(GraphNode(
                    node_id=ip_nid, node_type="injection_plan", source_id=ip_id,
                    title=ip["task"],
                ))
                for ref in ip.get("selected", []):
                    ctx_nid = _nid("context", ref["context_id"])
                    edges.append(GraphEdge(
                        edge_id=_eid("ip_selects", ip_nid, ctx_nid),
                        edge_type="injection_plan_selects_context",
                        from_node_id=ip_nid, to_node_id=ctx_nid,
                    ))
                for ref in ip.get("warned", []):
                    ctx_nid = _nid("context", ref["context_id"])
                    edges.append(GraphEdge(
                        edge_id=_eid("ip_warns", ip_nid, ctx_nid),
                        edge_type="injection_plan_warns_context",
                        from_node_id=ip_nid, to_node_id=ctx_nid,
                        metadata={"warnings": ref.get("warnings", [])},
                    ))
                for ref in ip.get("excluded", []):
                    ctx_nid = _nid("context", ref["context_id"])
                    edges.append(GraphEdge(
                        edge_id=_eid("ip_excludes", ip_nid, ctx_nid),
                        edge_type="injection_plan_excludes_context",
                        from_node_id=ip_nid, to_node_id=ctx_nid,
                    ))

        # Deterministic sort
        nodes.sort(key=lambda n: (n.node_type, n.source_id))
        edges.sort(key=lambda e: (e.edge_type, e.from_node_id, e.to_node_id))

        return GraphExport(
            generated_at=datetime.now(timezone.utc).astimezone(),
            chronicle_id=cid,
            nodes=nodes,
            edges=edges,
        )
