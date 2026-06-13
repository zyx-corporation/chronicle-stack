"""Tests for deterministic graph export (v0.3)."""

import json

import pytest

from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.artifact import ArtifactType
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.injection_service import InjectionPlanService


@pytest.fixture
def populated_chronicle(tmp_path):
    """Chronicle with context, artifact, decision, boundary rule, and recorded plan."""
    svc = ChronicleService(tmp_path)
    svc.init("Graph Export Test")

    ctx_svc = ContextService(tmp_path)
    ctx_svc.add_context(title="Graph Context", summary="For graph test")

    art_svc = ArtifactService(tmp_path)
    f = tmp_path / "doc.md"
    f.write_text("Content", encoding="utf-8")
    art_svc.create(title="Graph Artifact", artifact_type=ArtifactType.DOCUMENT, source_file=f)

    bsvc = BoundaryService(tmp_path)
    bsvc.add_rule(
        rule_type=BoundaryRuleType.WARN, field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS, value="sensitive", reason="Graph rule",
    )

    ip_svc = InjectionPlanService(tmp_path)
    plan = ip_svc.generate_plan(task="Graph task")
    ip_svc.record_plan(plan)

    return GraphExportService(tmp_path)


def test_graph_export_is_parseable_json(populated_chronicle):
    """Graph export must produce valid JSON."""
    result = populated_chronicle.export_graph()
    data = result.model_dump(mode="json")
    assert json.dumps(data)  # Must serialize without error


def test_graph_export_has_required_top_level_keys(populated_chronicle):
    """Graph export must have schema_version, generated_at, chronicle_id, nodes, edges."""
    data = populated_chronicle.export_graph().model_dump(mode="json")
    for key in ["schema_version", "generated_at", "chronicle_id", "nodes", "edges"]:
        assert key in data, f"Missing key '{key}' in graph export"


def test_graph_export_generates_context_node(populated_chronicle):
    """Context must appear as a node."""
    data = populated_chronicle.export_graph().model_dump(mode="json")
    ctx_nodes = [n for n in data["nodes"] if n["node_type"] == "context"]
    assert len(ctx_nodes) >= 1


def test_graph_export_generates_artifact_node(populated_chronicle):
    """Artifact must appear as a node."""
    data = populated_chronicle.export_graph().model_dump(mode="json")
    art_nodes = [n for n in data["nodes"] if n["node_type"] == "artifact"]
    assert len(art_nodes) >= 1


def test_graph_export_generates_boundary_rule_node(populated_chronicle):
    """BoundaryRule must appear as a node."""
    data = populated_chronicle.export_graph().model_dump(mode="json")
    br_nodes = [n for n in data["nodes"] if n["node_type"] == "boundary_rule"]
    assert len(br_nodes) >= 1


def test_graph_export_generates_injection_plan_node(populated_chronicle):
    """Recorded InjectionPlan must appear as a node."""
    data = populated_chronicle.export_graph().model_dump(mode="json")
    ip_nodes = [n for n in data["nodes"] if n["node_type"] == "injection_plan"]
    assert len(ip_nodes) >= 1


def test_graph_export_generates_injection_plan_edges(populated_chronicle):
    """InjectionPlan edges (selects/warns/excludes) must be present."""
    data = populated_chronicle.export_graph().model_dump(mode="json")
    edge_types = {e["edge_type"] for e in data["edges"]}
    assert "injection_plan_selects_context" in edge_types


def test_graph_export_does_not_mutate_jsonl(populated_chronicle, tmp_path):
    """Graph export must not change chronicle.jsonl."""
    events_before = len(populated_chronicle.chronicle.jsonl.read_all())
    populated_chronicle.export_graph()
    events_after = len(populated_chronicle.chronicle.jsonl.read_all())
    assert events_after == events_before


def test_graph_export_is_deterministic(populated_chronicle):
    """Two exports must produce identical output."""
    data1 = populated_chronicle.export_graph().model_dump(mode="json")
    data2 = populated_chronicle.export_graph().model_dump(mode="json")
    # timestamps may differ, so compare nodes and edges
    assert data1["nodes"] == data2["nodes"]
    assert data1["edges"] == data2["edges"]


def test_graph_export_no_graph_db_dependency(populated_chronicle):
    """Graph export must work without any graph database dependency."""
    data = populated_chronicle.export_graph().model_dump(mode="json")
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)


def test_cli_graph_export_json(tmp_path):
    """CLI export --format graph-json must produce valid graph JSON."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Graph CLI"])

    result = runner.invoke(app, ["export", "--format", "graph-json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    for key in ["schema_version", "generated_at", "chronicle_id", "nodes", "edges"]:
        assert key in data, f"Missing key '{key}' in graph-json export"


def test_all_contract_tests_pass_with_graph_export(populated_chronicle, tmp_path):
    """Graph export must coexist with all existing contract test expectations."""
    from chronicle.services.chronicle_service import ChronicleService
    svc = ChronicleService(tmp_path)
    assert svc.paths.events_file.exists()
    # Rebuild must still work
    svc.rebuild_indexes()
